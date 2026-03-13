import os
import gradio as gr
from llm_agent import run_anatomy_agent

os.environ["NO_PROXY"] = "127.0.0.1,localhost"
os.environ["http_proxy"] = ""
os.environ["https_proxy"] = ""

def chat_function(message: str, history):
    """
    Функция-обработчик сообщений для интерфейса Gradio.
    Принимает текст пользователя и возвращает ответ от ИИ-агента.
    """
    if not message.strip():
        return "Пожалуйста, введите анатомический запрос."
    
    answer = run_anatomy_agent(message)
    return answer

demo = gr.ChatInterface(
    fn=chat_function, 
    title="Анатомический Ассистент FMA",
    description=(
        "Интеллектуальная система анатомического разбора на базе YandexGPT и онтологии FMA. "
        "Ассистент умеет строить логические цепочки, находить связи между органами "
        "и описывать структуру человеческого тела."
    )
)

if __name__ == "__main__":
    print("\n" + "="*50)
    print("Запуск веб-интерфейса Gradio...")
    print("Локальный адрес: http://127.0.0.1:7860")
    print("="*50)
    
    demo.launch(server_name="127.0.0.1", server_port=7860)