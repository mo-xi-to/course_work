import os
from dotenv import load_dotenv

load_dotenv()

YANDEX_KEY = os.getenv("YANDEX_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")

YANDEX_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
YANDEX_MODEL_URI = f"gpt://{YANDEX_FOLDER_ID}/yandexgpt/latest"

FMA_DB_PATH = "data/FMA.csv"
SYSTEM_PROMPT_PATH = "prompts/instructions.txt"