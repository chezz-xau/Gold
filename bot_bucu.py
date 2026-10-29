from datetime import datetime
import os
import threading
import time
from flask import Flask, request
import pandas as pd
import requests

app = Flask(__name__)


@app.route("/")
def home():
  return "Bot Syezz (Dynamic H1 & M30 MA1) Aktif!"


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TWELVE_API_KEY = os.getenv("TWELVE_DATA_API")


def send_telegram_message(message, chat_id=CHAT_ID):
  if not TOKEN or not chat_id:
    return
  url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
  payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
  try:
    requests.post(url, json=payload, timeout=10)
  except Exception as e:
    print(f"Ralat Telegram: {e}")


def get_market_data(tf="30min"):
  url = f"https://api.twelvedata.com/time_series?symbol=XAU/USD&interval={tf}&outputsize=100&apikey={TWELVE_API_KEY}"
  try:
    res = requests.get(url, timeout=10)
    data = res.json()
    if "values" in data:
      df = pd.DataFrame(data["values"])
      df = df.iloc[::-1].reset_index(drop=True)
      for col in ["open", "high", "low", "close"]:
        df[col] = df[col].astype(float)
      return df
    return None
  except Exception as e:
    print(f"Ralat API: {e}")
    return None


def get_bucu_points(df):
  if df is None or len(df) < 5:
    return None, None
  df = df.copy()
  df["ma1"] = df["close"]
  highs, lows = [], []
  for i in range(2, len(df) - 2):
    if (
        df["ma1"].iloc[i] < df["ma1"].iloc[i - 1]
        and df["ma1"].iloc[i] < df["ma1"].iloc[i - 2]
        and df["ma1"].iloc[i] < df["ma1"].iloc[i + 1]
        and df["ma1"].iloc[i] < df["ma1"].iloc[i + 2]
    ):
      lows.append(df["ma1"].iloc[i])
    if (
        df["ma1"].iloc[i] > df["ma1"].iloc[i - 1]
        and df["ma1"].iloc[i] > df["ma1"].iloc[i - 2]
        and df["ma1"].iloc[i] > df["ma1"].iloc[i + 1]
        and df["ma1"].iloc[i] > df["ma1"].iloc[i + 2]
    ):
      highs.append(df["ma1"].iloc[i])
  return highs[-1] if highs else None, lows[-1] if lows else None


def analyze_current_trend():
  df_h1 = get_market_data("1h")
  df_m30 = get_market_data("30min")

  h1_close = float(df_h1.iloc[-2]["close"]) if df_h1 is not None else 0
  h1_high, h1_low = get_bucu_points(df_h1)

  m30_close = float(df_m30.iloc[-2]["close"]) if df_m30 is not None else 0
  m30_high, m30_low = get_bucu_points(df_m30)

  # H1 Major Trend: Automatik bertukar Bullish jika close atas bucu high, jika tidak kekal Bearish/Retracement
  if h1_high is not None and h1_close > h1_high:
    h1_status = "🟢 BULLISH (Uptrend Major)"
  else:
    h1_status = "🔴 BEARISH (Downtrend / Retracement Major)"

  # M30 MA(1) Breakout
  if m30_high is not None and m30_close > m30_high:
    m30_status = "🟢 BULLISH (Breakout Buy MA1)"
  elif m30_low is not None and m30_close < m30_low:
    m30_status = "🔴 BEARISH (Breakout Sell MA1)"
  else:
    m30_status = "🔴 BEARISH (Retrace Zone / Dalam Bucu MA1)"

  msg = (
      f"📊 *ANALISIS TREND DINAMIK SYEZZ*\n\n"
      f"⏰ *Analisis H1 (Major Trend):*\n"
      f"• Status H1: {h1_status}\n"
      f"• Close H1: `${h1_close:.2f}`\n\n"
      f"📉 *Analisis M30 (MA Period 1):*\n"
      f"• Status M30: {m30_status}\n"
      f"• Close M30: `${m30_close:.2f}`\n"
      f"• Bucu High MA1: `${m30_high if m30_high else 0:.2f}`\n"
      f"• Bucu Low MA1: `${m30_low if m30_low else 0:.2f}`"
  )
  return msg


@app.route(f"/{TOKEN}", methods=["POST"])
def telegram_webhook():
  data = request.get_json()
  if "message" in data:
    message = data["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    if text.startswith("/trend"):
      send_telegram_message(analyze_current_trend(), chat_id=chat_id)
  return "OK", 200


def run_bot():
  last_time = None
  while True:
    try:
      df_m30 = get_market_data("30min")
      if df_m30 is not None and len(df_m30) >= 10:
        candle = df_m30.iloc[-2]
        c_time = str(candle["time"])
        close = float(candle["close"])
        b_high, b_low = get_bucu_points(df_m30)

        if c_time != last_time:
          if b_low is not None and close < b_low:
            send_telegram_message(
                f"🚨 *BREAKOUT SELL M30 (MA1)*! 🔴\nClose: `${close:.2f}`"
            )
            last_time = c_time
          elif b_high is not None and close > b_high:
            send_telegram_message(
                f"🚨 *BREAKOUT BUY M30 (MA1)*! 🟢\nClose: `${close:.2f}`"
            )
            last_time = c_time
      time.sleep(30)
    except Exception as e:
      print(f"Ralat: {e}")
      time.sleep(30)


if __name__ == "__main__":
  bot_thread = threading.Thread(target=run_bot)
  bot_thread.daemon = True
  bot_thread.start()
  port = int(os.getenv("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
