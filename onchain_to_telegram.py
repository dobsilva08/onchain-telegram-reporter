# onchain_to_telegram.py
# ==========================================================
# Relatório On-Chain BTC — FASE 6.2 (Opção C)
# Percentual vs média histórica local
# ==========================================================

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
    classify_position
)

# ----------------------------------------------------------
# Configurações
# ----------------------------------------------------------

METRICS_FILE = "metrics.json"
HISTORY_FILE = "history_metrics.json"

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BRT = timezone(timedelta(hours=-3))

# ----------------------------------------------------------
# Utilidades de histórico
# ----------------------------------------------------------

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {"exchange_netflow": [], "exchange_inflow": [], "whale_inflow": []}
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def update_history(history, key, value, max_len=30):
    history[key].append(value)
    history[key] = history[key][-max_len:]

def avg_last(values, n):
    if len(values) < n:
        return None
    return sum(values[-n:]) / n

def pct_vs_avg(current, avg):
    if avg is None or avg == 0:
        return None
    return (current - avg) / abs(avg) * 100

# ----------------------------------------------------------
# Telegram
# ----------------------------------------------------------

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    r = requests.post(url, json=payload, timeout=15)
    r.raise_for_status()

# ----------------------------------------------------------
# MAIN
# ----------------------------------------------------------

def main():
    with open(METRICS_FILE, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    history = load_history()

    # -----------------------------
    # Dados atuais
    # -----------------------------

    inflow = metrics["exchange_inflow"]["ma7"]
    netflow = metrics["exchange_netflow"]["value"]
    whale_inflow = metrics["whale_inflow"]["value_24h"]

    # -----------------------------
    # Atualiza histórico
    # -----------------------------

    update_history(history, "exchange_inflow", inflow)
    update_history(history, "exchange_netflow", netflow)
    update_history(history, "whale_inflow", whale_inflow)

    save_history(history)

    # -----------------------------
    # Médias (Opção C)
    # -----------------------------

    avg_inflow_14d = avg_last(history["exchange_inflow"], 14)
    avg_netflow_7d = avg_last(history["exchange_netflow"], 7)
    avg_whale_7d = avg_last(history["whale_inflow"], 7)

    pct_inflow = pct_vs_avg(inflow, avg_inflow_14d)
    pct_netflow = pct_vs_avg(netflow, avg_netflow_7d)
    pct_whale = pct_vs_avg(whale_inflow, avg_whale_7d)

    # -----------------------------
    # Interpretações
    # -----------------------------

    t1, _, s1 = interpret_exchange_inflow(
        metrics["exchange_inflow"]["ma7"],
        metrics["exchange_inflow"]["avg_90d"],
        metrics["exchange_inflow"]["percentil"]
    )

    t2, _, s2 = interpret_exchange_netflow(netflow)
    t3, _, s3 = interpret_exchange_reserve(
        metrics["exchange_reserve"]["current"],
        metrics["exchange_reserve"]["avg_180d"]
    )

    t4a, _, s4a = interpret_whale_inflow(
        whale_inflow,
        metrics["whale_inflow"]["avg_30d"]
    )

    t4b, _, s4b = interpret_whale_ratio(
        metrics["whale_ratio"]["value"]
    )

    scores = [s1, s2, s3, s4a, s4b]

    score = compute_score(scores)
    bias, strength = aggregate_bias(scores)
    recommendation = classify_position(score)

    # -----------------------------
    # Texto percentual
    # -----------------------------

    def pct_text(pct, days):
        if pct is None:
            return "Sem base histórica suficiente para comparação percentual."
        direction = "acima" if pct > 0 else "abaixo"
        return f"Isto representa {abs(pct):.0f}% {direction} da média dos últimos {days} dias."

    # -----------------------------
    # Mensagem
    # -----------------------------

    today = datetime.now(BRT).strftime("%d/%m/%Y")

    message = f"""
📊 *Dados On-Chain BTC — {today} — Diário*

*1️⃣ Exchange Inflow (MA7)*
{t1}
_{pct_text(pct_inflow, 14)}_

*2️⃣ Exchange Netflow*
{t2}
_{pct_text(pct_netflow, 7)}_

*3️⃣ Reservas em Exchanges*
{t3}

*4️⃣ Fluxos de Baleias*
{t4a}
_{pct_text(pct_whale, 7)}_
{t4b}

📌 *Interpretação Executiva*
• Score On-Chain: *{score}/100*
• Viés de Mercado: *{bias} ({strength})*
• Recomendação: *{recommendation}*
"""

    send_telegram(message.strip())

if __name__ == "__main__":
    main()
