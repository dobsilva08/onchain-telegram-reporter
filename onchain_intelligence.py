#!/usr/bin/env python3
"""Standalone daily BTC On-Chain Intelligence report. Does not modify the legacy pipeline."""
import os
import json
import tempfile
import requests
import matplotlib.pyplot as plt
from telegram_sender import send_photo
from datetime import datetime, timezone
from onchain_metrics import collect_new_metrics
from telegram_sender import send


def money(v):
    if not isinstance(v, (int, float)):
        return "N/D"
    if v >= 1e12: return f"US$ {v/1e12:.2f}T"
    if v >= 1e9: return f"US$ {v/1e9:.2f}B"
    if v >= 1e6: return f"US$ {v/1e6:.2f}M"
    return f"US$ {v:,.0f}"


def pct(v):
    return "N/D" if not isinstance(v, (int, float)) else f"{v:+.2f}%"


def interpret_sopr(v):
    if not isinstance(v, (int, float)): return "Dados indisponíveis."
    if v > 1: return "Moedas movimentadas, em agregado, realizadas com lucro."
    if v < 1: return "Moedas movimentadas, em agregado, realizadas com prejuízo."
    return "Equilíbrio aproximado entre lucro e prejuízo realizado."


def interpret_liquidity(v):
    if not isinstance(v, (int, float)): return "Variação indisponível."
    if v > 0: return "Oferta agregada em expansão."
    if v < 0: return "Oferta agregada em retração."
    return "Oferta agregada estável."


def fmt(v, digits=3):
    return "N/D" if not isinstance(v, (int, float)) else f"{v:.{digits}f}"

def load_history():
    path="onchain_intelligence_history.json"
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_history(data, history):
    vp=data.get("valuation_profitability", {}) or {}
    liq=data.get("stablecoin_liquidity", {}) or {}
    entry={"date":datetime.now(timezone.utc).strftime("%Y-%m-%d"),
           "mvrv":vp.get("mvrv_zscore"),"sopr":vp.get("sopr"),"sopr7":vp.get("sopr_7d"),
           "stablecoins":liq.get("total_usd"),"stable_change":liq.get("change_30d_pct")}
    history.append(entry)
    # Keep a rolling history and avoid duplicate entries for the same UTC date.
    history=[h for h in history if h.get("date") != entry["date"]]
    history.append(entry)
    history=history[-365:]
    with open("onchain_intelligence_history.json","w",encoding="utf-8") as f:
        json.dump(history,f,ensure_ascii=False,indent=2)
    return history

def delta_text(current, previous, label, digits=3):
    if not isinstance(current,(int,float)) or not isinstance(previous,(int,float)):
        return f"{label}: comparação anterior indisponível."
    change=current-previous
    return f"{label}: {previous:.{digits}f} → {current:.{digits}f} ({change:+.{digits}f})."

def interpret_mvrv(v):
    if not isinstance(v,(int,float)): return "Dados indisponíveis; não é possível avaliar valuation."
    if v < 0: return "Z-Score negativo: valuation abaixo da referência histórica calculada; pode refletir estresse, mas não confirma fundo."
    if v < 1: return "Faixa relativamente moderada/baixa frente aos extremos históricos; não indica euforia isoladamente."
    if v < 3: return "Valuation em faixa intermediária; observar tendência e demais indicadores."
    return "Valuation elevado frente ao histórico; risco de aquecimento aumenta, sem ser sinal automático de topo."

def sopr_context(v):
    if not isinstance(v,(int,float)): return "Dados indisponíveis."
    if v < 1: return "SOPR abaixo de 1 indica realização agregada de moedas movimentadas com prejuízo."
    if v > 1: return "SOPR acima de 1 indica realização agregada de moedas movimentadas com lucro."
    return "SOPR próximo de 1 indica equilíbrio entre lucro e prejuízo realizado."

