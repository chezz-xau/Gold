

import os
import requests
import pandas as pd
import yfinance as yf

# Pre-filled with your exact verified tokens
TOKEN = "8825296896:AAEvBExEDqiwUKW3kTGYJa2Ao1OhDjBpwHQ"
CHAT_ID = "8825296896"

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
    
    # 1. Determine breakout status
    if close_price > upper_bound:
        message = f"🚨 **XAU/USD BULLISH BREAKOUT!** 🚨\n\n💰 Price closed at: **${close_price:.2f}**\n📈 Broke above 20-candle high: ${upper_bound:.2f}"
    elif close_price < lower_bound:
        message = f"🚨 **XAU/USD BEARISH BREAKOUT!** 🚨\n\n💰 Price closed at: **${close_price:.2f}**\n📉 Broke below 20-candle low: ${lower_bound:.2f}"
    else:
        # 2. This part ensures the bot always messages you every 30 minutes!
        message = f"ℹ️ **Gold M30 Scan Status** ℹ️\n\n💰 Current Close: ${close_price:.2f}\n🟢 Upper Breakout Target: ${upper_bound:.2f}\n🔴 Lower Breakout Target: ${lower_bound:.2f}\n\n*Status: Market is consolidating inside the range.*"
        
    # 3. Send the message via Telegram
    url = f"https://telegram.org{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)
    print("Update message pushed to Telegram successfully!")

if __name__ == "__main__":
    check_gold_breakout()
