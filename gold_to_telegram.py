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
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k and v and k not in os.environ:
                os.environ[k.strip()] = v.strip()

def today_brt_str():
    meses = ["janeiro","fevereiro","março","abril","maio","junho",
             "julho","agosto","setembro","outubro","novembro","dezembro"]
    now = datetime.now(BRT)
    return f"{now.day} de {meses[now.month-1]} de {now.year}"

def iso_to_brt_human(iso_date: str) -> str:
    try:
        dt = datetime.strptime(iso_date, "%Y-%m-%d").replace(tzinfo=BRT)
        meses = ["janeiro","fevereiro","março","abril","maio","junho",
                 "julho","agosto","setembro","outubro","novembro","dezembro"]
        return f"{dt.day} de {meses[dt.month-1]} de {dt.year}"
    except Exception:
        return iso_date

def read_counter(counter_file: str, start_counter: int = 1) -> int:
    try:
        data = json.load(open(counter_file, "r", encoding="utf-8")) if os.path.exists(counter_file) else {}
        val = int(data.get("diario_xau", start_counter))
        data["diario_xau"] = val + 1
        with open(counter_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return val
    except Exception:
        return start_counter

def build_prompt_xau(data_str: str, numero: int, metrics: Optional[Dict[str, Any]]) -> str:
    header = f"OURO (XAU) — {data_str} — Diário — Nº {numero}"
    rules = (
        "Você é um analista de mercados focado em **Ouro (XAU)**. "
        "Produza um relatório em português do Brasil, objetivo e profissional.\n"
        "TÍTULO (linha única):\n" + header + "\n\n"
        "REGRAS:\n"
        "- Se houver métricas (JSON), use-as; se não houver, NÃO invente números: descreva sinais qualitativos.\n"
        "- Sem links; inclua a data completa no primeiro parágrafo.\n"
        "- Estrutura fixa (na ordem):\n"
        "  1) Preço spot e variação (qualitativo)\n"
        "  2) Futuros (COMEX): basis / OI (qualitativo)\n"
        "  3) ETFs de ouro: fluxos e variação de holdings (qualitativo)\n"
        "  4) Fluxos cambiais relevantes e correlações (DXY/real yields) — qualitativo\n"
        "  5) Drivers macro do dia/semana\n"
        "  6) Interpretação Executiva — 5–8 bullets\n"
        "  7) Conclusão\n\n"
        "DADOS (JSON opcional):\n"
    )
    dados = json.dumps(metrics, ensure_ascii=False, indent=2) if metrics else "null"
    return rules + dados

def fallback_content_xau(data_str: str, numero: int, motivo: str) -> str:
    return textwrap.dedent(f"""
    ⚠️ Não foi possível gerar o relatório automático hoje (OURO).
    Motivo: {motivo}
    Data: {data_str} — Diário — Nº {numero}

    Use o esqueleto abaixo para registro:

    1) Preço spot e variação — qualitativo.
    2) Futuros (COMEX): basis / OI — qualitativo.
    3) ETFs de ouro: fluxos/holdings — qualitativo.
    4) Fluxos cambiais (DXY/real yields) — qualitativo.
    5) Drivers macro do dia.
    6) Interpretação Executiva — 5–8 bullets.
    7) Conclusão.
    """).strip()

# ---------------- LLM PROVIDERS (com fallback no Groq) ----------------

def llm_generate(provider: str, model: str, prompt: str, keys: Dict[str, str]) -> Optional[str]:
    provider = (provider or "groq").lower()

    if provider == "groq":
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": "Bearer " + keys.get("GROQ_API_KEY", ""), "Content-Type": "application/json"}

        preferred = model or os.getenv("GROQ_MODEL") or "llama-3.1-70b"
        candidates = [preferred, "llama-3.1-8b", "mixtral-8x7b-32768"]

        last_err = None
        for m in candidates:
            payload = {
                "model": m,
                "messages": [
                    {"role": "system", "content": "Você é um analista sênior de mercados e escreve em português do Brasil."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.35,
                "max_tokens": 1800,
            }
            r = requests.post(url, headers=headers, json=payload, timeout=120)

            if r.status_code in (401, 403, 429):
                return None

            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]

            if r.status_code in (400, 404) and "model" in r.text.lower():
                last_err = f"HTTP {r.status_code} — {r.text[:180]}"
                continue

            raise RuntimeError(f"GROQ error: HTTP {r.status_code} — {r.text}")

        raise RuntimeError(f"GROQ error (todos os modelos falharam). Último: {last_err}")

    if provider == "openai":
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": "Bearer " + keys.get("OPENAI_API_KEY", ""), "Content-Type": "application/json"}
        payload = {"model": model or "gpt-4o",
                   "messages":[{"role":"system","content":"Você é um analista sênior de mercados e escreve em português do Brasil."},
                               {"role":"user","content":prompt}],
                   "temperature":0.35,"max_tokens":1800}
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        if r.status_code in (401,403,429):
            return None
        if r.status_code != 200:
            raise RuntimeError(f"OpenAI error: HTTP {r.status_code} — {r.text}")
        return r.json()["choices"][0]["message"]["content"]

    if provider == "openrouter":
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {"Authorization": "Bearer " + keys.get("OPENROUTER_API_KEY",""),
                   "Content-Type": "application/json"}
        payload = {"model": model or "meta-llama/llama-3.1-70b-instruct",
                   "messages":[{"role":"system","content":"Você é um analista sênior de mercados e escreve em português do Brasil."},
                               {"role":"user","content":prompt}],
                   "temperature":0.35,"max_tokens":1800}
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        if r.status_code in (401,403,429):
            return None
        if r.status_code != 200:
            raise RuntimeError(f"OpenRouter error: HTTP {r.status_code} — {r.text}")
        return r.json()["choices"][0]["message"]["content"]

    if provider == "anthropic":
        url = "https://api.anthropic.com/v1/messages"
        headers = {"x-api-key": keys.get("ANTHROPIC_API_KEY",""),
                   "anthropic-version": "2023-06-01",
                   "content-type": "application/json"}
        payload = {"model": model or "claude-3-5-sonnet-20240620",
                   "max_tokens": 1800,
                   "temperature": 0.35,
                   "messages":[{"role":"user","content":prompt}]}
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        if r.status_code in (401,403,429):
            return None
        if r.status_code != 200:
            raise RuntimeError(f"Anthropic error: HTTP {r.status_code} — {r.text}")
        data = r.json()
        parts = data.get("content", [])
        text = "".join(p.get("text","") for p in parts if isinstance(p, dict))
        return text

    raise RuntimeError(f"Provider desconhecido: {provider}")

# --------- Telegram helpers ---------

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
    ap = argparse.ArgumentParser(description="Relatório OURO (XAU) diário → Telegram (mensagem).")
    ap.add_argument("--date")
    ap.add_argument("--start-counter", type=int, default=1)
    ap.add_argument("--counter-file", default=os.path.join(os.path.dirname(__file__), "counters.json"))
    ap.add_argument("--metrics")
    ap.add_argument("--provider", choices=["groq","openai","openrouter","anthropic"], default=os.environ.get("PROVIDER","groq"))
    ap.add_argument("--model")
    ap.add_argument("--send-as", choices=["message","pdf","both"], default="message")
    args = ap.parse_args()

    keys = {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY",""),
        "GROQ_API_KEY": os.environ.get("GROQ_API_KEY",""),
        "OPENROUTER_API_KEY": os.environ.get("OPENROUTER_API_KEY",""),
        "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY",""),
    }

    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN") or ""
    tg_chat  = os.environ.get("TELEGRAM_CHAT_ID") or ""
    if args.send_as in ("message","both") and (not tg_token or not tg_chat):
        raise SystemExit("Defina TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID para envio por mensagem.")

    data_str = iso_to_brt_human(args.date) if args.date else today_brt_str()
    numero   = read_counter(args.counter_file, start_counter=args.start_counter)

    metrics = None
    if args.metrics and os.path.exists(args.metrics):
        metrics = json.load(open(args.metrics, "r", encoding="utf-8"))

    prompt  = build_prompt_xau(data_str, numero, metrics)

    try:
        content = llm_generate(args.provider, args.model, prompt, keys)
        motivo  = None if content else f"sem cota/limite em {args.provider.upper()} ou chave ausente."
    except Exception as e:
        content = None
        motivo  = f"erro no provedor {args.provider.upper()}: {e}"

    titulo = f"📊 <b>OURO (XAU) — {data_str} — Diário — Nº {numero}</b>"
    full   = f"{titulo}\n\n{content.strip() if content else fallback_content_xau(data_str, numero, motivo)}"

    if args.send_as in ("message","both"):
        msgs = _chunk_message(full, limit=3900)
        telegram_send_messages(tg_token, tg_chat, msgs, parse_mode="HTML")
        print(f"[ok] Mensagem enviada em {len(msgs)} parte(s).")

    if args.send_as in ("pdf","both"):
        out_dir = os.path.join(os.path.dirname(__file__), "out")
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, f"OURO (XAU) — {data_str} — Diário — Nº {numero}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(full)
        print("[ok] Texto salvo em:", path)

if __name__ == "__main__":
    main()