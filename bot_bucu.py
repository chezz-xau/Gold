import os
import threading
import time
from datetime import datetime
import pandas as pd
import requests
from flask import Flask

# ---------------------------------------------------------
# 1. SETUP FLASK (Supaya Render kesan port yang sah)
# ---------------------------------------------------------
app = Flask(__name__)


@app.route("/")
def home():
  return "Bot M30 Breakout Syezz sedang aktif!"


# ---------------------------------------------------------
# 2. KONFIGURASI TELEGRAM & API
# ---------------------------------------------------------
TOKEN = os.getenv("TELEGRAM_TOKEN", "MASUKKAN_TOKEN_BOT_ANDA")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "MASUKKAN_CHAT_ID_ANDA")


def send_telegram_message(message):
  """Fungsi untuk menghantar mesej amaran ke Telegram"""
  url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
  payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
  try:
    response = requests.post(url, json=payload, timeout=10)
    if response.status_code != 200:
      print(f"Gagal hantar Telegram: {response.text}")
  except Exception as e:
    print(f"Ralat sambungan Telegram: {e}")


def get_market_data():
  """[PENTING] Gantikan bahagian ini dengan sumber data broker anda

  (Contoh: MetaTrader API, TwelveData, atau endpoint data anda).
  Pastikan DataFrame yang dipulangkan mempunyai kolum:
  ['time', 'open', 'high', 'low', 'close']
  """
  # --- CONTOH TEMPLATE DATA FETCH ---
  # url = "https://api.brokeranda.com/data?symbol=XAUUSD.vx&tf=M30"
  # df = pd.read_json(url)
  # return df
  pass


# ---------------------------------------------------------
# 3. LOGIK PENCARIAN BUCU SAH (ELAK REPAINTING)
# ---------------------------------------------------------
def get_valid_bucu(df):
  """Mencari aras Bucu High & Low yang sah (Fractal Body).

  Aras ini dikunci dan tidak berubah-ubah mengikut candle live.
  """
  if df is None or len(df) < 5:
    return None, None

  df = df.copy()
  df["body_low"] = df[["open", "close"]].min(axis=1)
  df["body_high"] = df[["open", "close"]].max(axis=1)

  valid_bucu_lows = []
  valid_bucu_highs = []

  # Imbas data (abaikan 2 candle terakhir yang belum lengkap struktur swing)
  for i in range(2, len(df) - 2):
    # Logik Bucu Low Sah (Bentuk V)
    if (
        df["body_low"].iloc[i] < df["body_low"].iloc[i - 1]
        and df["body_low"].iloc[i] < df["body_low"].iloc[i - 2]
        and df["body_low"].iloc[i] < df["body_low"].iloc[i + 1]
        and df["body_low"].iloc[i] < df["body_low"].iloc[i + 2]
    ):
      valid_bucu_lows.append(df["body_low"].iloc[i])

    # Logik Bucu High Sah (Bentuk A)
    if (
        df["body_high"].iloc[i] > df["body_high"].iloc[i - 1]
        and df["body_high"].iloc[i] > df["body_high"].iloc[i - 2]
        and df["body_high"].iloc[i] > df["body_high"].iloc[i + 1]
        and df["body_high"].iloc[i] > df["body_high"].iloc[i + 2]
    ):
      valid_bucu_highs.append(df["body_high"].iloc[i])

  last_bucu_low = valid_bucu_lows[-1] if valid_bucu_lows else None
  last_bucu_high = valid_bucu_highs[-1] if valid_bucu_highs else None

  return last_bucu_high, last_bucu_low


# ---------------------------------------------------------
# 4. GELUNG UTAMA BOT (BACKGROUND PROCESS)
# ---------------------------------------------------------
def run_bot():
  print("🤖 Bot M30 Breakout Syezz dimulakan...")
  last_processed_time = None

  while True:
    try:
      df = get_market_data()

      if df is not None and len(df) >= 5:
        # AMBIL CANDLE YANG SUDAH CLOSE (iloc[-2])
        # iloc[-1] adalah candle live sedang gerak (jangan guna untuk alert close)
        completed_candle = df.iloc[-2]
        current_candle_time = str(completed_candle["time"])
        close_price = float(completed_candle["close"])

        # Dapatkan bucu sah terkini
        bucu_high, bucu_low = get_valid_bucu(df)

        # Semak jika ini candle M30 baharu yang baru selesai tutup
        if current_candle_time != last_processed_time:

          # Syarat Breakout Sell (Bearish Body Close melepasi Bucu Low sah)
          if bucu_low is not None and close_price < bucu_low:
            msg = (
                f"🚨 *ALERT BREAKOUT M30 (BEARISH BODY)*! 🔴\n\n"
                f"Candle M30 baharu sahaja *CLOSE*!\n"
                f"• Close M30: `${close_price:.2f}`\n"
                f"• Bucu Body Low Tembus: `${bucu_low:.2f}`\n\n"
                f"_Struktur M30 Terdekat sah bertukar kepada Downtrend / Bearish!_"
            )
            send_telegram_message(msg)
            last_processed_time = current_candle_time
            print(f"[{datetime.now()}] Alert Breakout Sell berjaya dihantar!")

      # Semak setiap 60 saat
      time.sleep(60)

    except Exception as e:
      print(f"Ralat berlaku dalam gelung utama bot: {e}")
      time.sleep(30)


# ---------------------------------------------------------
# 5. EXECUTION UTAMA (FLASK + THREADING)
# ---------------------------------------------------------
if __name__ == "__main__":
  # Jalankan bot di background thread
  bot_thread = threading.Thread(target=run_bot)
  bot_thread.daemon = True
  bot_thread.start()

  # Jalankan server Flask pada port Render
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
