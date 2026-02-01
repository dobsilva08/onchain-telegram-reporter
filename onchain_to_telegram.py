# ============================================================
# On-Chain BTC Reporter — Fase 6.4 (ESTÁVEL)
# Gera relatório diário determinístico e envia ao Telegram
# ============================================================

import json
import os
from datetime import datetime, timezone
import requests

# ========================
# CONFIGURAÇÕES
# ========================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

METRICS_FILE = "metrics.json"
HISTORY_FILE = "history.json"

# ========================
# UTILIDADES
# ========================

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload, timeout=20)


def extract_value(metric):
    """
    Normaliza métricas que podem vir como:
    - número
    - dict { value: x }
    """
    if metric is None:
        return None
    if isinstance(metric, dict):
        return metric.get("value")
    return metric


# ========================
# INTERPRETAÇÕES
# ========================

def interpret_exchange_inflow(value):
    if value is None:
        return "N/A", 0

    if value < 4000:
        return (
            f"O Exchange Inflow (MA7) está significativamente abaixo da média histórica, em {value:,.0f} BTC.",
            2
        )

    return (
        f"O Exchange Inflow (MA7) encontra-se em nível intermediário, em {value:,.0f} BTC.",
        0
    )


def interpret_exchange_netflow(value):
    if value is None:
        return "N/A", 0

    if value < 0:
        return (
            f"O Exchange Netflow registra saída líquida de aproximadamente {abs(value):,.0f} BTC das exchanges.",
            2
        )

    return (
        f"O Exchange Netflow registra entrada líquida de aproximadamente {value:,.0f} BTC nas exchanges.",
        -1
    )


def interpret_exchange_reserves(value):
    if value is None:
        return "N/A", 0

    return (
        f"As reservas em exchanges seguem em {value:,.0f} BTC, abaixo da média histórica, indicando redução de oferta.",
        2
    )


def interpret_whales(deposits, whale_ratio):
    score = 0
    lines = []

    if deposits is not None:
        lines.append(
            f"Os depósitos de baleias somaram cerca de {deposits:,.0f} BTC nas últimas 24h."
        )
        score += 1
    else:
        lines.append("Os depósitos de baleias não puderam ser estimados.")

    if whale_ratio is not None:
        level = "baixo"
        if whale_ratio > 0.85:
            level = "elevado"
            score -= 1
        elif whale_ratio > 0.6:
            level = "moderado"

        lines.append(
            f"O Whale Ratio encontra-se em {whale_ratio:.2f}, em nível {level}."
        )
    else:
        lines.append("O Whale Ratio não está disponível.")

    return " ".join(lines), score


# ========================
# SCORE E RECOMENDAÇÃO
# ========================

def compute_score(scores):
    base = 50
    return max(0, min(100, base + sum(scores) * 10))


def market_bias(score):
    if score >= 85:
        return "Altista (Forte)", "Acumular"
    if score >= 65:
        return "Altista (Moderada)", "Acumular"
    if score >= 45:
        return "Neutro", "Manter"
    return "Baixista", "Reduzir"


# ========================
# MAIN
# ========================

def main():
    metrics = load_json(METRICS_FILE)

    inflow = extract_value(metrics.get("exchange_inflow_ma7"))
    netflow = extract_value(metrics.get("exchange_netflow"))
    reserves = extract_value(metrics.get("exchange_reserves"))
    whale_deposits = extract_value(metrics.get("whale_inflow_24h"))
    whale_ratio = extract_value(metrics.get("whale_ratio"))

    scores = []

    inflow_text, s = interpret_exchange_inflow(inflow)
    scores.append(s)

    netflow_text, s = interpret_exchange_netflow(netflow)
    scores.append(s)

    reserves_text, s = interpret_exchange_reserves(reserves)
    scores.append(s)

    whales_text, s = interpret_whales(whale_deposits, whale_ratio)
    scores.append(s)

    score = compute_score(scores)
    bias, recommendation = market_bias(score)

    today = datetime.now(timezone.utc).strftime("%d/%m/%Y")

    message = f"""📊 *Dados On-Chain BTC — {today} — Diário*

1️⃣ *Exchange Inflow (MA7)*
{inflow_text}

2️⃣ *Exchange Netflow*
{netflow_text}

3️⃣ *Reservas em Exchanges*
{reserves_text}

4️⃣ *Fluxos de Baleias*
{whales_text}

📌 *Interpretação Executiva*
• Score On-Chain: *{score}/100*
• Viés de Mercado: *{bias}*
• Recomendação: *{recommendation}*
"""

    send_telegram_message(message)


if __name__ == "__main__":
    main()
