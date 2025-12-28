import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import random

# --- 1. CONFIGURATION & STYLE ---
st.set_page_config(page_title="Blishko Trades", page_icon="📈", layout="wide")

# CSS pour se rapprocher du style "Apple Bourse"
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #000000; /* Noir profond style OLED */
        color: #ffffff;
    }
    
    /* Gros titres */
    .big-asset-title { font-size: 2.5rem; font-weight: 700; margin-bottom: 0; line-height: 1.2; }
    .big-price { font-size: 4rem; font-weight: 600; margin: 0; line-height: 1; }
    .big-change { font-size: 1.5rem; font-weight: 500; margin-top: 5px; }
    
    /* Sélecteur d'actif stylisé */
    .stSelectbox > div > div {
        background-color: #1c1c1e; border: none; color: white; font-size: 1.2rem;
    }

    /* Onglets de navigation */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: #1c1c1e; padding: 5px; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { height: 40px; border-radius: 7px; border: none; color: #8e8e93; }
    .stTabs [aria-selected="true"] { background-color: #3a3a3c !important; color: white !important; }

    /* Cacher les éléments inutiles de Streamlit */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 2. FONCTIONS DE DONNÉES (Back-end) ---

@st.cache_data(ttl=60) # Met en cache l'historique pour 60 secondes pour éviter de spammer Binance
def get_binance_history_24h(symbol):
    """Récupère l'historique des 24 dernières heures (bougies 1h) sur Binance"""
    # Cette fonction résout le problème de la courbe plate au démarrage
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval=1h&limit=24"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        # Formatage des données pour Pandas
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'etc', 'etc', 'etc', 'etc', 'etc', 'etc'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['close'] = df['close'].astype(float)
        return df[['timestamp', 'close']]
    except:
        # Si erreur, on renvoie un DataFrame vide pour ne pas faire planter
        return pd.DataFrame(columns=['timestamp', 'close'])

def get_live_price(symbol, is_crypto=True):
    """Récupère le dernier prix (Crypto=Réel, Bourse=Simulé)"""
    if is_crypto:
        try:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
            return float(requests.get(url, timeout=2).json()['price'])
        except: return None
    else:
        # Simulation Bourse (car API payantes)
        base_prices = {'MSFT': 402.50, 'GOOGL': 173.20, 'GOLD': 2045.00}
        volatility = 0.0005 if symbol != 'GOLD' else 0.0002
        return base_prices.get(symbol, 100) * (1 + np.random.normal(0, volatility))

# --- 3. FONCTION GRAPHIQUE PROFESSIONNELLE (Plotly) ---

def create_pro_chart(df, current_price, prev_close, asset_name):
    """Génère un graphique style 'Apple Bourse' avec Plotly"""
    
    # Déterminer la couleur (Vert ou Rouge)
    is_up = current_price >= prev_close
    main_color = '#30d158' if is_up else '#ff453a' # Couleurs iOS
    
    # Création du graphique
    fig = go.Figure()

    # Ajout de la ligne
    fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['close'],
        mode='lines',
        line=dict(color=main_color, width=3),
        fill='tozeroy', # Remplissage sous la courbe
        fillcolor=f"rgba({int(main_color[1:3], 16)}, {int(main_color[3:5], 16)}, {int(main_color[5:7], 16)}, 0.2)", # Couleur transparente
        hoverinfo='x+y'
    ))

    # Configuration du layout (Axes invisibles, style épuré)
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0), height=350,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, fixedrange=True),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, fixedrange=True, 
                   range=[df['close'].min()*0.995, df['close'].max()*1.005]) # Zoom auto adapté
    )
    return fig

# --- 4. INTERFACE UTILISATEUR (Front-end) ---

st.title("BLISHKO TRADES")
tab_crypto, tab_bourse = st.tabs(["Crypto", "Actions & Matières"])

