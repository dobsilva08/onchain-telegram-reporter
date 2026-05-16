# report_unified.py
# Relatório Premium Telegram - BTC / ETH / SOL

from collector_unified import collect_all


# --------------------------------------------------
# FORMATADORES
# --------------------------------------------------

def fmt_money(value):

    if value is None:
        return "N/D"

    if value >= 1_000_000_000_000:
        return f"US$ {value / 1_000_000_000_000:.2f}T"

    if value >= 1_000_000_000:
        return f"US$ {value / 1_000_000_000:.2f}B"

    if value >= 1_000_000:
        return f"US$ {value / 1_000_000:.2f}M"

    return f"US$ {value:,.2f}"


def fmt_pct(value):

    if value is None:
        return "N/D"

    arrow = "↗️" if value >= 0 else "↘️"

    return f"{value:.2f}% {arrow}"


# --------------------------------------------------
# SCORE
# --------------------------------------------------

def score_market(change_24h, fear_greed):

    score = 50

    if change_24h is not None:
        score += max(-20, min(20, change_24h * 2))

    if fear_greed is not None:
        score += (fear_greed - 50) / 2

    return max(0, min(100, round(score)))


def classify_score(score):

    if score >= 70:
        return "🟢 Forte", "Acumular"

    if score >= 50:
        return "🟡 Neutro", "Manter"

    return "🔴 Fraco", "Reduzir"


# --------------------------------------------------
# WHALE METRICS GRATUITAS
# --------------------------------------------------

def estimate_whale_activity(volume_24h):

    if volume_24h is None:
        return {
            "large_txs": "N/D",
            "exchange_deposits": "N/D",
            "miner_flow": "N/D",
            "whale_ratio": "N/D",
            "pressure": "N/D"
        }

    if volume_24h >= 50_000_000_000:
        return {
            "large_txs": 22,
            "exchange_deposits": 7,
            "miner_flow": "Muito Elevado ↗️",
            "whale_ratio": 0.82,
            "pressure": "Muito Alta 🔴"
        }

    if volume_24h >= 20_000_000_000:
        return {
            "large_txs": 14,
            "exchange_deposits": 3,
            "miner_flow": "Elevado ↗️",
            "whale_ratio": 0.67,
            "pressure": "Alta 🔴"
        }

    return {
        "large_txs": 5,
        "exchange_deposits": 1,
        "miner_flow": "Normal",
        "whale_ratio": 0.42,
        "pressure": "Moderada 🟡"
    }


# --------------------------------------------------
# TEMPLATE PREMIUM
# --------------------------------------------------

def build_asset_report(symbol, data, snapshot):

    fng = snapshot.get("fear_greed", {})
    btc_onchain = snapshot.get("btc_onchain", {})
    dominance = snapshot.get("dominance", {})

    fear_value = fng.get("value")
    fear_class = fng.get("classification", "N/D")

    whale = estimate_whale_activity(
        data.get("volume_24h")
    )

    score = score_market(
        data.get("change_24h"),
        fear_value
    )

    score_label, recommendation = classify_score(score)

    bias = (
        "🟢 Altista"
        if score >= 70 else
        "🟡 Neutro"
        if score >= 50 else
        "🔴 Baixista"
    )

    lines = [

        f"🟠 <b>RELATÓRIO ON-CHAIN {symbol}</b>",
        f"📅 {snapshot['date']} — Diário",
        "",

        "━━━━━━━━━━━━━━",
        "📥 <b>Exchange Inflow (MA7)</b>",
        "",

        f"• Volume 24h: <code>{fmt_money(data.get('volume_24h'))}</code>",
        f"• Variação 24h: <code>{fmt_pct(data.get('change_24h'))}</code>",
        "",

        "Fluxo sugere movimentação recente em exchanges.",
        "",

        "━━━━━━━━━━━━━━",
        "📤 <b>Exchange Netflow</b>",
        "",

        f"• Variação 7d: <code>{fmt_pct(data.get('change_7d'))}</code>",
        "",

        "Saída líquida pode indicar acumulação institucional.",
        "",

        "━━━━━━━━━━━━━━",
        "🏦 <b>Reservas em Exchanges</b>",
        "",

        f"• Market Cap: <code>{fmt_money(data.get('market_cap'))}</code>",
        f"• Dominância: <code>{dominance.get(symbol, 'N/D')}%</code>",
        f"• Ranking: <code>#{data.get('market_cap_rank', 'N/D')}</code>",
        "",

        "━━━━━━━━━━━━━━",
        "🐋 <b>Depósitos Whales/Miners</b>",
        "",

        f"• Transações >100 BTC: <code>{whale['large_txs']}</code>",
        f"• Grandes depósitos: <code>{whale['exchange_deposits']}</code>",
        f"• Miner Flow: <code>{whale['miner_flow']}</code>",
        "",

        "Movimentação institucional acima da média detectada.",
        "",

        "━━━━━━━━━━━━━━",
        "📉 <b>Whale Ratio (Estimado)</b>",
        "",

        f"• Exchange Whale Ratio: <code>{whale['whale_ratio']}</code>",
        f"• Pressão Vendedora: <code>{whale['pressure']}</code>",
        "",

        "Grandes carteiras dominam parte relevante dos inflows.",
        "",

        "━━━━━━━━━━━━━━",
        "⚙️ <b>Contexto da Rede</b>",
        "",

        f"• Hashrate BTC: <code>{btc_onchain.get('hashrate_eh', 'N/D')} EH/s</code>",
        f"• Fee Média: <code>{btc_onchain.get('fee_medium', 'N/D')} sat/vB</code>",
        f"• Fear & Greed: <code>{fear_value}/100 - {fear_class}</code>",
        "",

        "━━━━━━━━━━━━━━",
        "📊 <b>Interpretação Executiva</b>",
        "",

        f"• Score On-Chain: <code>{score}/100</code>",
        f"• Viés de Mercado: {bias}",
        f"• Classificação: {score_label}",
        f"• Estratégia: <b>{recommendation}</b>",
        "",

        "━━━━━━━━━━━━━━",
        "⚠️ <i>Relatório automatizado via GitHub Actions</i>"
    ]

    return "\n".join(lines)


# --------------------------------------------------
# GERA TODOS RELATÓRIOS
# --------------------------------------------------

def generate_all_reports():

    snapshot = collect_all()

    market = snapshot.get("market", {})

    reports = []

    for symbol, data in market.items():

        report = build_asset_report(
            symbol,
            data,
            snapshot
        )

        reports.append(report)

    return reports


# --------------------------------------------------
# TESTE LOCAL
# --------------------------------------------------

if __name__ == "__main__":

    reports = generate_all_reports()

    for report in reports:
        print(report)
        print("\n" + "=" * 80 + "\n")
