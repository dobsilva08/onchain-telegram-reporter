import os
import json
import requests
from datetime import datetime

# =========================
# CONFIG TELEGRAM
# =========================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("❌ Variáveis TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID não definidas")

TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"


# =========================
# FUNÇÃO TELEGRAM
# =========================
def send_telegram_message(text: str):
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    response = requests.post(TELEGRAM_URL, json=payload, timeout=15)
    response.raise_for_status()


# =========================
# LOAD DATA
# =========================
def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# =========================
# MAIN
# =========================
def main():
    metrics = load_json("metrics.json")

    exchange_inflow = metrics.get("exchange_inflow_ma7", "N/A")
    exchange_netflow = metrics.get("exchange_netflow", "N/A")
    reserves = metrics.get("exchange_reserves", "N/A")
    whale_flow = metrics.get("whale_inflow_24h", "N/A")
    whale_ratio = metrics.get("whale_ratio", "N/A")

    today = datetime.utcnow().strftime("%d/%m/%Y")

    message = f"""
🔗📊 *Dados On-Chain BTC — {today} — Diário*

1️⃣ *Exchange Inflow (MA7)*
{exchange_inflow}

2️⃣ *Exchange Netflow*
{exchange_netflow}

3️⃣ *Reservas em Exchanges*
{reserves}

4️⃣ *Fluxos de Baleias*
Depósitos: {whale_flow}
Whale Ratio: {whale_ratio}

📌 *Interpretação Executiva*
• Sistema: Determinístico
• Status: Operacional
"""

    send_telegram_message(message.strip())


if __name__ == "__main__":
    main()
