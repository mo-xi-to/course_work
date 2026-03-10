import os

OPENROUTER_KEY = os.getenv("OPENROUTER_KEY", "КЛЮЧ")
OPENROUTER_URL = "https://openrouter.ai/api/v1"
FMA_CSV_PATH = "FMA.csv"

MODELS = {
    "Qwen-3-235B": "qwen/qwen3-vl-235b-a22b-thinking",
    "Llama-3.3-70B": "meta-llama/llama-3.3-70b-instruct:free",
    "Gemma-3-27B": "google/gemma-3-27b-it:free",
    "GPT-OSS-120B": "openai/gpt-oss-120b:free",
    "Step-3.5-Flash": "stepfun/step-3.5-flash:free",
    "GLM-4.5-Air": "z-ai/glm-4.5-air:free",
    "Nemotron-Nano": "nvidia/nemotron-nano-12b-v2-vl:free",
}

CURRENT_MODEL = "Qwen-3-235B"