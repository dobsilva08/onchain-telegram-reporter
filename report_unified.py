# report_unified.py
# Gerador de relatórios premium Telegram
# BTC + ETH + SOL

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
# TEMPLATE PREMIUM
# --------------------------------------------------

def build_asset_report(symbol, data, snapshot):

    fng = snapshot.get("fear_greed", {})
    btc_onchain = snapshot.get("btc_onchain", {})
    dominance = snapshot.get("dominance", {})

    fear_value = fng.get("value")
    fear_class = fng.get("classification", "N/D")

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
        "🐋 <b>Fluxos de Baleias</b>",
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
