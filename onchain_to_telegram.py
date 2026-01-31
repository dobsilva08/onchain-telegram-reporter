#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import requests
from datetime import datetime, timezone, timedelta

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

from alerts_engine import check_signal_and_alert

# ==========================================================
# CONFIGURAÇÕES GERAIS
# ==========================================================

BRT = timezone(timedelta(hours=-3))
METRICS_FILE = "metrics.json"
COUNTERS_FILE = "counters.json"

# ==========================================================
# FUNÇÕES AUXILIARES
# ==========================================================

def today_brt_str():
    meses = [
        "janeiro","fevereiro","março","abril","maio","junho",
        "julho","agosto","setembro","outubro","novembro","dezembro"
    ]
    now = datetime.now(BRT)
    return f"{now.day} de {meses[now.month-1]} de {now.year}"

def read_counter(file, key):
    data = json.load(open(file, "r", encoding="utf-8")) if os.path.exists(file) else {}
    val = int(data.get(key, 1))
    data[key] = val + 1
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return val

def chunk(text, limit=3900):
    parts = []
    acc = ""
    for line in text.split("\n"):
        if len(acc) + len(line) + 1 <= limit:
            acc += line + "\n"
        else:
            parts.append(acc.strip())
            acc = line + "\n"
    if acc.strip():
        parts.append(acc.strip())
    return parts

def telegram_send(token, chat_id, messages):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    for msg in messages:
        r = requests.post(
            url,
            data={
                "chat_id": chat_id,
                "text": msg,
                "disable_web_page_preview": True
            },
            timeout=30
        )
        if r.status_code != 200:
            print("Erro Telegram:", r.text)
        time.sleep(0.6)

# ==========================================================
# MAIN
# ==========================================================

def main():
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat  = os.environ.get("TELEGRAM_CHAT_ID")

    if not tg_token or not tg_chat:
        raise SystemExit("❌ TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID não definidos")

    # ======================
    # CARREGAR MÉTRICAS
    # ======================
    with open(METRICS_FILE, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    # ======================
    # ALERTAS COMPRA / VENDA
    # ======================
    alerts = check_signal_and_alert(metrics)
    for alert in alerts:
        telegram_send(tg_token, tg_chat, [alert])

    # ======================
    # RELATÓRIO DIÁRIO
    # ======================
    numero = read_counter(COUNTERS_FILE, "btc_diario")
    data_str = today_brt_str()

    t1, _, s1 = interpret_exchange_inflow(
        metrics["exchange_inflow"]["ma7"],
        metrics["exchange_inflow"]["avg_90d"],
        metrics["exchange_inflow"]["percentil"]
    )

    t2, _, s2 = interpret_exchange_netflow(
        metrics["exchange_netflow"]["value"]
    )

    t3, _, s3 = interpret_exchange_reserve(
        metrics["exchange_reserve"]["current"],
        metrics["exchange_reserve"]["avg_180d"]
    )

    t4a, _, s4a = interpret_whale_inflow(
        metrics["whale_inflow"]["value_24h"],
        metrics["whale_inflow"]["avg_30d"]
    )

    t4b, _, s4b = interpret_whale_ratio(
        metrics["whale_ratio"]["value"]
    )

    score = compute_score([s1, s2, s3, s4a, s4b])
    direction, strength = aggregate_bias([s1, s2, s3, s4a, s4b])
    classification = classify_position(score)

    alerts_text = detect_alerts(
        metrics["exchange_inflow"]["percentil"],
        metrics["whale_ratio"]["value"],
        metrics["whale_inflow"]["value_24h"],
        metrics["whale_inflow"]["avg_30d"]
    )

    sections = [
        f"1) Exchange Inflow (MA7)\n{t1}",
        f"2) Exchange Netflow (Total)\n{t2}",
        f"3) Reservas em Exchanges\n{t3}",
        f"4) Fluxos de Baleias\n{t4a}\n\n{t4b}",
        f"5) Contexto Institucional\n{institutional_block(metrics['institutional']['etf_flow'])}"
    ]

    if alerts_text:
        sections.append(
            "⚠️ ALERTAS ON-CHAIN\n" +
            "\n".join(f"- {a}" for a in alerts_text)
        )

    sections.extend([
        f"📊 Score On-Chain: {score}/100",
        f"📈 Viés Operacional: {direction} ({strength})",
        f"🎯 Classificação: {classification}"
    ])

    report = (
        f"📊 Dados On-Chain BTC — {data_str} — Diário — Nº {numero}\n\n" +
        "\n\n".join(sections)
    )

    telegram_send(tg_token, tg_chat, chunk(report))

# ==========================================================
# ENTRYPOINT
# ==========================================================

if __name__ == "__main__":
    main()
