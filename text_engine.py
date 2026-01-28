# text_engine.py
# Motor determinístico de interpretação on-chain
# 100% gratuito, auditável e sem IA


# ================= INTERPRETAÇÕES INDIVIDUAIS ================= #

def interpret_exchange_inflow(ma7, avg_90d, percentil):
    delta = (ma7 - avg_90d) / avg_90d * 100

    if percentil <= 10:
        bias = "altista"
        score = 2
        text = (
            f"O Exchange Inflow (MA7) permanece em patamar extremamente baixo, em {ma7:,.0f} BTC, "
            f"aproximadamente {abs(delta):.0f}% abaixo da média de 90 dias, indicando ausência "
            "relevante de pressão vendedora e ambiente favorável à acumulação."
        )

    elif percentil <= 40:
        bias = "levemente altista"
        score = 1
        text = (
            f"O Exchange Inflow (MA7) encontra-se em nível moderadamente baixo, em {ma7:,.0f} BTC, "
            "sugerindo pressão vendedora controlada no curto prazo."
        )

    elif percentil <= 70:
        bias = "neutro"
        score = 0
        text = (
            f"O Exchange Inflow (MA7) está em patamar neutro, em {ma7:,.0f} BTC, próximo à média histórica, "
            "sem sinais claros de acumulação ou distribuição."
        )

    else:
        bias = "baixista"
        score = -2
        text = (
            f"O Exchange Inflow (MA7) apresenta elevação relevante, em {ma7:,.0f} BTC, acima da média histórica, "
            "indicando aumento da pressão vendedora no curto prazo."
        )

    return text, bias, score


def interpret_exchange_netflow(value):
    if abs(value) < 500:
        bias = "neutro"
        score = 0
        text = (
            "O Exchange Netflow permanece próximo do equilíbrio, indicando ambiente de consolidação "
            "e ausência de pressão direcional relevante."
        )

    elif value < 0:
        bias = "altista"
        score = 1
        text = (
            f"O Exchange Netflow apresenta saída líquida de aproximadamente {value:,.0f} BTC, indicando "
            "retirada de ativos das exchanges e redução da oferta disponível para venda."
        )

    else:
        bias = "baixista"
        score = -1
        text = (
            f"O Exchange Netflow mostra entrada líquida de aproximadamente {value:,.0f} BTC, sinalizando "
            "potencial aumento de oferta e risco de pressão vendedora."
        )

    return text, bias, score


def interpret_exchange_reserve(current, avg_180d):
    delta = (current - avg_180d) / avg_180d * 100

    if delta < -20:
        bias = "fortemente altista"
        score = 3
        text = (
            f"As reservas em exchanges estão em {current:,.0f} BTC, cerca de {abs(delta):.0f}% abaixo da média de 180 dias, "
            "indicando redução estrutural de oferta e sinal altista de médio prazo."
        )

    elif delta < -5:
        bias = "altista"
        score = 2
        text = (
            f"As reservas em exchanges permanecem em nível reduzido, em {current:,.0f} BTC, sugerindo "
            "continuidade do processo de acumulação."
        )

    else:
        bias = "neutro"
        score = 0
        text = (
            f"As reservas em exchanges encontram-se relativamente estáveis, em {current:,.0f} BTC, sem mudanças "
            "estruturais relevantes na dinâmica de oferta."
        )

    return text, bias, score


def interpret_whale_inflow(value_24h, avg_30d):
    if value_24h < avg_30d * 0.5:
        bias = "altista"
        score = 1
        text = (
            f"Os depósitos de baleias permanecem baixos, com cerca de {value_24h:,.0f} BTC nas últimas 24 horas, "
            "indicando ausência de movimentos relevantes de distribuição."
        )

    elif value_24h > avg_30d * 1.5:
        bias = "baixista"
        score = -2
        text = (
            f"Observa-se aumento expressivo nos depósitos de baleias, com aproximadamente {value_24h:,.0f} BTC, "
            "o que pode sinalizar preparação para eventos de distribuição."
        )

    else:
        bias = "neutro"
        score = 0
        text = (
            f"Os fluxos de baleias permanecem dentro da normalidade histórica, com cerca de {value_24h:,.0f} BTC nas últimas 24 horas."
        )

    return text, bias, score


def interpret_whale_ratio(value):
    if value < 0.6:
        bias = "altista"
        score = 1
        text = (
            f"O Whale Ratio encontra-se em {value:.2f}, abaixo do nível crítico, indicando baixa dominância "
            "de grandes participantes nos depósitos recentes."
        )

    elif value < 0.85:
        bias = "neutro"
        score = 0
        text = (
            f"O Whale Ratio está em {value:.2f}, em faixa intermediária, sugerindo equilíbrio "
            "entre grandes e pequenos participantes."
        )

    else:
        bias = "baixista"
        score = -2
        text = (
            f"O Whale Ratio atingiu {value:.2f}, nível elevado historicamente, indicando forte concentração "
            "de depósitos por grandes participantes e risco de distribuição."
        )

    return text, bias, score


# ================= AGREGADORES E CLASSIFICAÇÕES ================= #

def compute_score(scores):
    """
    Score final on-chain normalizado entre 0 e 100.
    Base neutra = 50.
    """
    total = sum(scores)
    normalized = max(0, min(100, 50 + total * 10))
    return normalized


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


# ================= ALERTAS E INSTITUCIONAL ================= #

def detect_alerts(exchange_inflow_percentil, whale_ratio, whale_inflow, avg_whale):
    alerts = []

    if exchange_inflow_percentil > 70:
        alerts.append(
            "Elevação abrupta no Exchange Inflow, indicando possível aumento de pressão vendedora."
        )

    if whale_ratio > 0.85:
        alerts.append(
            "Whale Ratio em nível crítico, indicando alta concentração de depósitos por grandes participantes."
        )

    if whale_inflow > avg_whale * 1.5:
        alerts.append(
            "Depósitos de baleias acima do padrão histórico, sugerindo possível preparação para distribuição."
        )

    return alerts


def institutional_block(etf_flow_usd):
    if etf_flow_usd > 0:
        return (
            f"Os fluxos institucionais permanecem positivos, com entrada líquida estimada de "
            f"US$ {etf_flow_usd/1e6:.0f} milhões em ETFs spot de Bitcoin no último pregão, reforçando "
            "a demanda estrutural por parte de investidores institucionais."
        )
    elif etf_flow_usd < 0:
        return (
            f"Os fluxos institucionais registraram saída líquida de aproximadamente "
            f"US$ {abs(etf_flow_usd)/1e6:.0f} milhões em ETFs spot de Bitcoin, indicando redução "
            "temporária do apetite institucional."
        )
    else:
        return (
            "Os fluxos institucionais permaneceram neutros no último pregão, sem entradas ou "
            "saídas relevantes em ETFs spot de Bitcoin."
        )
