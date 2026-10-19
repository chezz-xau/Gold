import os
import time
import threading
from datetime import datetime
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8825296896:AAGLjzkFMzAXSXOcpNrLwkooftfpFlCYyN4")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "83535443393")
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "ab57d3086cd74858ac947545f0d3f106")

SYMBOL = "XAU/USD"
INTERVAL_ALERT = "15min"
LOOKBACK_CANDLES = 20

BASE_TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def send_telegram_message(chat_id, text):
    url = f"{BASE_TELEGRAM_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Ralat hantar mesej: {e}")

def fetch_time_series(symbol, interval, outputsize=50):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize={outputsize}&apikey={TWELVE_DATA_API_KEY}"
    try:
        res = requests.get(url, timeout=10).json()
        if "values" in res:
            return res["values"]
    except Exception as e:
        print(f"Ralat API: {e}")
    return None

def analyze_market_structure(interval_name):
    # Jeda 2 saat supaya API tidak cecah limit request
    time.sleep(2)
    data = fetch_time_series(SYMBOL, interval_name, outputsize=50)
    if not data or len(data) < 30:
        return f"**{interval_name.upper()}**: Data tidak mencukupi."
    closes = [float(item["close"]) for item in data]
    highs = [float(item["high"]) for item in data]
    lows = [float(item["low"]) for item in data]
    recent_high, past_high = max(highs[:15]), max(highs[15:35])
    recent_low, past_low = min(lows[:15]), min(lows[15:35])
    
    if recent_high > past_high and recent_low > past_low:
        status = "🟢 Bullish Structure (HH & HL)"
    elif recent_high < past_high and recent_low < past_low:
        status = "🔴 Bearish Structure (LH & LL)"
    else:
        status = "🟡 Consolidation / Range"
    return f"**Timeframe {interval_name.upper()}**:\n  └─ Struktur: {status}\n  └─ Harga: `{closes[0]:.2f}`"

def get_price_and_levels():
    data = fetch_time_series(SYMBOL, INTERVAL_ALERT, outputsize=LOOKBACK_CANDLES)
    if not data:
        return None, None, None
    return float(data[0]["close"]), max([float(x["high"]) for x in data[1:]]), min([float(x["low"]) for x in data[1:]])

def background_scanner():
    print("🚀 Background Scanner bermula...")
    last_alert = None
    while True:
        try:
            price, res, sup = get_price_and_levels()
            if price is not None:
                if price > res and last_alert != "UP":
                    send_telegram_message(TELEGRAM_CHAT_ID, f"🚨 **BREAKOUT BULLISH**\nHarga `{price:.2f}` tembus Resistance `{res:.2f}`!")
                    last_alert = "UP"
                elif price < sup and last_alert != "DOWN":
                    send_telegram_message(TELEGRAM_CHAT_ID, f"🚨 **BREAKOUT BEARISH**\nHarga `{price:.2f}` tembus Support `{sup:.2f}`!")
                    last_alert = "DOWN"
                elif sup <= price <= res:
                    last_alert = None
        except Exception as e:
            print(f"Ralat scanner: {e}")
        time.sleep(60)

def telegram_listener():
    print("🤖 Telegram Listener bermula...")
    try:
        requests.get(f"{BASE_TELEGRAM_URL}/deleteWebhook?drop_pending_updates=True", timeout=5)
    except Exception as e:
        print(f"Ralat webhook: {e}")
        
    offset = 0
    while True:
        try:
            res = requests.get(f"{BASE_TELEGRAM_URL}/getUpdates?offset={offset}&timeout=20", timeout=25).json()
            if res.get("ok") and res.get("result"):
                for update in res["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"].strip()
                        if text in ["/start", "/help"]:
                            send_telegram_message(chat_id, "👋 **XAUUSD Bot Aktif!**\nGunakan `/harga` atau `/trend`.")
                        elif text == "/harga":
                            p, r, s = get_price_and_levels()
                            send_telegram_message(chat_id, f"📊 **HARGA SEMASA**\n💰 Harga: `{p:.2f}`\n🔴 Res: `{r:.2f}`\n🟢 Sup: `{s:.2f}`" if p else "❌ Gagal ambil data.")
                        elif text == "/trend":
                            send_telegram_message(chat_id, f"📈 **ANALISIS STRUKTUR**\n\n{analyze_market_structure('30min')}\n\n{analyze_market_structure('1h')}")
        except Exception as e:
            print(f"Ralat listener: {e}")
            time.sleep(3)

if __name__ == "__main__":
    threading.Thread(target=background_scanner, daemon=True).start()
    telegram_listener()

