import os
import requests


def send(message: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN não definido nos secrets do GitHub")

    if not chat_id:
        raise RuntimeError("TELEGRAM_CHAT_ID não definido nos secrets do GitHub")

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    response = requests.post(url, json=payload, timeout=30)

    if response.status_code != 200:
        raise RuntimeError(
            f"Erro ao enviar mensagem Telegram: {response.status_code} - {response.text}"
        )
