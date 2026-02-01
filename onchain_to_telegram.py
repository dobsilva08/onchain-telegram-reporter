import json
from datetime import datetime
from text_engine import (
    compute_weighted_score,
    classify_regime,
    decide_recommendation,
    stabilize_state
)
from telegram_utils import send_message  # você já tem isso funcionando

HISTORY_FILE = "history.json"
METRICS_FILE = "metrics.json"


def load_history():
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_history(score, regime, recommendation, reason):
    data = {
        "last_score": score,
        "last_regime": regime,
        "last_recommendation": recommendation,
        "last_change_reason": reason,
        "last_date": datetime.utcnow().isoformat()
    }
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)


def main():
    with open(METRICS_FILE, "r") as f:
        metrics = json.load(f)

    # Scores normalizados já calculados antes
    scores = {
        "exchange_inflow": metrics["signals"]["exchange_inflow"],
        "exchange_netflow": metrics["signals"]["exchange_netflow"],
        "exchange_reserve": metrics["signals"]["exchange_reserve"],
        "whale_flows": metrics["signals"]["whale_flows"]
    }

    raw_score = compute_weighted_score(scores)

    history = load_history()
    stabilized = stabilize_state(raw_score, history)

    final_score = stabilized["score"]
    final_regime = stabilized["regime"]
    recommendation = decide_recommendation(final_regime)

    save_history(
        final_score,
        final_regime,
        recommendation,
        stabilized["reason"]
    )

    message = f"""
📊 Dados On-Chain BTC — Diário

• Score On-Chain: {final_score}/100
• Regime: {final_regime}
• Recomendação: {recommendation}

ℹ️ {stabilized['reason']}
"""

    send_message(message)


if __name__ == "__main__":
    main()
