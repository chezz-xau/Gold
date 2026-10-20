import os
import time
import threading
import telebot
import requests

# Token Telegram dimasukkan terus untuk elak ralat space
TELEGRAM_BOT_TOKEN = "8825296896:AAGLjzkFMzAXSXOcpNrLwkooftfpFlCYyN4".strip()

# Ambil konfigurasi lain daripada Environment Variables Railway secara selamat
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "").strip()

SYMBOL = "XAU/USD"

# Inisialisasi Bot menggunakan telebot
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
    # Hantar mesej makluman sementara
    wait_msg = bot.reply_to(message, "📊 *Sedang mengambil data harga XAU/USD terkini...*", parse_mode="Markdown")
    
    try:
        # Memanggil API Twelve Data menggunakan API Key dari Variables Railway
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
    
    # Kemaskini mesej sementara tadi dengan harga sebenar
    bot.edit_message_text(reply_text, chat_id=message.chat.id, message_id=wait_msg.message_id, parse_mode="Markdown")

@bot.message_handler(commands=['status'])
def send_status(message):
    bot.reply_to(message, "🟢 Bot aktif dan berjalan lancar di Railway!", parse_mode="Markdown")

def background_scanner():
    """Fungsi pengimbas latar belakang (Background Scanner)."""
    print("🚀 Background Scanner bermula...", flush=True)
    while True:
        try:
            time.sleep(60)
        except Exception as e:
            print(f"Ralat Scanner: {e}", flush=True)
            time.sleep(10)

def telegram_listener():
    """Fungsi pendengar Telegram menggunakan infinity_polling yang stabil."""
    print("🤖 Telegram Listener bermula (Telebot)...", flush=True)
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"Ralat Listener: {e}", flush=True)
            time.sleep(5)

if __name__ == "__main__":
    print("Sistem dimulakan...", flush=True)
    
    # Utas Pengimbas Latar Belakang
    t_scanner = threading.Thread(target=background_scanner, daemon=True)
    t_scanner.start()
    
    # Jalankan Telegram Bot Listener
    try:
        telegram_listener()
    except KeyboardInterrupt:
        print("Bot dihentikan.", flush=True)












