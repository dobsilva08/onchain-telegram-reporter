# onchain_to_telegram.py
# ==========================================================
# Gera relatório on-chain BTC e envia para Telegram
# Compatível com FASE 6 — Opção A
# ==========================================================

import json
import os
from datetime import datetime, timezone, timedelta

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

import requests

# ----------------------------------------------------------
# Configurações
# ----------------------------------------------------------

METRICS_FILE = "metrics.json"

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BRT = timezone(timedelta(hours=-3))

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
    if not os.path.exists(METRICS_FILE):
        raise RuntimeError("metrics.json não encontrado")

    with open(METRICS_FILE, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    # ------------------------------------------------------
    # Dados
    # ------------------------------------------------------

    inflow = metrics["exchange_inflow"]
    netflow = metrics["exchange_netflow"]
    reserve = metrics["exchange_reserve"]
    whale_inflow = metrics["whale_inflow"]
    whale_ratio = metrics["whale_ratio"]

    # ------------------------------------------------------
    # Interpretações
    # ------------------------------------------------------

    t1, _, s1 = interpret_exchange_inflow(
        inflow["ma7"],
        inflow["avg_90d"],
        inflow["percentil"]
    )

    t2, _, s2 = interpret_exchange_netflow(
        netflow["value"]
    )

    t3, _, s3 = interpret_exchange_reserve(
        reserve["current"],
        reserve["avg_180d"]
    )

    t4a, _, s4a = interpret_whale_inflow(
        whale_inflow["value_24h"],
        whale_inflow["avg_30d"]
    )

    t4b, _, s4b = interpret_whale_ratio(
        whale_ratio["value"]
    )

    scores = [s1, s2, s3, s4a, s4b]

    score = compute_score(scores)
    bias, strength = aggregate_bias(scores)
    recommendation = classify_position(score)

    # ------------------------------------------------------
    # Mensagem
    # ------------------------------------------------------

    today = datetime.now(BRT).strftime("%d/%m/%Y")

    message = f"""
📊 *Dados On-Chain BTC — {today} — Diário*

*1️⃣ Exchange Inflow (MA7)*
{t1}

*2️⃣ Exchange Netflow*
{t2}

*3️⃣ Reservas em Exchanges*
{t3}

*4️⃣ Fluxos de Baleias*
{t4a}
{t4b}

📌 *Interpretação Executiva*
• Score On-Chain: *{score}/100*
• Viés de Mercado: *{bias} ({strength})*
• Recomendação: *{recommendation}*
"""

    send_telegram(message.strip())

# ----------------------------------------------------------

if __name__ == "__main__":
    main()
