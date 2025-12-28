import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import time
import random

# --- 1. CONFIGURATION DU SITE ---
st.set_page_config(
    page_title="Blishkoma Trades",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed" # Barre latérale cachée par défaut pour le look "App"
)

# --- 2. CSS "PRESTIGE" (Design Moderne & Centré) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #000000;
        color: #ffffff;
    }

    /* Cacher les éléments parasites de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* TITRE PRINCIPAL (LOGO) */
    .main-title {
        font-size: 3.5rem;
        font-weight: 900;
        text-align: center;
        background: -webkit-linear-gradient(45deg, #ffffff, #888888);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-top: 20px;
        margin-bottom: 5px;
        letter-spacing: -2px;
        text-transform: uppercase;
    }

    /* INDEX SESSION (Le chiffre sous le titre) */
    .session-container {
        text-align: center;
        margin-bottom: 50px;
        padding: 20px;
        background: rgba(255,255,255,0.05);
        border-radius: 20px;
        backdrop-filter: blur(10px);
        width: fit-content;
        margin-left: auto;
        margin-right: auto;
    }
    .session-label {
        font-size: 0.9rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .session-value {
        font-size: 2.5rem;
        font-weight: 700;
    }

    /* DÉTAILS ACTIF (Partie basse) */
    .asset-header {
        margin-top: 30px;
        border-top: 1px solid #333;
        padding-top: 20px;
    }
    .price-big { font-size: 4rem; font-weight: 700; line-height: 1; }
    
    /* BOUTONS TIMEFRAME */
    div.stButton > button {
        background-color: #1c1c1e;
        color: #888;
        border: none;
        border-radius: 20px;
        padding: 5px 20px;
        font-size: 0.9rem;
        font-weight: 600;
        width: 100%;
    }
    div.stButton > button:hover {
        background-color: #333;
        color: white;
    }
    div.stButton > button:focus {
        background-color: #333;
        color: #0A84FF;
        border: 1px solid #0A84FF;
    }

</style>
""", unsafe_allow_html=True)

# --- 3. DONNÉES & SESSION ---

# Liste réduite pour la performance globale (pour que ça charge vite)
BASKET = ["BTC-USD", "ETH-USD", "AAPL", "MSFT", "TSLA"]

ASSETS = {
    "Cryptomonnaies": {
        "Bitcoin": "BTC-USD",
        "Ethereum": "ETH-USD",
        "Ripple": "XRP-USD",
        "Render": "RNDR-USD",
        "Solana": "SOL-USD"
    },
    "Bourse & Actions": {
        "Apple": "AAPL",
        "Microsoft": "MSFT",
        "Alphabet": "GOOGL",
        "Tesla": "TSLA",
        "Or (Gold)": "GC=F"
    }
}

TIMEFRAMES = {"1J": "1d", "5J": "5d", "1M": "1mo", "6M": "6mo", "1A": "1y", "5A": "5y"}
INTERVALS = {"1d": "5m", "5d": "15m", "1mo": "1h", "6mo": "1d", "1y": "1d", "5y": "1wk"}

# --- INITIALISATION DE LA SESSION (PERFORMANCE DEPUIS ARRIVÉE) ---
if 'init_prices' not in st.session_state:
    st.session_state.init_prices = {}
    st.session_state.start_time = time.time()
    
    # On récupère les prix initiaux du panier au premier chargement
    try:
        data = yf.download(BASKET, period="1d", interval="1m", progress=False)['Close'].iloc[-1]
        for symbol in BASKET:
            # Gestion sécurité si yfinance renvoie format complexe
            try:
                price = float(data[symbol].item())
            except:
                price = float(data[symbol])
            st.session_state.init_prices[symbol] = price
    except:
        pass # Si erreur réseau au démarrage, on ignore

# --- FONCTIONS ---

@st.cache_data(ttl=60)
def get_chart_data(symbol, period, interval):
    """Récupère les données historiques"""
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        return df
    except:
        return pd.DataFrame()

def calculate_session_performance():
    """Calcule la moyenne de variation du panier depuis l'ouverture du site"""
    if not st.session_state.init_prices:
        return 0.0
    
    total_change = 0
    count = 0
    
    # On récupère les prix actuels
    try:
        current_data = yf.download(BASKET, period="1d", interval="1m", progress=False)['Close'].iloc[-1]
        for symbol in BASKET:
            if symbol in st.session_state.init_prices:
                start_p = st.session_state.init_prices[symbol]
                try:
                    curr_p = float(current_data[symbol].item())
                except:
                    curr_p = float(current_data[symbol])
                
                if start_p > 0:
                    change = ((curr_p - start_p) / start_p) * 100
                    total_change += change
                    count += 1
    except:
        return 0.0

    if count == 0: return 0.0
    return total_change / count

# --- 4. INTERFACE UTILISATEUR ---

# A. EN-TÊTE CENTRÉ (HERO SECTION)
st.markdown('<div class="main-title">BLISHKOMA TRADES</div>', unsafe_allow_html=True)

# Calcul Performance Session
session_perf = calculate_session_performance()
perf_color = "#30d158" if session_perf >= 0 else "#ff453a"
perf_sign = "+" if session_perf >= 0 else ""

st.markdown(f"""
<div class="session-container">
    <div class="session-label">Performance Session (Moyenne Marché)</div>
    <div class="session-value" style="color: {perf_color};">
        {perf_sign}{session_perf:.3f}%
    </div>
</div>
""", unsafe_allow_html=True)


# B. SÉLECTION ET GRAPHIQUE (Partie Basse)
col_nav1, col_nav2 = st.columns([1, 3])

with col_nav1:
    st.markdown("### Sélection")
    cat = st.radio("Marché", ["Cryptomonnaies", "Bourse & Actions"], label_visibility="collapsed")
    asset_name = st.radio("Actif", list(ASSETS[cat].keys()))
    symbol = ASSETS[cat][asset_name]
    
    if st.button("🔄 Rafraîchir"):
        st.cache_data.clear()
        st.rerun()

with col_nav2:
    # Gestion Timeframe
    if 'timeframe' not in st.session_state: st.session_state.timeframe = "1J"
    
    # Boutons Timeframe Alignés
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    labels = ["1J", "5J", "1M", "6M", "1A", "5A"]
    cols = [c1, c2, c3, c4, c5, c6]
    
    for i, tf in enumerate(labels):
        if cols[i].button(tf, key=f"btn_{tf}"):
            st.session_state.timeframe = tf
            
    current_tf = st.session_state.timeframe
    
    # Chargement Données
    with st.spinner("Chargement des données..."):
        df = get_chart_data(symbol, TIMEFRAMES[current_tf], INTERVALS[TIMEFRAMES[current_tf]])
    
    if not df.empty and 'Close' in df.columns:
        # Valeurs
        try:
            cur_price = float(df['Close'].iloc[-1].item())
            open_price = float(df['Open'].iloc[0].item())
        except:
            cur_price = float(df['Close'].iloc[-1])
            open_price = float(df['Open'].iloc[0])
            
        diff = cur_price - open_price
        pct = (diff / open_price) * 100
        color = "#30d158" if diff >= 0 else "#ff453a"
        
        # Affichage Prix Gros
        st.markdown(f"""
        <div class="asset-header">
            <div style="font-size: 1.5rem; color:#888;">{asset_name}</div>
            <div class="price-big">${cur_price:,.2f}</div>
            <div style="font-size: 1.2rem; color:{color}; font-weight:600;">
                {diff:+.2f} ({pct:+.2f}%) <span style="color:#666; font-size:0.8rem">Since {current_tf}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # --- GRAPHIQUE CORRIGÉ (ZOOM DYNAMIQUE) ---
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Close'],
            mode='lines',
            line=dict(color=color, width=2),
            fill='tozeroy',
            fillcolor=f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.1)",
            hoverinfo='y'
        ))
        
        # Calcul du range Y pour éviter la "ligne plate"
        y_min = df['Close'].min()
        y_max = df['Close'].max()
        padding = (y_max - y_min) * 0.05 # 5% de marge
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=20, b=0),
            height=450,
            xaxis=dict(showgrid=False, showticklabels=False), # Pas de grille X
            yaxis=dict(
                showgrid=True, 
                gridcolor='#222', 
                side='right', 
                range=[y_min - padding, y_max + padding], # FORCE LE ZOOM
                tickformat=".2f"
            ),
            showlegend=False,
            hovermode="x unified"
        )
        
        # Désactiver la barre d'outils (le truc moche en haut à droite)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
    else:
        st.error("Données indisponibles. Le marché est peut-être fermé ou l'actif non trouvé.")
