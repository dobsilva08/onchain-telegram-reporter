import json
import os
from datetime import datetime
import requests

# =========================
# CONFIG
# =========================
METRICS_FILE = "metrics.json"
HISTORY_FILE = "history.json"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# =========================
# TELEGRAM
# =========================
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    requests.post(url, json=payload, timeout=20)

# =========================
# NORMALIZAÇÃO CRÍTICA (PATCH 6.5.1)
# =========================
def normalize(value):
    """
    Aceita:
    - None
    - número
    - {"value": número}
    """
    if value is None:
        return None
    if isinstance(value, dict):
        return value.get("value")
    return value

# =========================
# LOAD METRICS
# =========================
def load_metrics():
    if not os.path.exists(METRICS_FILE):
        return {}

    with open(METRICS_FILE, "r") as f:
        return json.load(f)

# =========================
# LOAD / SAVE HISTORY
# =========================
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)

def save_history(score, recommendation):
    data = {
        "last_score": score,
        "last_recommendation": recommendation,
        "last_date": datetime.utcnow().isoformat()
    }
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

# =========================
# SCORE ENGINE (DETERMINÍSTICO)
# =========================
def compute_score(values):
    score = 50

    if values["exchange_inflow"] is not None and values["exchange_inflow"] < 0:
        score += 15

    if values["exchange_netflow"] is not None and values["exchange_netflow"] < 0:
        score += 15

    if values["exchange_reserve"] is not None:
        score += 10

    if values["whale_ratio"] is not None and values["whale_ratio"] < 0.6:
        score += 10

    return max(0, min(100, score))

def classify(score):
    if score >= 85:
        return "Altista (Forte)", "Acumular"
    elif score >= 65:
        return "Altista (Moderada)", "Acumular"
    elif score >= 45:
        return "Neutro", "Manter"
    else:
        return "Baixista", "Reduzir"

# =========================
# MAIN
# =========================
def main():
    metrics = load_metrics()

    # -------- NORMALIZAÇÃO --------
    exchange_inflow = normalize(metrics.get("exchange_inflow_ma7"))
    exchange_netflow = normalize(metrics.get("exchange_netflow"))
    exchange_reserve = normalize(metrics.get("exchange_reserve"))
    whale_deposits = normalize(metrics.get("whale_inflow_24h"))
    whale_ratio = normalize(metrics.get("whale_ratio"))

    values = {
        "exchange_inflow": exchange_inflow,
        "exchange_netflow": exchange_netflow,
        "exchange_reserve": exchange_reserve,
        "whale_deposits": whale_deposits,
        "whale_ratio": whale_ratio
    }

    # -------- SCORE --------
    score = compute_score(values)
    bias, recommendation = classify(score)

    save_history(score, recommendation)

    today = datetime.now().strftime("%d/%m/%Y")

    # -------- MESSAGE --------
    msg = f"""
📊 <b>Dados On-Chain BTC — {today} — Diário</b>

<b>1️⃣ Exchange Inflow (MA7)</b>
{exchange_inflow if exchange_inflow is not None else "N/A"}

<b>2️⃣ Exchange Netflow</b>
{exchange_netflow if exchange_netflow is not None else "N/A"}

<b>3️⃣ Reservas em Exchanges</b>
{exchange_reserve if exchange_reserve is not None else "N/A"}

<b>4️⃣ Fluxos de Baleias</b>
Depósitos: {whale_deposits if whale_deposits is not None else "N/A"}
Whale Ratio: {whale_ratio if whale_ratio is not None else "N/A"}

📌 <b>Interpretação Executiva</b>
• Score On-Chain: {score}/100
• Viés de Mercado: {bias}
• Recomendação: {recommendation}
"""

    send_telegram_message(msg.strip())

if __name__ == "__main__":
    main()
