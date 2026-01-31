# text_engine.py
# Interpretação determinística on-chain — FASE 3

def inflow_text(ma7, percentil):
    if percentil <= 20:
        return f"O Exchange Inflow (MA7) permanece baixo, em {ma7:,} BTC, indicando baixa pressão vendedora."
    if percentil <= 60:
        return f"O Exchange Inflow (MA7) encontra-se em nível intermediário, em {ma7:,} BTC."
    return f"O Exchange Inflow (MA7) apresenta elevação, em {ma7:,} BTC, sugerindo aumento de pressão vendedora."


def netflow_text(value):
    if value < 0:
        return f"O Exchange Netflow registra saída líquida de aproximadamente {abs(value):,} BTC das exchanges."
    if value > 0:
        return f"O Exchange Netflow indica entrada líquida de aproximadamente {value:,} BTC nas exchanges."
    return "O Exchange Netflow permanece próximo do equilíbrio."


def reserve_text(current, avg):
    if avg == 0:
        return f"As reservas em exchanges estão estimadas em {current:,} BTC."
    delta = (current - avg) / avg * 100
    if delta < -5:
        return f"As reservas em exchanges seguem em {current:,} BTC, abaixo da média histórica, indicando redução de oferta."
    return f"As reservas em exchanges permanecem estáveis, em torno de {current:,} BTC."


def whale_text(inflow, avg, ratio):
    t1 = (
        f"Os depósitos de baleias somaram cerca de {inflow:,} BTC nas últimas 24h."
        if inflow < avg else
        f"Observa-se aumento nos depósitos de baleias, com {inflow:,} BTC nas últimas 24h."
    )

    if ratio < 0.6:
        t2 = f"O Whale Ratio está em {ratio:.2f}, indicando baixa dominância de grandes participantes."
    elif ratio < 0.85:
        t2 = f"O Whale Ratio encontra-se em {ratio:.2f}, em faixa intermediária."
    else:
        t2 = f"O Whale Ratio atingiu {ratio:.2f}, nível elevado historicamente."

    return t1 + " " + t2

