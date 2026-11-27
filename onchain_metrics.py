# onchain_metrics.py
"""BTC MVRV/SOPR (Kote Charts, optional key) and aggregate stablecoin liquidity (DeFiLlama)."""
import os
import requests
from datetime import datetime, timezone

TIMEOUT = 20
KOTE_BASE = "https://kotecharts.com/api/v1/public/charts"
LLAMA_BASE = "https://stablecoins.llama.fi"


def _get_json(url, params=None, headers=None):
    response = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def _kote_series(metric_id):
    key = os.getenv("KOTE_API_KEY")
    if not key:
        return None
    try:
        payload = _get_json(f"{KOTE_BASE}/{metric_id}", {"granularity": "day"}, {"X-API-Key": key})
        data = payload.get("data", payload)
        series = data.get("series", [])
        return series if isinstance(series, list) else None
    except Exception as exc:
        print(f"[ONCHAIN METRICS] Kote {metric_id} unavailable: {exc}")
        return None


def _value(point, preferred):
    for key in preferred:
        value = point.get(key) if isinstance(point, dict) else None
        if isinstance(value, (int, float)):
            return value
    if isinstance(point, dict):
        for key, value in point.items():
            if key != "t" and isinstance(value, (int, float)):
                return value
    return None


def fetch_mvrv_sopr():
    result = {"mvrv_zscore": None, "sopr": None, "sopr_7d": None, "mvrv_series": None, "source": "Kote Charts", "available": False}
    mvrv = _kote_series("mvrv-z-score")
    sopr = _kote_series("sopr")
    result["mvrv_series"] = mvrv
    if mvrv:
        result["mvrv_zscore"] = _value(mvrv[-1], ["mvrvZ", "zscore", "zScore", "value"])
        result["mvrv_date"] = mvrv[-1].get("t")
    if sopr:
        vals = [_value(p, ["sopr", "value", "ratio"]) for p in sopr[-7:]]
        vals = [v for v in vals if isinstance(v, (int, float))]
        result["sopr"] = _value(sopr[-1], ["sopr", "value", "ratio"])
        result["sopr_date"] = sopr[-1].get("t")
        if vals:
            result["sopr_7d"] = sum(vals) / len(vals)
    result["available"] = result["mvrv_zscore"] is not None or result["sopr"] is not None
    return result


def _aggregate_circulating(value):
    """DeFiLlama historical rows expose circulating supply as a per-coin mapping."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        numeric = [float(v) for v in value.values() if isinstance(v, (int, float))]
        return sum(numeric) if numeric else None
    return None


def fetch_stablecoin_liquidity():
    result = {"total_usd": None, "change_30d_pct": None, "source": "DeFiLlama", "available": False}
    try:
        series = _get_json(f"{LLAMA_BASE}/stablecoincharts/all")
        if not isinstance(series, list) or len(series) < 2:
            return result
        latest = series[-1]
        latest_ts = latest.get("date")
        latest_val = _aggregate_circulating(latest.get("totalCirculating"))
        if latest_val is None:
            return result
        prior = None
        if isinstance(latest_ts, (int, float)):
            target = latest_ts - 30 * 86400
            prior = min(series, key=lambda p: abs(p.get("date", 0) - target))
        elif len(series) >= 31:
            prior = series[-31]
        prior_val = _aggregate_circulating(prior.get("totalCirculating")) if prior else None
        result["total_usd"] = latest_val
        if isinstance(prior_val, (int, float)) and prior_val:
            result["change_30d_pct"] = (latest_val / prior_val - 1) * 100
        result["date"] = datetime.fromtimestamp(latest_ts, tz=timezone.utc).strftime("%Y-%m-%d") if isinstance(latest_ts, (int, float)) else None
        result["available"] = True
    except Exception as exc:
        print(f"[ONCHAIN METRICS] Stablecoin data unavailable: {exc}")
    return result


def collect_new_metrics():
    return {"valuation_profitability": fetch_mvrv_sopr(), "stablecoin_liquidity": fetch_stablecoin_liquidity()}
