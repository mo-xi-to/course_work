import time
from llm_agent import run_anatomy_agent

TEST_QUESTIONS = [
    {"level": "1. Простой поиск", "query": "Найди идентификатор FMA для желудка (Stomach)."},
    {"level": "2. Структурный состав", "query": "Из каких основных частей состоит сердце?"},
    {"level": "3. Функциональные связи", "query": "Какие артерии кровоснабжают аорту и какой нерв ею управляет?"},
    {"level": "4. Логический вывод", "query": "Если голова есть, обязан ли мозг быть на месте? Докажи по FMA."},
    {"level": "5. Магистральные цепочки", "query": "Связана ли кровь в большом пальце стопы с аортой? Докажи через цепочку сосудов."}
]

def run_system_evaluation():
    """Проводит оценку качества ответов и скорости работы ассистента."""
    report_data = []
    
    print(f"Запуск оценки системы (YandexGPT + FMA)...")
    print(f"Будет выполнено {len(TEST_QUESTIONS)} тестов.\n")

    for item in TEST_QUESTIONS:
        level = item["level"]
        query = item["query"]
        print(f"Тестирую уровень: {level}...")
        
        start_time = time.time()
        try:
            answer = run_anatomy_agent(query)
            duration = round(time.time() - start_time, 2)
            
            if answer.startswith("ОШИБКА:"):
                status = "ОШИБКА"
            else:
                status = "УСПЕХ"
            
            report_data.append({
                "level": level,
                "query": query,
                "time": f"{duration}с",
                "status": status,
                "answer": answer.replace('\n', ' ') + "..."
            })
            print(f"[{status}] завершено за {duration}с")
            
        except Exception as e:
            report_data.append({
                "level": level, "query": query, "time": "-", "status": "КРАХ", "answer": str(e)
            })
            print(f"[КРАХ] Произошла системная ошибка: {e}")

        time.sleep(5)

    report_filename = "system_evaluation.md"
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write("# Отчет об оценке анатомического ассистента\n\n")
        f.write("Данный отчет содержит результаты тестирования логики многошагового вывода на базе YandexGPT и FMA.\n\n")
        f.write("| Уровень сложности | Время | Статус | Запрос | Сокращенный ответ |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        
        for r in report_data:
            line = f"| {r['level']} | {r['time']} | {r['status']} | {r['query']} | {r['answer']} |\n"
            f.write(line)
    
    print(f"\nОценка завершена! Результаты сохранены в файл: {report_filename}")

if __name__ == "__main__":
    run_system_evaluation()