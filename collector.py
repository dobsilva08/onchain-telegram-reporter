# collector.py
# ==========================================================
# FASE 6 — OPÇÃO A
# Coletor on-chain REAL, gratuito, sem API key
# Fonte principal: Blockchain.com (endpoint público)
# ==========================================================

import json
import os
import requests
from datetime import datetime, timezone, timedelta

# ----------------------------------------------------------
# Configurações
# ----------------------------------------------------------

METRICS_FILE = "metrics.json"
BLOCKCHAIN_LARGE_TX = (
    "https://api.blockchain.info/charts/large-transactions"
    "?timespan=7days&format=json"
)

BRT = timezone(timedelta(hours=-3))

# ----------------------------------------------------------
# Utilidades
# ----------------------------------------------------------

def log(msg):
    print(f"[collector] {msg}")

def load_previous_metrics():
    if os.path.exists(METRICS_FILE):
        try:
            with open(METRICS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_metrics(data):
    with open(METRICS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ----------------------------------------------------------
# Coleta Blockchain.com (proxy de fluxo e baleias)
# ----------------------------------------------------------

def fetch_large_transactions():
    try:
        r = requests.get(BLOCKCHAIN_LARGE_TX, timeout=15)
        r.raise_for_status()
        raw = r.json()
        return raw.get("values", [])
    except Exception as e:
        log(f"ERRO ao buscar large transactions: {e}")
        return []

# ----------------------------------------------------------
# Processamento
# ----------------------------------------------------------

def compute_metrics_from_large_txs(values):
    """
    Usa grandes transações como proxy de:
    - Exchange Inflow (MA7)
    - Whale Inflow 24h
    - Whale Ratio
    """

    if not values:
        return None

    # Ordena por data
    values = sorted(values, key=lambda x: x["x"])

    # Últimos 7 dias
    volumes = [v["y"] for v in values if v.get("y") is not None]

    if not volumes:
        return None

    # Proxy metrics
    avg_7d = sum(volumes) / len(volumes)
    last_24h = volumes[-1]

    whale_ratio = round(last_24h / avg_7d, 2) if avg_7d > 0 else 0

    # Percentil simples
    sorted_vols = sorted(volumes)
    position = sorted_vols.index(last_24h)
    percentil = int(position / len(sorted_vols) * 100)

    return {
        "exchange_inflow": {
            "ma7": int(avg_7d),
            "avg_90d": int(avg_7d),  # proxy conservador
            "percentil": percentil
        },
        "exchange_netflow": {
            # proxy: saída se inflow abaixo da média
            "value": int(-last_24h if last_24h < avg_7d else last_24h)
        },
        "exchange_reserve": {
            # placeholder seguro (fase 7 melhora)
            "current": 1_500_000,
            "avg_180d": 1_600_000
        },
        "whale_inflow": {
            "value_24h": int(last_24h),
            "avg_30d": int(avg_7d)
        },
        "whale_ratio": {
            "value": whale_ratio
        },
        "institutional": {
            "etf_flow": 0
        }
    }

# ----------------------------------------------------------
# MAIN
# ----------------------------------------------------------

def main():
    log("Iniciando coleta on-chain (FASE 6 — Opção A)")

    previous = load_previous_metrics()
    values = fetch_large_transactions()

    metrics = compute_metrics_from_large_txs(values)

    if metrics is None:
        log("Falha na coleta — usando último snapshot válido")
        if previous:
            save_metrics(previous)
            return
        else:
            log("Nenhum dado anterior disponível — abortando com zeros")
            metrics = {
                "exchange_inflow": {"ma7": 0, "avg_90d": 0, "percentil": 0},
                "exchange_netflow": {"value": 0},
                "exchange_reserve": {"current": 0, "avg_180d": 0},
                "whale_inflow": {"value_24h": 0, "avg_30d": 0},
                "whale_ratio": {"value": 0},
                "institutional": {"etf_flow": 0}
            }

    save_metrics(metrics)
    log("metrics.json gerado com sucesso")

if __name__ == "__main__":
    main()
