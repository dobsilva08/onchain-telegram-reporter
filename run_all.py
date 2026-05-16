# run_all.py
# Orquestrador principal - coleta + relatórios + envio Telegram
# Pipeline: BTC + ETH + SOL unificados

import sys

from collector_unified import collect_all
from report_unified import generate_all_reports
from telegram_sender import send
from alerts_engine import detect_regime_change


def calc_score(btc, fng):
    score = 50 + (btc.get("change_24h") or 0) * 2
    score += (fng.get("value", 50) - 50) / 10
    return max(0, min(100, round(score)))


def calc_recommendation(score):
    if score >= 60:
        return "Acumular"
    elif score <= 40:
        return "Reduzir"
    else:
        return "Manter"


def main():
    print("[STEP 1] Coletando dados...")
    snapshot = collect_all()

    print("\n[STEP 2] Gerando relatórios...")
    reports = generate_all_reports()

    print("\n[STEP 3] Enviando relatórios ao Telegram...")
    for asset_report in reports:
        send(asset_report)

        asset_line = asset_report.split("\n")[0]
        print(f"  [OK] {asset_line} enviado")

    print("\n[STEP 4] Verificando alertas de regime...")

    market = snapshot.get("market", {})
    fng = snapshot.get("fear_greed", {})
    btc = market.get("BTC", {})

    score = calc_score(btc, fng)
    recommendation = calc_recommendation(score)

    current_state = {
        "score": score,
        "recommendation": recommendation,
        "date": snapshot["date"]
    }

    try:
        alerts = detect_regime_change(current_state)
    except Exception as e:
        print(f"[ERRO ALERTAS] {e}")
        alerts = []

    if alerts:
        print("\n[STEP 5] Enviando alertas de regime...")

        alert_header = "<b>ALERTA DE MUDANÇA DE REGIME</b>\n\n"
        alert_body = "\n".join(f"• {a}" for a in alerts)

        send(alert_header + alert_body)

        print(f"  [OK] {len(alerts)} alerta(s) enviado(s)")

    print("\n[CONCLUÍDO] Pipeline executado com sucesso!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERRO] {e}", file=sys.stderr)
        sys.exit(1)
