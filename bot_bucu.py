import os
import requests
from telebot import TeleBot

# Ambil pembolehubah persekitaran (Environment Variables)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TWELVE_DATA_API_KEY = os.getenv('TWELVE_DATA_API_KEY')

bot = TeleBot(TELEGRAM_BOT_TOKEN)
SYMBOL = 'XAU/USD'


def get_candles(interval='1h', outputsize=30):
  url = f'https://api.twelvedata.com/time_series?symbol={SYMBOL}&interval={interval}&outputsize={outputsize}&apikey={TWELVE_DATA_API_KEY}'
  try:
    res = requests.get(url).json()
    if 'values' in res:
      return [
          {
              'high': float(c['high']),
              'low': float(c['low']),
              'close': float(c['close']),
          }
          for c in reversed(res['values'])
      ]
  except Exception as e:
    print(f'Ralat API Twelve Data: {e}')
  return []


def kesan_trend_bucu(candles):
  if len(candles) < 6:
    return 'SIDEWAYS', 0, 0, 0

  close_terkini = candles[-1]['close']

  # Cari bucu atas (peaks / swing highs) & bucu bawah (troughs / swing lows)
  peaks = [
      c['high']
      for i, c in enumerate(candles[1:-1], 1)
      if c['high'] > candles[i - 1]['high'] and c['high'] > candles[i + 1]['high']
  ]
  troughs = [
      c['low']
      for i, c in enumerate(candles[1:-1], 1)
      if c['low'] < candles[i - 1]['low'] and c['low'] < candles[i + 1]['low']
  ]

  high_max = max(peaks) if peaks else close_terkini
  low_min = min(troughs) if troughs else close_terkini

  # Semak struktur siri bucu (Lower High & Lower Low = BEARISH | Higher High & Higher Low = BULLISH)
  if len(peaks) >= 2 and len(troughs) >= 2:
    if peaks[-1] < peaks[-2] and troughs[-1] < troughs[-2]:
      return 'BEARISH', high_max, low_min, close_terkini
    elif peaks[-1] > peaks[-2] and troughs[-1] > troughs[-2]:
      return 'BULLISH', high_max, low_min, close_terkini

  return 'SIDEWAYS', high_max, low_min, close_terkini


@bot.message_handler(commands=['trend', 'start'])
def send_trend(message):
  h1_candles = get_candles('1h', 30)
  m30_candles = get_candles('30min', 30)

  if not h1_candles or not m30_candles:
    bot.reply_to(message, '⚠️ Gagal mengambil data harga daripada API.')
    return

  h1_trend, h1_h, h1_l, h1_c = kesan_trend_bucu(h1_candles)
  m30_trend, m30_h, m30_l, m30_c = kesan_trend_bucu(m30_candles)

  h1_icon = '🔴' if h1_trend == 'BEARISH' else ('🟢' if h1_trend == 'BULLISH' else '⚖️')
  m30_icon = '🔴' if m30_trend == 'BEARISH' else ('🟢' if m30_trend == 'BULLISH' else '⚖️')

  msg = (
      f'📊 **ANALISIS STRUKTUR BUCU SEBENAR**\n\n'
      f'⏱️ **Trend H1:** {h1_icon} **{h1_trend}**\n'
      f'   • Close H1: `${h1_c:.2f}`\n'
      f'   • Bucu Tertinggi H1: `${h1_h:.2f}`\n'
      f'   • Bucu Terendah H1: `${h1_l:.2f}`\n\n'
      f'📈 **Analisis M30:**\n'
      f'   • Trend M30: {m30_icon} **{m30_trend}**\n'
      f'   • Close M30: `${m30_c:.2f}`\n'
      f'   • Bucu Tinggi M30: `${m30_h:.2f}`\n'
      f'   • Bucu Rendah M30: `${m30_l:.2f}`\n\n'
      f'🎯 **Status:** Bucu Swing Peak & Trough'
  )
  bot.reply_to(message, msg, parse_mode='Markdown')


if __name__ == '__main__':
  print('Bot Struktur Bucu Aktif...')
  bot.infinity_polling()

