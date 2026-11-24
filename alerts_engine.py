# alerts_engine.py
# Detecta mudança de regime on-chain, com recuperação de histórico inválido.
import json
import os

HISTORY_FILE = "history.json"


def load_last_state():
    if not os.path.exists(HISTORY_FILE):
        return None
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and {"last_recommendation", "last_score"} <= set(data):
            return data
        print("[AVISO ALERTAS] Histórico inválido ou incompleto; estado anterior ignorado.")
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[AVISO ALERTAS] Não foi possível ler histórico: {exc}")
    return None


def save_current_state(state):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"last_recommendation": state["recommendation"], "last_score": state["score"], "last_date": state["date"]},
            f, indent=2, ensure_ascii=False,
        )


def detect_regime_change(current_state):
    alerts = []
    last_state = load_last_state()
    if last_state:
        if last_state["last_recommendation"] != current_state["recommendation"]:
            alerts.append(f"Recomendação mudou de <b>{last_state['last_recommendation']}</b> para <b>{current_state['recommendation']}</b>.")
        try:
            delta_score = current_state["score"] - last_state["last_score"]
            if abs(delta_score) >= 15:
                direction = "aumentou" if delta_score > 0 else "caiu"
                alerts.append(f"Score On-Chain {direction} de {last_state['last_score']} para {current_state['score']}.")
        except (TypeError, KeyError):
            print("[AVISO ALERTAS] Score anterior inválido; comparação ignorada.")
    save_current_state(current_state)
    return alerts
