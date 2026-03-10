from typing import Dict, Any, List, Union
from fma_db import db

def search_anatomical_entity(label: str) -> Union[Dict[str, Any], str]:
    """
    Инструмент для первичного поиска сущности по текстовому названию.
    Возвращает FMAID и базовые данные.
    """
    data = db.get_entity_by_label(label)
    if not data:
        return "Сущность не найдена в базе данных."
    
    return {
        "FMAID": data.get("FMAID"),
        "Label": data.get("Preferred Label"),
        "Definition": data.get("Definitions", "Описание отсутствует")
    }

def get_anatomical_parts(fma_id: str) -> Union[Dict[str, Any], str]:
    """
    Инструмент для получения списка составных частей объекта (анатомический состав).
    """
    data = db.get_entity_by_id(fma_id)
    if not data: 
        return "Объект с таким ID не найден."
    
    parts = {
        "constitutional_parts": data.get("constitutional part"),
        "regional_parts": data.get("regional part"),
        "parts": data.get("part")
    }
    return {k: v for k, v in parts.items() if v}

def get_anatomical_hierarchy(fma_id: str) -> Union[Dict[str, Any], str]:
    """
    Инструмент для определения положения объекта в иерархии (вложенность).
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
    Инструмент для поиска специфических связей (кровоснабжение, иннервация).
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
    Инструмент глубокого сканирования всех 150+ типов отношений FMA.
    Результат группируется по семантическим категориям.
    """
    data = db.get_entity_by_id(fma_id)
    if not data: 
        return "ID не найден."
    
    categorized = {
        "СОСТАВ (parts)": [],
        "СОДЕРЖИТ (contains/surrounds)": [],
        "ВХОДИТ В (part of/located in)": [],
        "СВЯЗАННЫЕ СТРУКТУРЫ": [],
        "ПРОЧЕЕ": []
    }
    
    exclude = ['Class ID', 'Preferred Label', 'FMAID', 'Definitions']
    
    for k, v in data.items():
        if k in exclude: 
            continue
        
        key_low = k.lower()
        val_str = str(v)
        line = f"{k}: {val_str}"
        
        if "связанные структуры" in key_low:
            categorized["СВЯЗАННЫЕ СТРУКТУРЫ"].append(line)
        elif "part" in key_low and "of" not in key_low:
            categorized["СОСТАВ (parts)"].append(line)
        elif "contain" in key_low or "surround" in key_low:
            categorized["СОДЕРЖИТ (contains/surrounds)"].append(line)
        elif "of" in key_low or "in" in key_low:
            categorized["ВХОДИТ В (part of/located in)"].append(line)
        else:
            categorized["ПРОЧЕЕ"].append(line)

    output = []
    for cat, lines in categorized.items():
        if lines:
            output.append(f"--- {cat} ---\n" + "\n".join(lines))
    
    return "\n\n".join(output) if output else "Связи не найдены."

TOOL_SCHEMAS = [
    {
        "type": "function",
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
        "type": "function",
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
        "type": "function",
        "function": {
            "name": "get_anatomical_hierarchy",
            "description": "Определить, частью чего является орган и его положение в иерархии по FMAID.",
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
        "type": "function",
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
        "type": "function",
        "function": {
            "name": "get_all_entity_relations",
            "description": "ПОЛНЫЙ срез всех связей объекта. Используй для поиска неявных путей (например, через полости).",
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