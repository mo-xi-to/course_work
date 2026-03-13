from typing import Dict, Any, List, Union
from fma_db import db

def search_anatomical_entity(label: str) -> Union[Dict[str, Any], str]:
    """
    Инструмент для первичного поиска сущности по текстовому названию.
    Возвращает FMAID, предпочтительное имя и определение.
    """
    data = db.get_entity_by_label(label)
    if not data:
        return "Сущность не найдена в базе данных. Попробуйте уточнить название на английском."
    
    return {
        "FMAID": data.get("FMAID"),
        "Label": data.get("Preferred Label"),
        "Definition": data.get("Definitions", "Описание отсутствует")
    }

def get_anatomical_parts(fma_id: str):
    """Инструмент для получения списка составных частей объекта."""
    data = db.get_entity_by_id(fma_id)
    if not data: return "Объект не найден."
    
    parts = {
        "constitutional_parts": data.get("constitutional part"),
        "regional_parts": data.get("regional part"),
        "parts": data.get("part"),
        "СВЯЗАННЫЕ_СТРУКТУРЫ_И_КОМПОНЕНТЫ": data.get("СВЯЗАННЫЕ СТРУКТУРЫ")
    }
    return {k: v for k, v in parts.items() if v}

def get_anatomical_hierarchy(fma_id: str) -> Union[Dict[str, Any], str]:
    """
    Быстрый инструмент для определения положения объекта в иерархии (чья это часть).
    """
    data = db.get_entity_by_id(fma_id)
    if not data: 
        return "Объект с таким ID не найден."
    
    hierarchy = {
        "part_of": data.get("part of"),
        "regional_part_of": data.get("regional part of"),
        "member_of": data.get("member of")
    }
    return {k: v for k, v in hierarchy.items() if v}

def get_anatomical_relations(fma_id: str) -> Union[Dict[str, Any], str]:
    """
    Инструмент для поиска специфических связей: кровоснабжение и иннервация.
    """
    data = db.get_entity_by_id(fma_id)
    if not data: 
        return "Объект с таким ID не найден."
    
    relations = {
        "arterial_supply": data.get("arterial supply"),
        "nerve_supply": data.get("nerve supply"),
        "venous_drainage": data.get("venous drainage")
    }
    return {k: v for k, v in relations.items() if v}

def get_all_entity_relations(fma_id: str) -> str:
    """
    Инструмент глубокого сканирования ВСЕХ типов отношений FMA.
    Результат группируется по категориям для облегчения логического вывода модели.
    """
    data = db.get_entity_by_id(fma_id)
    if not data: return "ID не найден."
    
    categorized = {
        "СОСТАВ": [],
        "СВЯЗАННЫЕ СТРУКТУРЫ (КОМПОНЕНТЫ)": [],
        "СОДЕРЖИТ": [],
        "ВХОДИТ В": [],
        "ПРОЧЕЕ": []
    }
    
    exclude = ['Class ID', 'Preferred Label', 'FMAID', 'Definitions']
    
    for k, v in data.items():
        key_low = k.lower()
        line = f"{k}: {v}"
        if "связанные структуры" in key_low:
            categorized["СВЯЗАННЫЕ СТРУКТУРЫ (КОМПОНЕНТЫ)"].append(line)
        elif any(x in key_low for x in ["arterial", "nerve", "venous", "lymphatic"]):
            categorized["ФУНКЦИОНАЛЬНЫЕ СВЯЗИ (сосуды/нервы)"].append(line)
        elif "part of" in key_low or "member of" in key_low or "located in" in key_low:
            categorized["ВХОДИТ В"].append(line)
        elif "part" in key_low or "branch" in key_low or "tributary" in key_low:
            categorized["СОСТАВ"].append(line)
        elif "contain" in key_low or "surround" in key_low or "bound" in key_low:
            categorized["СОДЕРЖИМОЕ И ПОЛОСТИ"].append(line)
        else:
            categorized["ПРОЧЕЕ"].append(line)

    output = []
    for cat, lines in categorized.items():
        if lines:
            output.append(f"--- {cat} ---\n" + "\n".join(lines))
    
    return "\n\n".join(output) if output else "Связи не найдены."

YANDEX_TOOL_SCHEMAS = [
    {
        "function": {
            "name": "search_anatomical_entity",
            "description": "Поиск FMAID и базового описания органа по его названию на английском.",
            "parameters": {
                "type": "object",
                "properties": {
                    "label": {"type": "string", "description": "Название структуры, например 'Heart'"}
                },
                "required": ["label"]
            }
        }
    },
    {
        "function": {
            "name": "get_anatomical_parts",
            "description": "Получить список составляющих частей (анатомический состав) по FMAID.",
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
            "description": "Определить положение органа в иерархии (part of) по FMAID.",
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
            "description": "ПОЛНЫЙ список всех связей объекта. Используй для поиска неявных путей (через полости или компоненты).",
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