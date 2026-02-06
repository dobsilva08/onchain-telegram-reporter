import json
from datetime import datetime
import os
import requests

HISTORY_FILE = "history.json"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# -----------------------------
# SCORE (FASE 6.4 – SIMPLES E REAL)
# -----------------------------

def score_onchain(m):
    score = 50  # base neutra

    if m.get("price_change_24h", 0) > 0:
        score += 15

    if m.get("volume_24h", 0) > 0:
        score += 15

    if m.get("market_cap", 0) > 0:
        score += 20

    return min(score, 100)

# -----------------------------
# TELEGRAM
# -----------------------------

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload, timeout=10)

# -----------------------------
# MAIN
# -----------------------------

def main():
    with open(HISTORY_FILE, "r") as f:
        history = json.load(f)

    last = history[-1]
    m = last["metrics"]

    score = score_onchain(m)

    date = last["date"]
    asset = last["asset"]

    message = f"""
📊 *Dados On-Chain {asset} — {date} — Diário*

💰 *Preço:* ${m['price_usd']:,}
📉 *Variação 24h:* {m['price_change_24h']:.2f}%
📊 *Volume 24h:* ${m['volume_24h']:,}
🏦 *Market Cap:* ${m['market_cap']:,}

📌 *Interpretação Executiva*
• Score On-Chain: {score}/100
• Status: Operacional
"""

    send_telegram(message)

if __name__ == "__main__":
    main()
