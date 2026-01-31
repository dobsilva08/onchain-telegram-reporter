import os
import json
import requests
from datetime import datetime

from text_engine import (
    inflow_text,
    netflow_text,
    reserve_text,
    whale_text
)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise SystemExit("❌ Telegram env ausente")

with open("metrics.json", "r", encoding="utf-8") as f:
    m = json.load(f)

data = datetime.utcnow().strftime("%d/%m/%Y")

msg = f"""
📊 Dados On-Chain BTC — {data} — Diário

1️⃣ Exchange Inflow (MA7)
{inflow_text(m["exchange_inflow"]["ma7"], m["exchange_inflow"]["percentil"])}

2️⃣ Exchange Netflow
{netflow_text(m["exchange_netflow"]["value"])}

3️⃣ Reservas em Exchanges
{reserve_text(m["exchange_reserve"]["current"], m["exchange_reserve"]["avg_180d"])}

4️⃣ Fluxos de Baleias
{whale_text(
    m["whale_activity"]["inflow_24h"],
    m["whale_activity"]["avg_30d"],
    m["whale_activity"]["whale_ratio"]
)}
"""

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
r = requests.post(url, data={
    "chat_id": CHAT_ID,
    "text": msg
})

if r.status_code != 200:
    raise SystemExit("❌ Falha Telegram")
