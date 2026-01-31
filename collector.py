import json
from datetime import datetime

metrics = {
    "generated_at": datetime.utcnow().isoformat(),
    "exchange_inflow": {
        "ma7": 2500,
        "avg_90d": 4200,
        "percentil": 25
    }
}

with open("metrics.json", "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2, ensure_ascii=False)

print("✅ metrics.json gerado com sucesso")
