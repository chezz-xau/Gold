import os
import threading  # <-- Tambah threading
import time
from datetime import datetime
import pandas as pd
import requests
from flask import Flask  # <-- Import Flask

# Setup Flask app supaya Render anggap ini web service yang sah
app = Flask(__name__)


@app.route("/")
def home():
  return "Bot Bucu XAUUSD sedang aktif!"


# Fungsi utama bot anda (letak dalam function ni)
def run_bot():
  print("🤖 Bot M30 Breakout Syezz dimulakan...")
  last_processed_time = None
  SUPPORT_LEVEL = 4114.53

  while True:
    try:
      # Letak kod fetch market data dan logic alert anda di sini
      time.sleep(60)
    except Exception as e:
      print(f"Ralat: {e}")
      time.sleep(30)


# Jalankan bot menggunakan background thread, dan Flask pada port utama Render
if __name__ == "__main__":
  # Mulakan bot di background thread supaya tidak sekat Flask
  bot_thread = threading.Thread(target=run_bot)
  bot_thread.daemon = True
  bot_thread.start()

  # Jalankan Flask pada port yang dibekalkan oleh Render
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
