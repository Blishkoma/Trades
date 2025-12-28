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
    
    h1 {
        font-weight: 700;
        letter-spacing: -1px;
        color: #ffffff;
        text-align: center;
        margin-bottom: 30px;
    }

    .metric-card {
        background-color: #1c1f26;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #2d3342;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }

    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #ef4444, #eab308, #22c55e);
    }
    
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
if 'history' not in st.session_state:
    st.session_state.history = {
        'BTC': [], 'XRP': [], 'RENDER': [],
        'MSFT': [], 'GOOGL': [], 'GOLD': []
    }

if 'prices' not in st.session_state:
    st.session_state.prices = {
        'MSFT': 402.50, 'GOOGL': 173.20, 'GOLD': 2045.00
    }

# --- 4. FONCTIONS ---

def get_binance_price(symbol):
    """Récupère le prix réel sur Binance"""
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            return float(response.json()['price'])
        return None
    except:
        return None

def simulate_market_move(current_price, volatility=0.0005):
    """Simule la bourse (marché fermé le weekend ou données payantes)"""
    change_percent = np.random.normal(0, volatility)
    return current_price * (1 + change_percent)

def calculate_stable_sentiment(history_list):
    """Calcule un score stable (1-100)"""
    if len(history_list) < 5:
        return 50 
    
    current = history_list[-1]
    average = sum(history_list[-10:]) / 10 if len(history_list) >= 10 else sum(history_list) / len(history_list)
    
    if average == 0: return 50 # Sécurité anti-crash

    diff_percent = ((current - average) / average) * 1000
    score = 50 + diff_percent
    noise = random.uniform(-1, 1)
    final_score = score + noise
    
    return int(max(1, min(100, final_score)))

def display_asset(name, symbol, price, history, is_crypto=True):
    """Affiche une carte complète pour un actif"""
    
    # 1. Sécurité : Si le prix est 0 (chargement), on affiche un message d'attente
    if price == 0 or price is None:
        st.warning(f"Chargement de {name}...")
        return

    # 2. Calcul variation (Sécurisé contre la division par zéro)
    prev_price = history[-2] if len(history) > 1 else price
    delta = price - prev_price
    
    if prev_price > 0:
        delta_percent = (delta / prev_price) * 100
    else:
        delta_percent = 0.0
    
    color = "green" if delta >= 0 else "red"
    
    # 3. Affichage
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
        
        # Score de Sentiment
        score = calculate_stable_sentiment(history)
        st.write(f"**Indice de Confiance Marché : {score}/100**")
        st.progress(score)
        
        txt = "Neutre"
        if score > 60: txt = "Achat Fort (Bullish)"
        elif score < 40: txt = "Vente Forte (Bearish)"
        st.caption(f"Analyse: {txt}")
        st.markdown("---")

# --- 5. LOGIQUE PRINCIPALE ---

tab_crypto, tab_bourse = st.tabs(["₿ MARCHÉ CRYPTO", "📈 BOURSE & ACTIONS"])

# --- Mise à jour des données ---
# Crypto (Vrais prix Binance)
# Note : RENDER s'appelle parfois RNDR ou RENDER sur l'API, on tente RENDER
btc = get_binance_price("BTC")
xrp = get_binance_price("XRP")
render = get_binance_price("RENDER") 

# Ajout à l'historique seulement si on a reçu un prix valide
if btc: st.session_state.history['BTC'].append(btc)
if xrp: st.session_state.history['XRP'].append(xrp)
if render: st.session_state.history['RENDER'].append(render)

# Bourse (Simulation)
st.session_state.prices['MSFT'] = simulate_market_move(st.session_state.prices['MSFT'])
st.session_state.prices['GOOGL'] = simulate_market_move(st.session_state.prices['GOOGL'])
st.session_state.prices['GOLD'] = simulate_market_move(st.session_state.prices['GOLD'], volatility=0.0002)

st.session_state.history['MSFT'].append(st.session_state.prices['MSFT'])
st.session_state.history['GOOGL'].append(st.session_state.prices['GOOGL'])
st.session_state.history['GOLD'].append(st.session_state.prices['GOLD'])

# Nettoyage historique (max 100 points)
for key in st.session_state.history:
    if len(st.session_state.history[key]) > 100:
        st.session_state.history[key].pop(0)

# --- Affichage ---

with tab_crypto:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # On récupère le dernier prix, ou 0 si la liste est vide
        curr = st.session_state.history['BTC'][-1] if st.session_state.history['BTC'] else 0
        display_asset("Bitcoin (BTC)", "BTC", curr, st.session_state.history['BTC'])
        
    with col2:
        curr = st.session_state.history['XRP'][-1] if st.session_state.history['XRP'] else 0
        display_asset("Ripple (XRP)", "XRP", curr, st.session_state.history['XRP'])
        
    with col3:
        curr = st.session_state.history['RENDER'][-1] if st.session_state.history['RENDER'] else 0
        display_asset("Render (RNDR)", "RENDER", curr, st.session_state.history['RENDER'])

with tab_bourse:
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        display_asset("Microsoft (MSFT)", "MSFT", st.session_state.prices['MSFT'], st.session_state.history['MSFT'], is_crypto=False)
    with col_b:
        display_asset("Alphabet (GOOGL)", "GOOGL", st.session_state.prices['GOOGL'], st.session_state.history['GOOGL'], is_crypto=False)
    with col_c:
        display_asset("Or (Gold)", "GOLD", st.session_state.prices['GOLD'], st.session_state.history['GOLD'], is_crypto=False)

# Rechargement automatique
time.sleep(1.5)
st.rerun()