# === ONGLET CRYPTO ===
with tab_crypto:
    # Sélecteur style iOS
    selected_crypto = st.selectbox("Choisir un actif", 
                                   ["Bitcoin (BTC)", "Ripple (XRP)", "Render (RENDER)"], 
                                   label_visibility="collapsed")
    
    symbol_map = {"Bitcoin (BTC)": "BTC", "Ripple (XRP)": "XRP", "Render (RENDER)": "RENDER"}
    symbol = symbol_map[selected_crypto]

    # 1. Récupération des données (Loader discret si besoin)
    with st.spinner(f"Chargement des données 24h pour {symbol}..."):
        history_df = get_binance_history_24h(symbol)
        live_price = get_live_price(symbol, is_crypto=True)

    # 2. Calculs et Affichage Principal
    if live_price and not history_df.empty:
        prev_close_24h = history_df.iloc[0]['close'] # Prix d'il y a 24h
        change = live_price - prev_close_24h
        change_pct = (change / prev_close_24h) * 100
        color_class = "#30d158" if change >= 0 else "#ff453a"

        # Header style Apple
        st.markdown(f"""
            <div style="margin-top: 20px;">
                <div class="big-asset-title">{selected_crypto}</div>
                <div class="big-price">${live_price:,.2f}</div>
                <div class="big-change" style="color: {color_class};">
                    {change:+.2f} ({change_pct:+.2f}%) <span style="font-size:0.8rem; color:#8e8e93;">Aujourd'hui</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Graphique Pro Plotly
        st.plotly_chart(create_pro_chart(history_df, live_price, prev_close_24h, symbol), use_container_width=True, config={'displayModeBar': False})
        
        # (Optionnel) Sentiment IA simplifié pour le design
        sentiment_score = int(50 + change_pct * 2 + random.uniform(-2, 2))
        sentiment_score = max(1, min(100, sentiment_score))
        st.caption(f"Indice Sentiment IA (Expérimental) : {sentiment_score}/100")
        st.progress(sentiment_score)

    else:
        st.error("Impossible de récupérer les données de Binance pour le moment.")


# === ONGLET BOURSE (Simulation Simplifiée pour le design) ===
with tab_bourse:
    selected_stock = st.selectbox("Choisir un actif", 
                                  ["Microsoft (MSFT)", "Alphabet (GOOGL)", "Or (GOLD)"], 
                                  label_visibility="collapsed")
    
    stock_map = {"Microsoft (MSFT)": "MSFT", "Alphabet (GOOGL)": "GOOGL", "Or (GOLD)": "GOLD"}
    symbol = stock_map[selected_stock]
    
    # Simulation de données 24h pour le graphique
    live_price = get_live_price(symbol, is_crypto=False)
    dates = pd.date_range(end=datetime.now(), periods=24, freq='H')
    # Création d'une courbe aléatoire réaliste
    base = live_price * (1 - np.random.normal(0, 0.01))
    trend = np.linspace(base, live_price, 24) + np.random.normal(0, base*0.005, 24)
    history_df = pd.DataFrame({'timestamp': dates, 'close': trend})
    
    prev_close_24h = history_df.iloc[0]['close']
    change = live_price - prev_close_24h
    change_pct = (change / prev_close_24h) * 100
    color_class = "#30d158" if change >= 0 else "#ff453a"

    # Header style Apple
    st.markdown(f"""
        <div style="margin-top: 20px;">
            <div class="big-asset-title">{selected_stock}</div>
            <div class="big-price">${live_price:,.2f}</div>
            <div class="big-change" style="color: {color_class};">
                {change:+.2f} ({change_pct:+.2f}%) <span style="font-size:0.8rem; color:#8e8e93;">Aujourd'hui</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Graphique Pro Plotly
    st.plotly_chart(create_pro_chart(history_df, live_price, prev_close_24h, symbol), use_container_width=True, config={'displayModeBar': False})

# Note : Pas de st.rerun() automatique ici pour l'instant, car le chargement d'historique est lourd.
# L'utilisateur rafraîchit la page ou change d'actif pour mettre à jour. C'est plus stable pour une V3.
