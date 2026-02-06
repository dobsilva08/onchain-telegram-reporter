import json
from datetime import datetime
from telegram_utils import send_message

def load_last():
    with open("history.json", "r") as f:
        return json.load(f)[-1]

def score_onchain(m):
    score = 0
    if m["exchange_netflow"] and m["exchange_netflow"] < 0:
        score += 30
    if m["exchange_reserves"]:
        score += 30
    if m["whale_ratio"] and m["whale_ratio"] < 1:
        score += 40
    return score

def main():
    data = load_last()
    m = data["metrics"]
    score = score_onchain(m)

    msg = f"""
📊 *Dados On-Chain BTC — {datetime.utcnow().strftime('%d/%m/%Y')} — Diário*

1️⃣ *Exchange Inflow*
{m['exchange_inflow']}

2️⃣ *Exchange Netflow*
{m['exchange_netflow']}

3️⃣ *Reservas em Exchanges*
{m['exchange_reserves']}

4️⃣ *Fluxos de Baleias*
Whale Ratio: {round(m['whale_ratio'],2) if m['whale_ratio'] else 'N/A'}

📌 *Interpretação Executiva*
• Score On-Chain: {score}/100
• Viés: {'Altista' if score >= 70 else 'Neutro'}
• Recomendação: {'Acumular' if score >= 70 else 'Aguardar'}
"""
    send_message(msg)

if __name__ == "__main__":
    main()
