import os
import json
import requests
from datetime import datetime

from text_engine import (
    interpret_exchange_inflow,
    interpret_exchange_netflow,
    interpret_exchange_reserve,
    interpret_whale_inflow,
    interpret_whale_ratio,
    compute_score,
    aggregate_bias,
    classify_position,
    detect_alerts,
    institutional_block
)

# ==========================================================
# CONFIG TELEGRAM
# ==========================================================

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

print("DEBUG TELEGRAM")
print("BOT TOKEN EXISTS:", bool(BOT_TOKEN))
print("CHAT ID:", CHAT_ID)

if not BOT_TOKEN or not CHAT_ID:
    raise SystemExit("❌ Variáveis de ambiente do Telegram ausentes.")

# ==========================================================
# CARREGA MÉTRICAS
# ==========================================================

with open("metrics.json", "r", encoding="utf-8") as f:
    m = json.load(f)

# ==========================================================
# INTERPRETAÇÕES
# ==========================================================

t1, b1, s1 = interpret_exchange_inflow(
    m["exchange_inflow"]["ma7"],
    m["exchange_inflow"]["avg_90d"],
    m["exchange_inflow"]["percentil"]
)

t2, b2, s2 = interpret_exchange_netflow(m["exchange_netflow"]["value"])

t3, b3, s3 = interpret_exchange_reserve(
    m["exchange_reserve"]["current"],
    m["exchange_reserve"]["avg_180d"]
)

t4, b4, s4 = interpret_whale_inflow(
    m["whale_inflow"]["value_24h"],
    m["whale_inflow"]["avg_30d"]
)

t5, b5, s5 = interpret_whale_ratio(m["whale_ratio"]["value"])

alerts = detect_alerts(
    m["exchange_inflow"]["percentil"],
    m["whale_ratio"]["value"],
    m["whale_inflow"]["value_24h"],
    m["whale_inflow"]["avg_30d"]
)

inst = institutional_block(m["institutional"]["etf_flow"])

score = compute_score([s1, s2, s3, s4, s5])
bias, força = aggregate_bias([s1, s2, s3, s4, s5])
posição = classify_position(score)

# ==========================================================
# MONTA RELATÓRIO
# ==========================================================

data = datetime.utcnow().strftime("%d/%m/%Y")

msg = f"""
📊 *Dados On-Chain BTC — {data} — Diário*

1️⃣ *Exchange Inflow (MA7)*
{t1}

2️⃣ *Exchange Netflow*
{t2}

3️⃣ *Reservas em Exchanges*
{t3}

4️⃣ *Fluxos de Baleias*
• {t4}
• {t5}

5️⃣ *Contexto Institucional*
{inst}

6️⃣ *Interpretação Executiva*
• Viés: {bias} ({força})
• Score: {score}/100
• Recomendação: *{posição}*

"""

if alerts:
    msg += "\n🚨 *Alertas*\n"
    for a in alerts:
        msg += f"• {a}\n"

# ==========================================================
# ENVIO TELEGRAM
# ==========================================================

print("DEBUG: enviando mensagem ao Telegram")

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
r = requests.post(url, data={
    "chat_id": CHAT_ID,
    "text": msg,
    "parse_mode": "Markdown"
})

print("TELEGRAM STATUS:", r.status_code)
print("TELEGRAM RESPONSE:", r.text)

if r.status_code != 200:
    raise SystemExit("❌ Falha ao enviar mensagem ao Telegram")

print("✅ Mensagem enviada com sucesso")
