import os
import requests
import pandas as pd
import yfinance as yf

# Fetch hidden tokens from GitHub vault settings
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

def check_gold_breakout():
    df = yf.download("GC=F", interval="30m", period="5d")
    if df.empty:
        print("Data is empty.")
        return
        
    df['Upper'] = df['High'].shift(1).rolling(window=20).max()
    df['Lower'] = df['Low'].shift(1).rolling(window=20).min()
    
    last_candle = df.iloc[-2]
    close_price = float(last_candle['Close'])
    upper_bound = float(last_candle['Upper'])
    lower_bound = float(last_candle['Lower'])
    
    message = ""
    if close_price > upper_bound:
        message = f"🚨 XAU/USD BULLISH BREAKOUT (M30)!\nPrice: ${close_price:.2f}\nBroke above 20-candle high: ${upper_bound:.2f}"
    elif close_price < lower_bound:
        message = f"🚨 XAU/USD BEARISH BREAKOUT (M30)!\nPrice: ${close_price:.2f}\nBroke below 20-candle low: ${lower_bound:.2f}"
        
    if message:
        url = f"https://telegram.org{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message}
        requests.post(url, json=payload)
        print("Alert text pushed to phone!")
    else:
        print("No breakout detected inside the range.")

if __name__ == "__main__":
    check_gold_breakout()

