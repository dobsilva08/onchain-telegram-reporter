import requests
import json
from datetime import datetime

TIMEOUT = 10

# -----------------------------
# FONTES GRATUITAS (fallback)
# -----------------------------

def fetch_blockchain_chart(chart):
    url = f"https://api.blockchain.info/charts/{chart}?timespan=7days&format=json"
    r = requests.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    return data["values"][-1]["y"]

def fetch_coingecko_price(asset_id):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={asset_id}&vs_currencies=usd"
    r = requests.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()[asset_id]["usd"]

# -----------------------------
# FALLBACK GENÉRICO
# -----------------------------

def fetch_with_fallback(functions):
    for fn in functions:
        try:
            value = fn()
            if value is not None:
                return value
        except Exception as e:
            print(f"[FALLBACK] Fonte falhou: {e}")
    return None

# -----------------------------
# COLETA BTC (fase 6.4 estável)
# -----------------------------

def collect_btc_metrics():
    data = {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "asset": "BTC",
        "metrics": {}
    }

    data["metrics"]["exchange_inflow"] = fetch_with_fallback([
        lambda: fetch_blockchain_chart("exchange-volume")
    ])

    data["metrics"]["exchange_netflow"] = fetch_with_fallback([
        lambda: fetch_blockchain_chart("exchange-netflow")
    ])

    data["metrics"]["exchange_reserves"] = fetch_with_fallback([
        lambda: fetch_blockchain_chart("total-bitcoins")
    ])

    data["metrics"]["whale_ratio"] = fetch_with_fallback([
        lambda: fetch_coingecko_price("bitcoin") / 100000
    ])

    return data

# -----------------------------
# HISTÓRICO
# -----------------------------

def save_history(snapshot):
    try:
        with open("history.json", "r") as f:
            history = json.load(f)
    except:
        history = []

    history.append(snapshot)

    with open("history.json", "w") as f:
        json.dump(history, f, indent=2)

if __name__ == "__main__":
    snapshot = collect_btc_metrics()
    save_history(snapshot)
    print("[OK] Coleta concluída")
