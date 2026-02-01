# alerts_engine.py
# Detecta mudança de regime on-chain
# Compatível com history.json em formato de estado único

import json
import os

HISTORY_FILE = "history.json"

# ==========================================================
# LOAD / SAVE STATE
# ==========================================================

def load_last_state():
    if not os.path.exists(HISTORY_FILE):
        return None

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_current_state(state):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "last_recommendation": state["recommendation"],
                "last_score": state["score"],
                "last_date": state["date"],
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

# ==========================================================
# REGIME CHANGE DETECTION
# ==========================================================

def detect_regime_change(current_state):
    alerts = []

    last_state = load_last_state()

    if last_state:
        # Mudança de recomendação
        if last_state["last_recommendation"] != current_state["recommendation"]:
            alerts.append(
                f"Recomendação mudou de <b>{last_state['last_recommendation']}</b> "
                f"para <b>{current_state['recommendation']}</b>."
            )

        # Mudança relevante de score
        delta_score = current_state["score"] - last_state["last_score"]
        if abs(delta_score) >= 15:
            direction = "aumentou" if delta_score > 0 else "caiu"
            alerts.append(
                f"Score On-Chain {direction} de "
                f"{last_state['last_score']} para {current_state['score']}."
            )

    # Sempre salva o estado atual
    save_current_state(current_state)

    return alerts
