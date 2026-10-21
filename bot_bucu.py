import os
import time
from datetime import datetime, timedelta
import pytz
import requests
import telebot

# 1. AMBIL VARIABLES DARI ENVIRONMENT (RAILWAY)
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SYMBOL = "XAU/USD"
TIMEZONE = pytz.timezone("Asia/Kuala_Lumpur")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

last_m30_alert_state = None  

# 2. FUNGSI DAPATKAN DATA TWELVE DATA
def get_market_data(timeframe, outputsize=30):
    url = f"https://api.twelvedata.com/time_series?symbol={SYMBOL}&interval={timeframe}&outputsize={outputsize}&apikey={TWELVE_DATA_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        if "values" in data:
            return data["values"]
        return None
    except Exception as e:
        print(f"Error fetching {timeframe}: {e}")
        return None

# 3. FUNGSI ANALISA STRUKTUR (100% PURA BODY CANDLE)
def analyze_structure(candles, lookback_count):
    current_close = float(candles[0]["close"])
    history_candles = candles[1:lookback_count + 1]

    body_highs = []
    body_lows = []

    for c in history_candles:
        open_price = float(c["open"])
        close_price = float(c["close"])
        body_highs.append(max(open_price, close_price))
        body_lows.append(min(open_price, close_price))

    bucu_tertinggi = max(body_highs)
    bucu_terendah = min(body_lows)

    if current_close > bucu_tertinggi:
        trend = "🟢 BULLISH (Breakout Body)"
        state = "BULLISH_BREAKOUT"
    elif current_close < bucu_terendah:
        trend = "🔴 BEARISH (Breakout Body)"
        state = "BEARISH_BREAKOUT"
    else:
        trend = "🟡 SIDEWAYS (Dalam Range)"
        state = "SIDEWAYS"

    return {
        "close": current_close,
        "high": bucu_tertinggi,
        "low": bucu_terendah,
        "trend": trend,
        "state": state
    }

# 4. COMMAND TELEGRAM: /trend
@bot.message_handler(commands=['trend'])
def send_trend_analysis(message):
    data_h1 = get_market_data("1h", outputsize=30)
    data_m30 = get_market_data("30min", outputsize=30)

    if not data_h1 or not data_m30:
        bot.reply_to(message, "❌ Gagal mengambil data market dari Twelve Data.")
        return

    res_h1 = analyze_structure(data_h1, lookback_count=24)
    res_m30 = analyze_structure(data_m30, lookback_count=16)

    report = (
        "📊 **ANALISIS STRUKTUR BUCU (BODY PURA)**\n\n"
        "⏰ **Analisis H1 (Struktur Besar / Major):**\n"
        f"• **Trend H1:** {res_h1['trend']}\n"
        f"• **Close H1:** ${res_h1['close']:.2f}\n"
        f"• **Bucu Body High H1:** ${res_h1['high']:.2f}\n"
        f"• **Bucu Body Low H1:** ${res_h1['low']:.2f}\n\n"
        "📈 **Analisis M30 (Bucu Paling Hampir / Minor):**\n"
        f"• **Trend M30:** {res_m30['trend']}\n"
        f"• **Close M30:** ${res_m30['close']:.2f}\n"
        f"• **Bucu Body High M30:** ${res_m30['high']:.2f}\n"
        f"• **Bucu Body Low M30:** ${res_m30['low']:.2f}\n\n"
        "🎯 **Status:** Bucu Swing Body Only"
    )
    
    bot.send_message(message.chat.id, report, parse_mode="Markdown")

# 5. SEMAKAN AUTO-ALERT M30
def check_m30_breakout_alert():
    global last_m30_alert_state
    
    data_m30 = get_market_data("30min", outputsize=30)
    if not data_m30:
        return

    res_m30 = analyze_structure(data_m30, lookback_count=16)
    current_state = res_m30["state"]

    if current_state != last_m30_alert_state:
        if current_state == "BULLISH_BREAKOUT":
            alert_msg = (
                "🚀 **ALERT BREAKOUT M30 (BULLISH BODY)!** 🟢\n\n"
                f"Candle M30 baharu sahaja **CLOSE**!\n"
                f"• **Close M30:** ${res_m30['close']:.2f}\n"
                f"• **Bucu Body High Terlepas:** ${res_m30['high']:.2f}\n\n"
                "Struktur M30 Terdekat sah bertukar kepada **Uptrend / Bullish**!"
            )
            if TELEGRAM_CHAT_ID:
                bot.send_message(TELEGRAM_CHAT_ID, alert_msg, parse_mode="Markdown")
            last_m30_alert_state = current_state
            
        elif current_state == "BEARISH_BREAKOUT":
            alert_msg = (
                "⚠️ **ALERT BREAKOUT M30 (BEARISH BODY)!** 🔴\n\n"
                f"Candle M30 baharu sahaja **CLOSE**!\n"
                f"• **Close M30:** ${res_m30['close']:.2f}\n"
                f"• **Bucu Body Low Tembus:** ${res_m30['low']:.2f}\n\n"
                "Struktur M30 Terdekat sah bertukar kepada **Downtrend / Bearish**!"
            )
            if TELEGRAM_CHAT_ID:
                bot.send_message(TELEGRAM_CHAT_ID, alert_msg, parse_mode="Markdown")
            last_m30_alert_state = current_state
            
        elif current_state == "SIDEWAYS":
            last_m30_alert_state = current_state

# 6. SLEEP TIMER TEPAT MASA MALAYSIA (MYT)
def wait_until_m30_close():
    now = datetime.now(TIMEZONE)
    if now.minute < 30:
        next_close = now.replace(minute=30, second=5, microsecond=0)
    else:
        next_close = (now + timedelta(hours=1)).replace(minute=0, second=5, microsecond=0)
    
    sleep_seconds = (next_close - now).total_seconds()
    if sleep_seconds > 0:
        time.sleep(sleep_seconds)

# 7. MAIN RUNNER
if __name__ == "__main__":
    import threading

    def auto_check_loop():
        # Beri masa 5 saat pertama sebelum buat semakan
        time.sleep(5)
        check_m30_breakout_alert()
        while True:
            wait_until_m30_close()
            check_m30_breakout_alert()

    t = threading.Thread(target=auto_check_loop)
    t.daemon = True
    t.start()

    print("Bot Syezz beroperasi (MYT Timezone Set)...")
    bot.infinity_polling()
