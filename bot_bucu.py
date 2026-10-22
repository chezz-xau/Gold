import os
import time
from datetime import datetime
import pandas as pd
import requests

# Konfigurasi Telegram (Ambil dari Environment Variables Railway)
TOKEN = os.getenv("TELEGRAM_TOKEN", "MASUKKAN_TOKEN_BOT_ANDA_DI_SINI")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "MASUKKAN_CHAT_ID_ANDA_DI_SINI")


def send_telegram_message(message):
  """Fungsi untuk menghantar mesej ke Telegram"""
  url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
  payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
  try:
    response = requests.post(url, json=payload, timeout=10)
    if response.status_code != 200:
      print(f"Gagal hantar Telegram: {response.text}")
  except Exception as e:
    print(f"Ralat sambungan Telegram: {e}")


def get_market_data():
  """[PENTING] Gantikan bahagian ini dengan kod sambungan API data anda.

  Pastikan simbol merujuk kepada broker anda (Contoh: XAUUSD.vx)
  Data yang dipulangkan mesti dalam bentuk DataFrame pandas
  yang mempunyai kolum sekurang-kurangnya: ['time', 'close', 'low', 'high']
  """
  # Contoh struktur data dummy (Sila tukar kepada sumber data sebenar anda):
  # df = pd.read_json('https://api.brokeranda.com/data?symbol=XAUUSD.vx&tf=M30')
  pass


def main():
  print("🤖 Bot M30 Breakout Syezz dimulakan...")

  # Pembolehubah untuk menyimpan status masa candle terakhir yang sudah di-alert
  last_processed_time = None

  # ==========================================
  # TETAPAN ARAS RUJUKAN (FIXED SUPPORT LEVEL)
  # ==========================================
  # Tetapkan nilai aras support kekal di sini (Contoh: Bucu Body Low yang sah)
  # Jangan biarkan nilai ini berubah secara dinamik mengikut candle semasa.
  SUPPORT_LEVEL = 4114.53
  RESISTANCE_LEVEL = 4141.17

  while True:
    try:
      # 1. Tarik data pasaran terkini
      df = get_market_data()

      if df is not None and len(df) >= 2:
        # 2. AMBIL CANDLE YANG SUDAH CLOSE (iloc[-2])
        # iloc[-1] = Candle sedang berjalan (live/aktif) -> JANGAN GUNA UNTUK ALERT BREAKOUT
        # iloc[-2] = Candle M30 sebelumnya yang sah sudah TUTUP/CLOSE
        completed_candle = df.iloc[-2]

        current_candle_time = str(completed_candle["time"])
        close_price = float(completed_candle["close"])
        low_price = float(completed_candle["low"])

        # 3. SEMAK SYARAT: Adakah ini candle baharu yang belum diproses?
        if current_candle_time != last_processed_time:

          # --- SYARAT BREAKOUT SELL (BEARISH BODY CLOSE) ---
          # Harga penutup (Close) candle M30 melepasi ke bawah aras support tetap
          if close_price < SUPPORT_LEVEL:

            msg = (
                f"🚨 *ALERT BREAKOUT M30 (BEARISH BODY)*! 🔴\n\n"
                f"Candle M30 baharu sahaja *CLOSE*!\n"
                f"• Close M30: `${close_price:.2f}`\n"
                f"• Aras Support Tembus: `${SUPPORT_LEVEL}`\n\n"
                f"_Struktur M30 Terdekat sah bertukar kepada Downtrend / Bearish!_"
            )

            # Hantar alert ke Telegram
            send_telegram_message(msg)

            # Kemas kini masa supaya alert ini tidak hantar berulang kali
            last_processed_time = current_candle_time
            print(f"[{datetime.now()}] Alert Breakout Sell berjaya dihantar!")

          # --- SYARAT BREAKOUT BUY (Boleh tambah di sini jika perlu) ---
          # elif close_price > RESISTANCE_LEVEL:
          #     ...

      # Semak semula setiap 30 saat atau 1 minit untuk pastikan tiada close M30 terlepas
      time.sleep(60)

    except Exception as e:
      print(f"Ralat berlaku dalam gelung utama bot: {e}")
      time.sleep(30)  # Tunggu sebentar sebelum cuba semula jika berlaku ralat


if __name__ == "__main__":
  main()
