# ==========================================================
# text_engine.py
# Motor determinístico de interpretação on-chain (FASE 6.4)
# ==========================================================

def interpret_exchange_inflow(ma7, avg_90d, percentil):
    if avg_90d == 0:
        return (
            f"O Exchange Inflow (MA7) encontra-se em {ma7:,.0f} BTC. "
            "Sem base histórica suficiente para comparação."
        ), 0

    delta = (ma7 - avg_90d) / avg_90d * 100

    if percentil <= 20:
        return (
            f"O Exchange Inflow (MA7) está significativamente abaixo da média histórica, "
            f"em {ma7:,.0f} BTC."
        ), 3

    if percentil <= 50:
        return (
            f"O Exchange Inflow (MA7) encontra-se em nível intermediário, "
            f"em {ma7:,.0f} BTC."
        ), 1

    return (
        f"O Exchange Inflow (MA7) apresenta elevação relevante, "
        f"em {ma7:,.0f} BTC."
    ), -2


def interpret_exchange_netflow(value):
    if value < 0:
        return (
            f"O Exchange Netflow registra saída líquida de aproximadamente "
            f"{abs(value):,.0f} BTC das exchanges."
        ), 2

    return (
        f"O Exchange Netflow registra entrada líquida de aproximadamente "
        f"{value:,.0f} BTC nas exchanges."
    ), -2


def interpret_exchange_reserve(current, avg_180d):
    if avg_180d == 0:
        return (
            f"As reservas em exchanges seguem em {current:,.0f} BTC. "
            "Sem base histórica suficiente para comparação."
        ), 0

    delta = (current - avg_180d) / avg_180d * 100

    if delta < -10:
        return (
            f"As reservas em exchanges seguem em {current:,.0f} BTC, "
            "abaixo da média histórica, indicando redução de oferta."
        ), 3

    if delta < 0:
        return (
            f"As reservas em exchanges seguem levemente abaixo da média histórica, "
            f"em {current:,.0f} BTC."
        ), 1

    return (
        f"As reservas em exchanges encontram-se acima da média histórica, "
        f"em {current:,.0f} BTC."
    ), -2


def interpret_whale_inflow(value_24h, avg_30d):
    if avg_30d == 0:
        return (
            f"Os depósitos de baleias somaram cerca de {value_24h:,.0f} BTC nas últimas 24h."
        ), 0

    if value_24h > avg_30d * 1.5:
        return (
            f"Os depósitos de baleias somaram cerca de {value_24h:,.0f} BTC nas últimas 24h, "
            "acima da média."
        ), -2

    return (
        f"Os depósitos de baleias somaram cerca de {value_24h:,.0f} BTC nas últimas 24h."
    ), 1


def interpret_whale_ratio(value):
    if value >= 0.85:
        return f"O Whale Ratio encontra-se em {value:.2f}, em nível elevado.", -1
    if value >= 0.6:
        return f"O Whale Ratio encontra-se em {value:.2f}, em nível moderado.", 0
    return f"O Whale Ratio encontra-se em {value:.2f}, em faixa baixa.", 1


def compute_score(scores):
    base = 50 + sum(scores) * 5
    return max(0, min(100, base))


def aggregate_bias(scores):
    total = sum(scores)

    if total >= 6:
        return "Altista", "Forte"
    if total >= 3:
        return "Altista", "Moderada"
    if total <= -6:
        return "Baixista", "Forte"
    if total <= -3:
        return "Baixista", "Moderada"

    return "Neutro", "Fraca"


def classify_position(score):
    if score >= 75:
        return "Acumular"
    if score >= 50:
        return "Manter"
    return "Reduzir"
