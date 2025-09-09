#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Gera o relatório “Dados On-Chain — {data} — Diário — Nº {contador}”
# e envia como MENSAGEM no Telegram (sem PDF por padrão).

import os, json, argparse, requests, time, textwrap
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

# --- Fuso BRT (sem horário de verão)
BRT = timezone(timedelta(hours=-3), name="BRT")

def load_env_if_present():
    """Carrega variáveis de um .env (mesma pasta), se existir."""
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

def today_brt_str() -> str:
    meses = ["janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"]
    now = datetime.now(BRT)
    return f"{now.day} de {meses[now.month-1]} de {now.year}"

def iso_to_brt_human(iso_date: str) -> str:
    try:
        dt = datetime.strptime(iso_date, "%Y-%m-%d").replace(tzinfo=BRT)
        meses = ["janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"]
        return f"{dt.day} de {meses[dt.month-1]} de {dt.year}"
    except Exception:
        return iso_date

def read_counter(counter_file: str, start_counter: int = 1) -> int:
    """Lê/atualiza contador 'diario' em counters.json, retorna o Nº atual."""
    try:
        if os.path.exists(counter_file):
            with open(counter_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}
        val = int(data.get("diario", start_counter))
        data["diario"] = val + 1
        with open(counter_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return val
    except Exception:
        return start_counter

def build_prompt(data_str: str, numero: int, metrics: Optional[Dict[str, Any]]) -> str:
    header = f"Dados On-Chain — {data_str} — Diário — Nº {numero}"
    rules = (
        "Você é um analista on-chain sênior. Produza um relatório em português do Brasil no formato abaixo:\n"
        "Estilo objetivo, profissional, sem links. Estruture com subtítulos.\n\n"
        "TÍTULO (linha única):\n" + header + "\n\n"
        "REGRAS:\n"
        "- Se houver métricas (JSON), use-as; se não houver, não invente números.\n"
        "- Se limite a sinais qualitativos onde faltar dado (alta/baixa/estável) com prudência.\n"
        "- Conter a data completa no 1º parágrafo.\n"
        "- Blocos na ordem fixa (1 parágrafo cada, exceto onde indicado):\n"
        "  1) Exchange Inflow (MA7)\n"
        "  2) Exchange Netflow (Total)\n"
        "  3) Reservas em Exchanges\n"
        "  4) Fluxos de Baleias — 2 parágrafos: (a) depósitos whales/miners; (b) Whale Ratio\n"
        "  5) Resumo de Contexto Institucional\n"
        "  6) Interpretação Executiva — 5–8 bullets curtos e acionáveis\n"
        "  7) Conclusão — 1 parágrafo\n\n"
        "DADOS (JSON opcional):\n"
    )
    dados = json.dumps(metrics, ensure_ascii=False, indent=2) if metrics else "null"
    return rules + dados

def openai_generate(api_key: str, model: Optional[str], prompt: str) -> str:
    """Chama o endpoint chat/completions com modelo compatível (padrão gpt-4o)."""
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": "Bearer " + api_key, "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Você é um analista on-chain sênior e escreve em português do Brasil."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.35,
        "max_tokens": 1800,
    }
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"OpenAI API error: HTTP {r.status_code} — {r.text}")
    data = r.json()
    return data["choices"][0]["message"]["content"]

# --------- Telegram (mensagens em partes <= 4096 chars) ---------
def _chunk_message(text: str, limit: int = 3900) -> List[str]:
    parts: List[str] = []
    for block in text.split("\n\n"):
        b = block.strip()
        if not b:
            if parts and not parts[-1].endswith("\n\n"):
                parts[-1] += "\n\n"
            continue
        if len(b) <= limit:
            if not parts:
                parts.append(b)
            elif len(parts[-1]) + 2 + len(b) <= limit:
                parts[-1] += "\n\n" + b
            else:
                parts.append(b)
        else:
            acc = ""
            for line in b.splitlines():
                if len(acc) + len(line) + 1 <= limit:
                    acc += (("\n" if acc else "") + line)
                else:
                    if acc:
                        parts.append(acc)
                    acc = line
            if acc:
                parts.append(acc)
    return parts if parts else ["(vazio)"]

def telegram_send_messages(token: str, chat_id: str, messages: List[str], parse_mode: str = "HTML"):
    base = f"https://api.telegram.org/bot{token}/sendMessage"
    for msg in messages:
        data = {"chat_id": chat_id, "text": msg, "disable_web_page_preview": True}
        if parse_mode:
            data["parse_mode"] = parse_mode
        r = requests.post(base, data=data, timeout=120)
        if r.status_code != 200:
            raise RuntimeError(f"Telegram error: HTTP {r.status_code} — {r.text}")
        time.sleep(0.6)

# --------------------------- main --------------------------------------
def main():
    load_env_if_present()
    p = argparse.ArgumentParser(description="Gera e envia relatório diário como mensagem no Telegram.")
    p.add_argument("--date", help="Data (YYYY-MM-DD).")
    p.add_argument("--start-counter", type=int, default=1)
    p.add_argument("--counter-file", default=os.path.join(os.path.dirname(__file__), "counters.json"))
    p.add_argument("--metrics", help="Caminho de JSON com métricas reais (opcional).")
    p.add_argument("--model", help="Modelo OpenAI (padrão: $OPENAI_MODEL ou gpt-4o).")
    p.add_argument("--send-as", choices=["message","pdf","both"], default="message",
                   help="Formato de envio: message (padrão), pdf ou both.")
    args = p.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("Defina OPENAI_API_KEY (Secret do GitHub)")

    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat  = os.environ.get("TELEGRAM_CHAT_ID")
    if args.send_as in ("message","both") and (not tg_token or not tg_chat):
        raise SystemExit("Defina TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID para envio por mensagem.")

    data_str = iso_to_brt_human(args.date) if args.date else today_brt_str()
    numero   = read_counter(args.counter_file, start_counter=args.start_counter)

    metrics = None
    if args.metrics:
        with open(args.metrics, "r", encoding="utf-8") as f:
            metrics = json.load(f)

    prompt  = build_prompt(data_str, numero, metrics)
    content = openai_generate(api_key, args.model, prompt).strip()

    titulo  = f"📊 <b>Dados On-Chain — {data_str} — Diário — Nº {numero}</b>"
    corpo   = content
    full    = f"{titulo}\n\n{corpo}"

    if args.send_as in ("message","both"):
        msgs = _chunk_message(full, limit=3900)
        telegram_send_messages(tg_token, tg_chat, msgs, parse_mode="HTML")
        print(f"[ok] Enviado como mensagem no Telegram em {len(msgs)} parte(s).")

    if args.send_as in ("pdf","both"):
        # Mantém compatibilidade: salva texto num arquivo simples
        out_dir = os.path.join(os.path.dirname(__file__), "out")
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, f"Dados On-Chain — {data_str} — Diário — Nº {numero}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(textwrap.dedent(full))
        print("[ok] Texto salvo em:", path)

if __name__ == "__main__":
    main()

