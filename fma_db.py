import pandas as pd
import config
import os
from typing import Optional, Dict, Any, List

class FMADatabase:
    """
    Класс для управления доступом к данным онтологии FMA.
    Обеспечивает поиск по названиям, идентификаторам и реализацию 
    алгоритмов навигации по графу (прямой и обратный поиск).
    """

    def __init__(self) -> None:
        """Инициализация базы данных: загрузка CSV и первичная проверка файла."""
        if not os.path.exists(config.FMA_CSV_PATH):
            raise FileNotFoundError(f"Файл базы данных не найден: {config.FMA_CSV_PATH}")
        
        print("Загрузка базы данных FMA... Пожалуйста, подождите.")
        self.df = pd.read_csv(config.FMA_CSV_PATH, low_memory=False)
        print(f"База успешно загружена. Количество записей: {len(self.df)}")

    def _clean_row_data(self, row: pd.Series) -> Dict[str, Any]:
        """
        Внутренний метод для преобразования строки DataFrame в чистый словарь.
        Удаляет пустые значения (NaN) и лишние пробелы.
        """
        data = row.to_dict()
        return {
            str(k): v for k, v in data.items() 
            if pd.notna(v) and str(v).strip() != ""
        }

    def get_entity_by_label(self, label: str) -> Optional[Dict[str, Any]]:
        """
        Поиск анатомической сущности по названию (Preferred Label).
        Сначала ищет точное совпадение, затем пробует частичное.
        """
        search_label = str(label).lower().strip()
        
        result = self.df[self.df['Preferred Label'].str.lower() == search_label]
        
        if result.empty:
            result = self.df[self.df['Preferred Label'].str.contains(label, case=False, na=False)]
        
        if result.empty:
            return None
        
        return self._clean_row_data(result.iloc[0])

    def get_entity_by_id(self, fma_id: str) -> Optional[Dict[str, Any]]:
        """
        Комплексный поиск по идентификатору с использованием алгоритма обратных связей.
        Находит саму сущность и все структуры, которые на неё ссылаются.
        """
        clean_id = str(fma_id).lower().replace("fma:", "").replace("fma", "").strip()
        
        main_row = self.df[self.df['FMAID'].astype(str).str.contains(clean_id, na=False)]
        
        if main_row.empty:
            main_row = self.df[self.df['Class ID'].str.contains(clean_id, na=False)]
            
        if main_row.empty:
            return None
            
        clean_data = self._clean_row_data(main_row.iloc[0])
        
        hierarchy_columns = ['part of', 'constitutional part of', 'regional part of']
        children_names = []
        
        for col in hierarchy_columns:
            if col in self.df.columns:
                matches = self.df[self.df[col].astype(str).str.contains(clean_id, na=False)]
                children_names.extend(matches['Preferred Label'].tolist())
        
        if children_names:
            unique_children = sorted(list(set(children_names)))
            clean_data["СВЯЗАННЫЕ СТРУКТУРЫ"] = ", ".join(unique_children)
            
        return clean_data

db = FMADatabase()