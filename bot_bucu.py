def analyze_tf(timeframe):
    if not TWELVE_DATA_API_KEY:
        return "⚠️ API Key Twelve Data tiada."
    
    url = f"https://api.twelvedata.com/time_series?symbol=XAU/USD&interval={timeframe}&outputsize=10&apikey={TWELVE_DATA_API_KEY}"
    try:
        res = requests.get(url).json()
        if "values" not in res:
            return f"⚠️ Gagal dapatkan data {timeframe}."
        
        candles = res["values"] 
        # Index 0 = Candle live (sedang berjalan)
        # Index 1 = Candle terkini yang baru close (SMA 1)
        # Index 2 & 3 = 2 candle sebelum candle terkini (untuk cari bucu)
        
        last_close = float(candles[1]["close"]) # Harga close candle lepas (SMA 1)
        
        # Ambil bucu high & low daripada 2 candle sebelum candle terkini (Index 2 & 3)
        bucu_high = max(float(candles[2]["high"]), float(candles[3]["high"]))
        bucu_low = min(float(candles[2]["low"]), float(candles[3]["low"]))
        
        # Semakan Breakout berdasarkan Close candle
        if last_close > bucu_high:
            status = f"🚀 **BREAKOUT BUY**\n  • Close: ${last_close:.2f}\n  • Bucu High: ${bucu_high:.2f}"
        elif last_close < bucu_low:
            status = f"🔻 **BREAKOUT SELL**\n  • Close: ${last_close:.2f}\n  • Bucu Low: ${bucu_low:.2f}"
        else:
            status = (
                f"↔️ **SIDEWAYS / NO BREAKOUT**\n"
                f"  • Bucu High (2 candle lepas): ${bucu_high:.2f}\n"
                f"  • Bucu Low (2 candle lepas): ${bucu_low:.2f}\n"
                f"  • Close SMA(1): ${last_close:.2f}"
            )
            
        return status
    except Exception as e:
        return f"❌ Ralat analisa {timeframe}: {e}"
