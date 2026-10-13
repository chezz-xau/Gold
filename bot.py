import time
from datetime import datetime
import MetaTrader5 as mt5
import requests

# ==================== KONFIGURASI TELEGRAM ====================
TELEGRAM_BOT_TOKEN = "8825296896:AAEvBExEDqiwUKW3kTGYJa2Ao1OhDjBpwHQ"  #[span_3](start_span)[span_3](end_span)
TELEGRAM_CHAT_ID = "8353544393"  #[span_4](start_span)[span_4](end_span)

# ==================== KONFIGURASI TRADING ====================
SYMBOL = "XAUUSD"
TIMEFRAME = mt5.TIMEFRAME_M15  # Boleh tukar ke mt5.TIMEFRAME_H1 atau M5
LOOKBACK_CANDLES = 20  # Bilangan candle untuk cari Support/Resistance


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
  # Sambung ke terminal MetaTrader 5 (Valetax / Oanda)
  if not mt5.initialize():
    print("Gagal sambung ke MetaTrader 5. Pastikan aplikasi MT5 terbuka.")
    return

  # Ambil data harga sejarah
  rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 1, LOOKBACK_CANDLES + 1)
  if rates is None or len(rates) == 0:
    print("Gagal mengambil data harga XAUUSD.")
    mt5.shutdown()
    return

  # Cari zon High (Resistance) & Low (Support)
  highs = [r["high"] for r in rates[:-1]]
  lows = [r["low"] for r in rates[:-1]]

  resistance_level = max(highs)
  support_level = min(lows)

  # Ambil harga candle semasa (terkini)
  current_candle = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 1)
  if current_candle is None or len(current_candle) == 0:
    mt5.shutdown()
    return

  close_price = current_candle[0]["close"]

  print(
      f"[{datetime.now().strftime('%H:%M:%S')}] XAUUSD | Harga Semasa:"
      f" {close_price} | Resistance: {resistance_level} | Support:"
      f" {support_level}"
  )

  # Amaran Breakout Buy
  if close_price > resistance_level:
    msg = (
        f"🚨 *XAUUSD BREAKOUT BUY ALERT!* 🚨\n\n"
        f"📈 *Harga Semasa:* `{close_price}`\n"
        f"🟢 *Breakout Resistance:* `{resistance_level}`\n"
        f"⏰ *Masa:* `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n\n"
        f"💡 Sila semak carta MT5 anda sekarang!"
    )
    send_telegram_message(msg)
    time.sleep(300)  # Rehat 5 minit untuk elak spam amaran berturut-turut

  # Amaran Breakout Sell
  elif close_price < support_level:
    msg = (
        f"🚨 *XAUUSD BREAKOUT SELL ALERT!* 🚨\n\n"
        f"📉 *Harga Semasa:* `{close_price}`\n"
        f"🔴 *Breakout Support:* `{support_level}`\n"
        f"⏰ *Masa:* `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n\n"
        f"💡 Sila semak carta MT5 anda sekarang!"
    )
    send_telegram_message(msg)
    time.sleep(300)

  mt5.shutdown()


# ==================== PELAKSANAAN UTAMA ====================
if __name__ == "__main__":
  print("Bot Telegram XAUUSD Breakout bermula...")
  if mt5.initialize():
    print(
        f"Berjaya disambungkan ke akaun broker: {mt5.account_info().company}"
    )
    mt5.shutdown()

  while True:
    try:
      check_breakout()
      time.sleep(60)  # Semakan dilakukan setiap 60 saat
    except KeyboardInterrupt:
      print("Bot dihentikan.")
      break
    except Exception as e:
      print(f"Ralat: {e}")
      time.sleep(60)

