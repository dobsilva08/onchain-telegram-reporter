# ==========================================================
# onchain_to_telegram.py
# Relatório On-Chain BTC — Fase 6.4 compatível com engine atual
# Determinístico | Sem IA | Estável | GitHub Actions
# ==========================================================

import json
import os
import requests
from datetime import datetime, timezone, timedelta

from text_engine import (
    interpret_exchange_inflow,
    interpret_exchange_netflow,
    interpret_exchange_reserve,
    interpret_whale_flows,
    compute_weighted_score,
    classify_regime,
    decide_recommendation
)

# ==========================================================
# CONFIGURAÇÕES
# ==========================================================

METRICS_FILE = "metrics.json"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BRT = timezone(timedelta(hours=-3))

# ==========================================================
# TELEGRAM
# ==========================================================

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    r = requests.post(url, data=payload, timeout=30)
    r.raise_for_status()

# ==========================================================
# LOAD MÉTRICAS
# ==========================================================

def load_metrics():
    with open(METRICS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ==========================================================
# MAIN
# ==========================================================

def main():
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        raise RuntimeError("TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID ausentes.")

    metrics = load_metrics()
    report_date = datetime.now(BRT).strftime("%d/%m/%Y")

    signals = {}

    # =============================
    # 1) Exchange Inflow
    # =============================
    inflow = metrics["exchange_inflow"]
    txt1, s1 = interpret_exchange_inflow(
        inflow["ma7"],
        inflow["avg_90d"],
        inflow["percentil"]
    )
    signals["exchange_inflow"] = s1

    # =============================
    # 2) Exchange Netflow
    # =============================
    netflow = metrics["exchange_netflow"]
    txt2, s2 = interpret_exchange_netflow(
        netflow["value"],
        netflow["avg_30d"]
    )
    signals["exchange_netflow"] = s2

    # =============================
    # 3) Exchange Reserves
    # =============================
    reserves = metrics["exchange_reserve"]
    txt3, s3 = interpret_exchange_reserve(
        reserves["current"],
        reserves["avg_180d"]
    )
    signals["exchange_reserve"] = s3

    # =============================
    # 4) Whale Flows + Ratio
    # =============================
    whale = metrics["whale_inflow"]
    ratio = metrics["whale_ratio"]

    txt4, s4 = interpret_whale_flows(
        whale["value_24h"],
        whale["avg_30d"],
        ratio["value"]
    )
    signals["whale_flows"] = s4

    # =============================
    # SCORE / REGIME / RECOMENDAÇÃO
    # =============================
    score = compute_weighted_score(signals)
    regime = classify_regime(score)
    recommendation = decide_recommendation(regime)

    # =============================
    # RELATÓRIO
    # =============================
    message = f"""📊 <b>Dados On-Chain BTC — {report_date} — Diário</b>

<b>1️⃣ Exchange Inflow (MA7)</b>
{txt1}

<b>2️⃣ Exchange Netflow</b>
{txt2}

<b>3️⃣ Reservas em Exchanges</b>
{txt3}

<b>4️⃣ Fluxos de Baleias</b>
{txt4}

📌 <b>Interpretação Executiva</b>
• Score On-Chain: <b>{score}/100</b>
• Regime de Mercado: <b>{regime}</b>
• Recomendação: <b>{recommendation}</b>
"""

    send_telegram_message(message)

# ==========================================================
# ENTRYPOINT
# ==========================================================

if __name__ == "__main__":
    main()

