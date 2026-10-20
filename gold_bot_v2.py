import os
import time
import threading
import telebot
import requests

# Pembolehubah Persekitaran (Environment Variables)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

SYMBOL = "XAU/USD"
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

last_m30_time = None

def get_timeframe_data(interval, outputsize=15):
    """Mengambil data siri masa daripada Twelve Data API"""
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
        "🤖 *Syezz XAU/USD SMA 1 Peak Scanner Active!*\n\n"
        "Arahan sedia ada:\n"
        "• `/start` - Paparkan menu utama\n"
        "• `/trend` - Semak analisis bucu SMA 1 M30 & trend SMA 1 H1\n"
        "• `/status` - Semak status pelayan"
    )
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['trend'])
def send_trend(message):
    wait_msg = bot.reply_to(message, "📊 *Sedang mengesan bucu SMA 1 M30 & trend H1...*", parse_mode="Markdown")
    
    m30_data = get_timeframe_data("30min", outputsize=15)
    h1_data = get_timeframe_data("1h", outputsize=3)
    
    if not m30_data or len(m30_data) < 12 or not h1_data or len(h1_data) < 2:
        bot.edit_message_text("⚠️ Gagal menarik data siri masa daripada Twelve Data.", chat_id=message.chat.id, message_id=wait_msg.message_id)
        return

    # --- 1. PENENTUAN TREND H1 (Berdasarkan Arah SMA 1 H1) ---
    h1_sma1_current = float(h1_data[0]['close'])
    h1_sma1_prev = float(h1_data[1]['close'])
    
    if h1_sma1_current > h1_sma1_prev:
        h1_trend = "🟢 BULLISH (H1)"
    elif h1_sma1_current < h1_sma1_prev:
        h1_trend = "🔴 BEARISH (H1)"
    else:
        h1_trend = "⚖️ SIDEWAYS (H1)"

    # --- 2. ANALISIS BUCU SMA 1 M30 (CLOSED CANDLE BASIS) ---
    # m30_data[1] = Candle M30 yang BARU SAHAJA TUTUP (Closed)
    c_closed = m30_data[1]
    sma1_m30_current = float(c_closed['close'])
    
    # Ambil sejarah nilai Close (SMA 1) candle M30 terdahulu (indeks 2 hingga 12) untuk cari Bucu
    history_candles = m30_data[2:12]
    sma1_history = [float(c['close']) for c in history_candles]
    
    peak_highest = max(sma1_history)  # Bucu Tertinggi SMA 1 M30
    peak_lowest = min(sma1_history)   # Bucu Terendah SMA 1 M30

    # --- 3. LOGIK BREAKOUT & SIDEWAYS ---
    if sma1_m30_current > peak_highest:
        breakout_status = "🚀 **VALID BREAKOUT BUY M30!**\n(SMA 1 Close melepasi bucu tertinggi)"
    elif sma1_m30_current < peak_lowest:
        breakout_status = "🔻 **VALID BREAKOUT SELL M30!**\n(SMA 1 Close melepasi bucu terendah)"
    else:
        breakout_status = "⚖️ **SIDEWAYS**\n(Harga berada di pertengahan bucu tertinggi & terendah SMA 1)"

    reply_text = (
        f"📊 *ANALISIS BUCU SMA 1 M30 & H1*\n\n"
        f"🕒 *Trend H1 (SMA 1):* {h1_trend} (`${h1_sma1_current:.2f}`)\n\n"
        f"📈 *Analisis M30 (SMA 1 Closed Candle):*\n"
        f"• **SMA 1 Close Semasa:** `${sma1_m30_current:.2f}`\n"
        f"• **Bucu Tertinggi SMA1:** `${peak_highest:.2f}`\n"
        f"• **Bucu Terendah SMA1:** `${peak_lowest:.2f}`\n\n"
        f"🎯 *Status:* {breakout_status}\n\n"
        f"📌 *Masa Candle Tutup:* `{c_closed['datetime']}`"
    )
    
    bot.edit_message_text(reply_text, chat_id=message.chat.id, message_id=wait_msg.message_id, parse_mode="Markdown")

@bot.message_handler(commands=['status'])
def send_status(message):
    bot.reply_to(message, "🟢 Bot SMA 1 Peak Scanner aktif di Railway!", parse_mode="Markdown")

def background_breakout_scanner():
    global last_m30_time
    print("🚀 Background SMA 1 Peak Breakout Scanner M30 bermula...", flush=True)
    
    while True:
        try:
            m30_data = get_timeframe_data("30min", outputsize=15)
            if m30_data and len(m30_data) >= 12:
                c_closed = m30_data[1]
                candle_time = c_closed['datetime']
                
                # Semak hanya apabila candle M30 bertukar masa tutupnya (Candle Baharu)
                if candle_time != last_m30_time:
                    sma1_val = float(c_closed['close'])
                    history_candles = m30_data[2:12]
                    sma1_history = [float(c['close']) for c in history_candles]
                    
                    p_high = max(sma1_history)
                    p_low = min(sma1_history)
                    
                    alert_msg = None
                    if sma1_val > p_high:
                        alert_msg = (
                            f"🚨 *M30 SMA 1 PEAK BREAKOUT BUY!* 🚀\n\n"
                            f"💱 **Simbol:** `{SYMBOL}`\n"
                            f"🟡 **SMA 1 Close:** `${sma1_val:.2f}`\n"
                            f"📈 Sah melepasi Bucu Tertinggi SMA 1 (`${p_high:.2f}`)\n"
                            f"🕒 Masa Tutup: `{candle_time}`"
                        )
                    elif sma1_val < p_low:
                        alert_msg = (
                            f"🚨 *M30 SMA 1 PEAK BREAKOUT SELL!* 🔻\n\n"
                            f"💱 **Simbol:** `{SYMBOL}`\n"
                            f"🟡 **SMA 1 Close:** `${sma1_val:.2f}`\n"
                            f"📉 Sah melepasi Bucu Terendah SMA 1 (`${p_low:.2f}`)\n"
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
    
    # Jalankan scanner di thread berasingan
    t_scanner = threading.Thread(target=background_breakout_scanner, daemon=True)
    t_scanner.start()
    
    # Single-session polling untuk elak ralat 409
    print("🤖 Mulakan Telegram Polling...", flush=True)
    bot.infinity_polling(timeout=20, long_polling_timeout=10)





























