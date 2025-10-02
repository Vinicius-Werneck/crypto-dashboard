from flask import Flask, jsonify
import requests
import traceback

app = Flask(__name__)

BINANCE_TICKER_24H = "https://api.binance.com/api/v3/ticker/24hr"


@app.route("/")
def home():
    return "🚀 API Flask rodando no Render!"


@app.route("/binance")
def binance_data():
    try:
        response = requests.get(BINANCE_TICKER_24H, timeout=10)
        response.raise_for_status()  # dispara erro se status != 200
        data = response.json()
        return jsonify(data)
    except Exception as e:
        print("❌ Erro ao buscar dados da Binance:")
        print(f"Tipo: {type(e).__name__}")
        print(f"Mensagem: {e}")
        print("Stacktrace:")
        traceback.print_exc()
        return jsonify({"error": "Falha ao buscar dados da Binance"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
