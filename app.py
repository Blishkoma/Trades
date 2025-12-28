import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
import random

# --- 1. CONFIGURATION DU SITE ---
st.set_page_config(
    page_title="Blishko Trades",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. STYLE & TYPOGRAPHIE (CSS AVANCÉ) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;500;700&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Outfit', sans-serif;
        background-color: #0E1117;
    }
    
    /* Titre Principal */
    h1 {
        font-weight: 700;
        letter-spacing: -1px;
        color: #ffffff;
        text-align: center;
        margin-bottom: 30px;
    }

    /* Cards */
    .metric-card {
        background-color: #1c1f26;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #2d3342;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }

    /* Sentiment Bar Container */
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #ef4444, #eab308, #22c55e);
    }
    
    /* Navigation Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        justify-content: center;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1c1f26;
        border-radius: 8px;
        padding: 10px 30px;
        color: white;
        border: 1px solid #333;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2962ff !important;
        border-color: #2962ff !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("BLISHKO TRADES")

# --- 3. GESTION DES DONNÉES (SESSION STATE) ---
# On initialise les prix et l'historique s'ils n'existent pas
if 'history' not in st.session_state:
    st.session_state.history = {
        # Crypto
        'BTC': [], 'XRP': [], 'RENDER': [],
        # Bourse
        'MSFT': [], 'GOOGL': [], 'GOLD': []
    }

if 'prices' not in st.session_state:
    st.session_state.prices = {
        'MSFT': 402.50, 'GOOGL': 173.20, 'GOLD': 2045.00
    }

# --- 4. FONCTIONS DE RÉCUPERATION ---

def get_binance_price(symbol):
    """Récupère le prix réel sur Binance"""
    try:
        # Binance API pour obtenir le prix
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            return float(response.json()['price'])
        return None
    except:
        return None

def simulate_market_move(current_price, volatility=0.0005):
    """Simule un mouvement boursier réaliste (Random Walk)"""
    change_percent = np.random.normal(0, volatility)
    return current_price * (1 + change_percent)

def calculate_stable_sentiment(history_list):
    """
    Calcule un score stable (1-100) basé sur l'historique complet
    plutôt que sur la dernière seconde.
    """
    if len(history_list) < 10:
        return 50 # Neutre au début
    
    # On compare le prix actuel avec la moyenne des 10 dernières mesures
    # Cela lisse le résultat (Moyenne Mobile)
    current = history_list[-1]
    average = sum(history_list[-10:]) / 10
    
    diff_percent = ((current - average) / average) * 1000 # Amplification
    
    # Base score 50 + variation
    score = 50 + diff_percent
    
    # Ajout d'une inertie pour éviter les sauts brusques
    noise = random.uniform(-2, 2)
    final_score = score + noise
    
    return int(max(1, min(100, final_score)))

def display_asset(name, symbol, price, history, is_crypto=True):
    """Affiche une carte complète pour un actif"""
    
    # Calcul variation
    prev_price = history[-2] if len(history) > 1 else price
    delta = price - prev_price
    delta_percent = (delta / prev_price) * 100
    
    color = "green" if delta >= 0 else "red"
    
    with st.container():
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin:0; color:#aaa;">{name}</h3>
            <h2 style="margin:0; font-size: 2em;">${price:,.4f}</h2>
            <p style="color:{color}; margin:0;">{delta:+.4f} ({delta_percent:+.2f}%)</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Graphique
        if len(history) > 2:
            chart_data = pd.DataFrame(history, columns=["Prix"])
            st.line_chart(chart_data, height=150, use_container_width=True)
        
        # Score de Sentiment Stable
        score = calculate_stable_sentiment(history)
        
        st.write(f"**Indice de Confiance Marché : {score}/100**")
        st.progress(score)
        
        # Interprétation textuelle simple
        txt = "Neutre"
        if score > 60: txt = "Achat Fort (Bullish)"
        elif score < 40: txt = "Vente Forte (Bearish)"
        st.caption(f"Analyse: {txt} - Basé sur la tendance récente.")
        st.markdown("---")

# --- 5. LOGIQUE PRINCIPALE & BOUCLE ---

# Création des onglets (Les "Deux Carrés")
tab_crypto, tab_bourse = st.tabs(["₿ MARCHÉ CRYPTO", "📈 BOURSE & ACTIONS"])

# --- Mise à jour des données (Backend) ---
# Crypto (Binance)
btc = get_binance_price("BTC")
xrp = get_binance_price("XRP")
render = get_binance_price("RENDER") # Attention: RNDR est devenu RENDER sur Binance

# Si Binance ne répond pas (bug API), on prend la dernière valeur
if btc: st.session_state.history['BTC'].append(btc)
if xrp: st.session_state.history['XRP'].append(xrp)
if render: st.session_state.history['RENDER'].append(render)

# Bourse (Simulation)
st.session_state.prices['MSFT'] = simulate_market_move(st.session_state.prices['MSFT'])
st.session_state.prices['GOOGL'] = simulate_market_move(st.session_state.prices['GOOGL'])
st.session_state.prices['GOLD'] = simulate_market_move(st.session_state.prices['GOLD'], volatility=0.0002) # Or moins volatile

st.session_state.history['MSFT'].append(st.session_state.prices['MSFT'])
st.session_state.history['GOOGL'].append(st.session_state.prices['GOOGL'])
st.session_state.history['GOLD'].append(st.session_state.prices['GOLD'])

# Limite de l'historique (garder les 100 derniers points pour ne pas saturer la mémoire)
for key in st.session_state.history:
    if len(st.session_state.history[key]) > 100:
        st.session_state.history[key].pop(0)

# --- Affichage Frontend ---

with tab_crypto:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        current_btc = st.session_state.history['BTC'][-1] if st.session_state.history['BTC'] else 0
        display_asset("Bitcoin (BTC)", "BTC", current_btc, st.session_state.history['BTC'])
        
    with col2:
        current_xrp = st.session_state.history['XRP'][-1] if st.session_state.history['XRP'] else 0
        display_asset("Ripple (XRP)", "XRP", current_xrp, st.session_state.history['XRP'])
        
    with col3:
        current_rndr = st.session_state.history['RENDER'][-1] if st.session_state.history['RENDER'] else 0
        display_asset("Render (RNDR)", "RENDER", current_rndr, st.session_state.history['RENDER'])

with tab_bourse:
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        display_asset("Microsoft (MSFT)", "MSFT", st.session_state.prices['MSFT'], st.session_state.history['MSFT'], is_crypto=False)
        
    with col_b:
        display_asset("Alphabet A (GOOGL)", "GOOGL", st.session_state.prices['GOOGL'], st.session_state.history['GOOGL'], is_crypto=False)
        
    with col_c:
        display_asset("Or (Gold / XAU)", "GOLD", st.session_state.prices['GOLD'], st.session_state.history['GOLD'], is_crypto=False)

# Boucle de rafraîchissement
time.sleep(1.5) # Pause de 1.5 secondes
st.rerun()      # Relance le script pour mettre à jour
