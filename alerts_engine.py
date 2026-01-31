import json
import os
from datetime import datetime
from signal_engine import calculate_signal

STATE_FILE = "data/position_state.json"
HISTORY_FILE = "data/trade_history.json"

def load_state():
    if os.path.exists(STATE_FILE):
        return json.load(open(STATE_FILE, "r"))
    return {"last_signal": None}

def save_state(signal):
    state = {
        "last_signal": signal,
        "date": datetime.utcnow().isoformat()
    }
    json.dump(state, open(STATE_FILE, "w"), indent=2)

def log_trade(signal, action):
    history = []
    if os.path.exists(HISTORY_FILE):
        history = json.load(open(HISTORY_FILE, "r"))

    history.append({
        "date": datetime.utcnow().isoformat(),
        "signal": signal,
        "action": action
    })

    json.dump(history, open(HISTORY_FILE, "w"), indent=2)

def build_alert(signal, action):
    emoji = "📈" if signal == "COMPRA" else "📉"
    return (
        "🚨 BTC SIGNAL ALERT 🚨\n\n"
        f"₿ BITCOIN\n"
        f"{emoji} SINAL: {signal}\n"
        f"🔁 AÇÃO: {action}\n\n"
        f"⏰ {datetime.now().strftime('%H:%M:%S')}"
    )

def check_signal_and_alert(metrics):
    current_signal = calculate_signal(metrics)
    state = load_state()
    last_signal = state.get("last_signal")

    alerts = []

    if current_signal != last_signal:
        if last_signal == "COMPRA" and current_signal == "VENDA":
            alerts.append(build_alert("VENDA", "ZERAR POSIÇÃO"))
            log_trade("VENDA", "ZERAR")

        elif current_signal == "COMPRA":
            alerts.append(build_alert("COMPRA", "INICIAR POSIÇÃO"))
            log_trade("COMPRA", "ENTRAR")

        save_state(current_signal)

    return alerts
