import os
import re
import pandas as pd
from typing import Optional, Dict, Any, List

import logger

logger = logger.get_logger("Database")

import config

class FMADatabase:
    """
    Класс для управления доступом к онтологии FMA.
    Реализует механизмы прямого поиска, обратной навигации и извлечения латыни.
    """

    def __init__(self) -> None:
        """Загрузка данных и предварительная обработка идентификаторов."""
        if not os.path.exists(config.FMA_DB_PATH):
            logger.critical(f"Файл базы данных не найден по пути: {config.FMA_DB_PATH}")
            raise FileNotFoundError(f"Файл не найден: {config.FMA_DB_PATH}")
        
        try:
            logger.info(f"Начало загрузки базы из {config.FMA_DB_PATH}...")
            self.df = pd.read_csv(config.FMA_DB_PATH, low_memory=False)
            
            self.df['FMAID'] = self.df['FMAID'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            
            logger.info(f"База успешно загружена. Всего записей: {len(self.df)}")
        except Exception as e:
            logger.error(f"Ошибка при чтении CSV-файла: {e}")
            raise

    def _clean_row_data(self, row: pd.Series) -> Dict[str, Any]:
        """
        Внутренний метод очистки: удаляет NaN и 
        автоматически извлекает латинское название.
        """
        raw_data = row.to_dict()
        clean = {}
        latin_found = False

        for k, v in raw_data.items():
            if pd.isna(v) or str(v).strip() == "":
                continue
            
            key_lower = str(k).lower()
            if ('latin' in key_lower or 'ta name' in key_lower) and not latin_found:
                clean["LATIN_NAME_STRICT"] = str(v)
                latin_found = True
            else:
                clean[str(k)] = v
        return clean

    def get_entity_by_label(self, label: str) -> Optional[Dict[str, Any]]:
        """Поиск объекта по текстовому названию (Preferred Label)."""
        search_term = str(label).lower().strip()
        logger.debug(f"Поиск по названию: '{search_term}'")

        exact_match = self.df[self.df['Preferred Label'].str.lower() == search_term]
        if not exact_match.empty:
            return self._clean_row_data(exact_match.iloc[0])
        
        partial_match = self.df[self.df['Preferred Label'].str.contains(label, case=False, na=False)]
        if not partial_match.empty:
            return self._clean_row_data(partial_match.iloc[0])
            
        logger.warning(f"Сущность с названием '{label}' не найдена.")
        return None

    def get_entity_by_id(self, fma_id: str) -> Optional[Dict[str, Any]]:
        """
        Комплексный поиск по ID. Собирает прямые атрибуты и 
        активирует алгоритм обратного поиска.
        """
        clean_id = ''.join(filter(str.isdigit, str(fma_id)))
        fma_marker = f"fma{clean_id}"
        
        main_row = self.df[self.df['FMAID'] == clean_id]
        if main_row.empty:
            main_row = self.df[self.df['Class ID'].str.endswith(f"/{fma_marker}", na=False)]
        
        if main_row.empty:
            logger.warning(f"Объект с ID {fma_id} не найден.")
            return None
        
        clean_data = self._clean_row_data(main_row.iloc[0])
        obj_label = clean_data.get('Preferred Label', 'Unknown')

        logger.info(f"Глубокий анализ: {obj_label} (ID: {clean_id})")

        hierarchy_cols = ['part of', 'constitutional part of', 'regional part of', 'member of', 'contained in', 'located in', 'Parents']
        related_entities = []
        id_pattern = rf"(?:fma|/|^){clean_id}(?![0-9])"

        for col in hierarchy_cols:
            if col in self.df.columns:
                mask = self.df[col].astype(str).str.contains(id_pattern, na=False, regex=True)
                matches = self.df[mask]
                
                for _, row in matches.iterrows():
                    name = row['Preferred Label']
                    child_id = row['FMAID']
                    child_data = self._clean_row_data(row)
                    latin = child_data.get("LATIN_NAME_STRICT", "")
                    
                    if name != obj_label:
                        entry = f"{name} [ID: {child_id}]"
                        if latin: entry += f" (Latin: {latin})"
                        related_entities.append(entry)

        semantic_mask = self.df['Preferred Label'].str.lower().str.contains(f"of {obj_label.lower()}", na=False)
        semantic_matches = self.df[semantic_mask]
        for _, row in semantic_matches.iterrows():
            name = row['Preferred Label']
            child_id = row['FMAID']
            child_data = self._clean_row_data(row)
            latin = child_data.get("LATIN_NAME_STRICT", "")
            if name != obj_label:
                entry = f"{name} [ID: {child_id}]"
                if latin: entry += f" (Latin: {latin})"
                related_entities.append(entry)

        if related_entities:
            unique_links = sorted(list(set(related_entities)))
            clean_data["СВЯЗАННЫЕ СТРУКТУРЫ"] = "\n".join(unique_links[:60])
            logger.info(f"Найдено {len(unique_links)} связанных структур.")
        
        return clean_data

try:
    db = FMADatabase()
except Exception as e:
    logger.critical(f"Не удалось инициализировать базу данных: {e}")
    db = None