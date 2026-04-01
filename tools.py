from typing import Dict, Any, List, Union

import logger
from fma_db import db

logger = logger.get_logger("Tools")

def search_anatomical_entity(label: str) -> Union[Dict[str, Any], str]:
    """
    Первичный поиск сущности по текстовому названию.
    Возвращает идентификатор FMAID и базовое определение.
    """
    logger.info(f"Запрос на поиск сущности: '{label}'")
    data = db.get_entity_by_label(label)
    
    if not data:
        return "Сущность не найдена в базе данных. Попробуйте уточнить название."
    
    return {
        "FMAID": data.get("FMAID"),
        "Label": data.get("Preferred Label"),
        "Definition": data.get("Definitions", "Описание отсутствует"),
        "Latin_Name": data.get("LATIN_NAME_STRICT", "Не указано")
    }

def get_anatomical_parts(fma_id: str) -> Union[Dict[str, Any], str]:
    """Извлечение структурного состава объекта по его FMAID."""
    logger.info(f"Запрос состава для ID: {fma_id}")
    data = db.get_entity_by_id(fma_id)
    if not data:
        return "Объект с таким идентификатором не найден."
    
    parts = {
        "constitutional_parts": data.get("constitutional part"),
        "regional_parts": data.get("regional part"),
        "parts": data.get("part"),
        "COMPONENTS": data.get("СВЯЗАННЫЕ СТРУКТУРЫ")
    }
    return {k: v for k, v in parts.items() if v}

def get_anatomical_hierarchy(fma_id: str) -> Union[Dict[str, Any], str]:
    """Определение положения объекта в иерархии (чья это часть)."""
    logger.info(f"Запрос иерархии для ID: {fma_id}")
    data = db.get_entity_by_id(fma_id)
    if not data:
        return "Объект с таким идентификатором не найден."
    
    hierarchy = {
        "part_of": data.get("part of"),
        "regional_part_of": data.get("regional part of"),
        "member_of": data.get("member of"),
        "located_in": data.get("located in")
    }
    return {k: v for k, v in hierarchy.items() if v}

def get_anatomical_relations(fma_id: str) -> Union[Dict[str, Any], str]:
    """Поиск функциональных связей (кровоснабжение, иннервация)."""
    logger.info(f"Запрос функц. связей для ID: {fma_id}")
    data = db.get_entity_by_id(fma_id)
    if not data:
        return "Объект с таким идентификатором не найден."
    
    relations = {
        "arterial_supply": data.get("arterial supply"),
        "nerve_supply": data.get("nerve supply"),
        "venous_drainage": data.get("venous drainage")
    }
    return {k: v for k, v in relations.items() if v}

def get_all_entity_relations(fma_id: str) -> str:
    """
    Глубокий анализ всех доступных связей. 
    Данные группируются семантически для улучшения логики ИИ.
    """
    logger.info(f"Глубокое сканирование связей для ID: {fma_id}")
    data = db.get_entity_by_id(fma_id)
    if not data:
        return "Данные по указанному ID отсутствуют."
    
    categorized = {
        "СОСТАВ И КОМПОНЕНТЫ": [],
        "СОДЕРЖИМОЕ И ПОЛОСТИ": [],
        "ИЕРАРХИЯ (Входит в состав)": [],
        "ФУНКЦИОНАЛЬНЫЕ СВЯЗИ (Сосуды/Нервы)": [],
        "ПРОЧЕЕ": []
    }
    
    exclude = ['Class ID', 'Preferred Label', 'FMAID', 'Definitions', 'LATIN_NAME_STRICT']
    
    for k, v in data.items():
        if k in exclude:
            continue
        
        key_low = k.lower()
        line = f"{k}: {v}"
        
        if any(x in key_low for x in ["связанные структуры", "part", "branch", "tributary"]) and "of" not in key_low:
            categorized["СОСТАВ И КОМПОНЕНТЫ"].append(line)
        elif any(x in key_low for x in ["arterial", "nerve", "venous", "lymphatic"]):
            categorized["ФУНКЦИОНАЛЬНЫЕ СВЯЗИ (Сосуды/Нервы)"].append(line)
        elif any(x in key_low for x in ["of", "in", "member"]):
            categorized["ИЕРАРХИЯ (Входит в состав)"].append(line)
        elif any(x in key_low for x in ["contain", "surround", "bound"]):
            categorized["СОДЕРЖИМОЕ И ПОЛОСТИ"].append(line)
        else:
            categorized["ПРОЧЕЕ"].append(line)

    output = []
    for cat, lines in categorized.items():
        if lines:
            output.append(f"--- {cat} ---\n" + "\n".join(lines))
    
    return "\n\n".join(output) if output else "Специфических связей не обнаружено."

YANDEX_TOOL_SCHEMAS = [
    {
        "function": {
            "name": "search_anatomical_entity",
            "description": "Поиск FMAID и базового определения органа по названию (на английском).",
            "parameters": {
                "type": "object",
                "properties": {
                    "label": {"type": "string", "description": "Английское название, например 'Heart'"}
                },
                "required": ["label"]
            }
        }
    },
    {
        "function": {
            "name": "get_anatomical_parts",
            "description": "Получить список составляющих частей и компонентов объекта по его FMAID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fma_id": {"type": "string", "description": "Идентификатор FMA"}
                },
                "required": ["fma_id"]
            }
        }
    },
    {
        "function": {
            "name": "get_anatomical_hierarchy",
            "description": "Определить положение органа в иерархии (part of) по его FMAID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fma_id": {"type": "string", "description": "Идентификатор FMA"}
                },
                "required": ["fma_id"]
            }
        }
    },
    {
        "function": {
            "name": "get_anatomical_relations",
            "description": "Быстрый поиск кровоснабжения и иннервации объекта по его FMAID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fma_id": {"type": "string", "description": "Идентификатор FMA"}
                },
                "required": ["fma_id"]
            }
        }
    },
    {
        "function": {
            "name": "get_all_entity_relations",
            "description": "ПОЛНЫЙ срез всех связей объекта. Используй для поиска неявных цепочек (через полости, сосуды или компоненты).",
            "parameters": {
                "type": "object",
                "properties": {
                    "fma_id": {"type": "string", "description": "Идентификатор FMA"}
                },
                "required": ["fma_id"]
            }
        }
    }
]

AVAILABLE_FUNCTIONS = {
    "search_anatomical_entity": search_anatomical_entity,
    "get_anatomical_parts": get_anatomical_parts,
    "get_anatomical_hierarchy": get_anatomical_hierarchy,
    "get_anatomical_relations": get_anatomical_relations,
    "get_all_entity_relations": get_all_entity_relations
}