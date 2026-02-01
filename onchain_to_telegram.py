import os
import json
import requests
from datetime import datetime

# =========================
# CONFIGURAÇÃO TELEGRAM
# =========================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    raise RuntimeError("Variáveis TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID não definidas")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"


# =========================
# FUNÇÃO ENVIO TELEGRAM
# =========================
def send_telegram_message(text: str):
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }

    r = requests.post(TELEGRAM_API_URL, json=payload, timeout=30)
    r.raise_for_status()


# =========================
# FUNÇÕES AUXILIARES
# =========================
def load_json(path: str, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_value(metrics: dict, key: str):
    """
    Extrai metrics[key]['value'] com fallback seguro
    """
    try:
        return metrics.get(key, {}).get("value", "N/A")
    except Exception:
        return "N/A"


# =========================
# MAIN
# =========================
def main():
    metrics = load_json("metrics.json", {})
    history = load_json("history.json", {})

    # =========================
    # COLETA MÉTRICAS
    # =========================
    exchange_inflow_ma7 = get_value(metrics, "exchange_inflow_ma7")
    exchange_netflow = get_value(metrics, "exchange_netflow")
    exchange_reserves = get_value(metrics, "exchange_reserves")
    whale_inflow_24h = get_value(metrics, "whale_inflow_24h")
    whale_ratio = get_value(metrics, "whale_ratio")

    # =========================
    # INTERPRETAÇÃO SIMPLES
    # =========================
    score = 0
    bias = "Neutro"
    recommendation = "Aguardar"

    if isinstance(exchange_netflow, (int, float)) and exchange_netflow < 0:
        score += 30

    if isinstance(exchange_reserves, (int, float)):
        score += 30

    if isinstance(whale_ratio, (int, float)):
        if whale_ratio < 0.6:
            score += 40

    if score >= 80:
        bias = "Altista (Forte)"
        recommendation = "Acumular"
    elif score >= 60:
        bias = "Altista (Moderada)"
        recommendation = "Acumular"
    else:
        bias = "Neutro"
        recommendation = "Aguardar"

    # =========================
    # MENSAGEM
    # =========================
    today = datetime.utcnow().strftime("%d/%m/%Y")

    message = f"""📊 *Dados On-Chain BTC — {today} — Diário*

1️⃣ *Exchange Inflow (MA7)*
{exchange_inflow_ma7 if exchange_inflow_ma7 != "N/A" else "N/A"}

2️⃣ *Exchange Netflow*
{exchange_netflow if exchange_netflow != "N/A" else "N/A"}

3️⃣ *Reservas em Exchanges*
{exchange_reserves if exchange_reserves != "N/A" else "N/A"}

4️⃣ *Fluxos de Baleias*
Depósitos: {whale_inflow_24h if whale_inflow_24h != "N/A" else "N/A"}
Whale Ratio: {whale_ratio if whale_ratio != "N/A" else "N/A"}

📌 *Interpretação Executiva*
• Score On-Chain: {score}/100
• Viés de Mercado: {bias}
• Recomendação: {recommendation}
"""

    # =========================
    # ENVIO TELEGRAM
    # =========================
    send_telegram_message(message)

    # =========================
    # SALVA HISTÓRICO
    # =========================
    history.update({
        "last_score": score,
        "last_recommendation": recommendation,
        "last_date": datetime.utcnow().isoformat()
    })

    with open("history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


# =========================
# ENTRYPOINT
# =========================
if __name__ == "__main__":
    main()