def build_report(data, history):
    vp=data.get("valuation_profitability",{}) or {}
    liq=data.get("stablecoin_liquidity",{}) or {}
    mvrv=vp.get("mvrv_zscore"); sopr=vp.get("sopr"); sopr7=vp.get("sopr_7d")
    change=liq.get("change_30d_pct"); total=liq.get("total_usd")
    prev=next((h for h in reversed(history[:-1]) if h.get("date") != history[-1].get("date")),None) if history else None
    # prior record is the last available record before today's appended snapshot
    if history and len(history)>=2: prev=history[-2]
    lines=["🧭 <b>BTC — ON-CHAIN INTELLIGENCE</b>",f"<i>{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</i>",
    "", "━━━━━━━━━━━━━━","📊 <b>VALUATION — MVRV Z-SCORE</b>","",
    f"• Atual: <code>{fmt(mvrv)}</code>",
    f"• Comparação: {delta_text(mvrv,prev.get('mvrv') if prev else None,'MVRV')}",
    f"• Interpretação: {interpret_mvrv(mvrv)}",
    "", "━━━━━━━━━━━━━━","💰 <b>PROFITABILITY — SOPR</b>","",
    f"• SOPR diário: <code>{fmt(sopr,6)}</code>",
    f"• Média 7d: <code>{fmt(sopr7,6)}</code>",
    f"• Comparação diária: {delta_text(sopr,prev.get('sopr') if prev else None,'SOPR',6)}",
    f"• Contexto diário: {sopr_context(sopr)}",
    f"• Contexto média 7d: {sopr_context(sopr7)}",
    "", "━━━━━━━━━━━━━━","💧 <b>STABLECOIN LIQUIDITY</b>","",
    f"• Oferta agregada: <code>{money(total)}</code>",
    f"• Variação aproximada 30d: <code>{pct(change)}</code>",
    f"• Data da série: <code>{liq.get('date') or 'N/D'}</code>",
    f"• Comparação: {delta_text(total,prev.get('stablecoins') if prev else None,'Oferta stablecoins',2)}",
    f"• Interpretação: {interpret_liquidity(change)}",
    "", "━━━━━━━━━━━━━━","🧠 <b>ANÁLISE CRUZADA</b>",""]
    # rule-based joint interpretation
    if isinstance(mvrv,(int,float)) and isinstance(sopr7,(int,float)) and isinstance(change,(int,float)):
        if mvrv < 1 and sopr7 < 1 and change < 0:
            joint="Valuation moderado/baixo, realização semanal com prejuízo e oferta de stablecoins em retração. Contexto cauteloso; pode ser estresse ou acumulação, sem confirmação."
        elif mvrv < 1 and sopr7 < 1:
            joint="Valuation moderado/baixo junto de realização com prejuízo. Acompanhar recuperação do SOPR e evolução da liquidez."
        elif sopr7 > 1 and change > 0:
            joint="Realização semanal com lucro e oferta de stablecoins em expansão; combinação potencialmente mais favorável, mas exige confirmação de preço e fluxo."
        elif change < 0:
            joint="Oferta de stablecoins em retração é fator de cautela; SOPR e valuation devem ser acompanhados para confirmação."
        else:
            joint="Indicadores apresentam sinais mistos; não há confirmação direcional forte."
    else:
        joint="Dados incompletos para análise cruzada robusta."
    lines.append("• "+joint)
    lines.extend(["","━━━━━━━━━━━━━━","🔮 <b>CENÁRIOS CONDICIONAIS</b>","",
    "• <b>Bullish:</b> SOPR sustenta acima de 1, liquidez estabiliza/expande e preço confirma melhora.",
    "• <b>Neutro:</b> métricas oscilam sem convergência; mercado permanece em consolidação.",
    "• <b>Bearish:</b> SOPR permanece abaixo de 1, liquidez continua contraindo e preço perde suportes relevantes.",
    "• Cenários são condicionais, não previsões nem sinais automáticos.",
    "", "━━━━━━━━━━━━━━","🎯 <b>CONCLUSÃO EXECUTIVA</b>","",
    f"• Valuation: {interpret_mvrv(mvrv)}",
    f"• Realização: {sopr_context(sopr7)}",
    f"• Liquidez: {interpret_liquidity(change)}",
    "", "⚠️ <i>Indicadores são contextuais, não sinais automáticos nem recomendação financeira.</i>",
    "🤖 <i>Relatório independente via GitHub Actions.</i>"])
    return "\n".join(lines)




