import yfinance as yf
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
import streamlit as st
import pandas as pd

load_dotenv()


def get_technical_data(symbol):
    """Zuständig für alles, was aus dem Kursverlauf berechnet wird."""
    stock = yf.Ticker(symbol)
    df = stock.history(period="1y")  # 1 Jahr für SMA 200 nötig

    if df.empty:
        return None, None

    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # SMAs
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['SMA_200'] = df['Close'].rolling(window=200).mean()

    # Signale berechnen (Golden Cross)
    sma50_today = df['SMA_50'].iloc[-1]
    sma200_today = df['SMA_200'].iloc[-1]

    # Werte von gestern (vorletzte Zeile)
    sma50_yesterday = df['SMA_50'].iloc[-2]
    sma200_yesterday = df['SMA_200'].iloc[-2]

    # Logik für das echte Signal
    if sma50_yesterday <= sma200_yesterday and sma50_today > sma200_today:
        signal = "Golden Cross (Frisches Kaufsignal!)"
    elif sma50_yesterday >= sma200_yesterday and sma50_today < sma200_today:
        signal = "Death Cross (Verkaufssignal!)"
    elif sma50_today > sma200_today:
        signal = "Bullischer Aufwärtstrend"
    else:
        signal = "Bärischer Abwärtstrend"

    tech_metrics = {
        "RSI": round(df['RSI'].iloc[-1], 2),
        "SMA_50": round(sma50_today, 2),
        "SMA_200": round(sma200_today, 2),
        "Trend_Signal": signal
    }
    return df, tech_metrics


def get_stock_context(symbol):
    """Zuständig für Unternehmensdaten und Nachrichten."""
    stock = yf.Ticker(symbol)
    info = stock.info

    fundamental_data = {
        "name": info.get("longName", symbol),
        "price": info.get("currentPrice"),
        "kgv": info.get("trailingPE"),
        "market_cap": info.get("marketCap"),
        "target_price": info.get("targetMeanPrice"),
        "recommendation": info.get("recommendationKey")
    }
    return fundamental_data, stock.news


def generate_analysis_with_gemini(symbol, price_data, news, tech_data):
    # Fallback für Streamlit Cloud Secrets, falls os.getenv fehlschlägt
    api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

    if not api_key:
        return "Fehler: Key fehlt."

    # Modell auf 'gemini-2.5-flash'
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
        temperature=0.2
    )

    prompt = f"""
    Analysiere {symbol} als quantitativer Analyst.

    FUNDAMENTAL: {price_data}
    TECHNISCH: {tech_data} (RSI > 70 ist überkauft, < 30 überverkauft)
    NEWS: {news}

    AUFGABE:
    1. Kurzes Sentiment (Bullisch/Bärisch).
    2. Begründung durch Kombination von News und RSI.
    3. Ein konkretes Risiko benennen.
    Antworte kurz und präzise auf Deutsch (max. 150 Wörter).
    """

    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"KI-Analyse fehlgeschlagen: {str(e)}"

# --- DIESER TEIL HAT GEFEHLT: DER STARTER ---
if __name__ == "__main__":
    ticker = "TSLA"
    print(f"Starte Test-Analyse für {ticker}...")

    # Daten sammeln
    df, tech = get_technical_data(ticker)
    price, news = get_stock_context(ticker)

    # Analyse generieren
    if tech:
        report = generate_analysis_with_gemini(ticker, price, news, tech)
        print("\n--- KI ANALYSE ---")
        print(report)
        print(f"\nTechnische Werte: RSI: {tech['RSI']}, SMA20: {tech['SMA_20']}")
    else:
        print("Fehler: Keine Daten gefunden.")