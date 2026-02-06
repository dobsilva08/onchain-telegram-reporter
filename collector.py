import requests
import json
from datetime import datetime

HISTORY_FILE = "history_metrics.json"

def fetch_coinmetrics(metric, asset="btc"):
    url = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
    params = {
        "assets": asset,
        "metrics": metric,
        "frequency": "1d",
        "page_size": 1
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()["data"]
    return float(data[0][metric])

def collect_btc_metrics():
    return {
        "date": datetime.utcnow().isoformat(),
        "exchange_inflow": fetch_coinmetrics("ExchangeInflow"),
        "exchange_outflow": fetch_coinmetrics("ExchangeOutflow"),
        "exchange_reserve": fetch_coinmetrics("ExchangeBalance"),
        "whale_ratio": fetch_coinmetrics("ExchangeWhaleRatio")
    }

def save_history(entry):
    try:
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    except FileNotFoundError:
        history = []

    history.append(entry)

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

if __name__ == "__main__":
    data = collect_btc_metrics()
    save_history(data)
    print("✅ On-chain data coletado com sucesso")
