#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, json, argparse, datetime, pathlib, sys, textwrap, time
from zoneinfo import ZoneInfo
import requests

ASSET = "ETH"
ASSET_LOWER = "eth"
SENT_DIR = pathlib.Path(".sent") / ASSET_LOWER  # .sent/eth
SENT_DIR.mkdir(parents=True, exist_ok=True)
COUNTERS_FILE = pathlib.Path("counters.json")

SECTIONS = [
    "1. Exchange Inflow (MA7)",
    "2. Exchange Netflow (Total)",
    "3. Reservas em Exchanges",
    "4. Fluxos de Baleias (Whale-to-Exchange): depósitos de whales/mineradores e Whale Ratio",
    "5. Resumo de Contexto Institucional",
    "6. Interpretação Executiva",
    "7. Conclusão",
]

SYSTEM_PROMPT = """Você é um analista on-chain sênior. Escreva em português (Brasil), tom conciso, claro e acionável.
Estruture exatamente com as seções abaixo (títulos idênticos):
1. Exchange Inflow (MA7)
2. Exchange Netflow (Total)
3. Reservas em Exchanges
4. Fluxos de Baleias (Whale-to-Exchange): depósitos de whales/mineradores e Whale Ratio
5. Resumo de Contexto Institucional
6. Interpretação Executiva
7. Conclusão
Regras:
- Ativo-alvo: ETH (Ethereum).
- Não invente números exatos; foque em direção/magnitude, comparações semanais/diárias e implicações táticas.
- “Interpretação Executiva”: 5–8 bullets objetivos (entrada/saída de risco, drivers, atenção do trader).
- Evite floreios; nada de emojis aqui.
"""

PROMPT_TEMPLATE = """Gere o relatório “Dados On-Chain ETH — {data_long} — {periodo_pt} — Nº {numero}” para {ativo}.
Inclua TODAS as seções 1–7 exatamente como no enunciado do sistema.
Caso não seja possível obter insights, entregue um esqueleto comentado com “(revisar dados manualmente)”.
"""

def _today_keys(period: str, tz: str = "America/Sao_Paulo"):
    now = datetime.datetime.now(ZoneInfo(tz))
    if period == "daily":
        sent = f"done-daily-{now:%Y-%m-%d}"
    elif period == "weekly":
        # ISO week (Www)
        year, week, _ = now.isocalendar()
        sent = f"done-weekly-{year}-W{week:02d}"
    elif period == "monthly":
        sent = f"done-monthly-{now:%Y-%m}"
    else:
        raise ValueError("period must be daily|weekly|monthly")
    # Data longa pt-BR
    meses = ["janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"]
    data_long = f"{now.day} de {meses[now.month-1]} de {now.year}"
    periodo_pt = {"daily":"Diário","weekly":"Semanal","monthly":"Mensal"}[period]
    return sent, data_long, periodo_pt

def _load_counters():
    if COUNTERS_FILE.exists():
        with open(COUNTERS_FILE,"r",encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}

