import json
import os
from datetime import datetime
import requests

from text_engine import (
    interpret_exchange_inflow,
    interpret_exchange_netflow,
    interpret_exchange_reserve,
    interpret_whale_inflow,
    interpret_whale_ratio,
    compute_score,
    aggregate_bias,
    classify_position
)

# ==========================================================
# CONFIG
# ==========================================================

METRICS_FILE = "metrics.json"
HISTORY_METRICS_FILE = "history_metrics.json"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ==========================================================
# HELPERS
# ==========================================================

def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    r = requests.post(url, json=payload, timeout=15)
    r.raise_for_status()


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def average(values):
    if not values:
        return 0
    return sum(values) / len(values)


def percent_delta(current, avg):
    if avg == 0:
        return None
    return (current - avg) / avg * 100


# ==========================================================
# MAIN
# ==========================================================

def main():
    # ----------------------------
    # LOAD METRICS
    # ----------------------------
    metrics = load_json(METRICS_FILE, {})

    exchange_inflow = metrics.get("exchange_inflow", 0)
    exchange_netflow = metrics.get("exchange_netflow", 0)
    exchange_reserve = metrics.get("exchange_reserve", 0)
    whale_inflow_24h = metrics.get("whale_inflow_24h", 0)
    whale_ratio = metrics.get("whale_ratio", 0)

    # ----------------------------
    # LOAD HISTORY
    # ----------------------------
    history = load_json(HISTORY_METRICS_FILE, [])

    inflow_hist = [h["exchange_inflow"] for h in history if "exchange_inflow" in h]
    netflow_hist = [h["exchange_netflow"] for h in history if "exchange_netflow" in h]
    reserve_hist = [h["exchange_reserve"] for h in history if "exchange_reserve" in h]
    whale_hist = [h["whale_inflow"] for h in history if "whale_inflow" in h]

    avg_inflow = average(inflow_hist[-90:])
    avg_netflow = average(netflow_hist[-90:])
    avg_reserve = average(reserve_hist[-180:])
    avg_whale = average(whale_hist[-30:])

    # ----------------------------
    # INTERPRETAÇÕES
    # ----------------------------
    t1, b1, s1 = interpret_exchange_inflow(exchange_inflow, avg_inflow, 50)
    t2, b2, s2 = interpret_exchange_netflow(exchange_netflow)
    t3, b3, s3 = interpret_exchange_reserve(exchange_reserve, avg_reserve)
    t4, b4, s4 = interpret_whale_inflow(whale_inflow_24h, avg_whale)
    t5, b5, s5 = interpret_whale_ratio(whale_ratio)

    scores = [s1, s2, s3, s4, s5]
    score = compute_score(scores)
    bias, strength = aggregate_bias(scores)
    position = classify_position(score)

    # ----------------------------
    # BUILD MESSAGE
    # ----------------------------
    today = datetime.now().strftime("%d/%m/%Y")

    msg = []
    msg.append(f"📊 <b>Dados On-Chain BTC — {today} — Diário</b>\n")

    # 1 — Exchange Inflow
    msg.append("1️⃣ <b>Exchange Inflow (MA7)</b>")
    msg.append(t1)
    delta = percent_delta(exchange_inflow, avg_inflow)
    if delta is not None:
        msg.append(f"{delta:+.1f}% em relação à média histórica.\n")
    else:
        msg.append("Sem base histórica suficiente para comparação percentual.\n")

    # 2 — Exchange Netflow
    msg.append("2️⃣ <b>Exchange Netflow</b>")
    msg.append(t2)
    delta = percent_delta(exchange_netflow, avg_netflow)
    if delta is not None:
        msg.append(f"{delta:+.1f}% em relação à média histórica.\n")
    else:
        msg.append("Sem base histórica suficiente para comparação percentual.\n")

    # 3 — Reserves
    msg.append("3️⃣ <b>Reservas em Exchanges</b>")
    msg.append(t3)
    delta = percent_delta(exchange_reserve, avg_reserve)
    if delta is not None:
        msg.append(f"{delta:+.1f}% em relação à média histórica.\n")
    else:
        msg.append("Sem base histórica suficiente para comparação percentual.\n")

    # 4 — Whales
    msg.append("4️⃣ <b>Fluxos de Baleias</b>")
    msg.append(t4)
    delta = percent_delta(whale_inflow_24h, avg_whale)
    if delta is not None:
        msg.append(f"{delta:+.1f}% em relação à média histórica.")
    else:
        msg.append("Sem base histórica suficiente para comparação percentual.")
    msg.append(f"O Whale Ratio encontra-se em {whale_ratio:.2f}.\n")

    # Executive
    msg.append("📌 <b>Interpretação Executiva</b>")
    msg.append(f"• Score On-Chain: {score}/100")
    msg.append(f"• Viés de Mercado: {bias} ({strength})")
    msg.append(f"• Recomendação: <b>{position}</b>")

    final_message = "\n".join(msg)

    # ----------------------------
    # SEND
    # ----------------------------
    send_telegram(final_message)

    # ----------------------------
    # UPDATE HISTORY
    # ----------------------------
    history.append({
        "date": datetime.utcnow().isoformat(),
        "exchange_inflow": exchange_inflow,
        "exchange_netflow": exchange_netflow,
        "exchange_reserve": exchange_reserve,
        "whale_inflow": whale_inflow_24h,
        "whale_ratio": whale_ratio
    })

    save_json(HISTORY_METRICS_FILE, history)


if __name__ == "__main__":
    main()
