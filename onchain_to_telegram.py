# onchain_to_telegram.py
# Gera relatório on-chain BTC e alerta de mudança de regime
# 100% determinístico | Sem IA | Compatível com GitHub Actions

import json
import os
import requests
from datetime import datetime, timezone, timedelta

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

from alerts_engine import detect_regime_change

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
        raise RuntimeError("Variáveis TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID ausentes.")

    metrics = load_metrics()

    report_date = datetime.now(BRT).strftime("%d/%m/%Y")

    # =============================
    # 1) EXCHANGE INFLOW
    # =============================
    inflow = metrics["exchange_inflow"]
    txt1, bias1, s1 = interpret_exchange_inflow(
        inflow["ma7"], inflow["avg_90d"], inflow["percentil"]
    )

    # =============================
    # 2) EXCHANGE NETFLOW
    # =============================
    netflow = metrics["exchange_netflow"]
    txt2, bias2, s2 = interpret_exchange_netflow(netflow["value"])

    # =============================
    # 3) EXCHANGE RESERVES
    # =============================
    reserves = metrics["exchange_reserve"]
    txt3, bias3, s3 = interpret_exchange_reserve(
        reserves["current"], reserves["avg_180d"]
    )

    # =============================
    # 4) WHALES
    # =============================
    whale_flow = metrics["whale_inflow"]
    txt4a, bias4a, s4a = interpret_whale_inflow(
        whale_flow["value_24h"], whale_flow["avg_30d"]
    )

    whale_ratio = metrics["whale_ratio"]
    txt4b, bias4b, s4b = interpret_whale_ratio(whale_ratio["value"])

    # =============================
    # SCORE / VIÉS / RECOMENDAÇÃO
    # =============================
    score = compute_score([s1, s2, s3, s4a, s4b])
    market_bias, strength = aggregate_bias([s1, s2, s3, s4a, s4b])
    recommendation = classify_position(score)

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
{txt4a}
{txt4b}

📌 <b>Interpretação Executiva</b>
• Score On-Chain: <b>{score}/100</b>
• Viés de Mercado: <b>{market_bias} ({strength})</b>
• Recomendação: <b>{recommendation}</b>
"""

    send_telegram_message(message)

    # =============================
    # ALERTA DE MUDANÇA DE REGIME
    # =============================
    current_state = {
        "date": report_date,
        "score": score,
        "market_bias": f"{market_bias} ({strength})",
        "recommendation": recommendation
    }

    alerts = detect_regime_change(current_state)

    if alerts:
        alert_msg = "🚨 <b>ALERTA DE MUDANÇA DE REGIME</b>\n\n"
        alert_msg += "\n".join(f"• {a}" for a in alerts)
        send_telegram_message(alert_msg)


# ==========================================================
# ENTRYPOINT
# ==========================================================

if __name__ == "__main__":
    main()