def generate_mvrv_chart(series, current_value):
    if not isinstance(series, list) or len(series) < 2:
        return None
    points = []
    for p in series:
        if not isinstance(p, dict):
            continue
        v = p.get("value", p.get("zscore", p.get("zScore", p.get("mvrvZ"))))
        t = p.get("t", p.get("timestamp", p.get("date")))
        if isinstance(v, (int, float)) and t is not None:
            try:
                if isinstance(t, (int, float)):
                    dt = datetime.fromtimestamp(t / 1000 if t > 1e11 else t, tz=timezone.utc)
                else:
                    dt = datetime.fromisoformat(str(t).replace("Z", "+00:00"))
                points.append((dt, float(v)))
            except Exception:
                continue
    if len(points) < 2:
        return None
    points.sort(key=lambda x: x[0])
    dates = [x[0] for x in points]
    vals = [x[1] for x in points]

    # Best-effort public BTC/USD history; chart remains useful if price API is unavailable.
    price_dates, prices = [], []
    try:
        payload = requests.get(
            "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
            params={"vs_currency": "usd", "days": "max", "interval": "daily"},
            timeout=20,
        )
        payload.raise_for_status()
        price_data = payload.json().get("prices", [])
        price_dates = [datetime.fromtimestamp(p[0] / 1000, tz=timezone.utc) for p in price_data if len(p) >= 2]
        prices = [p[1] for p in price_data if len(p) >= 2]
        if not prices:
            raise ValueError("CoinGecko returned no price points")
    except Exception as exc:
        print(f"[CHART] CoinGecko unavailable; trying Blockchain.info: {exc}")
        try:
            fallback = requests.get(
                "https://api.blockchain.info/charts/market-price",
                params={"timespan": "all", "format": "json"},
                timeout=20,
            )
            fallback.raise_for_status()
            price_data = fallback.json().get("values", [])
            price_dates = [datetime.fromtimestamp(p["x"], tz=timezone.utc) for p in price_data if "x" in p and "y" in p]
            prices = [p["y"] for p in price_data if "x" in p and "y" in p]
        except Exception as fallback_exc:
            print(f"[CHART] BTC price history unavailable from fallback: {fallback_exc}")

    fig, ax = plt.subplots(figsize=(11, 5), facecolor="#111111")
    ax.set_facecolor("#111111")
    ax.plot(dates, vals, color="#D4AF37", linewidth=1.8, label="MVRV Z-Score")
    # 365-day rolling mean of MVRV.
    if len(vals) >= 365:
        rolling = [None] * 364
        rolling.extend([sum(vals[i-364:i+1]) / 365 for i in range(364, len(vals))])
        ax.plot(dates, rolling, color="#A78BFA", linewidth=1.4, label="Média móvel 365d")
    ax.axhline(0, color="red", linestyle="--", linewidth=1.5, label="Referência 0")
    ax.scatter([dates[-1]], [vals[-1]], color="white", s=45, zorder=4)
    ax.set_ylim(-5, 10)
    ax.set_ylabel("MVRV Z-Score", color="#D4AF37")
    ax.tick_params(axis="y", colors="#D4AF37")
    ax.grid(alpha=.2)
    for sp in ax.spines.values():
        sp.set_color("#555555")

    if price_dates and prices:
        ax2 = ax.twinx()
        ax2.plot(price_dates, prices, color="#14B8A6", linewidth=1.3, alpha=.9, label="Preço BTC/USD")
        ax2.set_yscale("log")
        ax2.set_ylabel("Preço BTC (USD, escala log)", color="#14B8A6")
        ax2.tick_params(axis="y", colors="#14B8A6")
        for sp in ax2.spines.values():
            sp.set_color("#555555")
        lines, labels = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines + lines2, labels + labels2, loc="upper left", bbox_to_anchor=(0, 0.90), facecolor="#222222", labelcolor="white")
    else:
        ax.legend(loc="upper left", bbox_to_anchor=(0, 0.90), facecolor="#222222", labelcolor="white")

    ax.text(0.015, 0.985, f"MVRV Atual: {float(current_value):.3f}" if isinstance(current_value, (int, float)) else f"MVRV Atual: {current_value}", transform=ax.transAxes, va="top", ha="left", color="#D4AF37", fontsize=12, fontweight="bold", bbox=dict(boxstyle="round,pad=0.35", facecolor="#222222", edgecolor="#D4AF37", alpha=0.95))
    ax.set_title("Bitcoin — Preço BTC/USD × MVRV Z-Score", color="white")
    ax.tick_params(axis="x", colors="white")
    fig.autofmt_xdate()
    plt.tight_layout()
    path = os.path.join(tempfile.gettempdir(), "mvrv_chart.png")
    plt.savefig(path, dpi=160)
    plt.close(fig)
    return path


def main():
    print("Coletando indicadores independentes...")
    data = collect_new_metrics()
    history=load_history()
    history=save_history(data,history)
    message = build_report(data,history)
    print(message)
    vp=data.get('valuation_profitability',{}) or {}
    chart=generate_mvrv_chart(vp.get('mvrv_series'),vp.get('mvrv_zscore'))
    if chart: send_photo(chart,'📊 <b>BTC — Preço × MVRV Z-Score</b>')
    send(message)
    print("Relatório enviado ao Telegram.")


if __name__ == "__main__":
    main()
