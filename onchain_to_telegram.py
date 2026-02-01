import json
import os
import requests
from datetime import datetime
from text_engine import (
    interpret_exchange_inflow,
    interpret_exchange_netflow,
    interpret_exchange_reserve,
    interpret_whale_flows
)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg}
    )


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def avg_last(history, key, days=30):
    values = [d[key] for d in history[-days:] if key in d]
    return sum(values) / len(values) if values else None


def main():
    metrics = load_json("metrics.json", {})
    history_metrics = load_json("history_metrics.json", [])

    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Evita duplicar o mesmo dia
    if not history_metrics or history_metrics[-1]["date"] != today:
        history_metrics.append({
            "date": today,
            "exchange_inflow": metrics["exchange_inflow_ma7"],
            "exchange_netflow": metrics["exchange_netflow"],
            "exchange_reserve": metrics["exchange_reserve"],
            "whale_inflow": metrics["whale_inflow_24h"],
            "whale_ratio": metrics["whale_ratio"]
        })
        save_json("history_metrics.json", history_metrics)

    avg_inflow = avg_last(history_metrics, "exchange_inflow")
    avg_netflow = avg_last(history_metrics, "exchange_netflow")
    avg_reserve = avg_last(history_metrics, "exchange_reserve")
    avg_whale = avg_last(history_metrics, "whale_inflow")

    t1, s1 = interpret_exchange_inflow(metrics["exchange_inflow_ma7"], avg_inflow)
    t2, s2 = interpret_exchange_netflow(metrics["exchange_netflow"], avg_netflow)
    t3, s3 = interpret_exchange_reserve(metrics["exchange_reserve"], avg_reserve)
    t4, s4 = interpret_whale_flows(
        metrics["whale_inflow_24h"],
        avg_whale,
        metrics["whale_ratio"]
    )

    score = 50 + (s1 + s2 + s3 + s4) * 10
    score = max(0, min(100, score))

    viés = "Altista" if score >= 60 else "Neutro" if score >= 40 else "Baixista"
    recomendacao = "Acumular" if score >= 70 else "Manter" if score >= 50 else "Reduzir"

    msg = f"""📊 Dados On-Chain BTC — {today} — Diário

1️⃣ Exchange Inflow (MA7)
{t1}

2️⃣ Exchange Netflow
{t2}

3️⃣ Reservas em Exchanges
{t3}

4️⃣ Fluxos de Baleias
{t4}

📌 Interpretação Executiva
• Score On-Chain: {score}/100
• Viés de Mercado: {viés}
• Recomendação: {recomendacao}
"""

    send(msg)


if __name__ == "__main__":
    main()
