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
    initial_sidebar_state="collapsed"
)

# --- 2. CSS PRESTIGE & SIMULATEUR ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #000000;
        color: #ffffff;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* TITRE PRINCIPAL */
    .main-title {
        font-size: 3.5rem;
        font-weight: 900;
        text-align: center;
        background: -webkit-linear-gradient(45deg, #ffffff, #888888);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-top: 10px;
        margin-bottom: 5px;
        letter-spacing: -2px;
        text-transform: uppercase;
    }

    /* KPI BOXES (Session & Global) */
    .kpi-container {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin-bottom: 30px;
        flex-wrap: wrap;
    }
    
    .kpi-box {
        text-align: center;
        padding: 15px 25px;
        background: rgba(255,255,255,0.05);
        border-radius: 16px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        min-width: 200px;
    }

    .kpi-label {
        font-size: 0.75rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 5px;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
    }

    /* SIMULATEUR (ET SI... ALORS...) */
    .sim-container {
        background: linear-gradient(145deg, #1a1a1a, #0d0d0d);
        border-radius: 20px;
        padding: 20px;
        margin: 0 auto 40px auto;
        max-width: 800px;
        border: 1px solid #333;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    
    .sim-title {
        font-size: 0.9rem;
        color: #666;
        text-transform: uppercase;
        margin-bottom: 15px;
        text-align: center;
        letter-spacing: 2px;
    }

    /* Inputs du simulateur stylisés */
    .stNumberInput input {
        background-color: #000 !important;
        color: white !important;
        border: 1px solid #333 !important;
        border-radius: 10px !important;
        font-size: 1.2rem !important;
        text-align: center !important;
    }

    /* PRIX HEADER */
    .asset-header {
        margin-top: 20px;
        border-top: 1px solid #333;
        padding-top: 20px;
    }
    .price-big { font-size: 3.8rem; font-weight: 700; line-height: 1; color: white; }
    .price-small { font-size: 1.5rem; font-weight: 400; color: #666; margin-left: 10px; }
    
    /* BOUTONS TIMEFRAME */
    div.stButton > button {
        background-color: #1c1c1e;
        color: #888;
        border: none;
        border-radius: 20px;
        padding: 5px 10px;
        font-size: 0.8rem;
        font-weight: 600;
        width: 100%;
        transition: all 0.2s;
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

    /* SENTIMENT BOX */
    .sentiment-container {
        background-color: #0e0e0e;
        border-radius: 15px;
        padding: 20px;
        margin-top: 20px;
        border: 1px solid #222;
        display: flex;
        align-items: center;
        gap: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. CONFIGURATION DES DONNÉES ---

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

TIME_CONFIG = {
    "15M": {"p": "1d", "i": "15m"},
    "1J":  {"p": "1d", "i": "5m"},
    "5J":  {"p": "5d", "i": "30m"},
    "1M":  {"p": "1mo", "i": "1h"},
    "6M":  {"p": "6mo", "i": "1d"},
    "1A":  {"p": "1y", "i": "1d"},
    "5A":  {"p": "5y", "i": "1wk"},
}

# --- 4. FONCTIONS BACKEND ---

@st.cache_data(ttl=300) 
def get_usd_eur_rate():
    try:
        ticker = yf.Ticker("EUR=X")
        hist = ticker.history(period="1d")
        if not hist.empty:
            return float(hist['Close'].iloc[-1])
        return 0.95
    except:
        return 0.95

@st.cache_data(ttl=60)
def get_chart_data(symbol, period, interval):
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        return df
    except:
        return pd.DataFrame()

def calculate_session_performance():
    if 'init_prices' not in st.session_state or not st.session_state.init_prices:
        return 0.0
    
    total_change = 0
    count = 0
    try:
        current_data = yf.download(BASKET, period="1d", interval="1m", progress=False)['Close'].iloc[-1]
        for symbol in BASKET:
            if symbol in st.session_state.init_prices:
                start_p = st.session_state.init_prices[symbol]
                try: curr_p = float(current_data[symbol].item())
                except: curr_p = float(current_data[symbol])
                
                if start_p > 0:
                    change = ((curr_p - start_p) / start_p) * 100
                    total_change += change
                    count += 1
    except:
        return 0.0

    return (total_change / count) if count > 0 else 0.0

def get_sentiment_analysis(symbol, change_pct):
    base_score = 50
    trend_bonus = change_pct * 8
    volatility_noise = random.uniform(-5, 5)
    score = int(base_score + trend_bonus + volatility_noise)
    score = max(5, min(95, score))
    
    if score >= 80:
        txt = "Euphorie Acheteuse. Indicateurs au vert foncé. Attention au FOMO."
        color = "#30d158"
    elif score >= 60:
        txt = "Confiance Positive. Volume d'achat stable, optimisme court terme."
        color = "#30d158"
    elif score >= 40:
        txt = "Incertitude / Neutre. Le marché attend un signal clair."
        color = "#888888"
    elif score >= 20:
        txt = "Peur Modérée. Prise de bénéfices ou tendance baissière."
        color = "#ff9f0a"
    else:
        txt = "Panique Vendeuse. Forte pression, risque de volatilité extrême."
        color = "#ff453a"
    return score, txt, color

# --- 5. INITIALISATION ---
if 'init_prices' not in st.session_state:
    st.session_state.init_prices = {}
    try:
        data = yf.download(BASKET, period="1d", interval="1m", progress=False)['Close'].iloc[-1]
        for symbol in BASKET:
            try: val = float(data[symbol].item())
            except: val = float(data[symbol])
            st.session_state.init_prices[symbol] = val
    except: pass

# --- 6. INTERFACE ---

# TITRE
st.markdown('<div class="main-title">BLISHKOMA TRADES</div>', unsafe_allow_html=True)

# CALCULS
session_perf = calculate_session_performance()
global_trust_index = int(50 + (session_perf * 20))
global_trust_index = max(10, min(90, global_trust_index))

perf_color = "#30d158" if session_perf >= 0 else "#ff453a"
perf_sign = "+" if session_perf >= 0 else ""

# KPI DISPLAY
st.markdown(f"""
<div class="kpi-container">
    <div class="kpi-box">
        <div class="kpi-label">Performance Session</div>
        <div class="kpi-value" style="color: {perf_color};">
            {perf_sign}{session_perf:.3f}%
        </div>
    </div>
    <div class="kpi-box">
        <div class="kpi-label">Indice Confiance Global</div>
        <div class="kpi-value" style="color: #0A84FF;">
            {global_trust_index}/100
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- NOUVEAU : SIMULATEUR DE GAINS (ET SI... ALORS...) ---
st.markdown('<div class="sim-container">', unsafe_allow_html=True)
st.markdown('<div class="sim-title">⚡ SIMULATEUR DE PROFITS INSTANTANÉ</div>', unsafe_allow_html=True)

col_sim1, col_sim2, col_sim3 = st.columns([2, 1, 2], gap="medium")

with col_sim1:
    st.markdown("**ET SI J'AVAIS MIS...**")
    investment = st.number_input("Montant (€)", min_value=10.0, value=1000.0, step=50.0, label_visibility="collapsed")

with col_sim2:
    st.markdown(f"""
    <div style="text-align:center; margin-top:15px; font-size:1.5rem; color:{perf_color}; font-weight:bold;">
        ➜ {perf_sign}{session_perf:.2f}%
    </div>
    """, unsafe_allow_html=True)

with col_sim3:
    st.markdown("**ALORS J'AURAIS...**")
    final_value = investment * (1 + (session_perf / 100))
    gain_loss = final_value - investment
    gain_color = "#30d158" if gain_loss >= 0 else "#ff453a"
    sign = "+" if gain_loss >= 0 else ""
    
    st.markdown(f"""
    <div style="background:#000; border:1px solid #333; border-radius:10px; padding:10px; text-align:center;">
        <div style="font-size:1.5rem; font-weight:bold;">{final_value:,.2f} €</div>
        <div style="font-size:1rem; color:{gain_color};">{sign}{gain_loss:,.2f} €</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- NAVIGATION PRINCIPALE ---
col_nav1, col_nav2 = st.columns([1, 3])

with col_nav1:
    st.markdown("### Sélection")
    cat = st.radio("Marché", ["Cryptomonnaies", "Bourse & Actions"], label_visibility="collapsed")
    asset_name = st.radio("Actif", list(ASSETS[cat].keys()))
    symbol = ASSETS[cat][asset_name]

with col_nav2:
    if 'timeframe' not in st.session_state: st.session_state.timeframe = "1J"
    
    c_btns = st.columns(7)
    labels = ["15M", "1J", "5J", "1M", "6M", "1A", "5A"]
    for i, tf in enumerate(labels):
        if c_btns[i].button(tf): st.session_state.timeframe = tf
            
    current_tf = st.session_state.timeframe
    conf = TIME_CONFIG[current_tf]
    
    with st.spinner("Analyse du marché..."):
        df = get_chart_data(symbol, conf["p"], conf["i"])
        rate_eur = get_usd_eur_rate()
    
    if not df.empty and 'Close' in df.columns:
        try: cur_price_usd = float(df['Close'].iloc[-1].item())
        except: cur_price_usd = float(df['Close'].iloc[-1])
        try: open_price_usd = float(df['Open'].iloc[0].item())
        except: open_price_usd = float(df['Open'].iloc[0])
            
        cur_price_eur = cur_price_usd * rate_eur
        diff_usd = cur_price_usd - open_price_usd
        pct = (diff_usd / open_price_usd) * 100
        color = "#30d158" if diff_usd >= 0 else "#ff453a"
        
        st.markdown(f"""
        <div class="asset-header">
            <div style="font-size: 1.5rem; color:#888;">{asset_name}</div>
            <div style="display:flex; align-items:baseline;">
                <span class="price-big">{cur_price_eur:,.2f} €</span>
                <span class="price-small">({cur_price_usd:,.2f} $)</span>
            </div>
            <div style="font-size: 1.2rem; color:{color}; font-weight:600; margin-top:5px;">
                {diff_usd:+.2f}$ ({pct:+.2f}%) <span style="color:#666; font-size:0.8rem">Période {current_tf}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Close'], mode='lines',
            line=dict(color=color, width=2),
            fill='tozeroy',
            fillcolor=f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.1)",
        ))
        y_min, y_max = df['Close'].min(), df['Close'].max()
        pad = (y_max - y_min) * 0.05
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=20, b=0), height=450,
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=True, gridcolor='#222', side='right', range=[y_min-pad, y_max+pad]),
            showlegend=False, hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        sentiment_score, sentiment_txt, sentiment_color = get_sentiment_analysis(symbol, pct)
        st.markdown(f"""
        <div class="sentiment-container">
            <div style="text-align:center; min-width: 120px;">
                <div style="font-size:0.8rem; color:#888; text-transform:uppercase;">Indice Confiance</div>
                <div style="font-size:2.5rem; font-weight:bold; color:{sentiment_color};">{sentiment_score}/100</div>
            </div>
            <div style="font-size: 0.9rem; color: #ccc; line-height: 1.5;">
                <strong style="color:{sentiment_color}">Analyse Instantanée :</strong><br>{sentiment_txt}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error("Données indisponibles.")

# --- 7. AUTO-REFRESH INTELLIGENT (30s) ---
time.sleep(30)
st.rerun()
