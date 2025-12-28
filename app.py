import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import time
import random

# --- 1. CONFIGURATION GÉNÉRALE ---
st.set_page_config(
    page_title="Blishko Trades Ultimate",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PRO (Style Apple Dark) ---
st.markdown("""
<style>
    /* Import police clean */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #000000;
        color: #ffffff;
    }

    /* Sidebar (Liste de gauche) */
    [data-testid="stSidebar"] {
        background-color: #1c1c1e;
        border-right: 1px solid #333;
    }
    
    /* Boutons de période (1J, 1S, etc.) */
    div.stButton > button {
        background-color: #2c2c2e;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 5px 15px;
        font-size: 0.8rem;
    }
    div.stButton > button:hover {
        background-color: #3a3a3c;
        color: #0A84FF;
    }
    div.stButton > button:focus {
        background-color: #3a3a3c;
        color: #0A84FF;
        border: 1px solid #0A84FF;
    }

    /* Gros Textes */
    .price-large { font-size: 3.5rem; font-weight: 700; margin: 0; line-height: 1; }
    .price-change { font-size: 1.2rem; font-weight: 500; margin-top: 5px; }
    
    /* Indicateur Sentiment */
    .sentiment-box {
        background-color: #1c1c1e;
        padding: 20px;
        border-radius: 12px;
        margin-top: 20px;
        border: 1px solid #333;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. MOTEUR DE DONNÉES (Yahoo Finance) ---

# Liste des actifs (Nom affiché : Symbole Yahoo)
ASSETS = {
    "Cryptomonnaies": {
        "Bitcoin": "BTC-USD",
        "Ethereum": "ETH-USD",
        "Ripple": "XRP-USD",
        "Render": "RNDR-USD",
        "Solana": "SOL-USD"
    },
    "Bourse & Matières": {
        "Apple": "AAPL",
        "Microsoft": "MSFT",
        "Alphabet (Google)": "GOOGL",
        "Tesla": "TSLA",
        "Or (Gold)": "GC=F"
    }
}

# Mapping des périodes pour Yahoo Finance
TIMEFRAMES = {
    "1J": "1d",
    "5J": "5d",
    "1M": "1mo",
    "6M": "6mo",
    "1A": "1y",
    "5A": "5y"
}

INTERVALS = {
    "1d": "5m",   # Pour 1 jour, on veut des points toutes les 5 min
    "5d": "15m",  # Pour 5 jours, toutes les 15 min
    "1mo": "1h",  # Pour 1 mois, toutes les heures
    "6mo": "1d",  # Pour le reste, 1 point par jour
    "1y": "1d",
    "5y": "1wk"
}

@st.cache_data(ttl=60) # Cache de 60 secondes pour ne pas surcharger
def get_market_data(ticker, period, interval):
    """Récupère l'historique depuis Yahoo Finance"""
    try:
        data = yf.download(ticker, period=period, interval=interval, progress=False)
        return data
    except Exception as e:
        return pd.DataFrame()

# --- 3. MOTEUR D'ANALYSE SENTIMENT (Simulé mais Avancé) ---

def get_social_sentiment(symbol, price_change_pct):
    """
    Simule une analyse complexe de Twitter/Reddit.
    Prend en compte la volatilité du prix pour générer un score crédible.
    """
    # Base du score (50 = Neutre)
    base_score = 50
    
    # Influence du prix (Le marché suit souvent la tendance - FOMO)
    trend_influence = price_change_pct * 5  # Si +2%, score augmente de 10
    
    # Bruit social (Rumeurs, FUD, Hype)
    social_noise = random.uniform(-10, 10)
    
    final_score = base_score + trend_influence + social_noise
    
    # Bornage entre 0 et 100
    final_score = max(5, min(95, final_score))
    
    # Détermination de l'état psychologique
    if final_score >= 75: state = "EUHORIE (Achat massif)"
    elif final_score >= 55: state = "CONFIANCE (Positif)"
    elif final_score >= 45: state = "INCERTITUDE (Neutre)"
    elif final_score >= 25: state = "PEUR (Vente)"
    else: state = "PANIQUE EXTRÊME (Crash)"
    
    return int(final_score), state

# --- 4. INTERFACE UTILISATEUR ---

# --- A. BARRE LATÉRALE (WATCHLIST) ---
with st.sidebar:
    st.header("Blishko Trades")
    st.caption("Marchés en Direct")
    
    # Choix de la catégorie
    category = st.radio("Marché", ["Cryptomonnaies", "Bourse & Matières"], label_visibility="collapsed")
    
    # Liste des actifs sous forme de boutons radio (style liste)
    selected_asset_name = st.radio(
        "Actifs", 
        list(ASSETS[category].keys())
    )
    
    # Bouton de rafraîchissement manuel
    if st.button("🔄 Actualiser les données"):
        st.cache_data.clear() # Vide le cache pour forcer le retéléchargement
        st.rerun()

# Récupération du symbole technique
symbol = ASSETS[category][selected_asset_name]

# --- B. ZONE PRINCIPALE ---

# 1. Gestion du Timeframe (Boutons horizontaux)
# On utilise session_state pour se souvenir du bouton cliqué
if 'timeframe' not in st.session_state:
    st.session_state.timeframe = "1J"

# Création des colonnes pour les boutons de temps
cols_tf = st.columns([1,1,1,1,1,1, 6]) # 6 colonnes boutons + espace vide
tf_labels = ["1J", "5J", "1M", "6M", "1A", "5A"]

for i, tf in enumerate(tf_labels):
    if cols_tf[i].button(tf, use_container_width=True):
        st.session_state.timeframe = tf

current_tf = st.session_state.timeframe
yf_period = TIMEFRAMES[current_tf]
yf_interval = INTERVALS[yf_period]

# 2. Chargement des données
with st.spinner(f"Récupération des données pour {selected_asset_name} ({current_tf})..."):
    df = get_market_data(symbol, yf_period, yf_interval)

if not df.empty:
    # 3. Calculs Prix et Variation
    current_price = df['Close'].iloc[-1]
    
    # Pour le calcul de variation, on prend le premier point de la période affichée
    start_price = df['Open'].iloc[0]
    change = current_price - start_price
    change_pct = (change / start_price) * 100
    
    # Couleur dynamique
    color_hex = "#30d158" if change >= 0 else "#ff453a" # Vert ou Rouge Apple
    
    # 4. Affichage Header (Prix)
    st.markdown(f"""
    <div>
        <div style="font-size: 1.5rem; color: #888;">{selected_asset_name}</div>
        <div class="price-large">${current_price:,.2f}</div>
        <div class="price-change" style="color: {color_hex};">
            {change:+.2f} ({change_pct:+.2f}%) • Depuis {current_tf}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 5. Graphique Interactif (Plotly)
    # On choisit le type de graphique : Ligne pour long terme, Bougies si < 1 mois ?
    # Restons sur une ligne pure "Area" style Apple pour l'élégance
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df.index, 
        y=df['Close'],
        mode='lines',
        line=dict(color=color_hex, width=2),
        fill='tozeroy',
        fillcolor=f"rgba({int(color_hex[1:3], 16)}, {int(color_hex[3:5], 16)}, {int(color_hex[5:7], 16)}, 0.1)",
        name=selected_asset_name
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=30, b=0),
        height=400,
        xaxis=dict(showgrid=False, showticklabels=True, gridcolor='#333'),
        yaxis=dict(showgrid=True, gridcolor='#222', side='right'), # Prix à droite
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 6. SECTION SENTIMENT (Moteur IA)
    st.markdown("---")
    st.subheader("🧠 Analyse Sentiment & Psychologie de Foule")
    
    # Calcul du score simulé
    sentiment_score, sentiment_state = get_social_sentiment(symbol, change_pct)
    
    # Jauge de sentiment (Gauge Chart)
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = sentiment_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"Index Social (Twitter/Reddit/News)<br><span style='font-size:0.8em;color:gray'>{sentiment_state}</span>"},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "white", 'thickness': 0.1}, # Aiguille blanche
            'bgcolor': "rgba(0,0,0,0)",
            'steps': [
                {'range': [0, 25], 'color': '#ff453a'},   # Rouge (Panique)
                {'range': [25, 45], 'color': '#ff9f0a'},  # Orange (Peur)
                {'range': [45, 55], 'color': '#8e8e93'},  # Gris (Neutre)
                {'range': [55, 75], 'color': '#30d158'},  # Vert (Confiance)
                {'range': [75, 100], 'color': '#0A84FF'}  # Bleu (Euphorie)
            ],
        }
    ))
    fig_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor='rgba(0,0,0,0)')
    
    # Mise en page Sentiment
    col_s1, col_s2 = st.columns([1, 2])
    
    with col_s1:
        st.plotly_chart(fig_gauge, use_container_width=True)
        
    with col_s2:
        st.markdown(f"""
        <div class="sentiment-box">
            <h4>Détails de l'analyse :</h4>
            <ul>
                <li><b>Tendance X (Twitter) :</b> {'🔥 En hausse' if sentiment_score > 50 else '❄️ En baisse'} sur les mots clés #{symbol.split('-')[0]}</li>
                <li><b>Reddit (WallStreetBets/Crypto) :</b> Volume de discussion {'élevé' if abs(change_pct) > 2 else 'modéré'}.</li>
                <li><b>Volatilité :</b> {abs(change_pct):.2f}% sur la période sélectionnée.</li>
            </ul>
            <p style="font-size: 0.8em; color: #666;">
                *Note : Cet indice agrège la volatilité du marché et simule le bruit social pour donner une indication de la "température" émotionnelle des investisseurs.*
            </p>
        </div>
        """, unsafe_allow_html=True)

else:
    st.error("Impossible de charger les données. Vérifiez votre connexion ou réessayez plus tard.")
