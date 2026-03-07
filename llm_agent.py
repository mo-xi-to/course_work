import json
import os
import httpx
import openai
from openai import OpenAI
from dotenv import load_dotenv

import config
from tools import TOOL_SCHEMAS, AVAILABLE_FUNCTIONS

load_dotenv()

def get_anatomy_client(base_url, api_key):
    """
    Создает сетевой клиент. 
    Отключает системные прокси для стабильного соединения.
    """
    http_client = httpx.Client(trust_env=False)
    return OpenAI(base_url=base_url, api_key=api_key, http_client=http_client)

def run_anatomy_agent(user_prompt: str, model_alias=config.CURRENT_MODEL):
    """
    Основная логика агента с многошаговым выводом.
    """
    model_id = config.MODELS.get(model_alias)
    if not model_id:
        return f"ОШИБКА: Модель {model_alias} не найдена в конфигурации."

    api_key = os.getenv("OPENROUTER_KEY")
    client = get_anatomy_client(config.OPENROUTER_URL, api_key)

    messages = [
        {
            "role": "system", 
            "content": (
                "Ты эксперт-анатом. Отвечай на русском. "
                "1. Сначала найди ID органа через 'search_anatomical_entity'. "
                "2. Используй этот ID для получения деталей в других инструментах. "
                "3. Ты можешь делать до 5 шагов поиска. Если данных в базе нет - не выдумывай."
            )
        },
        {"role": "user", "content": user_prompt}
    ]

    print(f"\n[АГЕНТ] Работа с моделью: {model_alias}")

    for step in range(5):
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
            return f"ОШИБКА: Проблема API ({e.status_code})."
        except Exception as e:
            return f"ОШИБКА: {type(e).__name__}"

        msg = response.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            return msg.content

        print(f"[ШАГ {step+1}] Вызов инструментов...")
        
        for tool_call in msg.tool_calls:
            fn_name = tool_call.function.name
            
            if fn_name not in AVAILABLE_FUNCTIONS:
                result = f"ОШИБКА: Инструмент {fn_name} не найден."
            else:
                try:
                    args = json.loads(tool_call.function.arguments)
                    print(f"   ⚙️ {fn_name}({args})")
                    result = AVAILABLE_FUNCTIONS[fn_name](**args)
                except Exception as e:
                    result = f"ОШИБКА выполнения: {e}"

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": fn_name,
                "content": str(result)
            })
            
    return "ОШИБКА: Превышен лимит шагов рассуждения."

if __name__ == "__main__":
    print("\nАнатомический ассистент запущен")
    while True:
        q = input("\nВопрос: ")
        if q.lower() in ["выход", "exit", "стоп"]:
            break
        print(run_anatomy_agent(q))