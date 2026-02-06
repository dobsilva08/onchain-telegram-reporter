import json
from datetime import datetime
import os
import requests

HISTORY_FILE = "history.json"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# -----------------------------
# SCORE ON-CHAIN (FASE 6.5)
# Simples, realista e estável
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
# FORMATAÇÃO DE VARIAÇÃO
# -----------------------------

def format_variation(value):
    if value > 0:
        return f"📈 +{value:.2f}%"
    elif value < 0:
        return f"📉 {value:.2f}%"
    else:
        return "➖ 0.00%"

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
    if not os.path.exists(HISTORY_FILE):
        raise FileNotFoundError("history.json não encontrado")

    with open(HISTORY_FILE, "r") as f:
        history = json.load(f)

    if not history:
        raise ValueError("history.json está vazio")

    last = history[-1]
    m = last["metrics"]

    asset = last.get("asset", "N/A")
    date = last.get("date", datetime.utcnow().strftime("%Y-%m-%d"))

    score = score_onchain(m)
    variation_24h = format_variation(m.get("price_change_24h", 0))

    message = f"""
📊 *Dados On-Chain {asset} — {date} — Diário*

💰 *Preço:* ${m.get('price_usd', 0):,}
📉 *Variação 24h:* {variation_24h}
📊 *Volume 24h:* ${m.get('volume_24h', 0):,}
🏦 *Market Cap:* ${m.get('market_cap', 0):,}

📌 *Interpretação Executiva*
• Score On-Chain: {score}/100
• Status: Operacional
"""

    send_telegram(message.strip())

if __name__ == "__main__":
    main()
