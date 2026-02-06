import requests
import json
from datetime import datetime

HISTORY_FILE = "history_metrics.json"

def fetch_json(url):
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return r.json()

def collect_btc_metrics():
    # Fontes públicas e gratuitas (Blockchain.com)
    inflow = fetch_json(
        "https://api.blockchain.info/charts/exchange-inflow?timespan=7days&format=json"
    )["values"][-1]["y"]

    netflow = fetch_json(
        "https://api.blockchain.info/charts/exchange-netflow?timespan=1days&format=json"
    )["values"][-1]["y"]

    reserves = fetch_json(
        "https://api.blockchain.info/charts/exchange-reserves?timespan=1days&format=json"
    )["values"][-1]["y"]

    whale_ratio = fetch_json(
        "https://api.blockchain.info/charts/whale-transaction-ratio?timespan=1days&format=json"
    )["values"][-1]["y"]

    return {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "asset": "BTC",
        "exchange_inflow": round(inflow, 2),
        "exchange_netflow": round(netflow, 2),
        "exchange_reserves": round(reserves, 2),
        "whale_ratio": round(whale_ratio, 2)
    }

def load_history():
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_history(entry):
    history = load_history()
    history.append(entry)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

if __name__ == "__main__":
    data = collect_btc_metrics()
    save_history(data)
    print("[collector] Dados coletados e salvos com sucesso")
