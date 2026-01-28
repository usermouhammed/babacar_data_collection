import pandas as pd
import numpy as np
import re
from typing import Optional, Dict 
import logging

logger = logging.getLogger(__name__)

class DataCleaner:
    
    def __init__(self):
        self.marque_mapping = {
            'peugeot': 'Peugeot',
            'renault': 'Renault',
            'toyota': 'Toyota',
            'hyundai': 'Hyundai',
            'ford': 'Ford',
            'bmw': 'BMW',
            'kia': 'Kia',
            'land rover': 'Land Rover',
            'jeep': 'Jeep',
            'citroen': 'Citroën',
            'mazda': 'Mazda',
            'mitsubishi': 'Mitsubishi',
            'honda': 'Honda',
            'yamaha': 'Yamaha',
            'suzuki': 'Suzuki',
            'sym': 'SYM',
            'ktm': 'KTM',
            'piaggio': 'Piaggio',
            'haouju': 'Haouju'
        }
    
    def clean_dataframe(self, df: pd.DataFrame, source: str = 'scraper') -> pd.DataFrame:
        
        if df.empty:
            return df
        
        df_clean = df.copy()
        
        if source == 'webscraper':
            df_clean = self._clean_webscraper_data(df_clean)
        else:
            df_clean = self._clean_scraper_data(df_clean)
        
        
        df_clean = self._common_cleaning(df_clean)
        
        logger.info(f"Données nettoyées: {len(df_clean)} lignes")
        return df_clean
    
    def _clean_scraper_data(self, df: pd.DataFrame) -> pd.DataFrame:
        
       
        numeric_cols = ['prix', 'kilometrage', 'annee']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        
        if 'marque' in df.columns:
            df['marque'] = df['marque'].str.lower()
            df['marque'] = df['marque'].map(self.marque_mapping).fillna(df['marque'].str.title())
        
        
        if 'adresse' in df.columns:
            df['adresse'] = df['adresse'].str.strip()
           
            df['ville'] = df['adresse'].apply(self._extract_city)
        
        return df
    
    def _clean_webscraper_data(self, df: pd.DataFrame) -> pd.DataFrame:
        
        
        column_mapping = {
            'Marque': 'marque',
            'Prix': 'prix_texte',
            'Adresse': 'adresse',
            'Kilometrage': 'kilometrage',
            'Boite_vitesse': 'boite_vitesse',
            'Carburant': 'carburant',
            'Annee': 'annee'
        }
        
       
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df = df.rename(columns={old_col: new_col})
        
        
        if 'titre_complet' not in df.columns and 'marque' in df.columns:
            
            df['titre_complet'] = df['marque']
            df = self._split_combined_title(df)
        
        
        if 'prix_texte' in df.columns:
            df['prix'] = df['prix_texte'].apply(self._extract_numeric_price)
        
        
        return self._clean_scraper_data(df)
    
    def _split_combined_title(self, df: pd.DataFrame) -> pd.DataFrame:
       
        def split_title(title):
            if not isinstance(title, str):
                return pd.Series([None, None, None])
            
            
            year_match = re.search(r'\b(19|20)\d{2}\b', title)
            year = year_match.group(0) if year_match else None
            
           
            parts = title.split()
            marque = parts[0] if parts else None
            
            
            if year and year in parts:
                parts.remove(year)
            if marque and marque in parts:
                parts.remove(marque)
            modele = ' '.join(parts) if parts else None
            
            return pd.Series([marque, modele, year])
        
        if 'marque' in df.columns:
            df[['marque', 'modele', 'annee']] = df['marque'].apply(split_title)
        
        return df
    
    def _extract_numeric_price(self, price_text: str) -> Optional[int]:
        
        if not isinstance(price_text, str):
            return None
        
        cleaned = re.sub(r'[^\d]', '', price_text)
        return int(cleaned) if cleaned else None
    
    def _extract_city(self, address: str) -> Optional[str]:
        if not isinstance(address, str):
            return None
        
        cities = ['Dakar', 'Thiès', 'Saint-Louis', 'Ziguinchor', 'Kaolack', 
                 'Mbour', 'Diourbel', 'Louga', 'Tambacounda', 'Kolda', 
                 'Matam', 'Kaffrine', 'Sédhiou', 'Rufisque', 'Guédiawaye']
        
        for city in cities:
            if city.lower() in address.lower():
                return city
        
        if ',' in address:
            parts = address.split(',')
            if len(parts) > 1:
                return parts[-1].strip()
        
        return None
    
    def _common_cleaning(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.drop_duplicates(subset=['titre_complet', 'prix'], keep='first')
        
       
        if 'prix' in df.columns:
            df = df[df['prix'].notna()]
            
            if len(df) > 0:
                q1 = df['prix'].quantile(0.05)
                q3 = df['prix'].quantile(0.95)
                df = df[(df['prix'] >= q1) & (df['prix'] <= q3)]
        
       
        text_cols = ['adresse', 'boite_vitesse', 'carburant', 'ville', 'modele']
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].fillna('Non spécifié')
        
        return df
    
    def merge_categories(self, data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        if not data_dict:
            return pd.DataFrame()
        
        all_dfs = []
        for category, df in data_dict.items():
            if not df.empty:
                df['categorie'] = category
                all_dfs.append(df)
        
        if all_dfs:
            merged_df = pd.concat(all_dfs, ignore_index=True)
            return merged_df
        
        return pd.DataFrame()