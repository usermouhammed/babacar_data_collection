import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import streamlit as st
import numpy as np
from typing import Optional

class DashboardVisualizer:
    
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.color_palette = px.colors.qualitative.Set3
    
    def create_summary_cards(self) -> None:
        if self.data.empty:
            st.warning("Aucune donnée disponible pour le dashboard")
            return
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_ads = len(self.data)
            st.metric("Total annonces", f"{total_ads:,}")
        
        with col2:
            if 'prix' in self.data.columns:
                avg_price = self.data['prix'].mean()
                st.metric("Prix moyen", f"{avg_price:,.0f} F CFA")
        
        with col3:
            if 'marque' in self.data.columns:
                unique_brands = self.data['marque'].nunique()
                st.metric("Marques", unique_brands)
        
        with col4:
            if 'categorie' in self.data.columns:
                categories = self.data['categorie'].nunique()
                st.metric("Catégories", categories)
    
    def create_price_distribution(self) -> None:
        """Distribution des prix"""
        if self.data.empty or 'prix' not in self.data.columns:
            return
        
        st.subheader("📊 Distribution des prix")
        
        
        fig = px.histogram(
            self.data,
            x='prix',
            nbins=30,
            title="Distribution des prix",
            labels={'prix': 'Prix (F CFA)'},
            color_discrete_sequence=['#636EFA']
        )
        
        fig.update_layout(
            xaxis_title="Prix (F CFA)",
            yaxis_title="Nombre d'annonces",
            bargap=0.1
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def create_brands_chart(self) -> None:
       
        if self.data.empty or 'marque' not in self.data.columns:
            return
        
        st.subheader(" Top 10 des marques")
        
        brand_counts = self.data['marque'].value_counts().head(10)
        
        fig = px.bar(
            x=brand_counts.values,
            y=brand_counts.index,
            orientation='h',
            title="Top 10 des marques les plus fréquentes",
            labels={'x': 'Nombre d\'annonces', 'y': 'Marque'},
            color=brand_counts.values,
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    def create_categories_chart(self) -> None:
       
        if self.data.empty or 'categorie' not in self.data.columns:
            return
        
        st.subheader(" Répartition par catégorie")
        
        cat_counts = self.data['categorie'].value_counts()
        
        fig = px.pie(
            values=cat_counts.values,
            names=cat_counts.index,
            title="Répartition des annonces par catégorie",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    def create_year_analysis(self) -> None:
       
        if self.data.empty or 'annee' not in self.data.columns:
            return
        
        st.subheader(" Analyse par année")
        
       
        valid_years = self.data[self.data['annee'].notna()].copy()
        valid_years['annee'] = valid_years['annee'].astype(int)
        
        if len(valid_years) == 0:
            return
        
       
        price_by_year = valid_years.groupby('annee')['prix'].agg(['mean', 'count']).reset_index()
       
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
       
        fig.add_trace(
            go.Bar(
                x=price_by_year['annee'],
                y=price_by_year['count'],
                name="Nombre d'annonces",
                marker_color='#FFA15A'
            ),
            secondary_y=False
        )
        
        
        fig.add_trace(
            go.Scatter(
                x=price_by_year['annee'],
                y=price_by_year['mean'],
                name="Prix moyen",
                line=dict(color='#636EFA', width=3),
                mode='lines+markers'
            ),
            secondary_y=True
        )
        
        fig.update_layout(
            title="Prix moyen et nombre d'annonces par année",
            xaxis_title="Année",
            hovermode="x unified"
        )
        
        fig.update_yaxes(title_text="Nombre d'annonces", secondary_y=False)
        fig.update_yaxes(title_text="Prix moyen (F CFA)", secondary_y=True)
        
        st.plotly_chart(fig, use_container_width=True)
    
    def create_geographical_distribution(self) -> None:
        if self.data.empty or 'ville' not in self.data.columns:
            return
        
        st.subheader(" Distribution géographique")
        
        city_counts = self.data['ville'].value_counts().head(15)
        
        fig = px.bar(
            x=city_counts.index,
            y=city_counts.values,
            title="Top 15 des villes",
            labels={'x': 'Ville', 'y': "Nombre d'annonces"},
            color=city_counts.values,
            color_continuous_scale='Blues'
        )
        
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    def create_correlation_heatmap(self) -> None:
        if self.data.empty:
            return
        
        st.subheader(" Corrélations entre variables")
        
        
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) >= 2:
            corr_matrix = self.data[numeric_cols].corr()
            
            fig = px.imshow(
                corr_matrix,
                text_auto=True,
                aspect="auto",
                title="Matrice de corrélation",
                color_continuous_scale='RdBu',
                zmin=-1,
                zmax=1
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Pas assez de données numériques pour la corrélation")
    
    def create_full_dashboard(self) -> None:
       
        st.title("📈 Dashboard Analytics - Dakar Auto")
        
       
        self.create_summary_cards()
        
        
        col1, col2 = st.columns(2)
        
        with col1:
            self.create_price_distribution()
        
        with col2:
            self.create_brands_chart()
        
        
        col3, col4 = st.columns(2)
        
        with col3:
            self.create_categories_chart()
        
        with col4:
            self.create_year_analysis()
        
        
        col5, col6 = st.columns(2)
        
        with col5:
            self.create_geographical_distribution()
        
        with col6:
            self.create_correlation_heatmap()
        
        
        st.subheader(" Données détaillées")
        st.dataframe(
            self.data,
            use_container_width=True,
            hide_index=True,
            column_config={
                "prix": st.column_config.NumberColumn(
                    "Prix",
                    format="%d F CFA"
                )
            }
        )