import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DakarAutoScraper:
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.base_url = "https://dakar-auto.com"
    
    def scrape_category(self, url: str, category: str, pages: int = 1) -> pd.DataFrame:
        
        all_data = []
        
        for page in range(1, pages + 1):
            page_url = f"{url}?page={page}" if page > 1 else url
            logger.info(f"Scraping page {page}: {page_url}")
            
            try:
                page_data = self._scrape_single_page(page_url, category)
                if page_data:
                    all_data.extend(page_data)
                    logger.info(f"✓ {len(page_data)} annonces trouvées sur la page {page}")
                else:
                    logger.warning(f"Aucune donnée sur la page {page}")
                
                
                if page < pages:
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"Erreur sur la page {page}: {e}")
                continue
        
        if all_data:
            df = pd.DataFrame(all_data)
            df['categorie'] = category
            return df
        return pd.DataFrame()
    
    def _scrape_single_page(self, url: str, category: str) -> List[Dict]:
        """Scrape une seule page"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
           
            listings = self._find_listings(soup)
            
            data = []
            for listing in listings:
                listing_data = self._extract_listing_data(listing, category)
                if listing_data:
                    listing_data['url_page'] = url
                    data.append(listing_data)
            
            return data
            
        except Exception as e:
            logger.error(f"Erreur lors du scraping de {url}: {e}")
            return []
    
    def _find_listings(self, soup: BeautifulSoup):
        """Trouve tous les conteneurs d'annonces"""
        
        selectors = [
            'div[class*="listing"]',
            'div[class*="card"]',
            'article',
            'div.col-lg-4',
            'div.col-md-6',
            'div:has(h2):has(h3)'
        ]
        
        for selector in selectors:
            listings = soup.select(selector)
            if len(listings) >= 3:  
                return listings
        
        
        return soup.find_all(['div', 'article'], 
                           attrs={'class': lambda x: x and any(
                               kw in str(x).lower() for kw in ['listing', 'card', 'annonce', 'item']
                           )})
    
    def _extract_listing_data(self, listing, category: str) -> Optional[Dict]:
        """Extrait les données d'une annonce"""
        try:
            data = {}
            
           
            title_elem = listing.find('h2')
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            data['titre_complet'] = title
            
           
            self._extract_title_parts(title, data)
            
            
            price_elem = listing.find('h3')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                data['prix_texte'] = price_text
                data['prix'] = self._extract_numeric_price(price_text)
            
            
            address_elem = price_elem.find_next('p') if price_elem else None
            if address_elem:
                data['adresse'] = address_elem.get_text(strip=True)
            
            
            self._extract_details(listing, data, category)
            
            return data
            
        except Exception as e:
            logger.error(f"Erreur extraction annonce: {e}")
            return None
    
    def _extract_title_parts(self, title: str, data: Dict):
        """Extrait marque, modèle et année du titre"""
        parts = title.split()
        if parts:
            data['marque'] = parts[0]
            
            
            year_match = re.search(r'\b(19|20)\d{2}\b', title)
            if year_match:
                data['annee'] = year_match.group(0)
                
                model_parts = parts[1:]
                if year_match.group(0) in model_parts:
                    model_parts.remove(year_match.group(0))
                data['modele'] = ' '.join(model_parts) if model_parts else ''
            else:
                data['annee'] = None
                data['modele'] = ' '.join(parts[1:]) if len(parts) > 1 else ''
    
    def _extract_numeric_price(self, price_text: str) -> Optional[int]:
        """Extrait le prix numérique"""
        try:
            cleaned = re.sub(r'[^\d]', '', price_text)
            return int(cleaned) if cleaned else None
        except:
            return None
    
    def _extract_details(self, listing, data: Dict, category: str):
        """Extrait les détails selon la catégorie"""
        list_items = listing.find_all('li')
        
        for li in list_items:
            text = li.get_text(strip=True).lower()
            
           
            if 'km' in text:
                km = re.sub(r'[^\d]', '', text)
                if km:
                    data['kilometrage'] = int(km)
            
          
            if category == 'voitures' or category == 'location':
                if 'automatique' in text:
                    data['boite_vitesse'] = 'Automatique'
                elif 'manuelle' in text:
                    data['boite_vitesse'] = 'Manuelle'
            
            
            if 'diesel' in text:
                data['carburant'] = 'Diesel'
            elif 'essence' in text:
                data['carburant'] = 'Essence'
        
        
        if 'kilometrage' not in data:
            data['kilometrage'] = None
        if 'boite_vitesse' not in data and category in ['voitures', 'location']:
            data['boite_vitesse'] = None
        if 'carburant' not in data and category == 'voitures':
            data['carburant'] = None
    
    def scrape_all_categories(self, pages_per_category: int = 1) -> Dict[str, pd.DataFrame]:
        """Scrape toutes les catégories"""
        categories = {
            'voitures': 'https://dakar-auto.com/senegal/voitures-4',
            'motos': 'https://dakar-auto.com/senegal/motos-and-scooters-3',
            'location': 'https://dakar-auto.com/senegal/location-de-voitures-19'
        }
        
        results = {}
        for category, url in categories.items():
            logger.info(f"Scraping catégorie: {category}")
            df = self.scrape_category(url, category, pages_per_category)
            if not df.empty:
                results[category] = df
        
        return results