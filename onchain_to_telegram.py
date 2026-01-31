import os
import json
import requests
from text_engine import interpret_exchange_inflow

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise SystemExit("❌ Variáveis Telegram ausentes")

with open("metrics.json", "r", encoding="utf-8") as f:
    m = json.load(f)

texto = interpret_exchange_inflow(
    m["exchange_inflow"]["ma7"],
    m["exchange_inflow"]["percentil"]
)

msg = f"""
📊 TESTE FASE 2 — interpretação on-chain

{texto}
"""

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
r = requests.post(url, data={
    "chat_id": CHAT_ID,
    "text": msg
})

if r.status_code != 200:
    raise SystemExit("❌ Erro ao enviar Telegram")
