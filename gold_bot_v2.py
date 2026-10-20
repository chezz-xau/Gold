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

def get_timeframe_data(interval, outputsize=4):
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
        "• `/trend` - Semak analisis M30 & H1 terkini (Strict Close Candle)\n"
        "• `/status` - Semak status pelayan"
    )
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['trend'])
def send_trend(message):
    wait_msg = bot.reply_to(message, "📊 *Sedang menganalisis Closed Candle M30 & H1 XAU/USD...*", parse_mode="Markdown")
    
    m30_data = get_timeframe_data("30min", outputsize=4)
    h1_data = get_timeframe_data("1h", outputsize=2)
    
    if not m30_data or len(m30_data) < 3 or not h1_data:
        bot.edit_message_text("⚠️ Gagal menarik data siri masa daripada Twelve Data.", chat_id=message.chat.id, message_id=wait_msg.message_id)
        return

    # M30[1] adalah candle yang BARU SAHAJA TUTUP, M30[2] adalah rujukan High/Low
    c_closed = m30_data[1] 
    c_ref = m30_data[2]     
    h1_current = h1_data[0]
    
    close_m30 = float(c_closed['close'])
    prev_high = float(c_ref['high'])
    prev_low = float(c_ref['low'])
    
    h1_close = float(h1_current['close'])
    h1_open = float(h1_current['open'])
    h1_trend = "🟢 BULLISH (H1)" if h1_close >= h1_open else "🔴 BEARISH (H1)"

    breakout_status = "⚖️ Market dalam zon konsolidasi / Sideways"
    if close_m30 > prev_high:
        breakout_status = "🚀 **VALID BREAKOUT BUY M30!**\n(Close candle sah melepasi High sebelumnya)"
    elif close_m30 < prev_low:
        breakout_status = "🔻 **VALID BREAKOUT SELL M30!**\n(Close candle sah melepasi Low sebelumnya)"

    reply_text = (
        f"📊 *ANALISIS CLOSED CANDLE M30 & H1*\n\n"
        f"🕒 *Trend H1:* {h1_trend} (`${h1_close:.2f}`)\n\n"
        f"📈 *Analisis M30 (Closed Candle):*\n"
        f"• Harga Close Candle: `${close_m30:.2f}`\n"
        f"• High Rujukan: `${prev_high:.2f}`\n"
        f"• Low Rujukan: `${prev_low:.2f}`\n\n"
        f"🎯 *Status:* {breakout_status}\n\n"
        f"📌 *Masa Candle Tutup:* `{c_closed['datetime']}`"
    )
    
    bot.edit_message_text(reply_text, chat_id=message.chat.id, message_id=wait_msg.message_id, parse_mode="Markdown")

@bot.message_handler(commands=['status'])
def send_status(message):
    bot.reply_to(message, "🟢 Bot & Strict Closed-Candle Scanner aktif di Railway!", parse_mode="Markdown")

def background_breakout_scanner():
    global last_m30_time
    print("🚀 Background Strict Closed-Candle Scanner M30 bermula...", flush=True)
    
    while True:
        try:
            m30_data = get_timeframe_data("30min", outputsize=4)
            if m30_data and len(m30_data) >= 3:
                c_closed = m30_data[1]  # Candle yang baru tutup
                c_ref = m30_data[2]      # Candle rujukan
                candle_time = c_closed['datetime']
                
                # Semak hanya apabila satu-satu candle M30 bertukar masa tutupnya
                if candle_time != last_m30_time:
                    close_val = float(c_closed['close'])
                    p_high = float(c_ref['high'])
                    p_low = float(c_ref['low'])
                    
                    alert_msg = None
                    if close_val > p_high:
                        alert_msg = (
                            f"🚨 *M30 VALID CLOSED BREAKOUT BUY!* 🚀\n\n"
                            f"💱 **Simbol:** `{SYMBOL}`\n"
                            f"💰 **Harga Close M30:** `${close_val:.2f}`\n"
                            f"📈 Sah Close melepasi High Rujukan (`${p_high:.2f}`)\n"
                            f"🕒 Masa Tutup: `{candle_time}`"
                        )
                    elif close_val < p_low:
                        alert_msg = (
                            f"🚨 *M30 VALID CLOSED BREAKOUT SELL!* 🔻\n\n"
                            f"💱 **Simbol:** `{SYMBOL}`\n"
                            f"💰 **Harga Close M30:** `${close_val:.2f}`\n"
                            f"📉 Sah Close melepasi Low Rujukan (`${p_low:.2f}`)\n"
                            f"🕒 Masa Tutup: `{candle_time}`"
                        )
                    
                    if alert_msg and CHAT_ID:
                        bot.send_message(CHAT_ID, alert_msg, parse_mode="Markdown")
                        last_m30_time = candle_time
                        
            time.sleep(60)
        except Exception as e:
            print(f"Ralat Background Scanner: {e}", flush=True)
            time.sleep(30)

if __name__ == "__main__":
    print("Sistem bot dimulakan...", flush=True)
    t_scanner = threading.Thread(target=background_breakout_scanner, daemon=True)
    t_scanner.start()
    
    print("🤖 Mulakan Telegram Polling...", flush=True)
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
























