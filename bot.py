import os
import time
import threading
from datetime import datetime
import requests

# ==========================================
# KONFIGURASI TELEGRAM & TWELVE DATA
# ==========================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8825296896:AAEvBExEDqiwUKW3kTGYJa2Ao1OhDjBpwHQ")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "83535443393")
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "ab57d3086cd74858ac947545f0d3f106")

SYMBOL = "XAU/USD"
INTERVAL_ALERT = "15min"
LOOKBACK_CANDLES = 20

BASE_TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# ==========================================
# FUNGSI PENGHANTARAN MESEJ TELEGRAM
# ==========================================
def send_telegram_message(chat_id, text):
    url = f"{BASE_TELEGRAM_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Ralat hantar mesej Telegram: {e}")

# ==========================================
# FUNGSI BANTUAN API TWELVE DATA
# ==========================================
def fetch_time_series(symbol, interval, outputsize=50):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize={outputsize}&apikey={TWELVE_DATA_API_KEY}"
    try:
        res = requests.get(url, timeout=10).json()
        if "values" in res:
            return res["values"]
        else:
            print(f"Ralat API Twelve Data ({interval}): {res.get('message', 'Tiada data')}")
            return None
    except Exception as e:
        print(f"Ralat sambungan API ({interval}): {e}")
        return None

def analyze_market_structure(interval_name):
    data = fetch_time_series(SYMBOL, interval_name, outputsize=50)
    if not data or len(data) < 30:
        return f"**{interval_name.upper()}**: Data struktur tidak mencukupi."
    
    closes = [float(item["close"]) for item in data]
    highs = [float(item["high"]) for item in data]
    lows = [float(item["low"]) for item in data]
    
    current_price = closes[0]
    
    # Menilai struktur besar (Higher Highs & Lower Lows)
    recent_high = max(highs[:15])
    recent_low = min(lows[:15])
    past_high = max(highs[15:35])
    past_low = min(lows[15:35])
    
    if recent_high > past_high and recent_low > past_low:
        status = "🟢 Bullish Structure (Higher Highs & Higher Lows)"
    elif recent_high < past_high and recent_low < past_low:
        status = "🔴 Bearish Structure (Lower Highs & Lower Lows)"
    else:
        status = "🟡 Consolidation / Range Structure"
        
    return f"**Timeframe {interval_name.upper()}**:\n  └─ Struktur: {status}\n  └─ Harga Semasa: `{current_price:.2f}`"

def get_price_and_levels():
    data = fetch_time_series(SYMBOL, INTERVAL_ALERT, outputsize=LOOKBACK_CANDLES)
    if not data:
        return None, None, None
    
    current_price = float(data[0]["close"])
    highs = [float(x["high"]) for x in data[1:]]
    lows = [float(x["low"]) for x in data[1:]]
    
    resistance = max(highs)
    support = min(lows)
    
    return current_price, resistance, support

# ==========================================
# BACKGROUND SCANNER (AUTOSCAN BREAKOUT)
# ==========================================
def background_scanner():
    print("🚀 Background Breakout Scanner bermula...")
    last_alert_type = None
    
    while True:
        try:
            price, resistance, support = get_price_and_levels()
            if price is not None:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] XAUUSD | Harga: {price:.2f} | Res: {resistance:.2f} | Sup: {support:.2f}")
                
                # Semak Breakout
                if price > resistance and last_alert_type != "UP":
                    alert_msg = f"🚨 **BREAKOUT BULLISH (XAU/USD)**\nHarga `{price:.2f}` telah menembusi Resistance `{resistance:.2f}`!"
                    send_telegram_message(TELEGRAM_CHAT_ID, alert_msg)
                    last_alert_type = "UP"
                elif price < support and last_alert_type != "DOWN":
                    alert_msg = f"🚨 **BREAKOUT BEARISH (XAU/USD)**\nHarga `{price:.2f}` telah menembusi Support `{support:.2f}`!"
                    send_telegram_message(TELEGRAM_CHAT_ID, alert_msg)
                    last_alert_type = "DOWN"
                elif support <= price <= resistance:
                    last_alert_type = None
                    
        except Exception as e:
            print(f"Ralat dalam background scanner: {e}")
            
        time.sleep(60)

# ==========================================
# TELEGRAM LISTENER (2-HALA VIA HTTP POLLING)
# ==========================================
def telegram_listener():
    print("🤖 Telegram 2-Way Listener bermula...")
    
    # Pembersihan Webhook lama untuk elak konflik
    try:
        requests.get(f"{BASE_TELEGRAM_URL}/deleteWebhook?drop_pending_updates=True", timeout=5)
    except Exception as e:
        print(f"Ralat pembersihan webhook: {e}")

    offset = 0
    while True:
        try:
            url = f"{BASE_TELEGRAM_URL}/getUpdates?offset={offset}&timeout=20"
            res = requests.get(url, timeout=25).json()
            
            if res.get("ok") and res.get("result"):
                for update in res["result"]:
                    offset = update["update_id"] + 1
                    
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"].strip()
                        
                        if text in ["/start", "/help"]:
                            reply = (
                                "👋 **Selamat datang ke XAUUSD Breakout & Structure Bot!**\n\n"
                                "Gunakan arahan berikut:\n"
                                "🔹 `/harga` - Semak harga semasa & paras SNR M15\n"
                                "🔹 `/trend` - Semak analisis struktur besar M30 & H1\n\n"
                                "⚡ Bot ini juga memantau *breakout* secara automatik!"
                            )
                            send_telegram_message(chat_id, reply)
                            
                        elif text == "/harga":
                            price, res_lvl, sup_lvl = get_price_and_levels()
                            if price:
                                reply = (
                                    f"📊 **XAU/USD HARGA SEMASA**\n"
                                    f"───────────────\n"
                                    f"💰 **Harga:** `{price:.2f}`\n"
                                    f"🔴 **Resistance (M15):** `{res_lvl:.2f}`\n"
                                    f"🟢 **Support (M15):** `{sup_lvl:.2f}`\n"
                                    f"⏰ `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
                                )
                            else:
                                reply = "❌ Gagal mengambil data harga terkini dari Twelve Data."
                            send_telegram_message(chat_id, reply)
                            
                        elif text == "/trend":
                            trend_m30 = analyze_market_structure("30min")
                            trend_h1 = analyze_market_structure("1h")
                            reply = (
                                f"📈 **ANALISIS STRUKTUR BESAR XAU/USD**\n"
                                f"───────────────\n"
                                f"{trend_m30}\n\n"
                                f"{trend_h1}\n"
                                f"───────────────\n"
                                f"⏰ `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
                            )
                            send_telegram_message(chat_id, reply)

        except Exception as e:
            print(f"Ralat dalam telegram listener: {e}")
            time.sleep(3)

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    # Jalankan scanner breakout di latar belakang
    scanner_thread = threading.Thread(target=background_scanner, daemon=True)
    scanner_thread.start()
    
    # Jalankan listener 2-hala di thread utama
    telegram_listener()


