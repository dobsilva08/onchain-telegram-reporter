
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Telegram Notifier — envia texto e/ou arquivos (PDF, imagens, etc.) via Bot API.
import os, time, json, argparse, mimetypes, requests

def load_env_if_present():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k and v and k not in os.environ:
                    os.environ[k.strip()] = v.strip()

class TelegramNotifier:
    def __init__(self, token: str, chat_id: str = None, proxy: str = None):
        self.base = f"https://api.telegram.org/bot{token}"
        self.chat_id = chat_id
        self.session = requests.Session()
        if proxy:
            self.session.proxies.update({"http": proxy, "https": proxy})
        self.timeout = (10, 60)

    def _request(self, method: str, path: str, **kwargs):
        url = f"{self.base}/{path.lstrip('/')}"
        r = self.session.request(method, url, timeout=self.timeout, **kwargs)
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text}")
        data = r.json()
        if not data.get("ok", False):
            raise RuntimeError(f"Telegram error: {data}")
        return data

    def get_updates(self, limit: int = 50):
        return self._request("GET", "getUpdates", params={"limit": limit})

    def discover_chat_id(self):
        data = self.get_updates(limit=50)
        chat_id = None
        for update in reversed(data.get("result", [])):
            msg = update.get("message") or update.get("edited_message") or {}
            chat = msg.get("chat") or {}
            if "id" in chat:
                chat_id = str(chat["id"])
                break
        return chat_id, data

    def send_message(self, text: str, parse_mode: str = "HTML", disable_web_page_preview: bool = True):
        if not self.chat_id:
            raise ValueError("chat_id não definido.")
        payload = {"chat_id": self.chat_id, "text": text, "disable_web_page_preview": disable_web_page_preview}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        return self._request("POST", "sendMessage", data=payload)

    def send_document(self, file_path: str, caption: str = None, parse_mode: str = "HTML"):
        if not self.chat_id:
            raise ValueError("chat_id não definido.")
        if not os.path.exists(file_path):
            raise FileNotFoundError(file_path)
        mime = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        files = {"document": (os.path.basename(file_path), open(file_path, "rb"), mime)}
        data = {"chat_id": self.chat_id}
        if caption:
            data["caption"] = caption
        if parse_mode:
            data["parse_mode"] = parse_mode
        return self._request("POST", "sendDocument", files=files, data=data)

def main():
    load_env_if_present()
    p = argparse.ArgumentParser()
    p.add_argument("--token", default=os.environ.get("TELEGRAM_BOT_TOKEN"))
    p.add_argument("--chat-id", default=os.environ.get("TELEGRAM_CHAT_ID"))
    p.add_argument("--proxy", default=os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY"))
    p.add_argument("--text")
    p.add_argument("--file")
    p.add_argument("--caption")
    p.add_argument("--setup", action="store_true")
    a = p.parse_args()

    if not a.token:
        raise SystemExit("Forneça --token ou TELEGRAM_BOT_TOKEN no .env")

    t = TelegramNotifier(a.token, a.chat_id, a.proxy)

    if a.setup:
        chat_id, raw = t.discover_chat_id()
        print(json.dumps(raw, ensure_ascii=False, indent=2))
        if chat_id:
            print("\n[ok] chat_id:", chat_id)
        else:
            print("\n[!] Envie /start para o bot e rode novamente.")
        return

    results = []
    if a.text:
        results.append(t.send_message(a.text))
    if a.file:
        results.append(t.send_document(a.file, a.caption))
    if not results:
        raise SystemExit("Nada para enviar. Use --text e/ou --file, ou --setup.")
    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
