# Motor determinístico on-chain
# Fase 6.5 — Comparação percentual vs média histórica

def percent_vs_avg(current, avg):
    if avg is None or avg == 0:
        return None
    return (current - avg) / avg * 100


def format_percent(pct):
    if pct is None:
        return ""
    direction = "acima" if pct > 0 else "abaixo"
    return f", {abs(pct):.0f}% {direction} da média de 30 dias"


def interpret_exchange_inflow(ma7, avg_30d):
    pct = percent_vs_avg(ma7, avg_30d)
    suffix = format_percent(pct)

    return (
        f"O Exchange Inflow (MA7) encontra-se em nível intermediário, em {ma7:,.0f} BTC{suffix}."
    ), 0


def interpret_exchange_netflow(value, avg_30d):
    pct = percent_vs_avg(abs(value), avg_30d)
    suffix = format_percent(pct)

    if value < 0:
        return (
            f"O Exchange Netflow registra saída líquida de aproximadamente {abs(value):,.0f} BTC das exchanges{suffix}."
        ), 1

    return (
        f"O Exchange Netflow registra entrada líquida de aproximadamente {value:,.0f} BTC nas exchanges{suffix}."
    ), -1


def interpret_exchange_reserve(current, avg_30d):
    pct = percent_vs_avg(current, avg_30d)
    suffix = format_percent(pct)

    return (
        f"As reservas em exchanges seguem em {current:,.0f} BTC, abaixo da média histórica{suffix}, indicando redução de oferta."
    ), 1


def interpret_whale_flows(value_24h, avg_30d, whale_ratio):
    pct = percent_vs_avg(value_24h, avg_30d)
    suffix = format_percent(pct)

    text = (
        f"Os depósitos de baleias somaram cerca de {value_24h:,.0f} BTC nas últimas 24h{suffix}.\n"
        f"O Whale Ratio encontra-se em {whale_ratio:.2f}, em faixa intermediária."
    )

    score = 0
    if whale_ratio > 0.85:
        score = -2
    elif whale_ratio < 0.6:
        score = 1

    return text, score
