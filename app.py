import os
import time
import gradio as gr
from collections import defaultdict

import logger
from llm_agent import run_anatomy_agent

logger.setup_logging()
logger = logger.get_logger("WebUI")

os.environ["NO_PROXY"] = "127.0.0.1,localhost"

user_limits = defaultdict(lambda: {"last_reset": time.time(), "count": 0})
DAILY_LIMIT = 50

def check_rate_limit(request: gr.Request) -> bool:
    client_ip = request.client.host
    now = time.time()
    user_data = user_limits[client_ip]

    if now - user_data["last_reset"] > 86400:
        logger.info(f"Лимит сброшен для IP: {client_ip}")
        user_data["last_reset"] = now
        user_data["count"] = 0

    if user_data["count"] >= DAILY_LIMIT:
        logger.warning(f"Отказ в доступе (лимит): {client_ip}")
        return False 
    
    user_data["count"] += 1
    logger.info(f"Запрос {user_data['count']}/{DAILY_LIMIT} от {client_ip}")
    return True

def chat_function(message: str, history, request: gr.Request) -> str:
    if not check_rate_limit(request):
        return "Лимит запросов исчерпан. Пожалуйста, попробуйте завтра."
    
    if not message.strip():
        return "Введите запрос."
    
    logger.info(f"Обработка сообщения: {message[:30]}...")
    return run_anatomy_agent(message)

demo = gr.ChatInterface(
    fn=chat_function, 
    title="Анатомический Ассистент FMA",
    description="Интеллектуальная система на базе YandexGPT и онтологии FMA.",
    theme=gr.themes.Default()
)

if __name__ == "__main__":
    logger.info("Gradio запускается...")
    demo.launch(server_name="0.0.0.0", server_port=7860)