import streamlit as st
import pandas as pd
import os
from datetime import datetime
import sys
import logging

sys.path.append('.')

from scraper import DakarAutoScraper
from cleaner import DataCleaner
from dashboard import DashboardVisualizer


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



st.set_page_config(
    page_title="Dakar Auto Scraper",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)


if 'scraped_data' not in st.session_state:
    st.session_state.scraped_data = {}
if 'cleaned_data' not in st.session_state:
    st.session_state.cleaned_data = None
if 'uploaded_data' not in st.session_state:
    st.session_state.uploaded_data = None

class DakarAutoApp:
   
    
    def __init__(self):
        self.scraper = DakarAutoScraper()
        self.cleaner = DataCleaner()
    
    def run(self):
        
        self.render_sidebar()
        
        
        st.title(" Dakar Auto - Scraper & Dashboard")
        st.markdown("---")
        
        
        page = st.session_state.get('page', 'scraper')
        
        if page == 'scraper':
            self.render_scraper_page()
        elif page == 'upload':
            self.render_upload_page()
        elif page == 'dashboard':
            self.render_dashboard_page()
        elif page == 'data_viewer':
            self.render_data_viewer()
    
    def render_sidebar(self):
        
        with st.sidebar:
            st.image("https://dakar-auto.com/images/logo.png", width=200)
            st.title("Navigation")
            
            
            page_options = {
                " Scraper en direct": "scraper",
                " Importer données": "upload",
                " Dashboard": "dashboard",
                " Visualiser données": "data_viewer"
            }
            
            for label, page_key in page_options.items():
                if st.button(label, use_container_width=True, key=f"nav_{page_key}"):
                    st.session_state.page = page_key
                    st.rerun()
            
            st.markdown("---")
            
            
            st.subheader(" Statut des données")
            if st.session_state.scraped_data:
                total_ads = sum(len(df) for df in st.session_state.scraped_data.values())
                st.success(f" {total_ads} annonces scrapées")
            
            if st.session_state.cleaned_data is not None:
                st.info(f" {len(st.session_state.cleaned_data)} annonces nettoyées")
            
            st.markdown("---")
            
            
            if st.session_state.cleaned_data is not None:
                self.download_data_button()
    
    def download_data_button(self):
        if st.session_state.cleaned_data is not None:
            csv_data = st.session_state.cleaned_data.to_csv(index=False).encode('utf-8-sig')
            
            st.download_button(
                label=" Télécharger données nettoyées",
                data=csv_data,
                file_name=f"dakar_auto_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    def render_scraper_page(self):
        
        st.header("Scraper en direct")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            
            st.subheader("Catégories à scraper")
            
            categories = st.multiselect(
                "Sélectionnez les catégories:",
                ["Voitures", "Motos", "Location"],
                default=["Voitures"]
            )
            
           
            pages = st.slider(
                "Nombre de pages par catégorie:",
                min_value=1,
                max_value=10,
                value=1,
                help="Attention: scraper trop de pages peut ralentir le site cible"
            )
        
        with col2:
            st.subheader("Paramètres")
            
            
            auto_clean = st.checkbox("Nettoyer automatiquement", value=True)
            save_raw = st.checkbox("Sauvegarder données brutes", value=True)
        
        
        if st.button(" Lancer le scraping", type="primary", use_container_width=True):
            with st.spinner("Scraping en cours..."):
                self.perform_scraping(categories, pages, save_raw, auto_clean)
    
    def perform_scraping(self, categories, pages, save_raw, auto_clean):
        
        category_urls = {
            "Voitures": "https://dakar-auto.com/senegal/voitures-4",
            "Motos": "https://dakar-auto.com/senegal/motos-and-scooters-3",
            "Location": "https://dakar-auto.com/senegal/location-de-voitures-19"
        }
        
        category_keys = {
            "Voitures": "voitures",
            "Motos": "motos",
            "Location": "location"
        }
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        scraped_data = {}
        total_categories = len(categories)
        
        for i, category in enumerate(categories):
            status_text.text(f"Scraping {category}...")
            
            try:
                df = self.scraper.scrape_category(
                    category_urls[category],
                    category_keys[category],
                    pages
                )
                
                if not df.empty:
                    scraped_data[category] = df
                    
                    
                    if save_raw:
                        filename = f"{category_keys[category]}_{datetime.now().strftime('%Y%m%d')}.csv"
                        df.to_csv(filename, index=False)
                        logger.info(f"Données brutes sauvegardées: {filename}")
                
                progress_bar.progress((i + 1) / total_categories)
                
            except Exception as e:
                st.error(f"Erreur lors du scraping de {category}: {str(e)}")
                continue
        
        if scraped_data:
            st.session_state.scraped_data = scraped_data
            
            
            if auto_clean:
                cleaned_df = self.cleaner.merge_categories(scraped_data)
                cleaned_df = self.cleaner.clean_dataframe(cleaned_df, 'scraper')
                st.session_state.cleaned_data = cleaned_df
                
                
                cleaned_filename = f"cleaned_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
                cleaned_df.to_csv(cleaned_filename, index=False)
                
                st.success(f" {sum(len(df) for df in scraped_data.values())} annonces scrapées et nettoyées!")
                st.info(f" Données nettoyées sauvegardées: {cleaned_filename}")
            else:
                st.success(f" {sum(len(df) for df in scraped_data.values())} annonces scrapées!")
        
        status_text.empty()
        progress_bar.empty()
    
    def render_upload_page(self):
        st.header(" Importer des données")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Import depuis Web Scraper")
            
            uploaded_file = st.file_uploader(
                "Choisissez un fichier CSV/Excel",
                type=['csv', 'xlsx', 'xls'],
                help="Importez vos données exportées depuis Web Scraper"
            )
            
            if uploaded_file is not None:
                try:
                   
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                    
                    st.session_state.uploaded_data = df
                    
                    
                    st.success(f" Fichier importé: {uploaded_file.name}")
                    st.info(f"{len(df)} lignes, {len(df.columns)} colonnes")
                    
                    with st.expander("Aperçu des données"):
                        st.dataframe(df.head(), use_container_width=True)
                
                except Exception as e:
                    st.error(f"Erreur lors de la lecture du fichier: {str(e)}")
        
        with col2:
            st.subheader("Nettoyage des données")
            
            if st.session_state.uploaded_data is not None:
                st.write("Options de nettoyage:")
                
                remove_duplicates = st.checkbox("Supprimer les doublons", value=True)
                clean_prices = st.checkbox("Nettoyer les prix", value=True)
                standardize_brands = st.checkbox("Standardiser les marques", value=True)
                
                if st.button(" Nettoyer les données", use_container_width=True):
                    with st.spinner("Nettoyage en cours..."):
                        df_clean = self.cleaner.clean_dataframe(
                            st.session_state.uploaded_data,
                            'webscraper'
                        )
                        
                        st.session_state.cleaned_data = df_clean
                        
                        
                        filename = f"webscraper_cleaned_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
                        df_clean.to_csv(filename, index=False)
                        
                        st.success(f" Données nettoyées: {len(df_clean)} lignes")
                        st.info(f" Fichier sauvegardé: {filename}")
                        
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Avant nettoyage", len(st.session_state.uploaded_data))
                        with col2:
                            st.metric("Après nettoyage", len(df_clean))
    
    def render_dashboard_page(self):
        """Page du dashboard"""
        if st.session_state.cleaned_data is None:
            st.warning(" Aucune donnée nettoyée disponible pour le dashboard")
            st.info("Veuillez d'abord scraper ou importer des données")
            return
        
        visualizer = DashboardVisualizer(st.session_state.cleaned_data)
        visualizer.create_full_dashboard()
    
    def render_data_viewer(self):
        """Page de visualisation des données"""
        st.header(" Visualisation des données")
        
        
        data_options = {}
        
        if st.session_state.scraped_data:
            for category, df in st.session_state.scraped_data.items():
                data_options[f"Scrapé - {category}"] = df
        
        if st.session_state.uploaded_data is not None:
            data_options["Importé (brut)"] = st.session_state.uploaded_data
        
        if st.session_state.cleaned_data is not None:
            data_options["Nettoyé"] = st.session_state.cleaned_data
        
        if not data_options:
            st.info("Aucune donnée disponible. Veuillez scraper ou importer des données.")
            return
        
        selected_data = st.selectbox(
            "Sélectionnez les données à visualiser:",
            list(data_options.keys())
        )
        
        df_to_display = data_options[selected_data]
        
        
        st.subheader(f"Données: {selected_data}")
        
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Lignes", len(df_to_display))
        with col2:
            st.metric("Colonnes", len(df_to_display.columns))
        with col3:
            missing = df_to_display.isnull().sum().sum()
            st.metric("Valeurs manquantes", missing)
        with col4:
            if 'prix' in df_to_display.columns:
                avg_price = df_to_display['prix'].mean()
                st.metric("Prix moyen", f"{avg_price:,.0f} F CFA")
        
        
        with st.expander(" Filtres avancés"):
            filter_cols = st.columns(3)
            
           
            if 'marque' in df_to_display.columns:
                marques = sorted(df_to_display['marque'].dropna().unique())
                selected_marques = st.multiselect("Marque:", marques, default=marques[:3])
                if selected_marques:
                    df_to_display = df_to_display[df_to_display['marque'].isin(selected_marques)]
            
            
            if 'prix' in df_to_display.columns:
                min_price = float(df_to_display['prix'].min())
                max_price = float(df_to_display['prix'].max())
                price_range = st.slider(
                    "Plage de prix (F CFA):",
                    min_value=min_price,
                    max_value=max_price,
                    value=(min_price, max_price)
                )
                df_to_display = df_to_display[
                    (df_to_display['prix'] >= price_range[0]) & 
                    (df_to_display['prix'] <= price_range[1])
                ]
        
        
        st.dataframe(
            df_to_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "prix": st.column_config.NumberColumn(
                    "Prix",
                    format="%d F CFA"
                ),
                "kilometrage": st.column_config.NumberColumn(
                    "Kilométrage",
                    format="%d km"
                )
            }
        )
        
        csv_data = df_to_display.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label=" Télécharger ces données",
            data=csv_data,
            file_name=f"filtered_{selected_data.lower().replace(' ', '_')}.csv",
            mime="text/csv",
            use_container_width=True
        )

def main():
    """Fonction principale"""
    
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stButton button {
        width: 100%;
        border-radius: 10px;
        padding: 10px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #1E3A8A;
    }
    </style>
    """, unsafe_allow_html=True)
    
    
    app = DakarAutoApp()
    app.run()

if __name__ == "__main__":

    main()
