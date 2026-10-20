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

def get_timeframe_data(interval, outputsize=15):
    """Ambil data yang lebih besar (cukup untuk cari puncak tertinggi & terendah terdekat)"""
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={SYMBOL}&interval={interval}&outputsize={outputsize}&apikey={TWELVE_DATA_API_KEY}"
        response = requests.get(url, timeout=10)
        data = response.json()
        if "values" in data:
            return data["values"] # Indeks 0 = terkini (sedang berjalan), Indeks 1 = baru tutup
    except Exception as e:
        print(f"Ralat API Timeframe {interval}: {e}", flush=True)
    return None

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    msg = (
        "🤖 *Syezz XAU/USD Peak Breakout Scanner Active!*\n"
        "📈 *Strategi:* SMA 1 (Puncak Tertinggi & Terendah M30)\n\n"
        "Arahan sedia ada:\n"
        "• `/start` - Paparkan menu utama\n"
        "• `/trend` - Semak analisis puncak M30 & Trend H1\n"
        "• `/status` - Semak status pelayan"
    )
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['trend'])
def send_trend(message):
    wait_msg = bot.reply_to(message, "📊 *Sedang mengesan puncak tertinggi & terendah SMA 1 M30...*", parse_mode="Markdown")
    
    m30_data = get_timeframe_data("30min", outputsize=15)
    h1_data = get_timeframe_data("1h", outputsize=2)
    
    if not m30_data or len(m30_data) < 10 or not h1_data:
        bot.edit_message_text("⚠️ Gagal menarik data siri masa daripada Twelve Data.", chat_id=message.chat.id, message_id=wait_msg.message_id)
        return

    # m30_data[1] adalah candle M30 yang BARU SAHAJA TUTUP (Closed)
    c_closed = m30_data[1]
    sma1_current = float(c_closed['close'])
    
    # Cari puncak tertinggi & terendah daripada sejarah terdekat (indeks 2 hingga 10)
    history_candles = m30_data[2:10]
    recent_highest_peak = max([float(c['high']) for c in history_candles])
    recent_lowest_trough = min([float(c['low']) for c in history_candles])
    
    h1_current = h1_data[0]
    h1_close = float(h1_current['close'])
    h1_open = float(h1_current['open'])
    h1_trend = "🟢 BULLISH (H1)" if h1_close >= h1_open else "🔴 BEARISH (H1)"

    # Logik Breakout Puncak M30
    breakout_status = "⚖️ **SIDEWAYS** (Harga berada di pertengahan puncak tertinggi & terendah)"
    if sma1_current > recent_highest_peak:
        breakout_status = "🚀 **VALID BREAKOUT BUY M30!**\n(SMA 1 melepasi puncak tertinggi terdekat)"
    elif sma1_current < recent_lowest_trough:
        breakout_status = "🔻 **VALID BREAKOUT SELL M30!**\n(SMA 1 melepasi puncak terendah terdekat)"

    reply_text = (
        f"📊 *ANALISIS PEAK BREAKOUT M30 & H1*\n\n"
        f"🕒 *Trend H1:* {h1_trend} (`${h1_close:.2f}`)\n\n"
        f"📈 *Analisis M30 (SMA 1 Peak Basis):*\n"
        f"• **SMA 1 Close Semasa:** `${sma1_current:.2f}`\n"
        f"• **Puncak Tertinggi (High):** `${recent_highest_peak:.2f}`\n"
        f"• **Puncak Terendah (Low):** `${recent_lowest_trough:.2f}`\n\n"
        f"🎯 *Status:* {breakout_status}\n\n"
        f"📌 *Masa Candle Tutup:* `{c_closed['datetime']}`"
    )
    
    bot.edit_message_text(reply_text, chat_id=message.chat.id, message_id=wait_msg.message_id, parse_mode="Markdown")

@bot.message_handler(commands=['status'])
def send_status(message):
    bot.reply_to(message, "🟢 Bot Peak Breakout Scanner aktif di Railway!", parse_mode="Markdown")

def background_breakout_scanner():
    global last_m30_time
    print("🚀 Background Peak Breakout Scanner M30 bermula...", flush=True)
    
    while True:
        try:
            m30_data = get_timeframe_data("30min", outputsize=15)
            if m30_data and len(m30_data) >= 10:
                c_closed = m30_data[1]
                candle_time = c_closed['datetime']
                
                # Semak hanya apabila satu-satu candle M30 bertukar masa tutupnya
                if candle_time != last_m30_time:
                    sma1_val = float(c_closed['close'])
                    history_candles = m30_data[2:10]
                    r_high = max([float(c['high']) for c in history_candles])
                    r_low = min([float(c['low']) for c in history_candles])
                    
                    alert_msg = None
                    if sma1_val > r_high:
                        alert_msg = (
                            f"🚨 *M30 PEAK BREAKOUT BUY ALERT!* 🚀\n\n"
                            f"💱 **Simbol:** `{SYMBOL}`\n"
                            f"🟡 **SMA 1 Close:** `${sma1_val:.2f}`\n"
                            f"📈 Sah melepasi Puncak Tertinggi (`${r_high:.2f}`)\n"
                            f"🕒 Masa Tutup: `{candle_time}`"
                        )
                    elif sma1_val < r_low:
                        alert_msg = (
                            f"🚨 *M30 PEAK BREAKOUT SELL ALERT!* 🔻\n\n"
                            f"💱 **Simbol:** `{SYMBOL}`\n"
                            f"🟡 **SMA 1 Close:** `${sma1_val:.2f}`\n"
                            f"📉 Sah melepasi Puncak Terendah (`${r_low:.2f}`)\n"
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

























