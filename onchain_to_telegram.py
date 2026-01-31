import os
import json
import requests
from datetime import datetime

from text_engine import (
    inflow_text,
    netflow_text,
    reserve_text,
    whale_text,
    compute_score,
    classify_bias,
    recommendation
)

# ==========================================================
# TELEGRAM
# ==========================================================

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise SystemExit("❌ Telegram env ausente")

# ==========================================================
# LOAD METRICS
# ==========================================================

with open("metrics.json", "r", encoding="utf-8") as f:
    m = json.load(f)

# ==========================================================
# INTERPRETAÇÃO
# ==========================================================

t1, s1 = inflow_text(m["exchange_inflow"]["ma7"], m["exchange_inflow"]["percentil"])
t2, s2 = netflow_text(m["exchange_netflow"]["value"])
t3, s3 = reserve_text(m["exchange_reserve"]["current"], m["exchange_reserve"]["avg_180d"])
t4, s4 = whale_text(
    m["whale_activity"]["inflow_24h"],
    m["whale_activity"]["avg_30d"],
    m["whale_activity"]["whale_ratio"]
)

score = compute_score([s1, s2, s3, s4])
bias = classify_bias(score)
rec = recommendation(score)

# ==========================================================
# HISTÓRICO
# ==========================================================

history_path = "history.json"

if os.path.exists(history_path):
    with open(history_path, "r", encoding="utf-8") as f:
        history = json.load(f)
else:
    history = {
        "last_recommendation": None,
        "last_score": None,
        "last_date": None
    }

alert_msg = None
if history["last_recommendation"] and history["last_recommendation"] != rec:
    alert_msg = (
        "🚨 *ALERTA DE MUDANÇA DE POSIÇÃO*\n\n"
        f"Anterior: *{history['last_recommendation']}*\n"
        f"Atual: *{rec}*\n"
        f"Score atual: {score}/100\n"
        f"Viés: {bias}"
    )

# Atualiza histórico
history["last_recommendation"] = rec
history["last_score"] = score
history["last_date"] = datetime.utcnow().isoformat()

with open(history_path, "w", encoding="utf-8") as f:
    json.dump(history, f, indent=2, ensure_ascii=False)

# ==========================================================
# RELATÓRIO
# ==========================================================

data = datetime.utcnow().strftime("%d/%m/%Y")

report_msg = f"""
📊 Dados On-Chain BTC — {data} — Diário

1️⃣ Exchange Inflow (MA7)
{t1}

2️⃣ Exchange Netflow
{t2}

3️⃣ Reservas em Exchanges
{t3}

4️⃣ Fluxos de Baleias
{t4}

📌 Interpretação Executiva
• Score On-Chain: {score}/100
• Viés de Mercado: {bias}
• Recomendação: {rec}
"""

def send(msg, markdown=False):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": msg,
    }
    if markdown:
        payload["parse_mode"] = "Markdown"

    r = requests.post(url, data=payload)
    if r.status_code != 200:
        raise SystemExit("❌ Erro ao enviar Telegram")

# ALERTA PRIMEIRO (se existir)
if alert_msg:
    send(alert_msg, markdown=True)

# RELATÓRIO DIÁRIO
send(report_msg)
