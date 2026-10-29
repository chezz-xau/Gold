from datetime import datetime
import os
import threading
import time
from flask import Flask, request
import pandas as pd
import requests

# ---------------------------------------------------------
# 1. SETUP FLASK
# ---------------------------------------------------------
app = Flask(__name__)


@app.route("/")
def home():
  return "Bot M30/H1 Trend Syezz Aktif!"


# ---------------------------------------------------------
# 2. KONFIGURASI TELEGRAM & API
# ---------------------------------------------------------
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


def get_market_data(timeframe="1h"):
  tf = "1h" if timeframe == "1h" else "30min"
  url = f"https://api.twelvedata.com/time_series?symbol=XAU/USD&interval={tf}&outputsize=100&apikey={TWELVE_API_KEY}"
  try:
    response = requests.get(url, timeout=10)
    data = response.json()
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


def get_valid_bucu(df):
  if df is None or len(df) < 5:
    return None, None
  df = df.copy()
  df["body_low"] = df[["open", "close"]].min(axis=1)
  df["body_high"] = df[["open", "close"]].max(axis=1)

  valid_bucu_lows = []
  valid_bucu_highs = []

  for i in range(2, len(df) - 2):
    if (
        df["body_low"].iloc[i] < df["body_low"].iloc[i - 1]
        and df["body_low"].iloc[i] < df["body_low"].iloc[i - 2]
        and df["body_low"].iloc[i] < df["body_low"].iloc[i + 1]
        and df["body_low"].iloc[i] < df["body_low"].iloc[i + 2]
    ):
      valid_bucu_lows.append(df["body_low"].iloc[i])

    if (
        df["body_high"].iloc[i] > df["body_high"].iloc[i - 1]
        and df["body_high"].iloc[i] > df["body_high"].iloc[i - 2]
        and df["body_high"].iloc[i] > df["body_high"].iloc[i + 1]
        and df["body_high"].iloc[i] > df["body_high"].iloc[i + 2]
    ):
      valid_bucu_highs.append(df["body_high"].iloc[i])

  return (
      valid_bucu_highs[-1] if valid_bucu_highs else None,
      valid_bucu_lows[-1] if valid_bucu_lows else None,
  )


# ---------------------------------------------------------
# 3. LOGIK KEKAL TREND (BEARISH OVERRIDE)
# ---------------------------------------------------------
def evaluate_trend(df):
  if df is None or len(df) < 10:
    return "🔴 BEARISH (Downtrend / Retrace Zone)", 0, 0, 0

  df = df.copy()
  close_price = float(df.iloc[-2]["close"])
  bucu_high, bucu_low = get_valid_bucu(df)

  # Jika harga close di atas Bucu High utama, baru jadi Bullish.
  # Selain itu, selagi di bawah Bucu High, ia DIPAKSA kekal Bearish (tiada lagi Sideways).
  if bucu_high is not None and close_price > bucu_high:
    trend = "🟢 BULLISH (Uptrend Major - Break Resistance)"
  else:
    trend = "🔴 BEARISH (Downtrend / Retrace Zone - Kekal Trend)"

  return trend, close_price, bucu_high if bucu_high else 0, bucu_low if bucu_low else 0


# ---------------------------------------------------------
# 4. FUNGSI ANALISIS /trend
# ---------------------------------------------------------
def analyze_current_trend():
  df_h1 = get_market_data(timeframe="1h")
  df_m30 = get_market_data(timeframe="30min")

  h1_status, h1_close, h1_high, h1_low = evaluate_trend(df_h1)
  m30_status, m30_close, m30_high, m30_low = evaluate_trend(df_m30)

  msg = (
      f"📊 *ANALISIS STRUKTUR MAJOR TREND (LOCKED BEARISH)*\n\n"
      f"⏰ *Analisis H1 (Major Trend):*\n"
      f"• Trend H1: {h1_status}\n"
      f"• Close H1: `${h1_close:.2f}`\n"
      f"• Bucu High H1: `${h1_high:.2f}`\n"
      f"• Bucu Low H1: `${h1_low:.2f}`\n\n"
      f"📉 *Analisis M30 (Minor Trend):*\n"
      f"• Trend M30: {m30_status}\n"
      f"• Close M30: `${m30_close:.2f}`\n"
      f"• Bucu High M30: `${m30_high:.2f}`\n"
      f"• Bucu Low M30: `${m30_low:.2f}`"
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
      response_text = analyze_current_trend()
      send_telegram_message(response_text, chat_id=chat_id)
  return "OK", 200


def run_bot():
  print("🤖 Bot Syezz Dikemaskini & Berjalan...")
  last_time = None
  while True:
    try:
      df_m30 = get_market_data(timeframe="30min")
      if df_m30 is not None and len(df_m30) >= 10:
        candle = df_m30.iloc[-2]
        c_time = str(candle["time"])
        close = float(candle["close"])
        b_high, b_low = get_valid_bucu(df_m30)

        if c_time != last_time:
          if b_low is not None and close < b_low:
            send_telegram_message(
                f"🚨 *BREAKOUT BEARISH M30*!\nClose: `${close:.2f}`"
            )
            last_time = c_time
          elif b_high is not None and close > b_high:
            send_telegram_message(
                f"🚨 *BREAKOUT BULLISH M30*!\nClose: `${close:.2f}`"
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
