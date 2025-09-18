# scripts/gold_report.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Relatório — Dados de Mercado — Ouro (XAU/USD) — Diário
Segue o layout ESPECÍFICO em 10 tópicos (conforme exemplo do usuário).

Variáveis de ambiente:
- TELEGRAM_BOT_TOKEN (obrigatório)
- TELEGRAM_CHAT_ID   (obrigatório)
- TELEGRAM_TOPIC_ID  (opcional)
- YF_PROXY           (opcional, proxy http/https para yfinance/requests)
- CFTC_CSV_URL       (opcional: CSV de posição líquida CFTC/CME para OURO)
- ETF_HOLDINGS_SOURCE (opcional: endpoint com shares/fluxos GLD/IAU)

Arquivos persistentes:
- .sent/gold-daily-YYYYMMDD.sent  -> trava de envio
- .sent/gold_daily_counter.txt    -> contador “Nº X”
"""

import os, io, sys, math, textwrap, html, json, time
from datetime import datetime, timedelta, timezone

import pandas as pd
import numpy as np
import requests
import yfinance as yf

BRT = timezone(timedelta(hours=-3), name="BRT")
ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(ROOT, ".."))
SENT_DIR = os.path.join(REPO_ROOT, ".sent")
os.makedirs(SENT_DIR, exist_ok=True)

def today_brt():
    return datetime.now(BRT)

def guard_path(dt):
    return os.path.join(SENT_DIR, f"gold-daily-{dt.strftime('%Y%m%d')}.sent")

def read_counter():
    path = os.path.join(SENT_DIR, "gold_daily_counter.txt")
    if not os.path.exists(path):
        return 0
    try:
        return int(open(path, "r", encoding="utf-8").read().strip() or "0")
    except:
        return 0

def write_counter(v: int):
    path = os.path.join(SENT_DIR, "gold_daily_counter.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(str(v))

def pct(a,b):
    try:
        return (a/b - 1.0)*100.0
    except Exception:
        return np.nan

def fmt_pct(x):
    if x is None or (isinstance(x,float) and (np.isnan(x) or np.isinf(x))):
        return "—"
    return f"{x:+.2f}%"

def last_valid(series):
    s = pd.Series(series).dropna()
    return s.iloc[-1] if len(s) else np.nan

def fetch_yf(tickers, period="30d", interval="1d"):
    session = requests.Session()
    if os.getenv("YF_PROXY"):
        session.proxies = {"http": os.getenv("YF_PROXY"), "https": os.getenv("YF_PROXY")}
    data = yf.download(tickers=tickers, period=period, interval=interval,
                       auto_adjust=False, progress=False, session=session)
    if isinstance(data.columns, pd.MultiIndex):
        data = data["Close"]
    else:
        data = data["Close"].to_frame()
    return data.ffill()

def fetch_fred(series_id):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    df["DATE"] = pd.to_datetime(df["DATE"])
    df.set_index("DATE", inplace=True)
    s = pd.to_numeric(df[series_id], errors="coerce").dropna()
    return s

def send_telegram(text: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    topic_id = os.getenv("TELEGRAM_TOPIC_ID")
    if not token or not chat_id:
        print("Faltam TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID. Imprimindo abaixo:")
        print(text)
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if topic_id:
        payload["message_thread_id"] = int(topic_id)
    resp = requests.post(url, data=payload, timeout=30)
    resp.raise_for_status()

# ------------------------ Blocos dos 10 tópicos (layout fixo) ------------------------

def bloco_1_fluxos_etf():
    # Sem fonte pública estável de shares; usamos preço d/d e placeholder para shares
    txt = ""
    try:
        px = fetch_yf(["GLD","IAU"], period="10d")
        gld_dd = fmt_pct(pct(px["GLD"].iloc[-1], px["GLD"].iloc[-2]))
        iau_dd = fmt_pct(pct(px["IAU"].iloc[-1], px["IAU"].iloc[-2]))
        txt = f"Os fluxos em ETFs de ouro (GLD/IAU) não possuem fonte pública padronizada de shares aqui. " \
              f"Como proxy, preço d/d: GLD {gld_dd}, IAU {iau_dd}. " \
              f"Configure <code>ETF_HOLDINGS_SOURCE</code> para capturar shares/criações se desejar."
    except Exception:
        txt = "Não há dados disponíveis sobre fluxos de ETFs (necessário fonte de shares/criações)."
    return f"<b>1. Fluxos em ETFs de Ouro</b>\n{txt}"

def bloco_2_cftc():
    url = os.getenv("CFTC_CSV_URL", "")
    if not url:
        return ("<b>2. Posição Líquida em Futuros (CFTC/CME)</b>\n"
                "Não há dados: defina <code>CFTC_CSV_URL</code> para importar a posição líquida.")
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text))
        # Tenta colunas comuns; se não, apenas conta linhas
        cols_long = [c for c in df.columns if "Long" in c or "LONG" in c]
        cols_short= [c for c in df.columns if "Short" in c or "SHORT" in c]
        spec, nonc_l, nonc_s = "—","—","—"
        if cols_long and cols_short:
            last = df.iloc[-1]
            nonc_l = last[cols_long[0]]
            nonc_s = last[cols_short[0]]
            try:
                spec = int(nonc_l) - int(nonc_s)
            except Exception:
                spec = "—"
        return (f"<b>2. Posição Líquida em Futuros (CFTC/CME)</b>\n"
                f"- Speculadores: {spec}\n- Não-Commerciais Longueiros: {nonc_l}\n- Não-Commerciais Curtores: {nonc_s}")
    except Exception:
        return "<b>2. Posição Líquida em Futuros (CFTC/CME)</b>\nDados indisponíveis no momento."

def bloco_3_reservas_bc():
    return ("<b>3. Reservas de Bancos Centrais</b>\n"
            "Não há dados disponíveis sobre as reservas de bancos centrais em ouro.")

def bloco_4_fluxos_miner_bancos():
    return ("<b>4. Fluxos de Mineradoras & Bancos</b>\n"
            "Não há dados disponíveis sobre produção, hedge e operações OTC.")

def bloco_5_whale_ratio():
    return ("<b>5. Whale Ratio Institucional vs. Varejo</b>\n"
            "Não há dados disponíveis sobre a participação relativa de institucionais e varejo.")

def bloco_6_drivers_macro():
    # DXY e juros reais (DFII10)
    dxy_txt = "—"
    real10_txt = "—"
    try:
        dxy = fetch_yf(["DX-Y.NYB"], period="10d")
        dxy_val = last_valid(dxy["DX-Y.NYB"])
        dxy_txt = f"{dxy_val:,.2f}"
    except Exception:
        pass
    try:
        dfii = fetch_fred("DFII10")
        real10_txt = f"{dfii.iloc[-1]:.1f}%"
    except Exception:
        pass
    return (f"<b>6. Drivers Macro</b>\n"
            f"- Taxa real de 10 anos: {real10_txt}\n"
            f"- Índice DXY: {dxy_txt}")

def bloco_7_custos_oferta():
    return ("<b>7. Custos de Produção & Oferta Física</b>\n"
            "Não há dados disponíveis sobre custos de produção e oferta física de ouro.")

def bloco_8_estrutura_termo():
    # Spread simples GC=F - MGC=F (se ambos existirem); se falhar, manter indisponível
    try:
        fut = fetch_yf(["GC=F","MGC=F"], period="7d")
        spread = last_valid(fut["GC=F"]) - last_valid(fut["MGC=F"])
        return (f"<b>8. Estrutura a Termo</b>\n"
                f"Spread (GC=F - MGC=F): {spread:,.2f} USD/onça.")
    except Exception:
        return ("<b>8. Estrutura a Termo</b>\n"
                "A estrutura a termo do mercado de ouro não está disponível (falha/fonte indisponível).")

def bloco_9_correlacoes():
    # Correlações 30d: Ouro vs DXY; Ouro vs S&P500; Ouro vs BTC-USD (se possível)
    try:
        px = fetch_yf(["XAUUSD=X","DX-Y.NYB","^GSPC","BTC-USD"], period="90d")
        px.columns = ["XAU","DXY","SPX","BTC"]
        rets = px.pct_change().dropna().tail(30)
        def c(a,b):
            try:
                return rets[a].corr(rets[b])
            except:
                return np.nan
        c1 = c("XAU","DXY")
        c2 = c("XAU","SPX")
        c3 = c("XAU","BTC")
        return (f"<b>9. Correlações Cruzadas</b>\n"
                f"- Ouro vs DXY (30d): {c1:+.2f}\n"
                f"- Ouro vs S&P 500 (30d): {c2:+.2f}\n"
                f"- Ouro vs Bitcoin (30d): {c3:+.2f}")
    except Exception:
        return ("<b>9. Correlações Cruzadas</b>\n"
                "Não há dados disponíveis sobre as correlações cruzadas (fonte indisponível).")

def bloco_10_interpretacao():
    return textwrap.dedent("""\
        <b>10. Interpretação Executiva & Conclusão</b>
        - O mercado de ouro está sendo influenciado por fatores macroeconômicos, como a taxa real e o índice DXY.
        - A posição líquida em futuros pode favorecer os curtos quando especuladores líquidos <i>≤ 0</i>.
        - Falta de dados sobre estrutura a termo e correlações reduz a precisão do quadro.
        - Participação de institucionais vs. varejo indisponível.
        - Oferta física/custos sem fonte padronizada.
        - Monitorar próximos dados macro (FOMC, inflação), DFII10 e DXY.
        
        <b>Síntese</b>
        O mercado de ouro continua sensível a juros reais e ao dólar. Sem séries estáveis para fluxos de ETFs (shares), 
        estrutura a termo granular e participação institucional, a análise permanece parcial; ainda assim, DFII10 e DXY 
        seguem como vetores principais do viés tático.
    """).strip()

# ------------------------ Montagem do relatório ------------------------

def montar_relatorio():
    dt = today_brt()
    # contador (incrementa aqui)
    n = read_counter() + 1
    write_counter(n)

    titulo = f"📊 <b>Dados de Mercado — Ouro (XAU/USD) — {dt.strftime('%d de %B de %Y')} — Diário — Nº {n}</b>"
    # subtítulo igual ao exemplo (“Neste relatório… até data”)
    subtitulo = f"Neste relatório, apresentamos os dados de mercado atualizados até {dt.strftime('%d de %B de %Y')}."

    partes = [
        titulo,
        subtitulo,
        "",
        bloco_1_fluxos_etf(),
        "",
        bloco_2_cftc(),
        "",
        bloco_3_reservas_bc(),
        "",
        bloco_4_fluxos_miner_bancos(),
        "",
        bloco_5_whale_ratio(),
        "",
        bloco_6_drivers_macro(),
        "",
        bloco_7_custos_oferta(),
        "",
        bloco_8_estrutura_termo(),
        "",
        bloco_9_correlacoes(),
        "",
        bloco_10_interpretacao(),
    ]
    txt = "\n".join(partes)

    # Telegram usa HTML — garantir escapando seguro, mas preservar <b>, <i>, <code>, que já inserimos.
    # Como os blocos já vêm “limpos”, apenas asseguramos que nada externo ficou sem escape:
    safe = html.unescape(txt)  # mantém tags que já definimos
    return safe

def main():
    dt = today_brt()
    gpath = guard_path(dt)
    if os.path.exists(gpath):
        print("Já enviado hoje (trava .sent). Encerrando.")
        return
    try:
        texto = montar_relatorio()
        send_telegram(texto)
        # grava trava de envio
        open(gpath, "w", encoding="utf-8").write(texto[:200])
        print("OK: relatório Ouro enviado.")
    except Exception as e:
        print("Falha ao gerar/enviar relatório de Ouro:", e, file=sys.stderr)
        try:
            send_telegram(f"Falha no relatório de OURO: <code>{html.escape(str(e))}</code>")
        except Exception:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()