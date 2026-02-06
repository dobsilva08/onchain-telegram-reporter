import json

def generate_market_report():
    with open("snapshot_market.json") as f:
        m = json.load(f)

    sign = "📈 +" if m["change_24h"] >= 0 else "📉 "
    change = f"{sign}{m['change_24h']:.2f}%"

    text = f"""
📊 Dados de Mercado {m['asset']} — {m['date']}

💰 Preço: ${m['price']:,.0f}
📈 Variação 24h: {change}
📊 Volume 24h: ${m['volume_24h']:,.0f}
🏦 Market Cap: ${m['market_cap']:,.0f}

📌 Interpretação Executiva
• Status: Operacional
""".strip()

    return text
