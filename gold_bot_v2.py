import os
import time
import threading
import telebot

# Konfigurasi Pembolehubah Persekitaran
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY")

SYMBOL = "XAU/USD"
INTERVAL_ALERT = "15min"
LOOKBACK_CANDLES = 20

# Inisialisasi Bot menggunakan telebot
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    msg = (
        "🤖 *My Breakout Scanner Bot Active!*\n\n"
        "Arahan yang sedia ada:\n"
        "• `/start` - Semak status bot\n"
        "• `/trend` - Semak analisis trend XAU/USD\n"
        "• `/status` - Semak sambungan pelayan"
    )
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['trend'])
def send_trend(message):
    bot.reply_to(message, "📊 *Analisis Trend XAU/USD:*\nData harga sedang diproses...", parse_mode="Markdown")

@bot.message_handler(commands=['status'])
def send_status(message):
    bot.reply_to(message, "🟢 Bot aktif dan berjalan lancar di Railway!", parse_mode="Markdown")

def background_scanner():
    """Fungsi pengimbas latar belakang (Background Scanner)."""
    print("🚀 Background Scanner bermula...")
    while True:
        try:
            # --- LOGIK IMBAAN HARGA AUTOMATIK ANDA DI SINI ---
            time.sleep(60)
        except Exception as e:
            print(f"Ralat Scanner: {e}")
            time.sleep(10)

def telegram_listener():
    """Fungsi pendengar Telegram menggunakan infinity_polling yang stabil."""
    print("🤖 Telegram Listener bermula (Telebot)...")
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"Ralat Listener: {e}")
            time.sleep(5)

if __name__ == "__main__":
    print("Sistem dimulakan...")
    
    # Utas Pengimbas Latar Belakang
    t_scanner = threading.Thread(target=background_scanner, daemon=True)
    t_scanner.start()
    
    # Jalankan Telegram Bot Listener
    try:
        telegram_listener()
    except KeyboardInterrupt:
        print("Bot dihentikan.")







