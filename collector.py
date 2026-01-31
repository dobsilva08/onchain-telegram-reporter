import json

metrics = {
    "exchange_inflow": {
        "ma7": 2500,
        "avg_90d": 4200,
        "percentil": 25
    },
    "exchange_netflow": {
        "value": -1800
    },
    "exchange_reserve": {
        "current": 1500000,
        "avg_180d": 1650000
    },
    "whale_inflow": {
        "value_24h": 950,
        "avg_30d": 1800
    },
    "whale_ratio": {
        "value": 0.62
    },
    "institutional": {
        "etf_flow": 250000000
    }
}

with open("metrics.json", "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2, ensure_ascii=False)

print("✅ metrics.json gerado")
