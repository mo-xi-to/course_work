import pandas as pd
import config
import os
import re
from typing import Optional, Dict, Any, List

class FMADatabase:
    def __init__(self) -> None:
        if not os.path.exists(config.FMA_DB_PATH):
            raise FileNotFoundError(f"Файл не найден: {config.FMA_DB_PATH}")
        
        print(f"Загрузка базы из {config.FMA_DB_PATH}...")
        self.df = pd.read_csv(config.FMA_DB_PATH, low_memory=False)
        # Очистка FMAID от лишних точек и пробелов
        self.df['FMAID'] = self.df['FMAID'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        print(f"База успешно загружена. Записей: {len(self.df)}")

    def _clean_row(self, row: pd.Series) -> Dict[str, Any]:
        """Удаление пустых значений из строки данных."""
        return {str(k): v for k, v in row.to_dict().items() if pd.notna(v) and str(v).strip() != ""}

    def get_entity_by_label(self, label: str) -> Optional[Dict[str, Any]]:
        """Поиск объекта по текстовому названию."""
        s = str(label).lower().strip()
        exact_match = self.df[self.df['Preferred Label'].str.lower() == s]
        if not exact_match.empty:
            return self._clean_row(exact_match.iloc[0])
        
        partial_match = self.df[self.df['Preferred Label'].str.contains(label, case=False, na=False)]
        return self._clean_row(partial_match.iloc[0]) if not partial_match.empty else None

    def get_entity_by_id(self, fma_id: str) -> Optional[Dict[str, Any]]:
        """
        Глубокий поиск по идентификатору. 
        Собирает прямые данные, обратные связи с ID и семантические соответствия.
        """
        clean_id = ''.join(filter(str.isdigit, str(fma_id)))
        fma_marker = f"fma{clean_id}" # Тот самый пропущенный маркер
        
        main_row = self.df[self.df['FMAID'] == clean_id]
        if main_row.empty:
            main_row = self.df[self.df['Class ID'].str.endswith(f"/{fma_marker}", na=False)]
        
        if main_row.empty: 
            return None
        
        clean_data = self._clean_row(main_row.iloc[0])
        obj_label = clean_data.get('Preferred Label', '')

        print(f"[DB] Сбор связей для: {obj_label} (ID: {clean_id})")

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
                    if name != obj_label:
                        related_entities.append(f"{name} [ID: {child_id}]")

        semantic_mask = self.df['Preferred Label'].str.lower().str.contains(f"of {obj_label.lower()}", na=False)
        semantic_matches = self.df[semantic_mask]
        for _, row in semantic_matches.iterrows():
            name = row['Preferred Label']
            child_id = row['FMAID']
            if name != obj_label:
                related_entities.append(f"{name} [ID: {child_id}]")

        if related_entities:
            unique_links = sorted(list(set(related_entities)))
            clean_data["СВЯЗАННЫЕ СТРУКТУРЫ"] = ", ".join(unique_links[:60])
            print(f"[DB] Успешно найдено {len(unique_links)} связей с ID.")
        else:
            print(f"[DB] Обратных связей не обнаружено.")
            
        return clean_data

db = FMADatabase()