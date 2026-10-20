import os
import time
import threading
import requests

# Konfigurasi Pembolehubah Persekitaran (Environment Variables)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY")

SYMBOL = "XAU/USD"
INTERVAL_ALERT = "15min"
LOOKBACK_CANDLES = 20

BASE_TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def send_telegram_message(chat_id, text):
    """Fungsi untuk menghantar mesej ke Telegram dengan kawalan ralat."""
    url = f"{BASE_TELEGRAM_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Ralat hantar mesej: {e}")
        return None

def background_scanner():
    """Fungsi pengimbas latar belakang (Background Scanner) dengan auto-reconnect."""
    print("🚀 Background Scanner bermula...")
    while True:
        try:
            # --- LETAKKAN KOD LOGIK UTAMA / SEMAKAN HARGA ANDA DI SINI ---
            # Contoh: panggil API Twelve Data, analisis harga, dan hantar alert jika perlu.
            
            # Semakan simulasi / lalang setiap 60 saat
            time.sleep(60)
            
        except requests.exceptions.RequestException as re:
            print(f"Ralat rangkaian pada Scanner: {re}. Cuba semula dalam 10 saat...")
            time.sleep(10)
        except Exception as e:
            print(f"Ralat tidak dijangka pada Scanner: {e}")
            time.sleep(10)

def telegram_listener():
    """Fungsi pendengar Telegram (Telegram Listener) dengan auto-reconnect."""
    print("🤖 Telegram Listener bermula...")
    offset = 0
    while True:
        try:
            url = f"{BASE_TELEGRAM_URL}/getUpdates"
            params = {"offset": offset, "timeout": 30}
            response = requests.get(url, params=params, timeout=40)
            
            if response.status_code == 200:
                data = response.json()
                for result in data.get("result", []):
                    offset = result["update_id"] + 1
                    # Proses mesej masuk di sini jika ada arahan khusus dari Telegram
                    message = result.get("message", {})
                    chat_id = message.get("chat", {}).get("id")
                    text = message.get("text", "")
                    
                    if text == "/status":
                        send_telegram_message(chat_id, "Bot sedang aktif dan berjalan lancar! 🟢")
                        
            # Sedikit jeda untuk mengelakkan gelung terlalu laju jika berlaku ralat pelayan
            time.sleep(2)
            
        except ('Connection aborted.', ConnectionResetError(104, 'Connection reset by peer')) as cre:
            # Menangani secara khusus ralat Connection reset by peer
            print(f"Ralat listener (Connection reset): {cre}. Menyambung semula dalam 5 saat...")
            time.sleep(5)
        except requests.exceptions.RequestException as re:
            print(f"Ralat rangkaian pada Listener: {re}. Menyambung semula dalam 5 saat...")
            time.sleep(5)
        except Exception as e:
            print(f"Ralat listener: {e}")
            time.sleep(5)

if __name__ == "__main__":
    print("Sistem dimulakan...")
    
    # Jalankan Background Scanner menggunakan Thread
    t_scanner = threading.Thread(target=background_scanner, daemon=True)
    t_scanner.start()
    
    # Jalankan Telegram Listener di utas utama (main thread)
    try:
        telegram_listener()
    except KeyboardInterrupt:
        print("Bot dihentikan secara manual.")



