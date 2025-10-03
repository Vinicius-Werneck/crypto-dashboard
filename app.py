from flask import Flask, jsonify, render_template, request
import requests

app = Flask(__name__)

# Lista de moedas suportadas
MAIN_COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
ALTCOINS = ["ADAUSDT", "SOLUSDT", "XRPUSDT"]
SHITCOINS = ["DOGEUSDT", "SHIBUSDT"]

BINANCE_API = "https://api.binance.com/api/v3"

@app.route("/")
def index():
    return render_template("index.html",
                           main_coins=MAIN_COINS,
                           altcoins=ALTCOINS,
                           shitcoins=SHITCOINS)


@app.route("/prices")
def get_prices():
    symbols = request.args.get("symbols", "BTCUSDT,ETHUSDT,BNBUSDT").split(",")
    results = []

    try:
        for sym in symbols:
            # Pega preço atual
            price_url = f"{BINANCE_API}/ticker/24hr?symbol={sym}"
            resp = requests.get(price_url)
            if resp.status_code != 200:
                continue
            data = resp.json()

            results.append({
                "symbol": sym,
                "price": float(data["lastPrice"]),
                "change": float(data["priceChangePercent"]),
                "rsi": None,  # opcional: você pode calcular RSI depois
                "weekly_high": "⚫",
                "weekly_low": "⚫",
                "monthly_high": "⚫",
                "monthly_low": "⚫"
            })
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/chart-data")
def get_chart_data():
    symbol = request.args.get("symbol", "BTCUSDT")
    interval = request.args.get("interval", "1d")  # 1d, 1h, 15m
    limit = int(request.args.get("limit", 30))

    try:
        url = f"{BINANCE_API}/klines?symbol={symbol}&interval={interval}&limit={limit}"
        resp = requests.get(url)
        data = resp.json()

        candles = []
        for c in data:
            candles.append({
                "timestamp": c[0],
                "open": float(c[1]),
                "high": float(c[2]),
                "low": float(c[3]),
                "close": float(c[4]),
                "volume": float(c[5])
            })

        return jsonify(candles)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
