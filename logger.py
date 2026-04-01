import logging
import sys

def setup_logging():
    """Централизованная настройка логирования для всего проекта"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout)
            # logging.FileHandler("anatomy_project.log", encoding='utf-8')
        ]
    )

def get_logger(module_name):
    """Возвращает настроенный логгер для конкретного модуля"""
    return logging.getLogger(module_name)