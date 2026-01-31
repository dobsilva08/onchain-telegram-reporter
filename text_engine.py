# text_engine.py
# Interpretação determinística on-chain — FASE 4

# =========================
# TEXTOS INDIVIDUAIS
# =========================

def inflow_text(ma7, percentil):
    if percentil <= 20:
        return f"O Exchange Inflow (MA7) permanece baixo, em {ma7:,} BTC, indicando baixa pressão vendedora.", 2
    if percentil <= 60:
        return f"O Exchange Inflow (MA7) encontra-se em nível intermediário, em {ma7:,} BTC.", 0
    return f"O Exchange Inflow (MA7) apresenta elevação, em {ma7:,} BTC, sugerindo aumento de pressão vendedora.", -2


def netflow_text(value):
    if value < 0:
        return f"O Exchange Netflow registra saída líquida de aproximadamente {abs(value):,} BTC das exchanges.", 1
    if value > 0:
        return f"O Exchange Netflow indica entrada líquida de aproximadamente {value:,} BTC nas exchanges.", -1
    return "O Exchange Netflow permanece próximo do equilíbrio.", 0


def reserve_text(current, avg):
    if avg == 0:
        return f"As reservas em exchanges estão estimadas em {current:,} BTC.", 0

    delta = (current - avg) / avg * 100
    if delta < -5:
        return (
            f"As reservas em exchanges seguem em {current:,} BTC, abaixo da média histórica, indicando redução de oferta.",
            2
        )
    return f"As reservas em exchanges permanecem estáveis, em torno de {current:,} BTC.", 0


def whale_text(inflow, avg, ratio):
    score = 0

    if inflow > avg:
        t1 = f"Observa-se aumento nos depósitos de baleias, com {inflow:,} BTC nas últimas 24h."
        score -= 1
    else:
        t1 = f"Os depósitos de baleias somaram cerca de {inflow:,} BTC nas últimas 24h."
        score += 1

    if ratio < 0.6:
        t2 = f"O Whale Ratio está em {ratio:.2f}, indicando baixa dominância de grandes participantes."
        score += 1
    elif ratio < 0.85:
        t2 = f"O Whale Ratio encontra-se em {ratio:.2f}, em faixa intermediária."
    else:
        t2 = f"O Whale Ratio atingiu {ratio:.2f}, nível elevado historicamente."
        score -= 2

    return f"{t1} {t2}", score


# =========================
# AGREGAÇÃO
# =========================

def compute_score(scores):
    total = sum(scores)
    score = 50 + total * 10
    return max(0, min(100, score))


def classify_bias(score):
    if score >= 65:
        return "Altista"
    if score <= 35:
        return "Baixista"
    return "Neutro"


def recommendation(score):
    if score >= 70:
        return "Acumular"
    if score >= 50:
        return "Manter"
    return "Reduzir"
