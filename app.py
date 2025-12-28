import streamlit as st
import time
import random
import requests
import pandas as pd
import numpy as np

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Sentinel Market AI",
    page_icon="⚡",
    layout="wide"
)

# Custom CSS pour le look "Dark Mode Finance"
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: white; }
    div[data-testid="stMetricValue"] { font-family: monospace; }
    .sentiment-box {
        padding: 10px; border-radius: 5px; text-align: center; margin-top: 10px; font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Sentinel Market AI")
st.markdown("### Analyse Prix & Sentiment (Twitter/News) en Temps Réel")

# --- FONCTIONS ---

def get_binance_price(symbol):
    """Récupère le vrai prix depuis Binance"""
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        response = requests.get(url)
        data = response.json()
        return float(data['price'])
    except:
        return 0.0

def simulate_stock_price(current_price):
    """Simule un mouvement boursier (car les API boursières temps réel sont payantes)"""
    change = (random.random() - 0.5) * 0.5
    return current_price + change

def analyze_sentiment_ai(symbol, price_change):
    """
    C'est ici que tu mettras ton IA plus tard.
    Pour l'instant, on simule une IA qui réagit à la volatilité.
    """
    # Base score aléatoire autour de 50
    score = 50 + (random.randint(-5, 5)) 
    
    # Si le prix monte, l'IA détecte de l'euphorie (FOMO)
    if price_change > 0:
        score += random.randint(5, 15)
    else:
        score -= random.randint(5, 15)
        
    # Bornes 1-100
    score = max(1, min(100, score))
    
    # Génération d'une phrase d'analyse factice
    phrases = [
        "Scan Twitter: Forte activité...", 
        "Reddit: Les traders sont inquiets...", 
        "News: Rumeur d'achat institutionnel...", 
        "Analyse technique: Support touché...",
        "Volatilité anormale détectée..."
    ]
    log = random.choice(phrases)
    
    return score, log

def display_sentiment_bar(score, log):
    """Affiche ta barre de sentiment 0-100"""
    color = "red"
    if score > 40: color = "orange"
    if score > 60: color = "green"
    
    st.progress(score)
    st.markdown(f"""
    <div class="sentiment-box" style="border: 1px solid {color}; color: {color};">
        SCORE IA: {score}/100 <br>
        <span style="font-size:0.8em; color: #888;">{log}</span>
    </div>
    """, unsafe_allow_html=True)

# --- INITIALISATION DES VARIABLES (SESSION STATE) ---
if 'tsla_price' not in st.session_state:
    st.session_state.tsla_price = 240.50
if 'aapl_price' not in st.session_state:
    st.session_state.aapl_price = 185.20
if 'history' not in st.session_state:
    st.session_state.history = {'BTC': [], 'ETH': [], 'TSLA': [], 'AAPL': []}

# --- BOUCLE PRINCIPALE ---
# Création des colonnes
col1, col2, col3, col4 = st.columns(4)

# Placeholders (zones vides qu'on va remplir à chaque seconde)
with col1:
    st.markdown("### ₿ Bitcoin")
    btc_metric = st.empty()
    btc_chart = st.empty()
    btc_sentiment = st.empty()

with col2:
    st.markdown("### Ξ Ethereum")
    eth_metric = st.empty()
    eth_chart = st.empty()
    eth_sentiment = st.empty()

with col3:
    st.markdown("### 🚗 Tesla (Sim)")
    tsla_metric = st.empty()
    tsla_chart = st.empty()
    tsla_sentiment = st.empty()

with col4:
    st.markdown("### 🍎 Apple (Sim)")
    aapl_metric = st.empty()
    aapl_chart = st.empty()
    aapl_sentiment = st.empty()

# Boucle d'actualisation infinie
while True:
    # 1. Récupération des Données
    btc_price = get_binance_price("BTCUSDT")
    eth_price = get_binance_price("ETHUSDT")
    
    st.session_state.tsla_price = simulate_stock_price(st.session_state.tsla_price)
    st.session_state.aapl_price = simulate_stock_price(st.session_state.aapl_price)

    # Mise à jour historique pour les graphiques
    for symbol, price in [('BTC', btc_price), ('ETH', eth_price), 
                          ('TSLA', st.session_state.tsla_price), ('AAPL', st.session_state.aapl_price)]:
        st.session_state.history[symbol].append(price)
        if len(st.session_state.history[symbol]) > 30: # Garder les 30 dernières secondes
            st.session_state.history[symbol].pop(0)

    # 2. Affichage BTC
    prev_btc = st.session_state.history['BTC'][-2] if len(st.session_state.history['BTC']) > 1 else btc_price
    btc_diff = btc_price - prev_btc
    btc_metric.metric("Prix", f"${btc_price:,.2f}", f"{btc_diff:.2f}")
    btc_chart.line_chart(st.session_state.history['BTC'], height=150)
    s_score, s_log = analyze_sentiment_ai("BTC", btc_diff)
    with btc_sentiment.container():
        display_sentiment_bar(s_score, s_log)

    # 3. Affichage ETH
    prev_eth = st.session_state.history['ETH'][-2] if len(st.session_state.history['ETH']) > 1 else eth_price
    eth_diff = eth_price - prev_eth
    eth_metric.metric("Prix", f"${eth_price:,.2f}", f"{eth_diff:.2f}")
    eth_chart.line_chart(st.session_state.history['ETH'], height=150)
    s_score, s_log = analyze_sentiment_ai("ETH", eth_diff)
    with eth_sentiment.container():
        display_sentiment_bar(s_score, s_log)

    # 4. Affichage Tesla
    tsla_diff = st.session_state.tsla_price - (st.session_state.history['TSLA'][-2] if len(st.session_state.history['TSLA']) > 1 else st.session_state.tsla_price)
    tsla_metric.metric("Prix", f"${st.session_state.tsla_price:.2f}", f"{tsla_diff:.2f}")
    tsla_chart.line_chart(st.session_state.history['TSLA'], height=150)
    s_score, s_log = analyze_sentiment_ai("TSLA", tsla_diff)
    with tsla_sentiment.container():
        display_sentiment_bar(s_score, s_log)

    # 5. Affichage Apple
    aapl_diff = st.session_state.aapl_price - (st.session_state.history['AAPL'][-2] if len(st.session_state.history['AAPL']) > 1 else st.session_state.aapl_price)
    aapl_metric.metric("Prix", f"${st.session_state.aapl_price:.2f}", f"{aapl_diff:.2f}")
    aapl_chart.line_chart(st.session_state.history['AAPL'], height=150)
    s_score, s_log = analyze_sentiment_ai("AAPL", aapl_diff)
    with aapl_sentiment.container():
        display_sentiment_bar(s_score, s_log)

    # Pause de 1 seconde avant la prochaine boucle
    time.sleep(1)
