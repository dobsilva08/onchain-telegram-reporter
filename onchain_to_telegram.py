import json
import os
from datetime import datetime
import requests

# ==========================================================
# CONFIG
# ==========================================================

METRICS_FILE = "metrics.json"
HISTORY_FILE = "history.json"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# ==========================================================
# UTILIDADES
# ==========================================================

def normalize(value):
    """
    Normaliza qualquer entrada para:
    - número
    - ou 'N/A'
    """
    if isinstance(value, dict):
        return value.get("value", "N/A")
    if value is None:
        return "N/A"
    return value


def load_metrics():
    if not os.path.exists(METRICS_FILE):
        return {}
    with open(METRICS_FILE, "r") as f:
        return json.load(f)


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def save_history(data):
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, json=payload, timeout=20)


# ==========================================================
# SCORE (DEFENSIVO)
# ==========================================================

def compute_score(values):
    score = 50  # base neutra

    if values["exchange_inflow"] != "N/A" and values["exchange_inflow"] < values["avg_inflow"]:
        score += 20

    if values["exchange_netflow"] != "N/A" and values["exchange_netflow"] < 0:
        score += 15

    if values["exchange_reserves"] != "N/A" and values["exchange_reserves"] < values["avg_reserves"]:
        score += 15

    if values["whale_ratio"] != "N/A" and values["whale_ratio"] < 0.6:
        score += 10

    return min(score, 100)


def market_bias(score):
    if score >= 85:
        return "Altista (Forte)", "Acumular"
    if score >= 65:
        return "Altista (Moderada)", "Acumular"
    if score >= 50:
        return "Neutro", "Manter"
    return "Baixista", "Reduzir"


# ==========================================================
# MAIN
# ==========================================================

def main():
    metrics = load_metrics()
    history = load_history()

    # -------- Normalização --------
    exchange_inflow = normalize(metrics.get("exchange_inflow_ma7"))
    exchange_netflow = normalize(metrics.get("exchange_netflow"))
    exchange_reserves = normalize(metrics.get("exchange_reserves"))
    whale_inflow = normalize(metrics.get("whale_inflow_24h"))
    whale_ratio = normalize(metrics.get("whale_ratio"))

    avg_inflow = normalize(metrics.get("avg_exchange_inflow_90d"))
    avg_reserves = normalize(metrics.get("avg_exchange_reserves_180d"))

    values = {
        "exchange_inflow": exchange_inflow,
        "exchange_netflow": exchange_netflow,
        "exchange_reserves": exchange_reserves,
        "whale_ratio": whale_ratio,
        "avg_inflow": avg_inflow if avg_inflow != "N/A" else float("inf"),
        "avg_reserves": avg_reserves if avg_reserves != "N/A" else float("inf"),
    }

    # -------- Score --------
    score = compute_score(values)
    bias, recommendation = market_bias(score)

    # -------- Mensagem --------
    today = datetime.now().strftime("%d/%m/%Y")

    msg = f"""
📊 <b>Dados On-Chain BTC — {today} — Diário</b>

<b>1️⃣ Exchange Inflow (MA7)</b>
{exchange_inflow if exchange_inflow != "N/A" else "N/A"}

<b>2️⃣ Exchange Netflow</b>
{exchange_netflow if exchange_netflow != "N/A" else "N/A"}

<b>3️⃣ Reservas em Exchanges</b>
{exchange_reserves if exchange_reserves != "N/A" else "N/A"}

<b>4️⃣ Fluxos de Baleias</b>
Depósitos: {whale_inflow if whale_inflow != "N/A" else "N/A"}
Whale Ratio: {whale_ratio if whale_ratio != "N/A" else "N/A"}

📌 <b>Interpretação Executiva</b>
• Score On-Chain: {score}/100
• Viés de Mercado: {bias}
• Recomendação: {recommendation}
"""

    send_telegram_message(msg)

    # -------- Histórico --------
    history.update({
        "last_score": score,
        "last_recommendation": recommendation,
        "last_date": datetime.utcnow().isoformat()
    })
    save_history(history)


if __name__ == "__main__":
    main()
