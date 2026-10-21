import os
import threading
import time
import requests
from flask import Flask
import telebot

# Ambil kunci rahsia daripada Environment Variables Render
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
TWELVE_DATA_API_KEY = os.environ.get("TWELVE_DATA_API_KEY")

# Mulakan bot Telegram
bot = telebot.TeleBot(TOKEN)

# Tetapan Flask untuk buka port di Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot XAUUSD is running and active!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# Fungsi semak harga XAUUSD (Syezz boleh sesuaikan logik pemantauan di sini)
def check_market():
    while True:
        try:
            # Contoh semakan API Twelve Data untuk Gold (XAU/USD)
            url = f"https://api.twelvedata.com/price?symbol=XAU/USD&apikey={TWELVE_DATA_API_KEY}"
            response = requests.get(url)
            data = response.json()
            
            if "price" in data:
                price = data["price"]
                print(f"Harga semasa XAUUSD: {price}")
                # Contoh hantar mesej percubaan (boleh diubah mengikut strategi SNR/SND Syezz)
                # bot.send_message(CHAT_ID, f"Harga semasa XAUUSD: {price}")
            
        except Exception as e:
            print(f"Ralat semasa semak pasaran: {e}")
            
        # Semak setiap 5 minit (300 saat) atau ikut kesesuaian
        time.sleep(300)

if __name__ == "__main__":
    # 1. Jalankan server Flask dalam background thread supaya port terbuka
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # 2. Jalankan fungsi pemantauan pasaran dalam thread asing
    market_thread = threading.Thread(target=check_market)
    market_thread.start()

    # 3. Jalankan bot polling Telegram secara berterusan
    print("Bot sedang berjalan...")
    bot.infinity_polling()
