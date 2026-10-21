import os
import threading
import time
import requests
from flask import Flask, request
import telebot

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
TWELVE_DATA_API_KEY = os.environ.get("TWELVE_DATA_API_KEY")

RENDER_URL = "https://gold-mfre.onrender.com"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot XAUUSD Webhook active!"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Bad Request', 400

# Fungsi untuk mengambil data candle & analisa bucu/SMA 1
def analyze_tf(timeframe):
    if not TWELVE_DATA_API_KEY:
        return "⚠️ API Key Twelve Data tiada."
    
    url = f"https://api.twelvedata.com/time_series?symbol=XAU/USD&interval={timeframe}&outputsize=10&apikey={TWELVE_DATA_API_KEY}"
    try:
        res = requests.get(url).json()
        if "values" not in res:
            return f"⚠️ Gagal dapatkan data {timeframe}."
        
        candles = res["values"]  # Index 0 = Candle semasa (live/terkini), Index 1 = Candle baru close
        
        # Candle yang baru close (Index 1)
        last_close = float(candles[1]["close"]) # SMA(1) = Close price
        
        # Mencari Bucu (High/Low) terdekat daripada 5 candle terdahulu (Index 2 hingga 6)
        past_highs = [float(c["high"]) for c in candles[2:7]]
        past_lows = [float(c["low"]) for c in candles[2:7]]
        
        bucu_tertinggi = max(past_highs)
        bucu_terendah = min(past_lows)
        
        # Semakan Breakout
        if last_close > bucu_tertinggi:
            status = f"🚀 **BREAKOUT BUY** (Close ${last_close:.2f} > Bucu High ${bucu_tertinggi:.2f})"
        elif last_close < bucu_terendah:
            status = f"🔻 **BREAKOUT SELL** (Close ${last_close:.2f} < Bucu Low ${bucu_terendah:.2f})"
        else:
            status = f"↔️ **SIDEWAYS / NO BREAKOUT**\n  • Bucu High: ${bucu_tertinggi:.2f}\n  • Bucu Low: ${bucu_terendah:.2f}\n  • Close SMA(1): ${last_close:.2f}"
            
        return status
    except Exception as e:
        return f"❌ Ralat analisa {timeframe}: {e}"

# Arahan /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message, 
        "Halo Syezz! Bot XAUUSD aktif.\n\n"
        "Gunakan arahan:\n"
        "• /harga - Semak harga & analisa Breakout Bucu (M30 & H1)"
    )

# Arahan /harga atau /price
@bot.message_handler(commands=['harga', 'price', 'trend'])
def send_price_and_trend(message):
    try:
        # Ambil harga semasa
        price_url = f"https://api.twelvedata.com/price?symbol=XAU/USD&apikey={TWELVE_DATA_API_KEY}"
        price_res = requests.get(price_url).json()
        current_price = float(price_res.get("price", 0)) if "price" in price_res else "N/A"
        
        # Analisa M30 dan H1
        analysis_m30 = analyze_tf("30min")
        analysis_h1 = analyze_tf("1h")
        
        text = (
            f"📊 **ANALISA TREND & BUCU SMA(1) XAU/USD**\n"
            f"-----------------------------------\n"
            f"💰 **Harga Live:** ${current_price:.2f}\n\n"
            f"⏱️ **TIMEFRAME M30:**\n{analysis_m30}\n\n"
            f"⏱️ **TIMEFRAME H1:**\n{analysis_h1}\n\n"
            f"💡 *Nota: SMA(1) mengikut aras penutupan candle terdekat.*"
        )
        bot.reply_to(message, text, parse_mode="Markdown")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ralat: {e}")

def check_market():
    while True:
        try:
            if TWELVE_DATA_API_KEY:
                url = f"https://api.twelvedata.com/price?symbol=XAU/USD&apikey={TWELVE_DATA_API_KEY}"
                response = requests.get(url)
                data = response.json()
                if "price" in data:
                    print(f"[LOG HARGA]: XAUUSD = {data['price']}")
        except Exception as e:
            print(f"Ralat pemantauan: {e}")
        time.sleep(300)

def auto_set_webhook():
    time.sleep(3)
    try:
        webhook_url = f"{RENDER_URL}/{TOKEN}"
        req_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}"
        res = requests.get(req_url).json()
        print(f"Status Auto-Set Webhook: {res}")
    except Exception as e:
        print(f"Ralat set webhook automatik: {e}")

if __name__ == "__main__":
    market_thread = threading.Thread(target=check_market)
    market_thread.daemon = True
    market_thread.start()

    webhook_thread = threading.Thread(target=auto_set_webhook)
    webhook_thread.daemon = True
    webhook_thread.start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
