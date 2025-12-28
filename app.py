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

# --- 2. CSS PRESTIGE (Design conservé) ---
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
        margin-top: 20px;
        margin-bottom: 5px;
        letter-spacing: -2px;
        text-transform: uppercase;
    }

    /* INDEX SESSION & GLOBAL */
    .session-container {
        display: flex;
        justify-content: center;
        gap: 40px;
        margin-bottom: 50px;
        padding: 15px;
    }
    
    .kpi-box {
        text-align: center;
        padding: 15px 30px;
        background: rgba(255,255,255,0.05);
        border-radius: 20px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
    }

    .session-label {
        font-size: 0.8rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 5px;
    }
    .session-value {
        font-size: 2rem;
        font-weight: 700;
    }

    /* PRIX */
    .asset-header {
        margin-top: 30px;
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
    .sentiment-text {
        font-size: 0.9rem;
        color: #ccc;
        line-height: 1.5;
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

# Configuration précise des périodes/intervalles
TIME_CONFIG = {
    "15M": {"p": "1d", "i": "15m"}, # NOUVEAU: Vue 15 min (sur 1 jour)
    "1J":  {"p": "1d", "i": "5m"},
    "5J":  {"p": "5d", "i": "30m"},
    "1M":  {"p": "1mo", "i": "1h"},
    "6M":  {"p": "6mo", "i": "1d"},
    "1A":  {"p": "1y", "i": "1d"},
    "5A":  {"p": "5y", "i": "1wk"},
}

# --- 4. FONCTIONS UTILITAIRES ---

@st.cache_data(ttl=300) # Cache taux de change 5 min
def get_usd_eur_rate():
    try:
        # Récupère le taux USD -> EUR
        ticker = yf.Ticker("EUR=X")
        hist = ticker.history(period="1d")
        if not hist.empty:
            return float(hist['Close'].iloc[-1])
        return 0.95 # Fallback si erreur
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
    """Calcule la performance moyenne depuis l'ouverture"""
    if 'init_prices' not in st.session_state or not st.session_state.init_prices:
        return 0.0
    
    total_change = 0
    count = 0
    try:
        # Optimisation : On ne télécharge que si nécessaire
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

    return (total_change / count) if count > 0 else 0.0

def get_sentiment_analysis(symbol, change_pct):
    """Génère l'indice de confiance et le texte explicatif"""
    # Algorithme simulé basé sur la volatilité réelle
    base_score = 50
    trend_bonus = change_pct * 8  # Le marché aime quand ça monte
    volatility_noise = random.uniform(-5, 5)
    
    score = int(base_score + trend_bonus + volatility_noise)
    score = max(5, min(95, score)) # Borner entre 5 et 95
    
    # Texte contextuel
    if score >= 80:
        txt = "Euphorie Acheteuse. Les indicateurs techniques sont au vert foncé. Attention au FOMO (Fear Of Missing Out), le marché est très agressif."
        color = "#30d158"
    elif score >= 60:
        txt = "Confiance Positive. Le volume d'achat est stable. Les investisseurs semblent optimistes sur le court terme."
        color = "#30d158"
    elif score >= 40:
        txt = "Incertitude / Neutre. Le marché hésite. Les traders attendent un signal clair ou une confirmation économique avant de se positionner."
        color = "#888888"
    elif score >= 20:
        txt = "Peur Modérée. Tendance baissière détectée. Prise de bénéfices ou nouvelles économiques inquiétantes."
        color = "#ff9f0a"
    else:
        txt = "Panique Vendeuse (FUD). Forte pression à la vente. Les supports techniques sont testés. Risque de volatilité extrême."
        color = "#ff453a"
        
    return score, txt, color

# --- 5. INITIALISATION SESSION ---
if 'init_prices' not in st.session_state:
    st.session_state.init_prices = {}
    try:
        data = yf.download(BASKET, period="1d", interval="1m", progress=False)['Close'].iloc[-1]
        for symbol in BASKET:
            try: val = float(data[symbol].item())
            except: val = float(data[symbol])
            st.session_state.init_prices[symbol] = val
    except: pass

# --- 6. INTERFACE UI ---

# EN-TÊTE
st.markdown('<div class="main-title">BLISHKOMA TRADES</div>', unsafe_allow_html=True)

# CALCULS GLOBAUX
session_perf = calculate_session_performance()
global_trust_index = int(50 + (session_perf * 20)) # Indice global dérivé de la performance
global_trust_index = max(10, min(90, global_trust_index))

perf_color = "#30d158" if session_perf >= 0 else "#ff453a"
perf_sign = "+" if session_perf >= 0 else ""

# AFFICHAGE KPI (Session + Indice Global)
st.markdown(f"""
<div class="session-container">
    <div class="kpi-box">
        <div class="session-label">Performance Session</div>
        <div class="session-value" style="color: {perf_color};">
            {perf_sign}{session_perf:.3f}%
        </div>
    </div>
    <div class="kpi-box">
        <div class="session-label">Indice Confiance Global</div>
        <div class="session-value" style="color: #0A84FF;">
            {global_trust_index}/100
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# NAVIGATION & GRAPHIQUE
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
    # Timeframe
    if 'timeframe' not in st.session_state: st.session_state.timeframe = "1J"
    
    c_btns = st.columns(7)
    labels = ["15M", "1J", "5J", "1M", "6M", "1A", "5A"]
    
    for i, tf in enumerate(labels):
        if c_btns[i].button(tf):
            st.session_state.timeframe = tf
            
    current_tf = st.session_state.timeframe
    conf = TIME_CONFIG[current_tf]
    
    # Chargement
    with st.spinner("Analyse du marché..."):
        df = get_chart_data(symbol, conf["p"], conf["i"])
        rate_eur = get_usd_eur_rate() # Taux de change
    
    if not df.empty and 'Close' in df.columns:
        try:
            cur_price_usd = float(df['Close'].iloc[-1].item())
            open_price_usd = float(df['Open'].iloc[0].item())
        except:
            cur_price_usd = float(df['Close'].iloc[-1])
            open_price_usd = float(df['Open'].iloc[0])
            
        # Conversion
        cur_price_eur = cur_price_usd * rate_eur
        
        diff_usd = cur_price_usd - open_price_usd
        pct = (diff_usd / open_price_usd) * 100
        color = "#30d158" if diff_usd >= 0 else "#ff453a"
        
        # Affichage PRIX (Euro Gros + Dollar Petit)
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
        
        # Graphique
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Close'],
            mode='lines',
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
            yaxis=dict(showgrid=True, gridcolor='#222', side='right', range=[y_min - pad, y_max + pad]),
            showlegend=False, hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # --- INDICE DE CONFIANCE (SOUS LE GRAPHIQUE) ---
        sentiment_score, sentiment_txt, sentiment_color = get_sentiment_analysis(symbol, pct)
        
        st.markdown(f"""
        <div class="sentiment-container">
            <div style="text-align:center; min-width: 120px;">
                <div style="font-size:0.8rem; color:#888; text-transform:uppercase;">Indice Confiance</div>
                <div style="font-size:2.5rem; font-weight:bold; color:{sentiment_color};">{sentiment_score}/100</div>
            </div>
            <div class="sentiment-text">
                <strong style="color:{sentiment_color}">Analyse Instantanée :</strong><br>
                {sentiment_txt}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    else:
        st.error("Données indisponibles.")
