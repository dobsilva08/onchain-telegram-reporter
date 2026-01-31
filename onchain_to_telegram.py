import os
import requests

print("=== START SCRIPT ===")

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

print("BOT TOKEN EXISTS:", bool(BOT_TOKEN))
print("CHAT ID:", CHAT_ID)

if not BOT_TOKEN or not CHAT_ID:
    raise SystemExit("❌ ERRO: Variáveis de ambiente do Telegram ausentes")

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

payload = {
    "chat_id": CHAT_ID,
    "text": "✅ TESTE FASE 0 — mensagem enviada com sucesso"
}

response = requests.post(url, data=payload)

print("STATUS CODE:", response.status_code)
print("RESPONSE TEXT:", response.text)

if response.status_code != 200:
    raise SystemExit("❌ ERRO: Telegram não aceitou a mensagem")

print("=== END SCRIPT ===")
