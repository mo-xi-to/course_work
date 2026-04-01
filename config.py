import os
import logger
from dotenv import load_dotenv

logger = logger.get_logger("Config")

load_dotenv()

YANDEX_KEY = os.getenv("YANDEX_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")

YANDEX_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

if YANDEX_FOLDER_ID:
    YANDEX_MODEL_URI = f"gpt://{YANDEX_FOLDER_ID}/yandexgpt/latest"
else:
    YANDEX_MODEL_URI = None
    logger.warning("YANDEX_FOLDER_ID не обнаружен в .env. Работа с YandexGPT будет невозможна.")

FMA_DB_PATH = "data/FMA.csv"
SYSTEM_PROMPT_PATH = "prompt/instructions.txt"

def check_config():
    """Проверяет наличие всех критически важных параметров"""
    missing_vars = []
    if not YANDEX_KEY: missing_vars.append("YANDEX_KEY")
    if not YANDEX_FOLDER_ID: missing_vars.append("YANDEX_FOLDER_ID")
    
    if missing_vars:
        logger.error(f"Отсутствуют переменные в .env: {', '.join(missing_vars)}")
        return False
    
    if not os.path.exists(FMA_DB_PATH):
        logger.error(f"Файл базы данных не найден по пути: {FMA_DB_PATH}")
        return False
        
    logger.info("Конфигурация успешно загружена и проверена.")
    return True