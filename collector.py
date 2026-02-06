import requests
import json
from datetime import datetime

HISTORY_FILE = "history_metrics.json"
ASSET = "btc"

def fetch_metric(metric):
    url = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
    params = {
        "assets": ASSET,
        "metrics": metric,
        "frequency": "1d",
        "page_size": 2
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()["data"]

def collect_btc_metrics():
    tx_value = fetch_metric("TxTfrValUSD")
    tx_value_adj = fetch_metric("TxTfrValAdjUSD")
    supply = fetch_metric("SplyCur")

    today = float(tx_value[0]["TxTfrValUSD"])
    yesterday = float(tx_value[1]["TxTfrValUSD"])

    netflow_proxy = today - yesterday

    return {
        "date": datetime.utcnow().isoformat(),
        "exchange_inflow_proxy_usd": today,
        "exchange_netflow_proxy_usd": netflow_proxy,
        "circulating_supply": float(supply[0]["SplyCur"]),
        "whale_activity_proxy": float(tx_value_adj[0]["TxTfrValAdjUSD"])
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
    print("✅ Dados on-chain reais coletados com sucesso")
