# text_engine.py
# Motor determinístico on-chain (FASE 5/6)
# 100% sem IA, blindado contra zeros

# ==========================================================
# INTERPRETAÇÕES
# ==========================================================

def interpret_exchange_inflow(ma7, avg_90d, percentil):
    if avg_90d == 0:
        return (
            "O Exchange Inflow (MA7) encontra-se indisponível para comparação histórica."
        ), "neutro", 0

    if percentil <= 30:
        return (
            f"O Exchange Inflow (MA7) encontra-se em nível intermediário, em {ma7:,} BTC."
        ), "neutro", 0

    return (
        f"O Exchange Inflow (MA7) apresenta elevação relevante, em {ma7:,} BTC."
    ), "baixista", -1


def interpret_exchange_netflow(value):
    if value < 0:
        return (
            f"O Exchange Netflow registra saída líquida de aproximadamente {abs(value):,} BTC das exchanges."
        ), "altista", 1

    if value > 0:
        return (
            f"O Exchange Netflow registra entrada líquida de aproximadamente {value:,} BTC nas exchanges."
        ), "baixista", -1

    return (
        "O Exchange Netflow permanece próximo do equilíbrio."
    ), "neutro", 0


def interpret_exchange_reserve(current, avg_180d):
    if avg_180d == 0:
        return (
            f"As reservas em exchanges seguem em {current:,} BTC."
        ), "neutro", 0

    if current < avg_180d:
        return (
            f"As reservas em exchanges seguem em {current:,} BTC, abaixo da média histórica, indicando redução de oferta."
        ), "altista", 2

    return (
        f"As reservas em exchanges encontram-se estáveis, em {current:,} BTC."
    ), "neutro", 0


def interpret_whale_inflow(value_24h, avg_30d):
    if avg_30d == 0:
        return (
            f"Os depósitos de baleias somaram cerca de {value_24h:,} BTC nas últimas 24h."
        ), "neutro", 0

    return (
        f"Os depósitos de baleias somaram cerca de {value_24h:,} BTC nas últimas 24h."
    ), "neutro", 0


def interpret_whale_ratio(value):
    if value == 0:
        return (
            "O Whale Ratio não pôde ser estimado de forma confiável."
        ), "neutro", 0

    if value < 0.65:
        return (
            f"O Whale Ratio encontra-se em {value:.2f}, em faixa intermediária."
        ), "neutro", 0

    return (
        f"O Whale Ratio atingiu {value:.2f}, nível elevado historicamente."
    ), "baixista", -1


# ==========================================================
# AGREGAÇÃO
# ==========================================================

def compute_score(scores):
    return max(0, min(100, 50 + sum(scores) * 10))


def aggregate_bias(scores):
    total = sum(scores)

    if total >= 2:
        return "Altista", "Moderada"
    if total <= -2:
        return "Baixista", "Moderada"
    return "Neutro", "Fraca"


def classify_position(score):
    if score >= 70:
        return "Acumular"
    if score >= 50:
        return "Manter"
    return "Reduzir"
