import json
import os
from datetime import datetime, timezone, timedelta
import requests

from text_engine import (
    interpret_exchange_inflow,
    interpret_exchange_netflow,
    interpret_exchange_reserve,
    interpret_whale_inflow,
    interpret_whale_ratio,
    compute_score,
    aggregate_bias,
    classify_position,
)

# ==========================
# CONFIG
# ==========================

METRICS_FILE = "metrics.json"
HISTORY_METRICS_FILE = "history_metrics.json"
HISTORY_STATE_FILE = "history.json"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BRT = timezone(timedelta(hours=-3))


# ==========================
# HELPERS
# ==========================

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    r = requests.post(url, json=payload, timeout=20)
    r.raise_for_status()


def percent_vs_avg(current, avg):
    if avg == 0:
        return None
    return ((current - avg) / avg) * 100


# ==========================
# MAIN
# ==========================

def main():
    metrics = load_json(METRICS_FILE, {})
    history_metrics = load_json(HISTORY_METRICS_FILE, [])
    history_state = load_json(HISTORY_STATE_FILE, {})

    # --------------------------
    # MÉTRICAS ATUAIS (CHAVES CORRETAS)
    # --------------------------
    exchange_inflow = metrics.get("exchange_inflow", 0)
    exchange_netflow = metrics.get("exchange_netflow", 0)
    exchange_reserve = metrics.get("exchange_reserve", 0)
    whale_inflow_24h = metrics.get("whale_inflow_24h", 0)
    whale_ratio = metrics.get("whale_ratio", 0)

    # --------------------------
    # HISTÓRICO (para percentuais)
    # --------------------------
    avg_inflow = history_metrics[-7:].count if False else (
        sum(m.get("exchange_inflow", 0) for m in history_metrics[-7:]) / len(history_metrics[-7:])
        if len(history_metrics) >= 7 else 0
    )

    avg_netflow = (
        sum(m.get("exchange_netflow", 0) for m in history_metrics[-7:]) / len(history_metrics[-7:])
        if len(history_metrics) >= 7 else 0
    )

    avg_reserve = (
        sum(m.get("exchange_reserve", 0) for m in history_metrics[-30:]) / len(history_metrics[-30:])
        if len(history_metrics) >= 30 else 0
    )

    avg_whale = (
        sum(m.get("whale_inflow_24h", 0) for m in history_metrics[-7:]) / len(history_metrics[-7:])
        if len(history_metrics) >= 7 else 0
    )

    # --------------------------
    # INTERPRETAÇÕES
    # --------------------------
    t1, b1, s1 = interpret_exchange_inflow(
        exchange_inflow, avg_inflow, percentil=50
    )
    t2, b2, s2 = interpret_exchange_netflow(exchange_netflow)
    t3, b3, s3 = interpret_exchange_reserve(exchange_reserve, avg_reserve)
    t4, b4, s4 = interpret_whale_inflow(whale_inflow_24h, avg_whale)
    t5, b5, s5 = interpret_whale_ratio(whale_ratio)

    scores = [s1, s2, s3, s4, s5]
    score = compute_score(scores)
    bias, strength = aggregate_bias(scores)
    recommendation = classify_position(score)

    # --------------------------
    # MENSAGEM
    # --------------------------
    today = datetime.now(BRT).strftime("%d/%m/%Y")

    def pct_line(current, avg):
        pct = percent_vs_avg(current, avg)
        if pct is None:
            return "Sem base histórica suficiente para comparação percentual."
        return f"Variação de {pct:+.1f}% em relação à média histórica."

    msg = f"""📊 <b>Dados On-Chain BTC — {today} — Diário</b>

<b>1️⃣ Exchange Inflow (MA7)</b>
{t1}
{pct_line(exchange_inflow, avg_inflow)}

<b>2️⃣ Exchange Netflow</b>
{t2}
{pct_line(exchange_netflow, avg_netflow)}

<b>3️⃣ Reservas em Exchanges</b>
{t3}
{pct_line(exchange_reserve, avg_reserve)}

<b>4️⃣ Fluxos de Baleias</b>
{t4}
{pct_line(whale_inflow_24h, avg_whale)}
Whale Ratio: {whale_ratio:.2f}

📌 <b>Interpretação Executiva</b>
• Score On-Chain: {score}/100  
• Viés de Mercado: {bias} ({strength})  
• Recomendação: <b>{recommendation}</b>
"""

    send_telegram(msg)

    # --------------------------
    # SALVA HISTÓRICO
    # --------------------------
    history_metrics.append({
        "date": datetime.utcnow().isoformat(),
        "exchange_inflow": exchange_inflow,
        "exchange_netflow": exchange_netflow,
        "exchange_reserve": exchange_reserve,
        "whale_inflow_24h": whale_inflow_24h,
        "whale_ratio": whale_ratio,
    })

    save_json(HISTORY_METRICS_FILE, history_metrics)

    save_json(HISTORY_STATE_FILE, {
        "last_score": score,
        "last_recommendation": recommendation,
        "last_date": datetime.utcnow().isoformat(),
    })


if __name__ == "__main__":
    main()
