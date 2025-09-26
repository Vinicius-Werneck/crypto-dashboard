from flask import Flask, render_template, jsonify, request
import requests

app = Flask(__name__)

# Categorias de moedas
ALTCOINS = [
    "AAVEUSDT",   # Aave
    "AVAXUSDT",   # Avalanche
    "ADAUSDT",    # Cardano
    "ATOMUSDT",   # Cosmos
    "DOTUSDT",    # Polkadot
    "LINKUSDT",   # Chainlink
    "MATICUSDT",  # Polygon
    "SOLUSDT",    # Solana
    "XRPUSDT",    # XRP
    "LTCUSDT",    # Litecoin
    "BCHUSDT",    # Bitcoin Cash
    "XLMUSDT",    # Stellar
    "TRXUSDT",    # Tron
    "SUIUSDT",    # Sui
    "HBARUSDT",   # Hedera
]

SHITCOINS = [
    "DOGEUSDT",   # Dogecoin
    "SHIBUSDT",   # Shiba Inu
    "PEPEUSDT",   # Pepe
    "FLOKIUSDT",  # Floki
    "BONKUSDT",   # Bonk
    "MEMEUSDT",   # Memecoin
    "WIFUSDT",    # Dogwifhat
]

# Moedas principais (sempre visíveis)
MAIN_COINS = [
    "BTCUSDT",    # Bitcoin
    "ETHUSDT",    # Ethereum
    "BNBUSDT",    # BNB
]

# Todas as moedas combinadas
ALL_SYMBOLS = MAIN_COINS + ALTCOINS + SHITCOINS

BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
BINANCE_TICKER_24H = "https://api.binance.com/api/v3/ticker/24hr"

@app.route("/")
def index():
    return render_template("index.html", 
                         main_coins=MAIN_COINS,
                         altcoins=ALTCOINS, 
                         shitcoins=SHITCOINS)

def calc_rsi_from_closes(closes, period=14):
    """
    Calcula RSI usando o método de Wilder (suavizado).
    Retorna o último valor de RSI.
    """
    if not closes or len(closes) < period + 1:
        return None

    # Diferenças entre candles consecutivos
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]

    # Ganhos e perdas iniciais
    gains = [d if d > 0 else 0 for d in deltas[:period]]
    losses = [-d if d < 0 else 0 for d in deltas[:period]]

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    # Aplica suavização de Wilder a partir do período+1
    for delta in deltas[period:]:
        gain = delta if delta > 0 else 0
        loss = -delta if delta < 0 else 0

        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

    if avg_loss == 0:
        return 100.0  # RSI máximo (sobrecompra total)

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)


def check_proximity_to_extremes(current_price, highs, lows, threshold=0.05):
    """
    Verifica a proximidade com máximas e mínimas
    Retorna um dicionário com:
    - high_status: proximidade da máxima
    - low_status: proximidade da mínima
    Cores: 🟢 (perto), 🟡 (médio), 🔴 (longe), ⚫ (sem dados)
    """
    if not highs or not lows or current_price is None:
        return {"high_status": "⚫", "low_status": "⚫"}
    
    max_high = max(highs)
    min_low = min(lows)
    
    # Proximidade da máxima
    high_distance_percent = ((max_high - current_price) / max_high) * 100 if max_high > 0 else 100
    
    if high_distance_percent <= 5:
        high_status = "🔴"  # PERTO da máxima = VERMELHO (cuidado)
    elif high_distance_percent <= 15:
        high_status = "🟡"  # MÉDIO da máxima = AMARELO
    else:
        high_status = "🟢"  # LONGE da máxima = VERDE (oportunidade)
    
    # Proximidade da mínima
    low_distance_percent = ((current_price - min_low) / min_low) * 100 if min_low > 0 else 100
    
    if low_distance_percent <= 5:
        low_status = "🟢"  # PERTO da mínima = VERDE (oportunidade)
    elif low_distance_percent <= 15:
        low_status = "🟡"  # MÉDIO da mínima = AMARELO
    else:
        low_status = "🔴"  # LONGE da mínima = VERMELHO (cuidado)
    
    return {"high_status": high_status, "low_status": low_status}

@app.route("/prices")
def prices():
    """
    /prices?symbols=BTCUSDT,ETHUSDT
    Retorna preço, change 24h, RSI diário e proximidade das máximas/mínimas
    """
    symbols_param = request.args.get("symbols", "")
    if symbols_param:
        symbols = symbols_param.split(",")
    else:
        symbols = ALL_SYMBOLS
    
    # consulta todos tickers 24h e filtra
    try:
        data = requests.get(BINANCE_TICKER_24H, timeout=10).json()
    except Exception:
        data = []

    result = []
    for d in data:
        try:
            if d.get("symbol") in symbols:
                price = float(d.get("lastPrice", 0))
                change = float(d.get("priceChangePercent", 0))

                # pegar candles diários para calcular RSI
                try:
                    params_daily = {"symbol": d["symbol"], "interval": "1d", "limit": 50}
                    klines_daily = requests.get(BINANCE_KLINES_URL, params=params_daily, timeout=10).json()
                    closes_daily = [float(c[4]) for c in klines_daily] if isinstance(klines_daily, list) else []
                    rsi = calc_rsi_from_closes(closes_daily, period=14)
                except Exception:
                    rsi = None

                # pegar dados semanais para verificar máxima/mínima semanal
                try:
                    params_weekly = {"symbol": d["symbol"], "interval": "1w", "limit": 10}
                    klines_weekly = requests.get(BINANCE_KLINES_URL, params=params_weekly, timeout=10).json()
                    highs_weekly = [float(c[2]) for c in klines_weekly] if isinstance(klines_weekly, list) else []
                    lows_weekly = [float(c[3]) for c in klines_weekly] if isinstance(klines_weekly, list) else []
                    weekly_proximity = check_proximity_to_extremes(price, highs_weekly, lows_weekly)
                except Exception:
                    weekly_proximity = {"high_status": "⚫", "low_status": "⚫"}

                # pegar dados mensais para verificar máxima/mínima mensal
                try:
                    params_monthly = {"symbol": d["symbol"], "interval": "1M", "limit": 6}
                    klines_monthly = requests.get(BINANCE_KLINES_URL, params=params_monthly, timeout=10).json()
                    highs_monthly = [float(c[2]) for c in klines_monthly] if isinstance(klines_monthly, list) else []
                    lows_monthly = [float(c[3]) for c in klines_monthly] if isinstance(klines_monthly, list) else []
                    monthly_proximity = check_proximity_to_extremes(price, highs_monthly, lows_monthly)
                except Exception:
                    monthly_proximity = {"high_status": "⚫", "low_status": "⚫"}

                result.append({
                    "symbol": d["symbol"],
                    "price": round(price, 8),
                    "change": round(change, 4),
                    "rsi": rsi,
                    "weekly_high": weekly_proximity["high_status"],
                    "weekly_low": weekly_proximity["low_status"],
                    "monthly_high": monthly_proximity["high_status"],
                    "monthly_low": monthly_proximity["low_status"]
                })
        except Exception:
            continue

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)