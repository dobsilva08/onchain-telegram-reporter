# text_engine.py
# Motor determinístico de interpretação on-chain
# Blindado contra dados ausentes / zero
# 100% sem IA, sem API externa

# ==========================================================
# INTERPRETAÇÕES INDIVIDUAIS
# ==========================================================

def interpret_exchange_inflow(ma7, avg_90d, percentil):
    if avg_90d == 0:
        return (
            "O Exchange Inflow (MA7) encontra-se indisponível para comparação histórica no momento. "
            "A leitura permanece neutra por ausência de base estatística confiável."
        ), "neutro", 0

    delta = (ma7 - avg_90d) / avg_90d * 100

    if percentil <= 10:
        return (
            f"O Exchange Inflow (MA7) permanece extremamente baixo, em {ma7:,.0f} BTC, cerca de "
            f"{abs(delta):.0f}% abaixo da média de 90 dias, indicando baixa pressão vendedora "
            "e ambiente favorável à acumulação."
        ), "altista", 2

    elif percentil <= 40:
        return (
            f"O Exchange Inflow (MA7) está em nível moderadamente baixo, em {ma7:,.0f} BTC, "
            "sugerindo pressão vendedora controlada."
        ), "levemente altista", 1

    elif percentil <= 70:
        return (
            f"O Exchange Inflow (MA7) encontra-se em patamar neutro, em {ma7:,.0f} BTC, "
            "próximo à média histórica."
        ), "neutro", 0

    else:
        return (
            f"O Exchange Inflow (MA7) apresenta elevação relevante, em {ma7:,.0f} BTC, "
            "indicando possível aumento de pressão vendedora."
        ), "baixista", -2


def interpret_exchange_netflow(value):
    if value == 0:
        return (
            "O Exchange Netflow permanece próximo do equilíbrio, indicando ausência de fluxo direcional relevante."
        ), "neutro", 0

    if value < 0:
        return (
            f"O Exchange Netflow apresenta saída líquida de aproximadamente {value:,.0f} BTC, "
            "indicando retirada de ativos das exchanges."
        ), "altista", 1

    return (
        f"O Exchange Netflow registra entrada líquida de aproximadamente {value:,.0f} BTC, "
        "sinalizando potencial aumento de oferta."
    ), "baixista", -1


def interpret_exchange_reserve(current, avg_180d):
    # 🔒 Proteção crítica
    if avg_180d == 0:
        return (
            f"As reservas em exchanges estão estimadas em {current:,.0f} BTC. "
            "Não foi possível calcular a variação histórica devido à indisponibilidade "
            "de dados médios confiáveis. A leitura permanece neutra."
        ), "neutro", 0

    delta = (current - avg_180d) / avg_180d * 100

    if delta < -20:
        return (
            f"As reservas em exchanges estão em {current:,.0f} BTC, cerca de {abs(delta):.0f}% "
            "abaixo da média de 180 dias, indicando redução estrutural da oferta."
        ), "fortemente altista", 3

    elif delta < -5:
        return (
            f"As reservas em exchanges permanecem em nível reduzido, em {current:,.0f} BTC, "
            "sugerindo continuidade do processo de acumulação."
        ), "altista", 2

    else:
        return (
            f"As reservas em exchanges encontram-se relativamente estáveis, em {current:,.0f} BTC."
        ), "neutro", 0


def interpret_whale_inflow(value_24h, avg_30d):
    if avg_30d == 0:
        return (
            f"Os fluxos de baleias somaram aproximadamente {value_24h:,.0f} BTC nas últimas 24 horas. "
            "Sem base histórica suficiente para comparação, a leitura permanece neutra."
        ), "neutro", 0

    if value_24h < avg_30d * 0.5:
        return (
            f"Os depósitos de baleias permanecem baixos, com cerca de {value_24h:,.0f} BTC nas últimas 24 horas."
        ), "altista", 1

    if value_24h > avg_30d * 1.5:
        return (
            f"Observa-se aumento expressivo nos depósitos de baleias, totalizando {value_24h:,.0f} BTC."
        ), "baixista", -2

    return (
        f"Os fluxos de baleias permanecem dentro da normalidade histórica, com cerca de {value_24h:,.0f} BTC."
    ), "neutro", 0


def interpret_whale_ratio(value):
    if value == 0:
        return (
            "O Whale Ratio não pôde ser estimado de forma confiável no período analisado."
        ), "neutro", 0

    if value < 0.6:
        return (
            f"O Whale Ratio está em {value:.2f}, abaixo do nível crítico, indicando baixa dominância de grandes participantes."
        ), "altista", 1

    if value < 0.85:
        return (
            f"O Whale Ratio encontra-se em {value:.2f}, em faixa intermediária."
        ), "neutro", 0

    return (
        f"O Whale Ratio atingiu {value:.2f}, nível elevado historicamente, indicando concentração de depósitos por baleias."
    ), "baixista", -2


# ==========================================================
# AGREGAÇÃO E CLASSIFICAÇÃO
# ==========================================================

def compute_score(scores):
    total = sum(scores)
    return max(0, min(100, 50 + total * 10))


def aggregate_bias(scores):
    total = sum(scores)

    if total >= 5:
        return "Altista", "Forte"
    elif total >= 2:
        return "Altista", "Moderada"
    elif total <= -5:
        return "Baixista", "Forte"
    elif total <= -2:
        return "Baixista", "Moderada"
    else:
        return "Neutro", "Fraca"


def classify_position(score):
    if score >= 70:
        return "Acumular"
    elif score >= 50:
        return "Manter"
    else:
        return "Reduzir"


# ==========================================================
# ALERTAS E CONTEXTO INSTITUCIONAL
# ==========================================================

def detect_alerts(exchange_inflow_percentil, whale_ratio, whale_inflow, avg_whale):
    alerts = []

    if exchange_inflow_percentil > 70:
        alerts.append("Elevação relevante no Exchange Inflow, sugerindo aumento de pressão vendedora.")

    if whale_ratio > 0.85:
        alerts.append("Whale Ratio em nível crítico, indicando concentração de depósitos por grandes participantes.")

    if avg_whale > 0 and whale_inflow > avg_whale * 1.5:
        alerts.append("Depósitos de baleias acima do padrão histórico, sugerindo possível distribuição.")

    return alerts


def institutional_block(etf_flow_usd):
    if etf_flow_usd > 0:
        return (
            f"Os fluxos institucionais foram positivos, com entrada estimada de "
            f"US$ {etf_flow_usd/1e6:.0f} milhões em ETFs spot de Bitcoin."
        )

    if etf_flow_usd < 0:
        return (
            f"Os fluxos institucionais registraram saída estimada de "
            f"US$ {abs(etf_flow_usd)/1e6:.0f} milhões em ETFs spot de Bitcoin."
        )

    return (
        "Os fluxos institucionais permaneceram neutros no período analisado."
    )
