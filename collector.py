import requests
import json
from datetime import datetime

HISTORY_FILE = "history.json"
TIMEOUT = 10

# -----------------------------
# UTIL
# -----------------------------

def safe_get(url):
    r = requests.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

# -----------------------------
# COINGECKO (FREE / ESTÁVEL)
# -----------------------------

def fetch_coingecko_market(asset_id):
    url = (
        "https://api.coingecko.com/api/v3/coins/markets"
        f"?vs_currency=usd&ids={asset_id}"
    )
    data = safe_get(url)
    return data[0] if data else None

# -----------------------------
# COLETA BTC (FASE 6.4)
# -----------------------------

def collect_btc_metrics():
    market = fetch_coingecko_market("bitcoin")

    snapshot = {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "asset": "BTC",
        "metrics": {
            "price_usd": market["current_price"] if market else None,
            "volume_24h": market["total_volume"] if market else None,
            "price_change_24h": market["price_change_percentage_24h"],
            "market_cap": market["market_cap"] if market else None,
        }
    }

    return snapshot

# -----------------------------
# HISTÓRICO (CORRIGIDO)
# -----------------------------

def load_history():
    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                return []  # CORREÇÃO CRÍTICA
    except:
        return []

def save_history(snapshot):
    history = load_history()
    history.append(snapshot)

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

# -----------------------------
# MAIN
# -----------------------------

if __name__ == "__main__":
    snapshot = collect_btc_metrics()
    save_history(snapshot)
    print("[OK] Coleta BTC concluída com sucesso")
