import os
import time
import threading
import requests

# Konfigurasi Pembolehubah Persekitaran
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY")

SYMBOL = "XAU/USD"
INTERVAL_ALERT = "15min"
LOOKBACK_CANDLES = 20

BASE_TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def send_telegram_message(chat_id, text):
    """Fungsi untuk menghantar mesej ke Telegram."""
    url = f"{BASE_TELEGRAM_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Ralat hantar mesej: {e}")
        return None

def process_command(chat_id, text):
    """Fungsi mengendalikan arahan daripada pengguna Telegram."""
    cmd = text.strip().lower()
    
    if cmd in ["/start", "/help"]:
        msg = (
            "🤖 *My Breakout Scanner Bot Active!*\n\n"
            "Arahan yang sedia ada:\n"
            "• `/start` - Semak status bot\n"
            "• `/trend` - Semak analisis trend XAU/USD\n"
            "• `/status` - Semak sambungan pelayan"
        )
        send_telegram_message(chat_id, msg)
        
    elif cmd == "/trend":
        # Anda boleh masukkan fungsi analisis trend sebenar anda di sini
        send_telegram_message(chat_id, "📊 *Analisis Trend XAU/USD:* Sedang memproses data harga...")
        
    elif cmd == "/status":
        send_telegram_message(chat_id, "🟢 Bot aktif dan berjalan di Railway!")

def background_scanner():
    """Fungsi pengimbas latar belakang (Background Scanner)."""
    print("🚀 Background Scanner bermula...")
    while True:
        try:
            # --- LOGIK PEMANTAUAN HARGA AUTOMATIK ANDA DI SINI ---
            time.sleep(60)
            
        except requests.exceptions.RequestException as re:
            print(f"Ralat rangkaian pada Scanner: {re}. Rehat 10s...")
            time.sleep(10)
        except Exception as e:
            print(f"Ralat Scanner: {e}")
            time.sleep(10)

def telegram_listener():
    """Fungsi pendengar Telegram dengan Auto-Reconnect & Command Processing."""
    print("🤖 Telegram Listener bermula...")
    offset = 0
    while True:
        try:
            url = f"{BASE_TELEGRAM_URL}/getUpdates"
            params = {"offset": offset, "timeout": 20}
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                for result in data.get("result", []):
                    offset = result["update_id"] + 1
                    message = result.get("message", {})
                    chat_id = message.get("chat", {}).get("id")
                    text = message.get("text", "")
                    
                    if text and chat_id:
                        # Proses arahan yang dihantar pengguna
                        process_command(chat_id, text)
                        
            time.sleep(1)
            
        except requests.exceptions.RequestException as re:
            print(f"Ralat sambungan Listener: {re}. Rehat 5s...")
            time.sleep(5)
        except Exception as e:
            print(f"Ralat Listener: {e}")
            time.sleep(5)

if __name__ == "__main__":
    print("Sistem dimulakan...")
    
    # Utas Pengimbas Latar Belakang
    t_scanner = threading.Thread(target=background_scanner, daemon=True)
    t_scanner.start()
    
    # Utas Utama Pendengar Telegram
    try:
        telegram_listener()
    except KeyboardInterrupt:
        print("Bot dihentikan.")




