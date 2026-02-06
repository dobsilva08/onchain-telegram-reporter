import json
import os
import requests
from datetime import datetime
import sys

# =========================
# CONFIG
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

DATA_DIR = "data"
SNAPSHOT_FILE = os.path.join(DATA_DIR, "snapshot.json")


# =========================
# TELEGRAM
# =========================
def send_telegram_message(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    r = requests.post(url, json=payload, timeout=30)
    r.raise_for_status()


# =========================
# LOAD SNAPSHOT (SAFE)
# =========================
def load_snapshot():
    if not os.path.exists(SNAPSHOT_FILE):
        print("⚠ snapshot.json não encontrado. Collector pode ter falhado.")
        sys.exit(0)  # sai sem quebrar o workflow

    with open(SNAPSHOT_FILE, "r") as f:
        return json.load(f)


# =========================
# SCORE ENGINE
# =========================
def calculate_score(m):
    score = 50

    netflow = m.get("exchange_netflow")
    if isinstance(netflow, (int, float)):
        score += 20 if netflow < 0 else -10

    whale_ratio = m.get("whale_ratio")
    if isinstance(whale_ratio, (int, float)):
        if whale_ratio < 0.6:
            score += 15
        elif whale_ratio > 0.85:
            score -= 15

    price_change = m.get("price_change_24h")
    if isinstance(price_change, (int, float)):
        score += 15 if price_change > 0 else -15

    return max(0, min(100, score))


def market_bias(score):
    if score >= 80:
        return "Altista (Forte)"
    if score >= 60:
        return "Altista (Moderada)"
    if score >= 40:
        return "Neutra"
    return "Baixista"


def recommendation(score):
    if score >= 70:
        return "Acumular"
    if score >= 50:
        return "Manter"
    return "Reduzir"


# =========================
# REPORT
# =========================
def build_report(m):
    date_str = datetime.utcnow().strftime("%d/%m/%Y")

    price = m.get("price")
    price_change = m.get("price_change_24h")
    volume = m.get("volume_24h")
    market_cap = m.get("market_cap")

    if isinstance(price_change, (int, float)):
        if price_change > 0:
            var_icon = "📈"
            var_sign = "+"
        elif price_change < 0:
            var_icon = "📉"
            var_sign = ""
        else:
            var_icon = "➖"
            var_sign = ""
        var_text = f"{var_icon} *Variação 24h:* {var_sign}{price_change:.2f}%"
    else:
        var_text = "➖ *Variação 24h:* N/A"

    score = calculate_score(m)

    return f"""
📊 *Dados On-Chain BTC — {date_str} — Diário*

💰 *Preço:* ${price:,.0f}
{var_text}
📊 *Volume 24h:* ${volume:,.0f}
🏦 *Market Cap:* ${market_cap:,.0f}

📌 *Interpretação Executiva*
• *Score On-Chain:* {score}/100
• *Viés de Mercado:* {market_bias(score)}
• *Recomendação:* {recommendation(score)}
""".strip()


# =========================
# MAIN
# =========================
def main():
    snapshot = load_snapshot()
    report = build_report(snapshot)
    send_telegram_message(report)
    print("✅ Relatório enviado com sucesso")


if __name__ == "__main__":
    main()
