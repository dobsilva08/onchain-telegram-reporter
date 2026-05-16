# collector_unified.py
# Coleta dados de mercado reais para BTC, ETH e SOL
# Fontes 100% gratuitas: CoinGecko API (sem chave) + mempool.space (BTC on-chain)

import requests
import json
import os
from datetime import datetime, timezone

TIMEOUT = 20
HISTORY_FILE = "history.json"

ASSETS = {
      "BTC": "bitcoin",
      "ETH": "ethereum",
      "SOL": "solana"
}

# --------------------------------------------------
# UTIL
# --------------------------------------------------

def fetch_json(url, params=None, headers=None):
      r = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
      r.raise_for_status()
      return r.json()

# --------------------------------------------------
# COINGECKO - precos, volume, market cap, dominancia
# --------------------------------------------------

def fetch_market_data():
      """Busca preco, variacao 24h, volume, market cap para BTC/ETH/SOL."""
      ids = ",".join(ASSETS.values())
      url = "https://api.coingecko.com/api/v3/coins/markets"
      params = {
          "vs_currency": "usd",
          "ids": ids,
          "order": "market_cap_desc",
          "per_page": 10,
          "page": 1,
          "sparkline": "false",
          "price_change_percentage": "24h,7d"
      }
      data = fetch_json(url, params=params)
      result = {}
      for coin in data:
                symbol = coin["symbol"].upper()
                result[symbol] = {
                    "price": coin.get("current_price"),
                    "change_24h": coin.get("price_change_percentage_24h"),
                    "change_7d": coin.get("price_change_percentage_7d_in_currency"),
                    "volume_24h": coin.get("total_volume"),
                    "market_cap": coin.get("market_cap"),
                    "market_cap_rank": coin.get("market_cap_rank"),
                    "ath": coin.get("ath"),
                    "ath_change_pct": coin.get("ath_change_percentage"),
                }
            return result

def fetch_dominance():
      """Busca dominancia de mercado BTC/ETH."""
    url = "https://api.coingecko.com/api/v3/global"
    data = fetch_json(url)
    dom = data.get("data", {}).get("market_cap_percentage", {})
    return {
              "BTC": round(dom.get("btc", 0), 2),
              "ETH": round(dom.get("eth", 0), 2),
    }

# --------------------------------------------------
# MEMPOOL.SPACE - BTC on-chain gratuito
# --------------------------------------------------

def fetch_btc_onchain():
      """Busca dados on-chain reais do BTC via mempool.space."""
    result = {}

    try:
              hashrate_data = fetch_json("https://mempool.space/api/v1/mining/hashrate/1w")
              if hashrate_data and "currentHashrate" in hashrate_data:
                            result["hashrate_eh"] = round(hashrate_data["currentHashrate"] / 1e18, 2)
                            result["difficulty"] = hashrate_data.get("currentDifficulty")
    except Exception:
        result["hashrate_eh"] = None
        result["difficulty"] = None

    try:
              mempool_data = fetch_json("https://mempool.space/api/v1/mempool")
              result["mempool_count"] = mempool_data.get("count")
              result["mempool_size_mb"] = round(mempool_data.get("vsize", 0) / 1e6, 2)
except Exception:
        result["mempool_count"] = None
        result["mempool_size_mb"] = None

    try:
              fees_data = fetch_json("https://mempool.space/api/v1/fees/recommended")
              result["fee_fast"] = fees_data.get("fastestFee")
              result["fee_medium"] = fees_data.get("halfHourFee")
              result["fee_slow"] = fees_data.get("hourFee")
except Exception:
        result["fee_fast"] = None
        result["fee_medium"] = None
        result["fee_slow"] = None

    try:
              block_height = fetch_json("https://mempool.space/api/blocks/tip/height")
              result["block_height"] = block_height
except Exception:
        result["block_height"] = None

    return result

# --------------------------------------------------
# FEAR & GREED INDEX
# --------------------------------------------------

def fetch_fear_greed():
      """Busca o Fear & Greed Index atual (alternative.me)."""
      try:
                data = fetch_json("https://api.alternative.me/fng/?limit=1")
                entry = data["data"][0]
                return {
                    "value": int(entry["value"]),
                    "classification": entry["value_classification"]
                }
except Exception:
        return {"value": None, "classification": "N/A"}

# --------------------------------------------------
# COLETA COMPLETA
# --------------------------------------------------

def collect_all():
      """Coleta e consolida todos os dados."""
      date_str = datetime.now(timezone.utc).strftime("%d/%m/%Y")
      time_str = datetime.now(timezone.utc).strftime("%H:%M UTC")

    print("[1/4] Coletando dados de mercado (CoinGecko)...")
    market = fetch_market_data()

    print("[2/4] Coletando dominancia (CoinGecko)...")
    dominance = fetch_dominance()

    print("[3/4] Coletando dados on-chain BTC (mempool.space)...")
    btc_onchain = fetch_btc_onchain()

    print("[4/4] Coletando Fear & Greed Index...")
    fng = fetch_fear_greed()

    snapshot = {
              "date": date_str,
              "time": time_str,
              "market": market,
              "dominance": dominance,
              "btc_onchain": btc_onchain,
              "fear_greed": fng
    }

    with open("snapshot.json", "w", encoding="utf-8") as f:
              json.dump(snapshot, f, indent=2, ensure_ascii=False)

    print(f"[OK] Snapshot salvo - {date_str} {time_str}")
    return snapshot

# --------------------------------------------------
# HISTORICO DE ESTADO (para alertas)
# --------------------------------------------------

def load_history():
      if os.path.exists(HISTORY_FILE):
                try:
                              with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                                                data = json.load(f)
                                                return data if isinstance(data, dict) else {}
                except Exception:
                              return {}
                      return {}

  def save_history(state: dict):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                  json.dump(state, f, indent=2, ensure_ascii=False)

    if __name__ == "__main__":
          collect_all()
