# alerts_engine.py
# Detecta mudança de regime e gera alerta operacional

import json
import os

HISTORY_FILE = "history.json"

def load_last_state():
    if not os.path.exists(HISTORY_FILE):
        return None
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data[-1] if data else None


def save_current_state(state):
    data = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    data.append(state)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def detect_regime_change(current):
    last = load_last_state()
    if not last:
        save_current_state(current)
        return None  # primeiro dia, sem alerta

    alerts = []

    # 1️⃣ Recomendação
    if current["recommendation"] != last["recommendation"]:
        alerts.append(
            f"📌 Recomendação mudou: {last['recommendation']} → {current['recommendation']}"
        )

    # 2️⃣ Viés de mercado
    if current["market_bias"] != last["market_bias"]:
        alerts.append(
            f"📊 Viés de mercado mudou: {last['market_bias']} → {current['market_bias']}"
        )

    # 3️⃣ Score
    score_delta = current["score"] - last["score"]
    if abs(score_delta) >= 15:
        direction = "⬆️ aumento" if score_delta > 0 else "⬇️ queda"
        alerts.append(
            f"🎯 Score On-Chain teve {direction} de {abs(score_delta)} pontos"
        )

    save_current_state(current)

    return alerts if alerts else None
