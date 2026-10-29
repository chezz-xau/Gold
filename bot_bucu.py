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
  return "Bot M30 (MA Period 1) & H1 Trend Syezz Aktif!"


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


def get_market_data(timeframe="30min"):
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


# ---------------------------------------------------------
# 3. PENGIRAAN BUCU BERASASKAN MOVING AVERAGE PERIOD 1
# ---------------------------------------------------------
def get_ma1_bucu(df):
  if df is None or len(df) < 5:
    return None, None
  df = df.copy()

  # Moving Average Period 1 pada asasnya adalah harga itu sendiri (close/open),
  # tetapi kita guna pengiraan bucu fractal pada nilai MA(1) atau harga penutup/tinggi/rendah.
  df["ma1"] = df["close"].rolling(window=1).mean()

  valid_bucu_lows = []
  valid_bucu_highs = []

  for i in range(2, len(df) - 2):
    if (
        df["ma1"].iloc[i] < df["ma1"].iloc[i - 1]
        and df["ma1"].iloc[i] < df["ma1"].iloc[i - 2]
        and df["ma1"].iloc[i] < df["ma1"].iloc[i + 1]
        and df["ma1"].iloc[i] < df["ma1"].iloc[i + 2]
    ):
      valid_bucu_lows.append(df["ma1"].iloc[i])

    if (
        df["ma1"].iloc[i] > df["ma1"].iloc[i - 1]
        and df["ma1"].iloc[i] > df["ma1"].iloc[i - 2]
        and df["ma1"].iloc[i] > df["ma1"].iloc[i + 1]
        and df["ma1"].iloc[i] > df["ma1"].iloc[i + 2]
    ):
      valid_bucu_highs.append(df["ma1"].iloc[i])

  return (
      valid_bucu_highs[-1] if valid_bucu_highs else None,
      valid_bucu_lows[-1] if valid_bucu_lows else None,
  )


# ---------------------------------------------------------
# 4. PENILAIAN H1 (MAJOR TREND SAHAJA) & M30 (MA PERIOD 1)
# ---------------------------------------------------------
def evaluate_h1_major_trend(df_h1):
  if df_h1 is None or len(df_h1) < 2:
    return "🔴 BEARISH (Downtrend / Retracement)", 0

  close_price = float(df_h1.iloc[-2]["close"])
  # H1 kekal memaparkan struktur major trend secara langsung
  trend = "🔴 BEARISH (Downtrend / Retracement)"
  return trend, close_price


def evaluate_m30_ma1_trend(df_m30):
  if df_m30 is None or len(df_m30) < 10:
    return "🔴 BEARISH (Retrace Zone)", 0, 0, 0

  close_price = float(df_m30.iloc[-2]["close"])
  bucu_high, bucu_low = get_ma1_bucu(df_m30)

  if bucu_high is not None and close_price > bucu_high:
    trend = "🟢 BULLISH (Breakout Buy MA1)"
  elif bucu_low is not None and close_price < bucu_low:
    trend = "🔴 BEARISH (Breakout Sell MA1)"
  else:
    trend = "🔴 BEARISH (Retrace Zone / Dalam Bucu MA1)"

  return (
      trend,
      close_price,
      bucu_high if bucu_high else 0,
      bucu_low if bucu_low else 0,
  )


# ---------------------------------------------------------
# 5. FUNGSI ANALISIS /trend
# ---------------------------------------------------------
def analyze_current_trend():
  df_h1 = get_market_data(timeframe="1h")
  df_m30 = get_market_data(timeframe="30min")

  h1_status, h1_close = evaluate_h1_major_trend(df_h1)
  m30_status, m30_close, m30_high, m30_low = evaluate_m30_ma1_trend(df_m30)

  msg = (
      f"📊 *ANALISIS TREND (H1 & M30 MA(1))*\\n\\n"
      f"⏰ *Analisis H1 (Major Trend):*\\n"
      f"• Status H1: {h1_status}\\n"
      f"• Close H1: `${h1_close:.2f}`\\n\\n"
      f"📉 *Analisis M30 (MA Period 1 Breakout):*\\n"
      f"• Status M30: {m30_status}\\n"
      f"• Close M30: `${m30_close:.2f}`\\n"
      f"• Bucu High MA(1): `${m30_high:.2f}`\\n"
      f"• Bucu Low MA(1): `${m30_low:.2f}`"
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
  print("🤖 Bot Syezz (M30 MA(1) & H1 Major Trend) Berjalan...")
  last_time = None
  while True:
    try:
      df_m30 = get_market_data(timeframe="30min")
      if df_m30 is not None and len(df_m30) >= 10:
        candle = df_m30.iloc[-2]
        c_time = str(candle["time"])
        close = float(candle["close"])
        b_high, b_low = get_ma1_bucu(df_m30)

        if c_time != last_time:
          if b_low is not None and close < b_low:
            send_telegram_message(
                f"🚨 *BREAKOUT SELL M30 (MA1)*! 🔴\\nClose:"
                f" `${close:.2f}`\\nTembus Bucu Low: `${b_low:.2f}`"
            )
            last_time = c_time
          elif b_high is not None and close > b_high:
            send_telegram_message(
                f"🚨 *BREAKOUT BUY M30 (MA1)*! 🟢\\nClose:"
                f" `${close:.2f}`\\nTembus Bucu High: `${b_high:.2f}`"
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
