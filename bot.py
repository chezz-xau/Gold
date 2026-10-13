
import time
from datetime import datetime
import requests

# ==================== KONFIGURASI TELEGRAM ====================
TELEGRAM_BOT_TOKEN = "8825296896:AAEvBExEDqiwUKW3kTGYJa2Ao1OhDjBpwHQ"  #[span_4](start_span)[span_4](end_span)
TELEGRAM_CHAT_ID = "8353544393"  #[span_5](start_span)[span_5](end_span)

# ==================== KONFIGURASI TWELVE DATA API ====================
TWELVE_DATA_API_KEY = "9e806a60369a422c8e51994dfe6af"  #[span_6](start_span)[span_6](end_span)
SYMBOL = "XAU/USD"
INTERVAL = "15min"  # Timeframe (cth: 1min, 5min, 15min, 1h)
LOOKBACK_CANDLES = 20


def send_telegram_message(message):
  """Fungsi untuk menghantar mesej amaran ke Telegram"""
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {
      "chat_id": TELEGRAM_CHAT_ID,
      "text": message,
      "parse_mode": "Markdown",
  }
  try:
    response = requests.post(url, json=payload)
    return response.json()
  except Exception as e:
    print(f"Ralat hantar Telegram: {e}")


def check_breakout():
  # Ambil data siri masa (time series) daripada Twelve Data API
  url = f"https://api.twelvedata.com/time_series?symbol={SYMBOL}&interval={INTERVAL}&outputsize={LOOKBACK_CANDLES + 5}&apikey={TWELVE_DATA_API_KEY}"

  try:
    response = requests.get(url)
    data = response.json()

    if "values" not in data:
      print(f"Ralat API: {data.get('message', 'Gagal ambil data')}")
      return

    candles = data["values"]
    # Susun semula dari lama ke baharu
    candles.reverse()

    # Ambil harga high dan low (kecuali candle semasa yang sedang berjalan)
    highs = [float(c["high"]) for c in candles[:-1]]
    lows = [float(c["low"]) for c in candles[:-1]]

    resistance_level = max(highs)
    support_level = min(lows)

    # Harga penutupan candle terkini
    close_price = float(candles[-1]["close"])

    print(
        f"[{datetime.now().strftime('%H:%M:%S')}] XAUUSD | Harga Semasa:"
        f" {close_price} | Resistance: {resistance_level} | Support:"
        f" {support_level}"
    )

    # Syarat Breakout Buy
    if close_price > resistance_level:
      msg = (
          f"🚨 *XAUUSD BREAKOUT BUY ALERT!* 🚨\n\n"
          f"📈 *Harga Semasa:* `{close_price}`\n"
          f"🟢 *Breakout Resistance:* `{resistance_level}`\n"
          f"⏰ *Masa:* `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n\n"
          f"💡 Sila semak carta anda sekarang!"
      )
      send_telegram_message(msg)
      time.sleep(300)  # Rehat 5 minit

    # Syarat Breakout Sell
    elif close_price < support_level:
      msg = (
          f"🚨 *XAUUSD BREAKOUT SELL ALERT!* 🚨\n\n"
          f"📉 *Harga Semasa:* `{close_price}`\n"
          f"🔴 *Breakout Support:* `{support_level}`\n"
          f"⏰ *Masa:* `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n\n"
          f"💡 Sila semak carta anda sekarang!"
      )
      send_telegram_message(msg)
      time.sleep(300)

  except Exception as e:
    print(f"Ralat semasa semak breakout: {e}")


# ==================== PELAKSANAAN UTAMA ====================
if __name__ == "__main__":
  print("Bot Telegram XAUUSD Breakout (Cloud API) bermula...")
  while True:
    try:
      check_breakout()
      time.sleep(60)  # Semak setiap 60 saat
    except KeyboardInterrupt:
      print("Bot dihentikan.")
      break
    except Exception as e:
      print(f"Ralat gelung utama: {e}")
      time.sleep(60)
