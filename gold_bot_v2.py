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

def get_timeframe_data(interval, outputsize=20):
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={SYMBOL}&interval={interval}&outputsize={outputsize}&apikey={TWELVE_DATA_API_KEY}"
        response = requests.get(url, timeout=10)
        data = response.json()
        if "values" in data:
            return data["values"]
    except Exception as e:
        print(f"Ralat API Timeframe {interval}: {e}", flush=True)
    return None

def find_nearest_peaks(m30_data):
    sma1_list = [float(c['close']) for c in m30_data[1:]]
    
    peak_highest = None
    peak_lowest = None

    for i in range(1, len(sma1_list) - 1):
        if sma1_list[i] > sma1_list[i-1] and sma1_list[i] > sma1_list[i+1]:
            peak_highest = sma1_list[i]
            break

    for i in range(1, len(sma1_list) - 1):
        if sma1_list[i] < sma1_list[i-1] and sma1_list[i] < sma1_list[i+1]:
            peak_lowest = sma1_list[i]
            break

    if peak_highest is None:
        peak_highest = max(sma1_list[:5])
    if peak_lowest is None:
        peak_lowest = min(sma1_list[:5])

    return peak_highest, peak_lowest

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    msg = (
        "🤖 *Syezz XAU/USD SMA 1 Peak Scanner Active!*\n\n"
        "Arahan sedia ada:\n"
        "• `/start` - Paparkan menu utama\n"
        "• `/trend` - Semak analisis bucu SMA 1 M30 terdekat & trend H1\n"
        "• `/status` - Semak status pelayan"
    )
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['trend'])
def send_trend(message):
    wait_msg = bot.reply_to(message, "📊 *Sedang mengesan bucu SMA 1 M30 terdekat & trend H1...*", parse_mode="Markdown")
    
    m30_data = get_timeframe_data("30min", outputsize=20)
    h1_data = get_timeframe_data("1h", outputsize=5)
    
    if not m30_data or len(m30_data) < 15 or not h1_data or len(h1_data) < 3:
        bot.edit_message_text("⚠️ Gagal menarik data siri masa daripada Twelve Data.", chat_id=message.chat.id, message_id=wait_msg.message_id)
        return

    # 1. TREND H1
    h1_sma1_closed = float(h1_data[1]['close'])
    h1_sma1_prev = float(h1_data[2]['close'])
    
    if h1_sma1_closed > h1_sma1_prev:
        h1_trend = "🟢 BULLISH (H1)"
    elif h1_sma1_closed < h1_sma1_prev:
        h1_trend = "🔴 BEARISH (H1)"
    else:
        h1_trend = "⚖️ SIDEWAYS (H1)"

    # 2. ANALISIS BUCU M30 TERDEKAT
    c_closed = m30_data[1]
    sma1_m30_current = float(c_closed['close'])
    
    peak_highest, peak_lowest = find_nearest_peaks(m30_data)

    # 3. LOGIK BREAKOUT
    if sma1_m30_current > peak_highest:
        breakout_status = "🚀 **VALID BREAKOUT BUY M30!**\n(SMA 1 Close melepasi bucu tertinggi terdekat)"
    elif sma1_m30_current < peak_lowest:
        breakout_status = "🔻 **VALID BREAKOUT SELL M30!**\n(SMA 1 Close melepasi bucu terendah terdekat)"
    else:
        breakout_status = "⚖️ **SIDEWAYS / ZON KONSOLIDASI**\n(Harga berada di antara bucu terdekat)"

    reply_text = (
        f"📊 *ANALISIS BUCU SMA 1 M30 & H1*\n\n"
        f"🕒 *Trend H1 (SMA 1 Closed):* {h1_trend} (`${h1_sma1_closed:.2f}`)\n\n"
        f"📈 *Analisis M30 (Bucu Swing Terdekat):*\n"
        f"• **SMA 1 Close Semasa:** `${sma1_m30_current:.2f}`\n"
        f"• **Bucu High Terdekat:** `${peak_highest:.2f}`\n"
        f"• **Bucu Low Terdekat:** `${peak_lowest:.2f}`\n\n"
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
            m30_data = get_timeframe_data("30min", outputsize=20)
            if m30_data and len(m30_data) >= 15:
                c_closed = m30_data[1]
                candle_time = c_closed['datetime']
                
                if candle_time != last_m30_time:
                    sma1_val = float(c_closed['close'])
                    p_high, p_low = find_nearest_peaks(m30_data)
                    
                    alert_msg = None
                    if sma1_val > p_high:
                        alert_msg = (
                            f"🚨 *M30 SMA 1 PEAK BREAKOUT BUY!* 🚀\n\n"
                            f"💱 **Simbol:** `{SYMBOL}`\n"
                            f"🟡 **SMA 1 Close:** `${sma1_val:.2f}`\n"
                            f"📈 Sah melepasi Bucu High Terdekat (`${p_high:.2f}`)\n"
                            f"🕒 Masa Tutup: `{candle_time}`"
                        )
                    elif sma1_val < p_low:
                        alert_msg = (
                            f"🚨 *M30 SMA 1 PEAK BREAKOUT SELL!* 🔻\n\n"
                            f"💱 **Simbol:** `{SYMBOL}`\n"
                            f"🟡 **SMA 1 Close:** `${sma1_val:.2f}`\n"
                            f"📉 Sah melepasi Bucu Low Terdekat (`${p_low:.2f}`)\n"
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
























