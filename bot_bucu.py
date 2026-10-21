import os
import threading
import time
import requests
from flask import Flask, request
import telebot

# Ambil kunci rahsia daripada Environment Variables Render
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
TWELVE_DATA_API_KEY = os.environ.get("TWELVE_DATA_API_KEY")

# URL Render
RENDER_URL = "https://gold-mfre.onrender.com"

# Mulakan bot Telegram
bot = telebot.TeleBot(TOKEN)

# Tetapan Flask
app = Flask(__name__)

# Endpoint utama untuk kesihatan Render / Keep-Alive
@app.route('/')
def home():
    return "Bot XAUUSD Webhook is running and active!"

# Endpoint khas untuk menerima mesej dari Telegram via Webhook
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Bad Request', 400

# Pengendali mesej /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Halo! Bot XAUUSD Syezz kini aktif menggunakan Webhook dan siap memantau pasaran.")

# Fungsi semak harga XAUUSD di latar belakang
def check_market():
    while True:
        try:
            if TWELVE_DATA_API_KEY:
                url = f"https://api.twelvedata.com/price?symbol=XAU/USD&apikey={TWELVE_DATA_API_KEY}"
                response = requests.get(url)
                data = response.json()
                
                if "price" in data:
                    price = data["price"]
                    print(f"Harga semasa XAUUSD: {price}")
            
        except Exception as e:
            print(f"Ralat pemantauan pasaran: {e}")
            
        time.sleep(300)

# Tetapkan Webhook di Telegram secara automatik
def auto_set_webhook():
    time.sleep(3)  # Tunggu Flask hidup sepenuhnya
    try:
        webhook_url = f"{RENDER_URL}/{TOKEN}"
        # Set webhook secara terus menggunakan Requests API Telegram
        req_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}"
        res = requests.get(req_url).json()
        print(f"Status Auto-Set Webhook: {res}")
    except Exception as e:
        print(f"Ralat set webhook automatik: {e}")

if __name__ == "__main__":
    # 1. Jalankan pemantau pasaran di latar belakang
    market_thread = threading.Thread(target=check_market)
    market_thread.daemon = True
    market_thread.start()

    # 2. Jalankan pendaftaran Webhook automatik di latar belakang
    webhook_thread = threading.Thread(target=auto_set_webhook)
    webhook_thread.daemon = True
    webhook_thread.start()

    # 3. Jalankan server Flask di thread utama
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
