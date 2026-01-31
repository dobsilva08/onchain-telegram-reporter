# alerts_engine.py
from signal_engine import calculate_signal

def check_signal_and_alert(score, bias, last_signal=None):
    signal = calculate_signal(score, bias)

    alert = None
    if last_signal and signal != last_signal:
        alert = f"🔄 Mudança de posição detectada: {last_signal} → {signal}"

    return signal, alert
