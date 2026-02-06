import json
from datetime import datetime
import os
import requests

HISTORY_FILE = "history_metrics.json"
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text})

def load_latest():
    with open(HISTORY_FILE, "r") as f:
        data = json.load(f)
        return data[-1]

def calculate_score(m):
    score = 50
    if m["exchange_netflow"] < 0:
        score += 20
    if m["exchange_inflow"] < 4000:
        score += 15
    if m["whale_ratio"] < 0.6:
        score += 15
    return min(score, 100)

def main():
    m = load_latest()
    score = calculate_score(m)

    text = f"""📊 Dados On-Chain {m["asset"]} — {datetime.utcnow().strftime('%d/%m/%Y')} — Diário

1️⃣ Exchange Inflow (MA7)
{m["exchange_inflow"]} BTC

2️⃣ Exchange Netflow
{m["exchange_netflow"]} BTC

3️⃣ Reservas em Exchanges
{m["exchange_reserves"]} BTC

4️⃣ Fluxos de Baleias
Whale Ratio: {m["whale_ratio"]}

📌 Interpretação Executiva
• Score On-Chain: {score}/100
• Viés de Mercado: {"Altista (Forte)" if score >= 80 else "Altista (Moderada)"}
• Recomendação: Acumular
"""

    send_message(text)

if __name__ == "__main__":
    main()
