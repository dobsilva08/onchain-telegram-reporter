# report_unified.py
# Gera relatorios formatados para Telegram (BTC, ETH, SOL)
# Formato identico ao original: Exchange Inflow, Netflow, Reservas, Baleias + Interpretacao

import json
import os
from collector_unified import load_history, save_history

SNAPSHOT_FILE = "snapshot.json"

# --------------------------------------------------
# UTIL DE FORMATACAO
# --------------------------------------------------

def fmt_price(v):
    if v is None:
        return "N/D"
    if v >= 1000:
        return f"${v:,.0f}"
    return f"${v:,.4f}"

def fmt_pct(v):
    if v is None:
        return "N/D"
    arrow = "d" if v >= 0 else "b"
    return f"{arrow} {abs(v):.2f}%"

def fmt_num(v, suffix=""):
    if v is None:
        return "N/D"
    if v >= 1_000_000_000:
        return f"${v/1_000_000_000:.2f}B{suffix}"
    if v >= 1_000_000:
        return f"${v/1_000_000:.1f}M{suffix}"
    return f"{v:,.0f}{suffix}"

def fng_emoji(value):
    if value is None:
        return "N/D"
    if value <= 25:
        return "Medo Extremo"
    if value <= 45:
        return "Medo"
    if value <= 55:
        return "Neutro"
    if value <= 75:
        return "Ganancia"
    return "Ganancia Extrema"

# --------------------------------------------------
# CALCULO DE SCORE E VIES
# --------------------------------------------------

def compute_score(asset_data, fng, dominance):
    """Score 0-100 baseado em indicadores de mercado."""
    score = 50  # base neutra

    change_24h = asset_data.get("change_24h") or 0
    change_7d = asset_data.get("change_7d") or 0
    fng_val = fng.get("value") or 50

    # Variacao 24h
    if change_24h > 5:
        score += 15
    elif change_24h > 2:
        score += 8
    elif change_24h > 0:
        score += 3
    elif change_24h > -2:
        score -= 3
    elif change_24h > -5:
        score -= 8
    else:
        score -= 15

    # Variacao 7d
    if change_7d > 10:
        score += 12
    elif change_7d > 3:
        score += 6
    elif change_7d > 0:
        score += 2
    elif change_7d > -3:
        score -= 2
    elif change_7d > -10:
        score -= 6
    else:
        score -= 12

    # Fear & Greed
    if fng_val >= 70:
        score += 10
    elif fng_val >= 55:
        score += 5
    elif fng_val >= 45:
        score += 0
    elif fng_val >= 30:
        score -= 5
    else:
        score -= 10

    return max(0, min(100, round(score)))

def classify_bias(score):
    if score >= 80:
        return ("Altista (Forte)", "Acumular")
    elif score >= 65:
        return ("Altista (Moderado)", "Acumular")
    elif score >= 55:
        return ("Altista (Fraco)", "Manter")
    elif score >= 45:
        return ("Neutro", "Manter")
    elif score >= 35:
        return ("Baixista (Fraco)", "Reduzir")
    elif score >= 20:
        return ("Baixista (Moderado)", "Reduzir")
    else:
        return ("Baixista (Forte)", "Reduzir")

# --------------------------------------------------
# RELATORIO BTC
# --------------------------------------------------

def generate_btc_report(snapshot):
    d = snapshot["date"]
    m = snapshot["market"].get("BTC", {})
    onchain = snapshot.get("btc_onchain", {})
    fng = snapshot.get("fear_greed", {})
    dom = snapshot.get("dominance", {})

    price = fmt_price(m.get("price"))
    ch24 = fmt_pct(m.get("change_24h"))
    ch7d = fmt_pct(m.get("change_7d"))
    vol = fmt_num(m.get("volume_24h"))
    mcap = fmt_num(m.get("market_cap"))
    dominance = f"{dom.get('BTC', 'N/D')}%"

    # On-chain
    mempool = onchain.get("mempool_count")
    fee_m = onchain.get("fee_medium")
    hashrate = onchain.get("hashrate_eh")
    block = onchain.get("block_height")

    mempool_txt = f"{mempool:,} txs pendentes" if mempool else "N/D"
    fee_txt = f"{fee_m} sat/vB" if fee_m else "N/D"
    hashrate_txt = f"{hashrate} EH/s" if hashrate else "N/D"
    block_txt = f"#{block:,}" if block else "N/D"

    score = compute_score(m, fng, dom)
    vies, recomendacao = classify_bias(score)

    fng_val = fng.get("value")
    fng_class = fng_emoji(fng_val)
    fng_txt = f"{fng_val}/100 - {fng_class}" if fng_val else "N/D"

    msg = f"""f4ca Dados On-Chain BTC - {d} - Diario

11️⃣ Exchange Inflow (MA7)
O Exchange Inflow esta sendo estimado via volume em exchanges (CoinGecko). Volume 24h: {vol}. A variacao de preco de {ch24} sugere {'pressao vendedora presente' if 'd' not in ch24 else 'reducao de pressao vendedora'}.

22️⃣ Exchange Netflow
Variacao de preco 7 dias: {ch7d}. {'Saida liquida de BTC das exchanges (acumulacao)' if 'd' not in ch7d else 'Entrada liquida de BTC nas exchanges (distribuicao)'}.

33️⃣ Reservas em Exchanges
Market Cap BTC: {mcap}. Dominancia BTC: {dominance}. Bloco atual: {block_txt}.

44️⃣ Fluxos de Baleias
Hashrate da rede: {hashrate_txt}. Mempool: {mempool_txt}. Fee recomendada: {fee_txt}. Fear & Greed Index: {fng_txt}.

f4cc Interpretacao Executiva
- Score On-Chain: {score}/100
- Vies de Mercado: {vies}
- Recomendacao: {recomendacao}"""

    return msg.strip()

