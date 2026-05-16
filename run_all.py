# run_all.py - Orquestrador unificado BTC+ETH+SOL
import sys
from collector_unified import collect_all
from report_unified import generate_all_reports
from alerts_engine import detect_regime_change
from telegram_sender import send

def _score(m, fng):
        s = 50 + min(15, max(-15, (m.get("change_24h") or 0) * 2))
        s += ((fng.get("value") or 50) - 50) / 10
        return max(0, min(100, round(s)))

def _rec(m, fng):
        s = _score(m, fng)
        return "Acumular" if s >= 60 else ("Manter" if s >= 40 else "Reduzir")

def main():
        print("== CRYPTO REPORTER INICIANDO ==")
        snapshot = collect_all()
        reports = generate_all_reports()
        btc = snapshot["market"].get("BTC", {})
        fng = snapshot.get("fear_greed", {})
        state = {"date": snapshot["date"], "score": _score(btc, fng), "recommendation": _rec(btc, fng)}
        try:
                    alerts = detect_regime_change(state)
except Exception:
        alerts = []
    for r in reports:
                send(r)
            if alerts:
                        send("<b>ALERTA</b>\n\n" + "\n".join(f"- {a}" for a in alerts))
                    print("== CONCLUIDO ==")

if __name__ == "__main__":
        try:
                    main()
except Exception as e:
        print(f"[ERRO] {e}", file=sys.stderr)
        sys.exit(1)# run_all.py
# Orquestrador principal - coleta + relatorios + envio Telegram
# Pipeline: BTC + ETH + SOL unificados

import sys
from collector_unified import collect_all
from report_unified import generate_all_reports
from telegram_sender import send
from alerts_engine import detect_regime_change

def main():
        print("[STEP 1] Coletando dados...")
        snapshot = collect_all()

    print("\n[STEP 2] Gerando relatorios...")
    reports = generate_all_reports()

    print("\n[STEP 3] Enviando relatorios ao Telegram...")
    for asset_report in reports:
                send(asset_report)
                asset_line = asset_report.split("\n")[0]
                print(f"  [OK] {asset_line} enviado")

    print("\n[STEP 4] Verificando alertas de regime...")
    market = snapshot.get("market", {})
    fng = snapshot.get("fear_greed", {})
    btc = market.get("BTC", {})
    score = max(0, min(100, round(50 + (btc.get("change_24h") or 0) * 2 + (fng.get("value", 50) - 50) / 10)))
    rec = "Acumular" if score >= 60 else ("Reduzir" if score <= 40 else "Manter")

    current_state = {
                "score": score,
                "recommendation": rec,
                "date": snapshot["date"]
    }

    alerts = detect_regime_change(current_state)

    if alerts:
                print(f"\n[STEP 5] Enviando alertas de regime...")
                alert_header = "<b>ALERTA DE MUDANCA DE REGIME</b>\n\n"
                alert_body = "\n".join(f" {a}" for a in alerts)
                send(alert_header + alert_body)
                print(f"  [OK] {len(alerts)} alerta(s) enviado(s)")

    print("\n[CONCLUIDO] Pipeline executado com sucesso!")

if __name__ == "__main__":
        try:
                    main()
except Exception as e:
        print(f"[ERRO] {e}")
        sys.exit(1)
