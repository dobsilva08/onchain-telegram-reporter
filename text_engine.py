# ==========================================================
# TEXT ENGINE — MOTOR DETERMINÍSTICO ON-CHAIN
# ==========================================================

def interpret_exchange_inflow(current, avg, percentil=50):
    if avg == 0:
        return (
            f"O Exchange Inflow (MA7) encontra-se em nível intermediário, em {current:,.0f} BTC.",
            "neutro",
            0,
        )

    delta = (current - avg) / avg * 100

    if delta < -20:
        return (
            f"O Exchange Inflow (MA7) está significativamente abaixo da média histórica, em {current:,.0f} BTC.",
            "altista",
            2,
        )

    if delta > 20:
        return (
            f"O Exchange Inflow (MA7) apresenta elevação relevante, em {current:,.0f} BTC.",
            "baixista",
            -2,
        )

    return (
        f"O Exchange Inflow (MA7) encontra-se em nível intermediário, em {current:,.0f} BTC.",
        "neutro",
        0,
    )


def interpret_exchange_netflow(value):
    if value < 0:
        return (
            f"O Exchange Netflow registra saída líquida de aproximadamente {abs(value):,.0f} BTC das exchanges.",
            "altista",
            1,
        )

    if value > 0:
        return (
            f"O Exchange Netflow registra entrada líquida de aproximadamente {value:,.0f} BTC nas exchanges.",
            "baixista",
            -1,
        )

    return (
        "O Exchange Netflow encontra-se próximo da neutralidade.",
        "neutro",
        0,
    )


def interpret_exchange_reserve(current, avg):
    if avg == 0:
        return (
            f"As reservas em exchanges seguem em {current:,.0f} BTC.",
            "neutro",
            0,
        )

    delta = (current - avg) / avg * 100

    if delta < -5:
        return (
            f"As reservas em exchanges seguem em {current:,.0f} BTC, abaixo da média histórica, indicando redução de oferta.",
            "altista",
            2,
        )

    if delta > 5:
        return (
            f"As reservas em exchanges seguem em {current:,.0f} BTC, acima da média histórica.",
            "baixista",
            -2,
        )

    return (
        f"As reservas em exchanges seguem em {current:,.0f} BTC, próximas da média histórica.",
        "neutro",
        0,
    )


def interpret_whale_inflow(current, avg):
    if avg == 0:
        return (
            f"Os depósitos de baleias somaram cerca de {current:,.0f} BTC nas últimas 24h.",
            "neutro",
            0,
        )

    if current > avg * 1.5:
        return (
            f"Os depósitos de baleias somaram cerca de {current:,.0f} BTC nas últimas 24h.",
            "baixista",
            -2,
        )

    if current < avg * 0.7:
        return (
            f"Os depósitos de baleias somaram cerca de {current:,.0f} BTC nas últimas 24h.",
            "altista",
            1,
        )

    return (
        f"Os depósitos de baleias somaram cerca de {current:,.0f} BTC nas últimas 24h.",
        "neutro",
        0,
    )


def interpret_whale_ratio(value):
    if value >= 0.85:
        return (
            f"O Whale Ratio encontra-se em {value:.2f}, em nível elevado.",
            "baixista",
            -2,
        )

    if value <= 0.6:
        return (
            f"O Whale Ratio encontra-se em {value:.2f}, em nível moderado.",
            "altista",
            1,
        )

    return (
        f"O Whale Ratio encontra-se em {value:.2f}, em faixa intermediária.",
        "neutro",
        0,
    )


# ==========================================================
# AGREGAÇÃO
# ==========================================================

def compute_score(scores):
    return max(0, min(100, 50 + sum(scores) * 10))


def aggregate_bias(scores):
    total = sum(scores)

    if total >= 4:
        return "Altista", "Forte"
    if total >= 2:
        return "Altista", "Moderada"
    if total <= -4:
        return "Baixista", "Forte"
    if total <= -2:
        return "Baixista", "Moderada"

    return "Neutro", "Fraca"


def classify_position(score):
    if score >= 70:
        return "Acumular"
    if score >= 50:
        return "Manter"
    return "Reduzir"
