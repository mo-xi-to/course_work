import os
import json
import requests
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

import config
from fma_db import db
from tools import YANDEX_TOOL_SCHEMAS, AVAILABLE_FUNCTIONS

load_dotenv()

def load_system_prompt() -> str:
    """Загружает текст системного промпта из внешнего текстового файла instructions.txt."""
    try:
        with open(config.SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "Ты профессиональный врач-анатом. Отвечай на русском языке, используя базу FMA." 

def call_yandex_api(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Выполняет прямой сетевой запрос к API Yandex Foundation Models.
    Обрабатывает историю диалога и передает схемы инструментов.
    """
    api_key = os.getenv("YANDEX_KEY")
    folder_id = os.getenv("YANDEX_FOLDER_ID")
    
    if not api_key or not folder_id:
        raise ValueError("Ошибка: В файле .env не заполнены YANDEX_KEY или YANDEX_FOLDER_ID")

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

    response = requests.post(config.YANDEX_URL, headers=headers, json=payload, timeout=90)
    
    if response.status_code != 200:
        return {"type": "error", "text": f"API Error {response.status_code}: {response.text}"}
    
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
    Запускает многошаговый цикл рассуждения агента.
    Поддерживает до 15 итераций и защищает от зацикливания.
    """
    if not user_prompt.strip():
        return "Запрос не может быть пустым."

    system_instruction = load_system_prompt()
    
    messages = [
        {"role": "system", "text": system_instruction},
        {"role": "user", "text": user_prompt}
    ]

    print(f"\n[АГЕНТ] Запуск разбора через YandexGPT...")
    
    calls_history: List[str] = []

    for step in range(15):
        response = call_yandex_api(messages)
        
        if response["type"] == "error":
            return f"ОШИБКА: {response['text']}"
            
        elif response["type"] == "text":
            return response["text"]
            
        elif response["type"] == "tool_call":
            messages.append(response["raw_message"])
            
            combined_results = []
            calls = response["calls"]
            print(f"[ШАГ {step+1}] Модель запрашивает {len(calls)} инструментов...")

            for call in calls:
                fn_name = call["functionCall"]["name"]
                args = call["functionCall"]["arguments"]
                
                call_key = f"{fn_name}_{args}"
                
                if call_key in calls_history:
                    print(f"ПРЕСЕЧЕНО ПОВТОРЕНИЕ: {fn_name}")
                    result = "ОШИБКА: Эти данные уже были получены ранее. Прямой связи нет. Смени стратегию поиска."
                else:
                    calls_history.append(call_key)
                    if fn_name in AVAILABLE_FUNCTIONS:
                        try:
                            print(f"Выполняю: {fn_name}({args})")
                            result = AVAILABLE_FUNCTIONS[fn_name](**args)
                        except Exception as e:
                            result = f"Ошибка выполнения функции: {e}"
                    else:
                        result = "Инструмент не найден в системе."
                
                combined_results.append(f"--- Результат {fn_name} ---\n{result}")

            messages.append({
                "role": "user",
                "text": "ДАННЫЕ ИЗ БАЗЫ FMA:\n\n" + "\n\n".join(combined_results) + "\n\nПроанализируй данные и ответь."
            })
                
    return "ОШИБКА: Превышен лимит итераций рассуждения (15 шагов)."

if __name__ == "__main__":
    print("\n" + "="*50)
    print(" АНАТОМИЧЕСКИЙ АССИСТЕНТ (YANDEX GPT + FMA) ")
    print(" Напишите 'выход' для завершения.")
    print("="*50)
    
    while True:
        try:
            query = input("\nВопрос: ")
            if query.lower() in ["выход", "exit", "стоп", "quit"]:
                print("Завершение сессии...")
                break
            
            answer = run_anatomy_agent(query)
            print(f"\nОТВЕТ:\n{answer}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\nКритическая ошибка: {e}")