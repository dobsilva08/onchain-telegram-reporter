import json
from datetime import datetime

metrics = {
    "generated_at": datetime.utcnow().isoformat(),

    "exchange_inflow": {
        "ma7": 2500,
        "percentil": 25
    },

    "exchange_netflow": {
        "value": -1800
    },

    "exchange_reserve": {
        "current": 1500000,
        "avg_180d": 1650000
    },

    "whale_activity": {
        "inflow_24h": 950,
        "avg_30d": 1800,
        "whale_ratio": 0.62
    }
}

with open("metrics.json", "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2, ensure_ascii=False)

print("✅ metrics.json gerado (FASE 3)")

