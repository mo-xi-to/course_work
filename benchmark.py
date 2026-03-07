import time
import config
from llm_agent import run_anatomy_agent

TEST_QUESTIONS = [
    {"level": "1. Поиск", "query": "Найди идентификатор FMA для желудка (Stomach)."},
    {"level": "2. Состав", "query": "Из каких основных частей состоит сердце и к какой системе оно относится?"},
    {"level": "3. Сосуды", "query": "Какие артерии кровоснабжают аорту и какой нерв ею управляет?"},
    {"level": "4. Разбор", "query": "Опиши структуру аорты, её ветви и положение в иерархии организма."}
]

def run_benchmark():
    """Сравнительный анализ всех моделей из конфига."""
    report_data = []
    models_to_test = list(config.MODELS.keys())
    
    print(f"Запуск теста для {len(models_to_test)} моделей...")

    for alias in models_to_test:
        print(f"\nТЕСТИРУЮ: {alias}")
        
        for item in TEST_QUESTIONS:
            level = item["level"]
            query = item["query"]
            print(f"Уровень {level}...")
            
            start_time = time.time()
            try:
                answer = run_anatomy_agent(query, model_alias=alias)
                duration = round(time.time() - start_time, 2)
                
                if answer.startswith("ОШИБКА:"):
                    status = "ОШИБКА"
                else:
                    status = "УСПЕХ"
                
                report_data.append({
                    "model": alias,
                    "level": level,
                    "time": f"{duration}с",
                    "status": status,
                    "answer": answer[:200].replace('\n', ' ') + "..."
                })
                print(f"[{status}] за {duration}с")
                
            except Exception as e:
                report_data.append({
                    "model": alias, "level": level, "time": "-", "status": "КРАХ", "answer": str(e)[:100]
                })

            time.sleep(20)

    with open("benchmark_results.md", "w", encoding="utf-8") as f:
        f.write("# Результаты тестирования моделей\n\n")
        f.write("| Модель | Уровень | Время | Статус | Сокращенный ответ |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        
        for r in report_data:
            line = f"| {r['model']} | {r['level']} | {r['time']} | {r['status']} | {r['answer']} |\n"
            f.write(line)
    
    print(f"\nОтчет создан: benchmark_results.md")

if __name__ == "__main__":
    run_benchmark()