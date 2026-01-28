#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, json, time, html
from datetime import datetime, timezone, timedelta
import requests

from text_engine import (
    interpret_exchange_inflow,
    interpret_exchange_netflow,
    interpret_exchange_reserve,
    interpret_whale_inflow,
    interpret_whale_ratio,
    compute_score,
    aggregate_bias,
    classify_position,
    detect_alerts,
    institutional_block
)

# ==========================================================
# CONFIG
# ==========================================================

BRT = timezone(timedelta(hours=-3), name="BRT")
METRICS_FILE = "metrics.json"
COUNTERS_FILE = "counters.json"

# ==========================================================
# HELPERS
# ==========================================================

def today_brt_str():
    meses = ["janeiro","fevereiro","março","abril","maio","junho",
             "julho","agosto","setembro","outubro","novembro","dezembro"]
    now = datetime.now(BRT)
    return f"{now.day} de {meses[now.month-1]} de {now.year}"

def read_counter(file, key):
    data = json.load(open(file)) if os.path.exists(file) else {}
    val = int(data.get(key, 1))
    data[key] = val + 1
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return val

def chunk(text, limit=3900):
    parts, acc = [], ""
    for line in text.split("\n"):
        if len(acc) + len(line) + 1 <= limit:
            acc += line + "\n"
        else:
            parts.append(acc)
            acc = line + "\n"
    if acc:
        parts.append(acc)
    return parts

def telegram_send(token, chat_id, messages):
    base = f"https://api.telegram.org/bot{token}/sendMessage"
    for msg in messages:
        r = requests.post(base, data={
            "chat_id": chat_id,
            "text": msg,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }, timeout=30)
        if r.status_code != 200:
            raise RuntimeError(r.text)
        time.sleep(0.6)

# ==========================================================
# MAIN
# ==========================================================

def main():
    # --- ENV ---
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat  = os.environ.get("TELEGRAM_CHAT_ID")

    if not tg_token or not tg_chat:
        raise SystemExit("TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID ausentes.")

    # --- LOAD METRICS ---
    if not os.path.exists(METRICS_FILE):
        raise SystemExit("metrics.json não encontrado. Execute o collector.py antes.")

    m = json.load(open(METRICS_FILE, encoding="utf-8"))

    # --- CONTADOR ---
    numero = read_counter(COUNTERS_FILE, "btc_diario")
    data_str = today_brt_str()

    # --- INTERPRETAÇÕES ---
    t1, b1, s1 = interpret_exchange_inflow(
        m["exchange_inflow"]["ma7"],
        m["exchange_inflow"]["avg_90d"],
        m["exchange_inflow"]["percentil"]
    )

    t2, b2, s2 = interpret_exchange_netflow(
        m["exchange_netflow"]["value"]
    )

    t3, b3, s3 = interpret_exchange_reserve(
        m["exchange_reserve"]["current"],
        m["exchange_reserve"]["avg_180d"]
    )

    t4a, b4a, s4a = interpret_whale_inflow(
        m["whale_inflow"]["value_24h"],
        m["whale_inflow"]["avg_30d"]
    )

    t4b, b4b, s4b = interpret_whale_ratio(
        m["whale_ratio"]["value"]
    )

    scores = [s1, s2, s3, s4a, s4b]

    score_total = compute_score(scores)
    direction, strength = aggregate_bias(scores)
    recommendation = classify_position(score_total)

    alerts = detect_alerts(
        m["exchange_inflow"]["percentil"],
        m["whale_ratio"]["value"],
        m["whale_inflow"]["value_24h"],
        m["whale_inflow"]["avg_30d"]
    )

    institutional_text = institutional_block(
        m["institutional"]["etf_flow"]
    )

    # --- RELATÓRIO ---
    sections = [
        f"**1. Exchange Inflow (MA7)**\n\n{t1}",
        f"**2. Exchange Netflow (Total)**\n\n{t2}",
        f"**3. Reservas em Exchanges**\n\n{t3}",
        f"**4. Fluxos de Baleias**\n\n{t4a}\n\n{t4b}",
        f"**5. Resumo de Contexto Institucional**\n\n{institutional_text}",
        f"**Score On-Chain**: {score_total}/100",
        f"**Viés Operacional (24h–7d)**\nDireção: {direction}\nForça do Sinal: {strength}",
        f"**Classificação Final**: {recommendation}"
    ]

    if alerts:
        sections.append(
            "**Sinais de Atenção**\n" + "\n".join([f"• {a}" for a in alerts])
        )

    corpo = "\n\n".join(sections)

    titulo = f"📊 <b>Dados On-Chain BTC — {data_str} — Diário — Nº {numero}</b>"
    full = f"{titulo}\n\n{html.escape(corpo, quote=False)}"

    telegram_send(tg_token, tg_chat, chunk(full))
    print("✅ Relatório enviado com sucesso.")

if __name__ == "__main__":
    main()
