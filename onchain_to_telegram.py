import json
import os
import requests
from datetime import datetime

# =========================
# CONFIG
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HISTORY_FILE = "history.json"
SNAPSHOT_FILE = "snapshot.json"


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
# LOAD DATA
# =========================
def load_snapshot():
    if not os.path.exists(SNAPSHOT_FILE):
        raise FileNotFoundError("snapshot.json não encontrado")
    with open(SNAPSHOT_FILE, "r") as f:
        return json.load(f)


# =========================
# SCORE ENGINE (SIMPLES E DETERMINÍSTICO)
# =========================
def calculate_score(m):
    score = 50  # base neutra

    # Fluxo líquido negativo (saída de exchanges) → bullish
    netflow = m.get("exchange_netflow")
    if isinstance(netflow, (int, float)):
        if netflow < 0:
            score += 20
        else:
            score -= 10

    # Whale ratio
    whale_ratio = m.get("whale_ratio")
    if isinstance(whale_ratio, (int, float)):
        if whale_ratio < 0.6:
            score += 15
        elif whale_ratio > 0.85:
            score -= 15

    # Variação positiva de preço
    price_change = m.get("price_change_24h")
    if isinstance(price_change, (int, float)):
        if price_change > 0:
            score += 15
        elif price_change < 0:
            score -= 15

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
# REPORT BUILDER
# =========================
def build_report(m):
    date_str = datetime.utcnow().strftime("%d/%m/%Y")

    price = m.get("price")
    price_change = m.get("price_change_24h")
    volume = m.get("volume_24h")
    market_cap = m.get("market_cap")

    # Variação visual
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

    text = f"""
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

    return text


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
