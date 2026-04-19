import streamlit as st
import plotly.graph_objects as go
from main import get_stock_context, generate_analysis_with_gemini, get_technical_data

# Seite breit machen
st.set_page_config(page_title="Quant-Analyst Pro", layout="wide")

st.title("📈 AI-Supported Stock Analysis Pro 📈")
st.markdown("---")


@st.cache_data(ttl=600)
def fetch_all_data(ticker):
    # Paket 1: Fundamentaldaten & News
    price_data, news = get_stock_context(ticker)
    # Paket 2: Technische Daten (df für Chart, tech_indicators für Metriken)
    df, tech_indicators = get_technical_data(ticker)
    return price_data, news, df, tech_indicators


ticker = st.text_input("Aktienkürzel eingeben:", "NVDA").upper()

if st.button("Analyse starten"):
    with st.spinner(f"Verarbeite Marktdaten für {ticker}..."):
        price_data, news, df, tech = fetch_all_data(ticker)

        if df is not None and price_data:
            # --- ROW 1: KEY METRICS ---
            m1, m2, m3, m4 = st.columns(4)

            # Aus price_data (Fundamentaler Koffer)
            m1.metric("Kurs", f"{price_data['price']:.2f} $")
            m3.metric("KGV (P/E)", f"{price_data.get('kgv', 'N/A')}")

            # Aus tech (Technischer Koffer)
            m2.metric("RSI (14)", tech['RSI'],
                      delta="Überkauft" if tech['RSI'] > 70 else "Neutral",
                      delta_color="inverse")
            m4.metric("Trend-Signal", tech['Trend_Signal'])

            st.divider()

            # --- ROW 2: CHART & KI ---
            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader("Trend-Analyse (Gleitende Durchschnitte)")
                fig = go.Figure()

                # Hauptkurs
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="Kurs", line=dict(color='#00ff00')))

                # Mittelfristiger Trend (SMA 50 aus dem Dataframe)
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name="SMA 50",
                                         line=dict(color='orange', dash='dash')))

                # Langfristiger Trend (SMA 200 aus dem Dataframe)
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], name="SMA 200",
                                         line=dict(color='red', width=2)))

                fig.update_layout(
                    template="plotly_dark",
                    xaxis_rangeslider_visible=False,
                    height=500,
                    margin=dict(l=0, r=0, t=30, b=0),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("KI-Einschätzung")
                # Übergabe beider Pakete an Gemini
                report = generate_analysis_with_gemini(ticker, price_data, news, tech)
                st.info(report)

                # Analysten-Infos aus price_data
                st.divider()
                st.write(f"**Analysten-Zielkurs:** {price_data.get('target_price', 'N/A')} $")
                st.write(f"**Empfehlung:** {price_data.get('recommendation', 'N/A').upper()}")

                # SMA-Werte aus tech für die Sidebar oder Details
                st.write(f"**SMA 50:** {tech['SMA_50']} $")
                st.write(f"**SMA 200:** {tech['SMA_200']} $")

        else:
            st.error("Fehler beim Abrufen der Daten. Bitte Ticker prüfen.")

# Sidebar
st.sidebar.markdown("### 🛠️ Tech-Stack")
st.sidebar.code("yfinance & Pandas\nPlotly Visuals\nGemini 1.5 Flash\nStreamlit Cloud")