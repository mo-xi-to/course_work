from fma_db import db

def search_anatomical_entity(label: str):
    """Инструмент для первичного поиска сущности по текстовому названию."""
    data = db.get_entity_by_label(label)
    if not data:
        return "Сущность не найдена в базе данных."
    return {
        "FMAID": data.get("FMAID"),
        "Label": data.get("Preferred Label"),
        "Definition": data.get("Definitions", "No definition available")
    }

def get_anatomical_parts(fma_id: str):
    """Инструмент для получения списка составных частей объекта по его FMAID."""
    data = db.get_entity_by_id(fma_id)
    if not data: return "Объект с таким ID не найден."
    
    parts = {
        "constitutional_parts": data.get("constitutional part"),
        "regional_parts": data.get("regional part"),
        "parts": data.get("part")
    }
    return {k: v for k, v in parts.items() if v}

def get_anatomical_hierarchy(fma_id: str):
    """Инструмент для определения положения объекта в иерархии (part of)."""
    data = db.get_entity_by_id(fma_id)
    if not data: return "Объект с таким ID не найден."
    
    hierarchy = {
        "part_of": data.get("part of"),
        "regional_part_of": data.get("regional part of")
    }
    return {k: v for k, v in hierarchy.items() if v}

# Описания инструментов
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_anatomical_entity",
            "description": "Используется для поиска FMAID и базового названия органа по его имени (на английском).",
            "parameters": {
                "type": "object",
                "properties": {
                    "label": {"type": "string", "description": "Название, например 'Aorta'"}
                },
                "required": ["label"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_anatomical_parts",
            "description": "Возвращает список внутренних частей органа по его FMAID.",
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
            "description": "Возвращает информацию о том, частью чего является орган. Требует FMAID.",
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
    "get_anatomical_hierarchy": get_anatomical_hierarchy
}