def _save_counters(data: dict):
    with open(COUNTERS_FILE,"w",encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _bump_counter(period: str) -> int:
    data = _load_counters()
    key = f"{ASSET_LOWER}_{period}"
    data.setdefault(key, 0)
    data[key] += 1
    _save_counters(data)
    return data[key]

def _seal_exists(filename: str) -> bool:
    return (SENT_DIR / filename).exists()

def _write_seal(filename: str):
    (SENT_DIR / filename).write_text(str(int(time.time())), encoding="utf-8")

def _call_llm(provider: str, model: str, prompt: str, max_tokens: int = 1200) -> str:
    """
    Tenta Groq (OpenAI-compatible), depois OpenAI, depois OpenRouter, depois Anthropic.
    """
    if provider == "groq" or (not provider and os.getenv("GROQ_API_KEY")):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"}
        body = {
            "model": model or os.getenv("GROQ_MODEL","llama-3.1-70b-versatile"),
            "messages": [
                {"role":"system","content":SYSTEM_PROMPT},
                {"role":"user","content":prompt},
            ],
            "temperature": 0.6,
            "max_tokens": max_tokens,
        }
        r = requests.post(url, headers=headers, json=body, timeout=90)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

    if provider == "openai" or (not provider and os.getenv("OPENAI_API_KEY")):
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"}
        body = {
            "model": model or os.getenv("OPENAI_MODEL","gpt-4o-mini"),
            "messages": [
                {"role":"system","content":SYSTEM_PROMPT},
                {"role":"user","content":prompt},
            ],
            "temperature": 0.6,
            "max_tokens": max_tokens,
        }
        r = requests.post(url, headers=headers, json=body, timeout=90)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

    if provider == "openrouter" or (not provider and os.getenv("OPENROUTER_API_KEY")):
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"}
        body = {
            "model": model or os.getenv("OPENROUTER_MODEL","meta-llama/llama-3.1-70b-instruct"),
            "messages": [
                {"role":"system","content":SYSTEM_PROMPT},
                {"role":"user","content":prompt},
            ],
            "temperature": 0.6,
            "max_tokens": max_tokens,
        }
        r = requests.post(url, headers=headers, json=body, timeout=90)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

    if provider == "anthropic" or (not provider and os.getenv("ANTHROPIC_API_KEY")):
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": os.environ["ANTHROPIC_API_KEY"],
            "anthropic-version": "2023-06-01",
        }
        body = {
            "model": model or os.getenv("ANTHROPIC_MODEL","claude-3-5-haiku-latest"),
            "max_tokens": max_tokens,
            "temperature": 0.6,
            "system": SYSTEM_PROMPT,
            "messages": [{"role":"user","content":prompt}],
        }
        r = requests.post(url, headers=headers, json=body, timeout=90)
        r.raise_for_status()
        return "".join([c.get("text","") for c in r.json()["content"]]).strip()

    raise RuntimeError("Nenhum provedor configurado. Defina GROQ/OPENAI/OPENROUTER/ANTHROPIC API KEY.")

def _send_telegram(text: str, as_document: bool = False):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    # Permite chat/ tópico específicos para ETH; se não houver, cai no padrão global
    chat_id = os.getenv("ETH_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")
    if not chat_id:
        raise RuntimeError("Defina ETH_TELEGRAM_CHAT_ID ou TELEGRAM_CHAT_ID")
    topic_id = os.getenv("ETH_TELEGRAM_TOPIC_ID")  # opcional (para tópicos)

    base = f"https://api.telegram.org/bot{token}"
    if as_document:
        files = {"document": ("relatorio.txt", text.encode("utf-8"))}
        data = {"chat_id": chat_id}
        if topic_id:
            data["message_thread_id"] = topic_id
        r = requests.post(f"{base}/sendDocument", data=data, files=files, timeout=90)
    else:
        data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        if topic_id:
            data["message_thread_id"] = topic_id
        r = requests.post(f"{base}/sendMessage", data=data, timeout=90)

    r.raise_for_status()
    return r.json()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default=os.getenv("PROVIDER","groq"))
    parser.add_argument("--model", default=os.getenv("MODEL","llama-3.1-70b-versatile"))
    parser.add_argument("--send-as", choices=["message","document"], default="message")
    parser.add_argument("--period", choices=["daily","weekly","monthly"], default="daily")
    args = parser.parse_args()

    sent_name, data_long, periodo_pt = _today_keys(args.period)
    if _seal_exists(sent_name):
        print(f"[{ASSET}] Selo existente: {sent_name} — nada a fazer.")
        return

    numero = _bump_counter(args.period)
    prompt = PROMPT_TEMPLATE.format(data_long=data_long, periodo_pt=periodo_pt, numero=numero, ativo=ASSET)

    try:
        body = _call_llm(args.provider, args.model, prompt)
    except Exception as e:
        aviso = f"(Falha no LLM: {e}). Entregando esqueleto para registro."
        body = "\n".join([
            f"Dados On-Chain — {data_long} — {periodo_pt} — Nº {numero}",
            "",
            *SECTIONS,
            "",
            aviso
        ])

    # Cabeçalho + corpo
    titulo = f"Dados On-Chain — {data_long} — {periodo_pt} — Nº {numero}"
    text = f"{titulo}\n\n{body}".strip()

    _send_telegram(text, as_document=(args["send_as"] if isinstance(args, dict) else args.send_as) == "document")
    _write_seal(sent_name)
    print(f"[{ASSET}] Enviado com sucesso ({args.period}). Selo: {sent_name} — Nº {numero}")

if __name__ == "__main__":
    main()
