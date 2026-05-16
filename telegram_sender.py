# telegram_sender.py
# Envia mensagens para o Telegram via Bot API
# parse_mode: HTML para suportar <b> e outros tags

import os
import requests

def send(message: str, parse_mode: str = "HTML"):
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token:
                raise RuntimeError("TELEGRAM_BOT_TOKEN nao definido nos secrets do GitHub")
            if not chat_id:
                        raise RuntimeError("TELEGRAM_CHAT_ID nao definido nos secrets do GitHub")

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    # Telegram tem limite de 4096 chars por mensagem
    if len(message) > 4096:
                message = message[:4090] + "\n[...]"

    payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
    }

    response = requests.post(url, json=payload, timeout=30)

    if response.status_code != 200:
                raise RuntimeError(
                                f"Erro ao enviar mensagem Telegram: {response.status_code} - {response.text}"
                )

    return response.json()
