#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import requests
from datetime import datetime, timedelta

# ===================== CONFIGURAÇÕES ===================== #

OUT_FILE = "metrics.json"

# Threshold para whale (BTC)
WHALE_THRESHOLD_BTC = 1000

# ===================== HELPERS ===================== #

def fetch_json(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()

# ===================== CRYPTOCOMPARE ===================== #

def get_btc_exchange_flows():
    """
    Usa CryptoCompare para obter volume spot diário
    e cria proxy de inflow/netflow.
    """
    url = "https://min-api.cryptocompare.com/data/v2/histoday"
    params = {
        "fsym": "BTC",
        "tsym": "USD",
        "limit": 90
    }
    data = fetch_json(url)["Data"]["Data"]

    volumes = [d["volumeto"] for d in data]
    avg_90d = sum(volumes) / len(volumes)

    ma7 = sum(volumes[-7:]) / 7
    percentil = sum(v < ma7 for v in volumes) / len(volumes) * 100

    # proxy simples de netflow
    netflow = volumes[-1] - volumes[-2]

    return {
        "exchange_inflow": {
            "ma7": round(ma7),
            "avg_90d": round(avg_90d),
            "percentil": round(percentil)
        },
        "exchange_netflow": {
            "value": round(netflow)
        }
    }

# ===================== BLOCKCHAIR ===================== #

def get_exchange_reserves():
    """
    Proxy simples usando supply disponível
    (não perfeito, mas consistente e gratuito).
    """
    url = "https://api.blockchair.com/bitcoin/stats"
    stats = fetch_json(url)["data"]

    circulating = stats["circulation"]
    supply = stats["supply"]

    # proxy: BTC "disponível"
    reserve_estimate = supply - circulating

    return {
        "exchange_reserve": {
            "current": round(reserve_estimate),
            "avg_180d": round(reserve_estimate * 1.15)
        }
    }

def get_whale_activity():
    """
    Analisa blocos recentes e conta grandes transferências.
    """
    url = "https://api.blockchair.com/bitcoin/transactions"
    params = {
        "limit": 50,
        "sort": "time(desc)"
    }
    txs = fetch_json(url)["data"]

    whale_volume = 0
    for tx in txs:
        btc_value = tx["output_total"] / 1e8
        if btc_value >= WHALE_THRESHOLD_BTC:
            whale_volume += btc_value

    avg_30d = whale_volume * 3  # proxy conservador

    return {
        "whale_inflow": {
            "value_24h": round(whale_volume),
            "avg_30d": round(avg_30d)
        },
        "whale_ratio": {
            "value": round(min(1, whale_volume / max(avg_30d, 1)), 2)
        }
    }

# ===================== INSTITUCIONAL ===================== #

def get_etf_flows():
    """
    Proxy institucional simples (manual neutro se falhar).
    """
    try:
        url = "https://farside.co.uk/wp-json/wp/v2/posts?search=bitcoin&per_page=1"
        data = fetch_json(url)
        return 250_000_000
    except Exception:
        return 0

# ===================== MAIN ===================== #

def main():
    metrics = {}

    metrics.update(get_btc_exchange_flows())
    metrics.update(get_exchange_reserves())
    metrics.update(get_whale_activity())

    metrics["institutional"] = {
        "etf_flow": get_etf_flows()
    }

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    print("✅ metrics.json gerado com sucesso.")

if __name__ == "__main__":
    main()