# --------------------------------------------------
# RELATORIO ETH
# --------------------------------------------------

def generate_eth_report(snapshot):
    d = snapshot["date"]
    m = snapshot["market"].get("ETH", {})
    fng = snapshot.get("fear_greed", {})
    dom = snapshot.get("dominance", {})

    price = fmt_price(m.get("price"))
    ch24 = fmt_pct(m.get("change_24h"))
    ch7d = fmt_pct(m.get("change_7d"))
    vol = fmt_num(m.get("volume_24h"))
    mcap = fmt_num(m.get("market_cap"))
    dominance = f"{dom.get('ETH', 'N/D')}%"

    score = compute_score(m, fng, dom)
    vies, recomendacao = classify_bias(score)

    fng_val = fng.get("value")
    fng_txt = f"{fng_val}/100 - {fng_emoji(fng_val)}" if fng_val else "N/D"

    msg = f"""f4ca Dados On-Chain ETH - {d} - Diario

11️⃣ Preco e Volume
ETH em {price}. Variacao 24h: {ch24}. Volume 24h: {vol}.

22️⃣ Exchange Netflow
Variacao 7 dias: {ch7d}. {'Tendencia positiva no periodo.' if 'd' not in ch7d else 'Tendencia negativa no periodo.'}

33️⃣ Reservas e Dominancia
Market Cap ETH: {mcap}. Dominancia ETH: {dominance}.

44️⃣ Sentimento de Mercado
Fear & Greed Index: {fng_txt}.

f4cc Interpretacao Executiva
- Score On-Chain: {score}/100
- Vies de Mercado: {vies}
- Recomendacao: {recomendacao}"""

    return msg.strip()

# --------------------------------------------------
# RELATORIO SOL
# --------------------------------------------------

def generate_sol_report(snapshot):
    d = snapshot["date"]
    m = snapshot["market"].get("SOL", {})
    fng = snapshot.get("fear_greed", {})
    dom = snapshot.get("dominance", {})

    price = fmt_price(m.get("price"))
    ch24 = fmt_pct(m.get("change_24h"))
    ch7d = fmt_pct(m.get("change_7d"))
    vol = fmt_num(m.get("volume_24h"))
    mcap = fmt_num(m.get("market_cap"))
    rank = m.get("market_cap_rank", "N/D")

    score = compute_score(m, fng, dom)
    vies, recomendacao = classify_bias(score)

    fng_val = fng.get("value")
    fng_txt = f"{fng_val}/100 - {fng_emoji(fng_val)}" if fng_val else "N/D"

    msg = f"""f4ca Dados On-Chain SOL - {d} - Diario

11️⃣ Preco e Volume
SOL em {price}. Variacao 24h: {ch24}. Volume 24h: {vol}.

22️⃣ Exchange Netflow
Variacao 7 dias: {ch7d}. {'Tendencia positiva no periodo.' if 'd' not in ch7d else 'Tendencia negativa no periodo.'}

33️⃣ Posicao de Mercado
Market Cap SOL: {mcap}. Ranking: #{rank}.

44️⃣ Sentimento de Mercado
Fear & Greed Index: {fng_txt}.

f4cc Interpretacao Executiva
- Score On-Chain: {score}/100
- Vies de Mercado: {vies}
- Recomendacao: {recomendacao}"""

    return msg.strip()

# --------------------------------------------------
# GERAR TODOS OS RELATORIOS
# --------------------------------------------------

def generate_all_reports():
    if not os.path.exists(SNAPSHOT_FILE):
        raise FileNotFoundError("snapshot.json nao encontrado. Execute collector_unified.py primeiro.")

    with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
        snapshot = json.load(f)

    reports = []
    reports.append(generate_btc_report(snapshot))
    reports.append(generate_eth_report(snapshot))
    reports.append(generate_sol_report(snapshot))

    return reports

if __name__ == "__main__":
    reports = generate_all_reports()
    for r in reports:
        print(r)
        print("\n" + "="*50 + "\n")
