import streamlit as st
import plotly.graph_objects as go
from main import get_stock_context, generate_analysis_with_gemini, get_technical_data

# Seite breit machen für das Dashboard-Feeling
st.set_page_config(page_title="Quant-Analyst Dashboard", layout="wide")

st.title("📈 AI-Supported Quant Dashboard")
st.markdown("---")


@st.cache_data(ttl=600)
def fetch_all_data(ticker):
    price_data, news = get_stock_context(ticker)
    df, tech_indicators = get_technical_data(ticker)
    return price_data, news, df, tech_indicators


ticker = st.text_input("Aktienkürzel eingeben:", "NVDA").upper()

if st.button("Analyse starten"):
    with st.spinner(f"Extrahiere Daten für {ticker}..."):
        price_data, news, df, tech = fetch_all_data(ticker)

        if df is not None:
            # Spalten-Layout: 2/3 Chart, 1/3 KI-Bericht
            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader("Kursverlauf & Indikatoren")
                fig = go.Figure()

                # Candlestick oder Line-Chart
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df['Close'],
                    name="Schlusskurs",
                    line=dict(color='#00ff00', width=2)
                ))

                # SMA 20 einblenden
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df['SMA_20'],
                    name="SMA 20 (Trend)",
                    line=dict(color='rgba(255, 255, 255, 0.5)', dash='dot')
                ))

                fig.update_layout(
                    template="plotly_dark",
                    xaxis_rangeslider_visible=False,
                    height=500,
                    margin=dict(l=0, r=0, t=30, b=0)
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("KI-Einschätzung")
                report = generate_analysis_with_gemini(ticker, price_data, news, tech)
                st.info(report)

                # Metriken unter dem Bericht
                st.divider()
                st.metric("RSI (14)", tech['RSI'], delta_color="inverse")
                st.caption("RSI > 70: Überkauft | < 30: Überverkauft")

        else:
            st.error("Keine historischen Daten für diesen Ticker gefunden.")

st.sidebar.markdown("### Tech-Stack")
st.sidebar.code("yfinance\nPlotly\nGemini 2.5 Flash\nStreamlit")