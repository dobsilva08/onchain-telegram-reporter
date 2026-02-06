import requests
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send(msg):
    if not TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN não definido nos secrets do GitHub")
    if not CHAT_ID:
        raise RuntimeError("TELEGRAM_CHAT_ID não definido nos secrets do GitHub")

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": msg
    }

    r = requests.post(url, json=payload, timeout=15)
    r.raise_for_status()
