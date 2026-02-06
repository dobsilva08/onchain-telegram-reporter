import json
from datetime import datetime

def collect_onchain(asset="BTC"):
    return {
        "asset": asset,
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "exchange_inflow": None,
        "exchange_netflow": None,
        "exchange_reserves": None,
        "whale_flows": None,
        "status": "Dados indisponíveis (fontes públicas gratuitas)"
    }

def main():
    snapshot = collect_onchain("BTC")
    with open("snapshot_onchain.json", "w") as f:
        json.dump(snapshot, f, indent=2)

if __name__ == "__main__":
    main()
