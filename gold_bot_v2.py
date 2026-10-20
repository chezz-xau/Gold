import os
import time
import threading
import telebot
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

SYMBOL = "XAU/USD"
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

last_m30_time = None

def get_timeframe_data(interval, outputsize=3):
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={SYMBOL}&interval={interval}&outputsize={outputsize}&apikey={TWELVE_DATA_API_KEY}"
        response = requests.get(url, timeout=10)
        data = response.json()
        if "values" in data:
            return data["values"]
    except Exception as e:
        print(f"Ralat API Timeframe {interval}: {e}", flush=True)
    return None

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    msg = (
        "🤖 *Syezz XAU/USD Breakout Scanner Active!*\n\n"
        "Arahan sedia ada:\n"
        "• `/start` - Paparkan menu utama\n"
        "• `/trend` - Semak analisis M30 & H1 terkini (Kriteria Close Candle)\n"
        "• `/status` - Semak status pelayan"
    )
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['trend'])
def send_trend(message):
    wait_msg = bot.reply_to(message, "📊 *Sedang menganalisis Close Candle M30 & H1 XAU/USD...*", parse_mode="Markdown")
    
    m30_data = get_timeframe_data("30min", outputsize=3)
    h1_data = get_timeframe_data("1h", outputsize=2)
    
    if not m30_data or not h1_data:
        bot.edit_message_text("⚠️ Gagal menarik data siri masa daripada Twelve Data.", chat_id=message.chat.id, message_id=wait_msg.message_id)
        return

    c0 = m30_data[0]
    c1 = m30_data[1]
    h1_current = h1_data[0]
    
    close_m30 = float(c0['close'])
    prev_high = float(c1['high'])
    prev_low = float(c1['low'])
    
    h1_close = float(h1_current['close'])
    h1_open = float(h1_current['open'])
    h1_trend = "🟢 BULLISH (H1)" if h1_close >= h1_open else "🔴 BEARISH (H1)"

    breakout_status = "⚖️ Market dalam zon konsolidasi / Sideways"
    if close_m30 > prev_high:
        breakout_status = "🚀 **VALID BREAKOUT BUY M30!**\n(Harga Close melepasi High candle sebelumnya)"
    elif close_m30 < prev_low:
        breakout_status = "🔻 **VALID BREAKOUT SELL M30!**\n(Harga Close melepasi Low candle sebelumnya)"

    reply_text = (
        f"📊 *ANALISIS MULTI-TIMEFRAME XAU/USD*\n\n"
        f"🕒 *Trend H1:* {h1_trend} (`${h1_close:.2f}`)\n\n"
        f"📈 *Analisis M30 (Close Candle Basis):*\n"
        f"• Harga Close Semasa: `${close_m30:.2f}`\n"
        f"• High Candle Lepas: `${prev_high:.2f}`\n"
        f"• Low Candle Lepas: `${prev_low:.2f}`\n\n"
        f"🎯 *Status:* {breakout_status}\n\n"
        f"📌 *Masa Candle:* `{c0['datetime']}`"
    )
    
    bot.edit_message_text(reply_text, chat_id=message.chat.id, message_id=wait_msg.message_id, parse_mode="Markdown")

@bot.message_handler(commands=['status'])
def send_status(message):
    bot.reply_to(message, "🟢 Bot & M30/H1 Scanner aktif di Railway!", parse_mode="Markdown")

def background_breakout_scanner():
    global last_m30_time
    print("🚀 Background Close-Candle Breakout Scanner M30 bermula...", flush=True)
    
    while True:
        try:
            m30_data = get_timeframe_data("30min", outputsize=2)
            if m30_data:
                current_candle = m30_data[0]
                prev_candle = m30_data[1]
                candle_time = current_candle['datetime']
                
                if candle_time != last_m30_time:
                    close_val = float(current_candle['close'])
                    p_high = float(prev_candle['high'])
                    p_low = float(prev_candle['low'])
                    
                    alert_msg = None
                    if close_val > p_high:
                        alert_msg = (
                            f"🚨 *M30 VALID BREAKOUT BUY ALERT!* 🚀\n\n"
                            f"💱 **Simbol:** `{SYMBOL}`\n"
                            f"💰 **Harga Close M30:** `${close_val:.2f}`\n"
                            f"📈 Sah Close melepasi High Sebelumnya (`${p_high:.2f}`)\n"
                            f"🕒 Masa Candle: `{candle_time}`"
                        )
                    elif close_val < p_low:
                        alert_msg = (
                            f"🚨 *M30 VALID BREAKOUT SELL ALERT!* 🔻\n\n"
                            f"💱 **Simbol:** `{SYMBOL}`\n"
                            f"💰 **Harga Close M30:** `${close_val:.2f}`\n"
                            f"📉 Sah Close melepasi Low Sebelumnya (`${p_low:.2f}`)\n"
                            f"🕒 Masa Candle: `{candle_time}`"
                        )
                    
                    if alert_msg and CHAT_ID:
                        bot.send_message(CHAT_ID, alert_msg, parse_mode="Markdown")
                        last_m30_time = candle_time
                        
            time.sleep(120)
        except Exception as e:
            print(f"Ralat Background Scanner: {e}", flush=True)
            time.sleep(30)

if __name__ == "__main__":
    print("Sistem bot dimulakan...", flush=True)
    t_scanner = threading.Thread(target=background_breakout_scanner, daemon=True)
    t_scanner.start()
    
    print("🤖 Mulakan Telegram Polling...", flush=True)
    bot.infinity_polling(timeout=20, long_polling_timeout=10)























