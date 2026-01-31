import os
import json
import requests

print("=== START SCRIPT ===")

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise SystemExit("❌ ERRO: Variáveis de ambiente do Telegram ausentes")

# Carrega métricas
with open("metrics.json", "r", encoding="utf-8") as f:
    metrics = json.load(f)

msg = f"""
📊 TESTE FASE 1 — métricas carregadas

Exchange Inflow MA7: {metrics['exchange_inflow']['ma7']}
Percentil: {metrics['exchange_inflow']['percentil']}
"""

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
r = requests.post(url, data={
    "chat_id": CHAT_ID,
    "text": msg
})

print("STATUS:", r.status_code)

if r.status_code != 200:
    raise SystemExit("❌ Falha no envio Telegram")

print("=== END SCRIPT ===")
