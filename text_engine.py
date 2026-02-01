# ==========================================================
# text_engine.py
# Motor determinístico de interpretação on-chain
# Sem IA | Sem API externa | Estável | Versionado
# ==========================================================

# ==========================================================
# INTERPRETAÇÕES INDIVIDUAIS
# ==========================================================

def interpret_exchange_inflow(ma7, avg_90d, percentil):
    if avg_90d == 0:
        return (
            f"O Exchange Inflow (MA7) encontra-se em {ma7:,.0f} BTC. "
            "Sem base histórica suficiente para comparação percentual."
        ), 0

    delta = (ma7 - avg_90d) / avg_90d * 100

    if percentil <= 20:
        return (
            f"O Exchange Inflow (MA7) está significativamente abaixo da média histórica, "
            f"em {ma7:,.0f} BTC ({delta:.1f}%)."
        ), 3

    if percentil <= 50:
        return (
            f"O Exchange Inflow (MA7) encontra-se em nível intermediário, "
            f"em {ma7:,.0f} BTC ({delta:.1f}%)."
        ), 1

    return (
        f"O Exchange Inflow (MA7) apresenta elevação relevante, "
        f"em {ma7:,.0f} BTC ({delta:.1f}%)."
    ), -2


def interpret_exchange_netflow(value, avg_30d):
    if avg_30d == 0:
        return (
            f"O Exchange Netflow registra saída líquida de aproximadamente "
            f"{abs(value):,.0f} BTC das exchanges. "
            "Sem base histórica suficiente para comparação percentual."
        ), 0

    delta = (value - avg_30d) / abs(avg_30d) * 100

    if value < 0:
        return (
            f"O Exchange Netflow registra saída líquida de aproximadamente "
            f"{abs(value):,.0f} BTC das exchanges ({delta:.1f}%)."
        ), 2

    return (
        f"O Exchange Netflow registra entrada líquida de aproximadamente "
        f"{value:,.0f} BTC nas exchanges ({delta:.1f}%)."
    ), -2


def interpret_exchange_reserve(current, avg_180d):
    if avg_180d == 0:
        return (
            f"As reservas em exchanges seguem em {current:,.0f} BTC. "
            "Sem base histórica suficiente para comparação percentual."
        ), 0

    delta = (current - avg_180d) / avg_180d * 100

    if delta < -10:
        return (
            f"As reservas em exchanges seguem em {current:,.0f} BTC, "
            f"{delta:.1f}% abaixo da média histórica, indicando redução de oferta."
        ), 3

    if delta < 0:
        return (
            f"As reservas em exchanges seguem levemente abaixo da média histórica, "
            f"em {current:,.0f} BTC ({delta:.1f}%)."
        ), 1

    return (
        f"As reservas em exchanges encontram-se acima da média histórica, "
        f"em {current:,.0f} BTC ({delta:.1f}%)."
    ), -2


def interpret_whale_flows(value_24h, avg_30d, whale_ratio):
    text = []

    if avg_30d == 0:
        text.append(
            f"Os depósitos de baleias somaram cerca de {value_24h:,.0f} BTC nas últimas 24h. "
            "Sem base histórica suficiente para comparação percentual."
        )
        score = 0
    else:
        delta = (value_24h - avg_30d) / avg_30d * 100

        if value_24h > avg_30d * 1.5:
            text.append(
                f"Os depósitos de baleias somaram cerca de {value_24h:,.0f} BTC nas últimas 24h "
                f"({delta:.1f}% acima da média)."
            )
            score = -2
        else:
            text.append(
                f"Os depósitos de baleias somaram cerca de {value_24h:,.0f} BTC nas últimas 24h "
                f"({delta:.1f}% em relação à média)."
            )
            score = 1

    # Whale Ratio
    if whale_ratio >= 0.85:
        text.append(f"O Whale Ratio encontra-se em {whale_ratio:.2f}, em nível elevado.")
        score -= 1
    elif whale_ratio >= 0.6:
        text.append(f"O Whale Ratio encontra-se em {whale_ratio:.2f}, em nível moderado.")
    else:
        text.append(f"O Whale Ratio encontra-se em {whale_ratio:.2f}, em faixa baixa.")
        score += 1

    return " ".join(text), score


# ==========================================================
# SCORE, REGIME E RECOMENDAÇÃO — FASE 6.5
# ==========================================================

def compute_weighted_score(signals):
    weights = {
        "exchange_inflow": 0.30,
        "exchange_netflow": 0.25,
        "exchange_reserve": 0.25,
        "whale_flows": 0.20
    }

    total = 0
    for key, weight in weights.items():
        total += signals.get(key, 0) * weight * 20

    score = int(50 + total)
    return max(0, min(100, score))


def classify_regime(score):
    if score >= 85:
        return "Altista Forte"
    if score >= 70:
        return "Altista Moderado"
    if score >= 45:
        return "Neutro"
    if score >= 30:
        return "Baixista Moderado"
    return "Baixista Forte"


def decide_recommendation(regime):
    if regime in ("Altista Forte", "Altista Moderado"):
        return "Acumular"
    if regime == "Neutro":
        return "Manter"
    return "Reduzir"


def stabilize_state(new_score, last_state):
    last_score = last_state.get("last_score", new_score)
    last_regime = last_state.get("last_regime", classify_regime(new_score))

    delta = abs(new_score - last_score)

    if delta <= 5:
        return {
            "score": last_score,
            "regime": last_regime,
            "changed": False,
            "reason": "Zona de tolerância (≤5 pontos)"
        }

    new_regime = classify_regime(new_score)

    if new_regime == last_regime:
        return {
            "score": new_score,
            "regime": last_regime,
            "changed": False,
            "reason": "Score variou sem mudança de regime"
        }

    return {
        "score": new_score,
        "regime": new_regime,
        "changed": True,
        "reason": f"Mudança de regime: {last_regime} → {new_regime}"
    }
