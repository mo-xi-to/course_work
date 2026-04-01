import os
import json
import requests
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

import config
import logger
from fma_db import db
from tools import YANDEX_TOOL_SCHEMAS, AVAILABLE_FUNCTIONS

logger = logger.get_logger("Agent")

load_dotenv()

def load_system_prompt() -> str:
    """
    Загружает текст системного промпта из внешнего файла.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, config.SYSTEM_PROMPT_PATH)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            logger.info(f"Системные инструкции загружены успешно (длина: {len(content)} симв.)")
            return content
    except FileNotFoundError:
        logger.error(f"Файл инструкций не найден по пути: {file_path}")
        return "Ты профессиональный врач-анатом. Отвечай на русском языке, используя базу FMA."

def call_yandex_api(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Выполняет сетевой запрос к API Yandex Foundation Models.
    Обрабатывает логику Parallel Tool Calling.
    """
    api_key = os.getenv("YANDEX_KEY")
    folder_id = os.getenv("YANDEX_FOLDER_ID")
    
    if not api_key or not folder_id:
        logger.critical("В файле .env отсутствуют YANDEX_KEY или YANDEX_FOLDER_ID")
        raise ValueError("Ключи API не настроены.")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {api_key}",
        "x-folder-id": folder_id
    }
    
    payload = {
        "modelUri": config.YANDEX_MODEL_URI,
        "completionOptions": {
            "stream": False,
            "temperature": 0.1,
            "maxTokens": 4000
        },
        "messages": messages,
        "tools": YANDEX_TOOL_SCHEMAS
    }

    try:
        response = requests.post(config.YANDEX_URL, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Ошибка сетевого запроса к Яндексу: {e}")
        return {"type": "error", "text": f"Ошибка связи с API: {e}"}
    
    result = response.json()
    message = result['result']['alternatives'][0]['message']
    
    if 'toolCallList' in message:
        return {
            "type": "tool_call", 
            "calls": message['toolCallList']['toolCalls'],
            "raw_message": message
        }
    else:
        return {
            "type": "text", 
            "text": message.get('text', '')
        }

def run_anatomy_agent(user_prompt: str) -> str:
    """
    Основная логика многошагового рассуждения агента.
    Реализует цикл до 15 итераций с защитой от повторных вызовов.
    """
    if not user_prompt.strip():
        return "Запрос пуст."

    logger.info(f"Новый запрос пользователя: '{user_prompt[:50]}...'")
    
    system_instruction = load_system_prompt()
    messages = [
        {"role": "system", "text": system_instruction},
        {"role": "user", "text": user_prompt}
    ]

    calls_history: List[str] = []

    for step in range(15):
        logger.info(f"Шаг рассуждения {step + 1}/15")
        
        response = call_yandex_api(messages)
        
        if response["type"] == "error":
            return f"ОШИБКА: {response['text']}"
            
        elif response["type"] == "text":
            logger.info("Агент сформировал финальный ответ.")
            return response["text"]
            
        elif response["type"] == "tool_call":
            messages.append(response["raw_message"])
            
            combined_results = []
            calls = response["calls"]
            logger.info(f"Модель инициировала {len(calls)} вызовов функций.")

            for call in calls:
                fn_name = call["functionCall"]["name"]
                args = call["functionCall"]["arguments"]
                
                call_key = f"{fn_name}_{args}"
                
                if call_key in calls_history:
                    logger.warning(f"Пресечена попытка повторного вызова: {call_key}")
                    result = "ОШИБКА: Эти данные уже были получены. Прямой связи нет. Смени стратегию поиска."
                else:
                    calls_history.append(call_key)
                    if fn_name in AVAILABLE_FUNCTIONS:
                        try:
                            logger.info(f"Выполнение инструмента: {fn_name}")
                            result = AVAILABLE_FUNCTIONS[fn_name](**args)
                        except Exception as e:
                            logger.error(f"Ошибка внутри инструмента {fn_name}: {e}")
                            result = f"Ошибка выполнения: {e}"
                    else:
                        logger.error(f"Модель вызвала несуществующий инструмент: {fn_name}")
                        result = "Инструмент не найден."
                
                combined_results.append(f"--- Результат {fn_name} ---\n{result}")

            messages.append({
                "role": "user",
                "text": "ДАННЫЕ ИЗ БАЗЫ FMA:\n\n" + "\n\n".join(combined_results) + "\n\nПроанализируй данные и ответь."
            })
                
    logger.error("Агент не смог завершить разбор за 15 шагов.")
    return "ОШИБКА: Превышен лимит итераций рассуждения."

if __name__ == "__main__": 
    logger.setup_logging()
    print("\nАнатомический ассистентЭ")
    
    while True:
        try:
            query = input("\nВопрос: ")
            if query.lower() in ["выход", "exit", "стоп"]:
                break
            
            print("\n" + "-"*30)
            print(run_anatomy_agent(query))
            print("-"*30)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.critical(f"Непредвиденный сбой: {e}", exc_info=True)