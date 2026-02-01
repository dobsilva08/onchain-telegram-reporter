import json
import os
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
)

# ===============================
# CONFIG
# ===============================

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BRT = timezone(timedelta(hours=-3))

METRICS_FILE = "metrics.json"
HISTORY_FILE = "history.json"

# ===============================
# HELPERS
# ===============================

def send_telegram_message(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    r = requests.post(url, data=payload, timeout=30)
    r.raise_for_status()


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ===============================
# MAIN
# ===============================

def main():
    metrics = load_json(METRICS_FILE, {})
    history = load_json(HISTORY_FILE, {})

    scores = []
    sections = []

    # -------- Exchange Inflow --------
    inflow = metrics.get("exchange_inflow", {})
    txt, bias, score = interpret_exchange_inflow(
        inflow.get("ma7", 0),
        inflow.get("avg_90d", 0),
        inflow.get("percentil", 50),
    )
    sections.append(f"1️⃣ <b>Exchange Inflow (MA7)</b>\n{txt}")
    scores.append(score)

    # -------- Exchange Netflow --------
    netflow = metrics.get("exchange_netflow", {})
    txt, bias, score = interpret_exchange_netflow(netflow.get("value", 0))
    sections.append(f"2️⃣ <b>Exchange Netflow</b>\n{txt}")
    scores.append(score)

    # -------- Exchange Reserves --------
    reserves = metrics.get("exchange_reserve", {})
    txt, bias, score = interpret_exchange_reserve(
        reserves.get("current", 0),
        reserves.get("avg_180d", 0),
    )
    sections.append(f"3️⃣ <b>Reservas em Exchanges</b>\n{txt}")
    scores.append(score)

    # -------- Whale Flows --------
    whale = metrics.get("whale_inflow", {})
    txt1, bias1, s1 = interpret_whale_inflow(
        whale.get("value_24h", 0),
        whale.get("avg_30d", 0),
    )

    ratio = metrics.get("whale_ratio", {})
    txt2, bias2, s2 = interpret_whale_ratio(ratio.get("value", 0))

    sections.append(
        "4️⃣ <b>Fluxos de Baleias</b>\n"
        f"{txt1}\n{txt2}"
    )
    scores.extend([s1, s2])

    # -------- Executive --------
    score_final = compute_score(scores)
    bias, strength = aggregate_bias(scores)
    recommendation = classify_position(score_final)

    sections.append(
        "📌 <b>Interpretação Executiva</b>\n"
        f"• Score On-Chain: {score_final}/100\n"
        f"• Viés de Mercado: {bias} ({strength})\n"
        f"• Recomendação: {recommendation}"
    )

    today = datetime.now(BRT).strftime("%d/%m/%Y")

    message = (
        f"📊 <b>Dados On-Chain BTC — {today} — Diário</b>\n\n"
        + "\n\n".join(sections)
    )

    send_telegram_message(message)

    # -------- Persist history (Opção A) --------
    history.update({
        "last_score": score_final,
        "last_recommendation": recommendation,
        "last_date": datetime.now(timezone.utc).isoformat(),
    })

    save_json(HISTORY_FILE, history)

    print("[OK] Relatório enviado. Alertas condicionais não dispararam (se aplicável).")


if __name__ == "__main__":
    main()
