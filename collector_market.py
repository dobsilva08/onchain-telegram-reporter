import requests
import json
from datetime import datetime

ASSET_MAP = {
    "BTC": "bitcoin"
}

def fetch_market(asset="BTC"):
    coin = ASSET_MAP[asset]
    url = f"https://api.coingecko.com/api/v3/coins/{coin}"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()

    return {
        "asset": asset,
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "price": data["market_data"]["current_price"]["usd"],
        "change_24h": data["market_data"]["price_change_percentage_24h"],
        "volume_24h": data["market_data"]["total_volume"]["usd"],
        "market_cap": data["market_data"]["market_cap"]["usd"]
    }

def main():
    snapshot = fetch_market("BTC")
    with open("snapshot_market.json", "w") as f:
        json.dump(snapshot, f, indent=2)

if __name__ == "__main__":
    main()
