#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, json, argparse, requests, time, textwrap
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

BRT = timezone(timedelta(hours=-3), name="BRT")

def load_env_if_present():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        for raw in open(env_path, "r", encoding="utf-8"):
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            k, v = line.split("=", 1)
            if k and v and k not in os.environ:
                os.environ[k.strip()] = v.strip()

def today_brt_str():
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
    try:
        data = json.load(open(counter_file, "r", encoding="utf-8")) if os.path.exists(counter_file) else {}
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
        "Você é um analista on-chain sênior. Produza um relatório em português do Brasil, objetivo e profissional.\n"
        "TÍTULO (linha única):\n" + header + "\n\n"
        "REGRAS:\n"
        "- Se houver métricas (JSON), use-as; se não houver, NÃO invente números: descreva sinais qualitativos.\n"
        "- Sem links; inclua a data completa no primeiro parágrafo.\n"
        "- Estrutura fixa (na ordem):\n"
        "  1) Exchange Inflow (MA7)\n"
        "  2) Exchange Netflow (Total)\n"
        "  3) Reservas em Exchanges\n"
        "  4) Fluxos de Baleias — 2 parágrafos: (a) depósitos whales/miners; (b) Whale Ratio\n"
        "  5) Resumo de Contexto Institucional\n"
        "  6) Interpretação Executiva — 5–8 bullets\n"
        "  7) Conclusão\n\n"
        "DADOS (JSON opcional):\n"
    )
    dados = json.dumps(metrics, ensure_ascii=False, indent=2) if metrics else "null"
    return rules + dados

def fallback_content(data_str: str, numero: int) -> str:
    return textwrap.dedent(f"""
    ⚠️ Não foi possível gerar o relatório automático hoje (quota da OpenAI insuficiente).
    Data: {data_str} — Diário — Nº {numero}

    Use o esqueleto abaixo para registro:

    1) Exchange Inflow (MA7)
    • Sinal qualitativo: (alta / baixa / estável). Observações principais.

    2) Exchange Netflow (Total)
    • Sinal qualitativo e implicações.

    3) Reservas em Exchanges
    • Tendência geral e leitura de risco de oferta.

    4) Fluxos de Baleias
    • (a) Depósitos de whales/miners: leitura qualitativa.
    • (b) Whale Ratio: leitura qualitativa e implicações.

    5) Resumo de Contexto Institucional
    • Narrativa macro/fluxos institucionais.

    6) Interpretação Executiva
    • 5–8 bullets curtos e acionáveis.

    7) Conclusão
    • Encerramento executivo com enquadramento de risco.
    """).strip()

def openai_generate(api_key: str, model: Optional[str], prompt: str) -> Optional[str]:
    """Retorna o texto ou None se quota insuficiente (429/insufficient_quota)."""
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
    if r.status_code == 429:
        try:
            err = r.json().get("error", {})
            if err.get("type") == "insufficient_quota":
                return None
        except Exception:
            pass
    if r.status_code != 200:
        raise RuntimeError(f"OpenAI API error: HTTP {r.status_code} — {r.text}")
    data = r.json()
    return data["choices"][0]["message"]["content"]

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

def main():
    load_env_if_present()
    ap = argparse.ArgumentParser(description="Relatório on-chain diário → Telegram (mensagem).")
    ap.add_argument("--date")
    ap.add_argument("--start-counter", type=int, default=1)
    ap.add_argument("--counter-file", default=os.path.join(os.path.dirname(__file__), "counters.json"))
    ap.add_argument("--metrics")
    ap.add_argument("--model")
    ap.add_argument("--send-as", choices=["message","pdf","both"], default="message")
    args = ap.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY") or ""
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN") or ""
    tg_chat  = os.environ.get("TELEGRAM_CHAT_ID") or ""

    data_str = iso_to_brt_human(args.date) if args.date else today_brt_str()
    numero   = read_counter(args.counter_file, start_counter=args.start_counter)

    metrics = None
    if args.metrics and os.path.exists(args.metrics):
        metrics = json.load(open(args.metrics, "r", encoding="utf-8"))

    prompt = build_prompt(data_str, numero, metrics)
    content = openai_generate(api_key, args.model, prompt)

    titulo = f"📊 <b>Dados On-Chain — {data_str} — Diário — Nº {numero}</b>"

    if content is None:
        corpo = fallback_content(data_str, numero)
        full  = f"{titulo}\n\n{corpo}\n\n<i>Motivo: quota insuficiente no provedor de IA. Verifique billing.</i>"
    else:
        full  = f"{titulo}\n\n{content.strip()}"

    if args.send_as in ("message","both"):
        if not tg_token or not tg_chat:
            raise SystemExit("Defina TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID para envio por mensagem.")
        msgs = _chunk_message(full, limit=3900)
        telegram_send_messages(tg_token, tg_chat, msgs, parse_mode="HTML")
        print(f"[ok] Mensagem enviada em {len(msgs)} parte(s).")

    if args.send_as in ("pdf","both"):
        out_dir = os.path.join(os.path.dirname(__file__), "out")
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, f"Dados On-Chain — {data_str} — Diário — Nº {numero}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(full)
        print("[ok] Texto salvo em:", path)

if __name__ == "__main__":
    main()
