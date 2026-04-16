import yfinance as yf
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()


def get_technical_data(symbol):
    stock = yf.Ticker(symbol)
    # Historische Daten für Indikatoren (letzte 60 Tage)
    df = stock.history(period="60d")

    if df.empty:
        return None, None

    # RSI Berechnung (vereinfacht)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # Gleitende Durchschnitte (SMA)
    df['SMA_20'] = df['Close'].rolling(window=20).mean()

    current_rsi = df['RSI'].iloc[-1]
    current_sma = df['SMA_20'].iloc[-1]

    return df, {"RSI": round(current_rsi, 2), "SMA_20": round(current_sma, 2)}


def get_stock_context(ticker):
    # Wir löschen die Session-Logik komplett und lassen yfinance machen
    stock = yf.Ticker(ticker)

    try:
        # Falls .info blockiert, nehmen wir .fast_info
        info = stock.info
        return info, stock.news
    except Exception:
        # Fallback, falls Yahoo gar nichts rausrückt
        return {"longName": ticker}, []

def generate_analysis_with_gemini(symbol, price_data, news, tech_data):
    api_key = os.getenv("GOOGLE_API_KEY")
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key, temperature=0.2)

    # Der Prompt wird jetzt deutlich professioneller
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

    response = llm.invoke(prompt)
    return response.content


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