import os
import time
import requests
from telebot import TeleBot

# Konfigurasi API
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TWELVE_DATA_API_KEY = os.getenv('TWELVE_DATA_API_KEY')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

bot = TeleBot(TELEGRAM_BOT_TOKEN)
SYMBOL = 'XAU/USD'


def get_candles(interval='30min', outputsize=50):
  url = f'https://api.twelvedata.com/time_series?symbol={SYMBOL}&interval={interval}&outputsize={outputsize}&apikey={TWELVE_DATA_API_KEY}'
  try:
    response = requests.get(url)
    data = response.json()
    if 'values' in data:
      candles = []
      for c in reversed(data['values']):
        candles.append({
            'datetime': c['datetime'],
            'open': float(c['open']),
            'high': float(c['high']),
            'low': float(c['low']),
            'close': float(c['close']),
        })
      return candles
  except Exception as e:
    print(f'Ralat mendapatkan data lilin: {e}')
  return []


def kira_struktur_bucu(candles):
  """Logik mengenalpasti bucu atas (peaks) dan bucu bawah (troughs)

  untuk menentukan struktur Bullish, Bearish, atau Sideways.
  """
  if len(candles) < 10:
    return 'SIDEWAYS', 0.0, 0.0, 0.0

  tutup_terkini = candles[-1]['close']
  peaks = []
  troughs = []

  # Cari bucu swing (high & low tempatan)
  for i in range(2, len(candles) - 2):
    if (
        candles[i]['high'] > candles[i - 1]['high']
        and candles[i]['high'] > candles[i - 2]['high']
        and candles[i]['high'] > candles[i + 1]['high']
        and candles[i]['high'] > candles[i + 2]['high']
    ):
      peaks.append((i, candles[i]['high']))

    if (
        candles[i]['low'] < candles[i - 1]['low']
        and candles[i]['low'] < candles[i - 2]['low']
        and candles[i]['low'] < candles[i + 1]['low']
        and candles[i]['low'] < candles[i + 2]['low']
    ):
      troughs.append((i, candles[i]['low']))

  bucu_tertinggi = max([p[1] for p in peaks]) if peaks else tutup_terkini
  bucu_terendah = min([t[1] for t in troughs]) if troughs else tutup_terkini

  # Semak siri bucu terakhir untuk tentukan arah struktur
  trend = 'SIDEWAYS'
  if len(peaks) >= 2 and len(troughs) >= 2:
    last_peak_lower = peaks[-1][1] < peaks[-2][1]
    last_trough_lower = troughs[-1][1] < troughs[-2][1]

    if last_peak_lower and last_trough_lower:
      trend = 'BEARISH'  # Lower High & Lower Low
    elif not last_peak_lower and not last_trough_lower:
      trend = 'BULLISH'  # Higher High & Higher Low

  return trend, bucu_tertinggi, bucu_terendah, tutup_terkini


@bot.message_handler(commands=['trend', 'start'])
f
def hantar_analisis_trend(message):
  try:
    # Ambil data H1 dan M30
    h1_candles = get_candles(interval='1h', outputsize=50)
    m30_candles = get_candles(interval='30min', outputsize=50)

    if not h1_candles or not m30_candles:
      bot.reply_to(message, '⚠️ Gagal mendapatkan data pasaran daripada Twelve Data.')
      return

    h1_trend, h1_high, h1_low, h1_close = kira_struktur_bucu(h1_candles)
    m30_trend, m30_high, m30_low, m30_close = kira_struktur_bucu(m30_candles)

    # Emoji status trend
    h1_emoji = (
        '🟢'
        if h1_trend == 'BULLISH'
        else ('🔴' if h1_trend == 'BEARISH' else '⚖️')
    )

    # Penilaian status harga semasa dalam julat bucu M30
    if m30_close > (m30_high + m30_low) / 2:
      status_posisi = (
          'Harga berada di separuh atas bucu (cenderung menguji bucu tertinggi)'
      )
    else:
      status_posisi = (
          'Harga berada di separuh bawah bucu (cenderung menguji bucu terendah)'
      )

    teks_mesej = (
        f'📊 **ANALISIS BUCU SWING XAU/USD**\n\n'
        f'⏱️ **Trend H1:** {h1_emoji} **{h1_trend}**\n'
        f'   • Harga Close H1: `${h1_close:.2f}`\n'
        f'   • Bucu Tinggi H1: `${h1_high:.2f}`\n'
        f'   • Bucu Rendah H1: `${h1_low:.2f}`\n\n'
        f'📈 **Analisis M30:**\n'
        f'   • Close Semasa: `${m30_close:.2f}`\n'
        f'   • Bucu Tertinggi M30: `${m30_high:.2f}`\n'
        f'   • Bucu Terendah M30: `${m30_low:.2f}`\n\n'
        f'🎯 **Status Struktur:** `{status_posisi}`\n\n'
        f'📌 **Kemaskini Sistem Aktif**'
    )

    bot.reply_to(message, teks_mesej, parse_mode='Markdown')

  except Exception as e:
    bot.reply_to(message, f'❌ Ralat memproses analisis: {e}')


if __name__ == '__main__':
  print('Sistem bot dimulakan dengan analisis struktur bucu...')
  bot.infinity_polling()

    

    

























