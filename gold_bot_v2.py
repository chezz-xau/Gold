import os
import time
import threading
import telebot
import requests

# 1. Konfigurasi Token Baharu & API Key
TELEGRAM_BOT_TOKEN = "8825296896:AAEmv0VGpTiGD1LtdIkKhQ5PxM6NORXvUXE".strip()
TWELVE_DATA_API_KEY = "ab57d3086cd74534887340b90e0c0342".strip()

SYMBOL = "XAU/USD"

# Inisialisasi Bot
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    msg = (
        "🤖 *My Breakout Scanner Bot Active!*\n\n"
        "Arahan yang sedia ada:\n"
        "• `/start` - Semak status bot\n"
        "• `/trend` - Semak harga & analisis trend XAU/USD\n"
        "• `/status` - Semak sambungan pelayan"
    )
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['trend'])
def send_trend(message):
    wait_msg = bot.reply_to(message, "📊 *Sedang mengambil data harga XAU/USD terkini...*", parse_mode="Markdown")
    
    try:
        url = f"https://api.twelvedata.com/price?symbol={SYMBOL}&apikey={TWELVE_DATA_API_KEY}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if "price" in data:
            price_val = float(data["price"])
            reply_text = (
                f"📊 *ANALISIS HARGA XAU/USD*\n\n"
                f"💱 **Simbol:** `{SYMBOL}`\n"
                f"💰 **Harga Semasa:** `${price_val:.2f}`\n\n"
                f"🟢 Status: *Data Live Twelve Data Berjaya Ditarik!*"
            )
        else:
            reply_text = f"⚠️ *Gagal mengambil data.* Response API: `{data}`"
            
    except Exception as e:
        reply_text = f"❌ *Ralat sambungan:* `{e}`"
    
    bot.edit_message_text(reply_text, chat_id=message.chat.id, message_id=wait_msg.message_id, parse_mode="Markdown")

@bot.message_handler(commands=['status'])
def send_status(message):
    bot.reply_to(message, "🟢 Bot aktif dan berjalan lancar di Railway!", parse_mode="Markdown")

def background_scanner():
    print("🚀 Background Scanner bermula...", flush=True)
    while True:
        try:
            time.sleep(60)
        except Exception as e:
            print(f"Ralat Scanner: {e}", flush=True)
            time.sleep(10)

def telegram_listener():
    print("🤖 Telegram Listener bermula (Telebot)...", flush=True)
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"Ralat Listener: {e}", flush=True)
            time.sleep(5)

if __name__ == "__main__":
    print("Sistem dimulakan...", flush=True)
    
    t_scanner = threading.Thread(target=background_scanner, daemon=True)
    t_scanner.start()
    
    try:
        telegram_listener()
    except KeyboardInterrupt:
        print("Bot dihentikan.", flush=True)

















