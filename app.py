import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import random

# --- 1. CONFIGURATION GÉNÉRALE ---
st.set_page_config(
    page_title="Blishko Trades",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PRO (Style Apple Dark) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #000000;
        color: #ffffff;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1c1c1e;
        border-right: 1px solid #333;
    }
    
    /* Boutons de période */
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

    /* Textes */
    .price-large { font-size: 3.5rem; font-weight: 700; margin: 0; line-height: 1; }
    .price-change { font-size: 1.2rem; font-weight: 500; margin-top: 5px; }
    
    /* Box Sentiment */
    .sentiment-box {
        background-color: #1c1c1e;
        padding: 20px;
        border-radius: 12px;
        margin-top: 20px;
        border: 1px solid #333;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. DONNÉES ---

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
        "Alphabet": "GOOGL",
        "Tesla": "TSLA",
        "Or (Gold)": "GC=F"
    }
}

TIMEFRAMES = {"1J": "1d", "5J": "5d", "1M": "1mo", "6M": "6mo", "1A": "1y", "5A": "5y"}
INTERVALS = {"1d": "5m", "5d": "15m", "1mo": "1h", "6mo": "1d", "1y": "1d", "5y": "1wk"}

@st.cache_data(ttl=60)
def get_market_data(ticker, period, interval):
    try:
        # Téléchargement
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        
        # --- FIX IMPORTANT : Nettoyage des données multi-niveaux ---
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1) # On garde juste 'Close', 'Open' etc.
            
        return df
    except Exception as e:
        return pd.DataFrame()

# --- 3. ANALYSE SENTIMENT (Simulée) ---

def get_social_sentiment(symbol, price_change_pct):
    base_score = 50
    trend_influence = price_change_pct * 5 
    social_noise = random.uniform(-10, 10)
    final_score = base_score + trend_influence + social_noise
    final_score = max(5, min(95, final_score))
    
    if final_score >= 75: state = "EUPHORIE (Achat)"
    elif final_score >= 55: state = "CONFIANCE"
    elif final_score >= 45: state = "INCERTITUDE"
    elif final_score >= 25: state = "PEUR (Vente)"
    else: state = "PANIQUE"
    
    return int(final_score), state

# --- 4. INTERFACE ---

with st.sidebar:
    st.header("Blishko Trades")
    category = st.radio("Marché", ["Cryptomonnaies", "Bourse & Matières"], label_visibility="collapsed")
    selected_asset_name = st.radio("Actifs", list(ASSETS[category].keys()))
    if st.button("🔄 Actualiser"):
        st.cache_data.clear()
        st.rerun()

symbol = ASSETS[category][selected_asset_name]

# --- ZONE PRINCIPALE ---

if 'timeframe' not in st.session_state:
    st.session_state.timeframe = "1J"

cols_tf = st.columns([1,1,1,1,1,1, 6])
tf_labels = ["1J", "5J", "1M", "6M", "1A", "5A"]

for i, tf in enumerate(tf_labels):
    if cols_tf[i].button(tf, use_container_width=True):
        st.session_state.timeframe = tf

current_tf = st.session_state.timeframe
yf_period = TIMEFRAMES[current_tf]
yf_interval = INTERVALS[yf_period]

with st.spinner(f"Chargement {selected_asset_name}..."):
    df = get_market_data(symbol, yf_period, yf_interval)

if not df.empty and 'Close' in df.columns:
    # --- FIX CRITIQUE : Conversion en nombres purs (float) ---
    try:
        current_price = float(df['Close'].iloc[-1].item())
        start_price = float(df['Open'].iloc[0].item())
    except:
        # Fallback si .item() échoue (rare)
        current_price = float(df['Close'].iloc[-1])
        start_price = float(df['Open'].iloc[0])

    change = current_price - start_price
    change_pct = (change / start_price) * 100
    
    color_hex = "#30d158" if change >= 0 else "#ff453a"
    
    # Affichage Header
    st.markdown(f"""
    <div>
        <div style="font-size: 1.5rem; color: #888;">{selected_asset_name}</div>
        <div class="price-large">${current_price:,.2f}</div>
        <div class="price-change" style="color: {color_hex};">
            {change:+.2f} ({change_pct:+.2f}%) • {current_tf}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Graphique
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Close'],
        mode='lines',
        line=dict(color=color_hex, width=2),
        fill='tozeroy',
        fillcolor=f"rgba({int(color_hex[1:3], 16)}, {int(color_hex[3:5], 16)}, {int(color_hex[5:7], 16)}, 0.1)"
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=30, b=0), height=400,
        xaxis=dict(showgrid=False, gridcolor='#333'),
        yaxis=dict(showgrid=True, gridcolor='#222', side='right')
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Sentiment
    st.markdown("---")
    st.subheader("🧠 Analyse Sentiment & Psychologie")
    
    sentiment_score, sentiment_state = get_social_sentiment(symbol, change_pct)
    
    col_s1, col_s2 = st.columns([1, 2])
    with col_s1:
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", value = sentiment_score,
            title = {'text': f"Index Social<br><span style='font-size:0.8em;color:gray'>{sentiment_state}</span>"},
            gauge = {
                'axis': {'range': [0, 100]},
                'bar': {'color': "white"},
                'steps': [
                    {'range': [0, 25], 'color': '#ff453a'},
                    {'range': [25, 45], 'color': '#ff9f0a'},
                    {'range': [45, 55], 'color': '#8e8e93'},
                    {'range': [55, 75], 'color': '#30d158'},
                    {'range': [75, 100], 'color': '#0A84FF'}
                ],
            }
        ))
        fig_gauge.update_layout(height=250, margin=dict(l=20,r=20,t=50,b=20), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_gauge, use_container_width=True)
        
    with col_s2:
        st.markdown(f"""
        <div class="sentiment-box">
            <h4>Analyse IA :</h4>
            <ul>
                <li><b>X (Twitter) :</b> {'🔥 Viral' if abs(change_pct) > 3 else 'Calme'} sur #{symbol.split('-')[0]}</li>
                <li><b>Reddit :</b> Volume {'élevé' if abs(change_pct) > 2 else 'modéré'}.</li>
                <li><b>Tendance :</b> {sentiment_state}</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

else:
    st.warning("Données indisponibles pour le moment. Réessayez ou changez de période.")
