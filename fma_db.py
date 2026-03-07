import pandas as pd
import config
import os

class FMADatabase:
    """Класс для управления доступом к данным FMA из CSV-файла"""

    def __init__(self):
        """Инициализация базы: загрузка данных и фильтрация."""
        if not os.path.exists(config.FMA_CSV_PATH):
            raise FileNotFoundError(f"Файл базы данных не найден по пути: {config.FMA_CSV_PATH}")
        
        print("Загрузка базы данных FMA...")
        self.df = pd.read_csv(config.FMA_CSV_PATH, low_memory=False)
        print(f"База успешно загружена. Количество записей: {len(self.df)}")

    def get_entity_by_label(self, label: str):
        """
        Поиск анатомической сущности по названию (Preferred Label).
        Возвращает очищенный от пустых ячеек словарь или None.
        """
        result = self.df[self.df['Preferred Label'].str.lower() == label.lower()]
        if result.empty:
            # Попытка нечеткого поиска (содержит подстроку)
            result = self.df[self.df['Preferred Label'].str.contains(label, case=False, na=False)]
        
        if result.empty:
            return None
        
        # Преобразование первой найденной строки в словарь без пустых значений
        data = result.iloc[0].to_dict()
        return {k: v for k, v in data.items() if pd.notna(v) and str(v).strip() != ""}

    def get_entity_by_id(self, fma_id: str):
        """
        Поиск сущности по уникальному FMAID.
        """
        clean_id = str(fma_id).lower().replace("fma:", "").replace("fma", "").strip()
        
        result = self.df[self.df['FMAID'].astype(str).str.contains(clean_id, na=False)]
        
        if result.empty:
            result = self.df[self.df['Class ID'].str.contains(clean_id, na=False)]
            
        if result.empty:
            return None
            
        data = result.iloc[0].to_dict()
        return {k: v for k, v in data.items() if pd.notna(v) and str(v).strip() != ""}

db = FMADatabase()