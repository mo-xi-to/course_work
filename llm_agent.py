import os
import json
import httpx
import openai
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Optional, Any

import config
from fma_db import db
from tools import TOOL_SCHEMAS, AVAILABLE_FUNCTIONS

load_dotenv()

def get_anatomy_client(base_url: str, api_key: str) -> OpenAI:
    """
    Инициализирует сетевой клиент для работы с API.
    trust_env=False отключает системные прокси для предотвращения ошибок соединения.
    """
    http_client = httpx.Client(trust_env=False)
    return OpenAI(base_url=base_url, api_key=api_key, http_client=http_client)

def run_anatomy_agent(user_prompt: str, model_alias: str = config.CURRENT_MODEL) -> str:
    """
    Основная логика многошагового агента. 
    Реализует цикл рассуждения (до 15 шагов) с защитой от зацикливания.
    """
    model_id = config.MODELS.get(model_alias)
    if not model_id:
        return f"ОШИБКА: Модель {model_alias} не найдена в конфигурации."

    api_key = os.getenv("OPENROUTER_KEY")
    if not api_key:
        return "ОШИБКА: API-ключ не найден. Проверьте файл .env"

    client = get_anatomy_client(config.OPENROUTER_URL, api_key)

    messages = [
        {
            "role": "system", 
            "content": (
                "Ты - эксперт по анатомической логике FMA. Твоя задача — доказать структурную связь между X и Y.\n"
                "СТРАТЕГИЯ РАБОТЫ:\n"
                "1. Сначала найди уникальные идентификаторы (FMAID) для обоих объектов.\n"
                "2. Вызови инструмент 'get_all_entity_relations' для обоих ID. Это обязательный шаг для глубокого анализа.\n"
                "3. ВНИМАНИЕ: Если ты видишь название или ID одного объекта в свойствах другого "
                "(особенно в блоке 'СВЯЗАННЫЕ СТРУКТУРЫ' или 'part of') - СВЯЗЬ ДОКАЗАНА.\n"
                "4. ПРАВИЛО ОСТАНОВКИ: Как только связь обнаружена, немедленно прекращай поиск и пиши ответ.\n"
                "5. ПРАВИЛО ПОВТОРОВ: Если инструмент вернул пустой результат, запрещено запрашивать его снова для того же ID."
            )
        },
        {"role": "user", "content": user_prompt}
    ]

    print(f"\n[АГЕНТ] Работа с моделью: {model_alias}")

    calls_history: List[str] = []

    for step in range(15):
        try:
            response = client.chat.completions.create(
                model=model_id,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                timeout=180.0
            )
        except openai.RateLimitError:
            return "ОШИБКА: Лимит запросов превышен (429)."
        except openai.APIStatusError as e:
            if e.status_code == 402:
                return "ОШИБКА: Ограничение провайдера (402)."
            return f"ОШИБКА: Проблема на стороне API ({e.status_code})."
        except Exception as e:
            return f"ОШИБКА СЕТИ: {type(e).__name__}"

        response_message = response.choices[0].message
        messages.append(response_message)

        if not response_message.tool_calls:
            return str(response_message.content)

        print(f"[ШАГ {step+1}] Обработка запросов инструментов...")
        
        for tool_call in response_message.tool_calls:
            fn_name = tool_call.function.name
            
            try:
                args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                print("   [!] Ошибка декодирования аргументов.")
                continue

            call_key = f"{fn_name}_{args.get('fma_id', args.get('label'))}"

            if call_key in calls_history:
                print(f"БЛОКИРОВКА ПОВТОРА: {fn_name}")
                result = (
                    "КРИТИЧЕСКАЯ ОШИБКА: Повторный вызов этого инструмента с теми же данными запрещен. "
                    "Этих данных здесь нет. Смени стратегию поиска: исследуй другой объект или "
                    "проверь иерархию (part of) для второго объекта запроса."
                )
            else:
                calls_history.append(call_key)
                if fn_name not in AVAILABLE_FUNCTIONS:
                    result = "ОШИБКА: Инструмент не найден в системе."
                else:
                    try:
                        print(f"{fn_name}({args})")
                        result = AVAILABLE_FUNCTIONS[fn_name](**args)
                    except Exception as e:
                        result = f"ОШИБКА ВЫПОЛНЕНИЯ: {e}"

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": fn_name,
                "content": str(result)
            })
            
    return "ОШИБКА: Превышен лимит итераций рассуждения (15 шагов)."


if __name__ == "__main__":

    
    print("\n" + "="*50)
    print("АНАТОМИЧЕСКИЙ АССИСТЕНТ ЗАПУЩЕН")
    print("Напишите 'выход' для завершения.")
    print("="*50)

    while True:
        try:
            q = input("\nВопрос: ")
            if q.lower() in ["выход", "exit", "стоп", "quit"]:
                print("Завершение сессии...")
                break
            
            if not q.strip():
                continue

            answer = run_anatomy_agent(q)
            print(f"\nОТВЕТ:\n{answer}")
            
        except KeyboardInterrupt:
            break