#!/usr/bin/env python3
import os, sys, argparse, requests

API_BASE = "https://api.telegram.org"

def tg_request(token, method, data=None, files=None):
    url = f"{API_BASE}/bot{token}/{method}"
    r = requests.post(url, data=data, files=files, timeout=30)
    try:
        j = r.json()
    except Exception:
        r.raise_for_status()
        raise
    if not j.get("ok"):
        raise SystemExit(f"Telegram API error: {j}")
    return j["result"]

def send_message(token, chat_id, thread_id, text, parse_mode=None, disable_preview=True):
    data = {"chat_id": chat_id, "text": text}
    if thread_id:
        data["message_thread_id"] = thread_id
    if parse_mode:
        data["parse_mode"] = parse_mode
    if disable_preview:
        data["disable_web_page_preview"] = True
    return tg_request(token, "sendMessage", data=data)

def send_photo(token, chat_id, thread_id, photo_path, caption=None, parse_mode=None):
    data = {"chat_id": chat_id}
    if thread_id:
        data["message_thread_id"] = thread_id
    if caption:
        data["caption"] = caption
    if parse_mode:
        data["parse_mode"] = parse_mode
    with open(photo_path, "rb") as fp:
        files = {"photo": fp}
        return tg_request(token, "sendPhoto", data=data, files=files)

def main():
    p = argparse.ArgumentParser(description="Send message/photo to a Telegram forum topic")
    p.add_argument("--text", help="Texto a enviar")
    p.add_argument("--file", help="Arquivo de texto cujo conteúdo será enviado")
    p.add_argument("--stdin", action="store_true", help="Ler texto do STDIN")
    p.add_argument("--photo", help="Caminho da imagem para enviar")
    p.add_argument("--caption", help="Legenda para a imagem")
    p.add_argument("--parse-mode", choices=["MarkdownV2","Markdown","HTML"], help="Parse mode do Telegram")
    args = p.parse_args()

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    thread_id = os.environ.get("TELEGRAM_TOPIC_ID")

    if not token or not chat_id:
        raise SystemExit("Faltando TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID.")
    if args.photo and not os.path.exists(args.photo):
        raise SystemExit(f"Imagem não encontrada: {args.photo}")

    text = args.text
    if args.file:
        with open(args.file, "r", encoding="utf-8") as fh:
            text = fh.read()
    if args.stdin:
        text = (text or "") + sys.stdin.read()

    if args.photo:
        send_photo(token, chat_id, thread_id, args.photo, caption=args.caption, parse_mode=args.parse_mode)
    if text:
        send_message(token, chat_id, thread_id, text, parse_mode=args.parse_mode)
    if not args.photo and not text:
        raise SystemExit("Nada para enviar. Use --text, --file/--stdin ou --photo.")

if __name__ == "__main__":
    main()