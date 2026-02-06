import json

def block(title):
    return f"\n{title}\nDados indisponíveis hoje (fonte gratuita)\n"

def generate_onchain_report():
    with open("snapshot_onchain.json") as f:
        o = json.load(f)

    text = f"""
📊 Dados On-Chain {o['asset']} — {o['date']}

1️⃣ Exchange Inflow (MA7){block("")}
2️⃣ Exchange Netflow{block("")}
3️⃣ Reservas em Exchanges{block("")}
4️⃣ Fluxos de Baleias{block("")}

📌 Interpretação Executiva
• Status: {o['status']}
""".strip()

    return text
