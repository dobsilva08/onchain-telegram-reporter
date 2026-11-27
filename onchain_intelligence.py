#!/usr/bin/env python3
"""Standalone daily BTC On-Chain Intelligence report. Does not modify the legacy pipeline."""
import os
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


def build_report(data):
    vp = data.get("valuation_profitability", {}) or {}
    liq = data.get("stablecoin_liquidity", {}) or {}
    mvrv = vp.get("mvrv_zscore")
    sopr = vp.get("sopr")
    sopr7 = vp.get("sopr_7d")
    change = liq.get("change_30d_pct")
    lines = [
        "🧭 <b>BTC — ON-CHAIN INTELLIGENCE</b>",
        f"<i>{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</i>",
        "", "━━━━━━━━━━━━━━", "📊 <b>VALUATION</b>", "",
        f"• MVRV Z-Score: <code>{mvrv if mvrv is not None else 'N/D'}</code>",
        "• Fonte: Kote Charts (API; disponibilidade depende da chave e endpoint)",
        "• Atribuição: https://kotecharts.com/c/mvrv-z-score",
        "", "━━━━━━━━━━━━━━", "💰 <b>PROFITABILITY — SOPR</b>", "",
        f"• SOPR diário: <code>{sopr if sopr is not None else 'N/D'}</code>",
        f"• SOPR média 7d: <code>{sopr7 if sopr7 is not None else 'N/D'}</code>",
        f"• Contexto: {interpret_sopr(sopr)}",
        "• Atribuição: https://kotecharts.com/c/sopr",
        "", "━━━━━━━━━━━━━━", "💧 <b>STABLECOIN LIQUIDITY</b>", "",
        f"• Oferta agregada: <code>{money(liq.get('total_usd'))}</code>",
        f"• Variação aproximada 30d: <code>{pct(change)}</code>",
        f"• Data da série: <code>{liq.get('date', 'N/D')}</code>",
        f"• Contexto: {interpret_liquidity(change)}",
        "• Fonte: DeFiLlama — API pública",
        "", "━━━━━━━━━━━━━━", "📝 <b>INTERPRETAÇÃO EXECUTIVA</b>", "",
        f"• Valuation: {'indicador disponível' if mvrv is not None else 'dados indisponíveis; sem inferência'}.",
        f"• Realização: {interpret_sopr(sopr)}",
        f"• Liquidez: {interpret_liquidity(change)}",
        "", "⚠️ <i>Indicadores são contextuais, não sinais automáticos nem recomendação financeira.</i>",
        "🤖 <i>Relatório independente via GitHub Actions.</i>",
    ]
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
    ax.annotate(f"Atual: {current_value}", (dates[-1], vals[-1]), xytext=(-60, 12),
                textcoords="offset points", color="white")
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
        ax.legend(lines + lines2, labels + labels2, loc="upper left", facecolor="#222222", labelcolor="white")
    else:
        ax.legend(loc="upper left", facecolor="#222222", labelcolor="white")

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
    message = build_report(data)
    print(message)
    vp=data.get('valuation_profitability',{}) or {}
    chart=generate_mvrv_chart(vp.get('mvrv_series'),vp.get('mvrv_zscore'))
    if chart: send_photo(chart,'📊 <b>BTC — Preço × MVRV Z-Score</b>\\nDourado: MVRV; roxo: média 365d; verde: preço BTC/USD; vermelho tracejado: zero.')
    send(message)
    print("Relatório enviado ao Telegram.")


if __name__ == "__main__":
    main()
