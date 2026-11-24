# run_all.py
# Orquestrador principal - coleta + relatórios + envio Telegram
import sys

from collector_unified import collect_all
from report_unified import generate_all_reports
from telegram_sender import send
from alerts_engine import detect_regime_change


def calc_score(btc, fng):
    score = 50 + (btc.get("change_24h") or 0) * 2
    # API indisponível ou resposta incompleta: neutralizar Fear & Greed.
    fng_value = fng.get("value")
    if fng_value is None:
        fng_value = 50
    score += (fng_value - 50) / 10
    return max(0, min(100, round(score)))


def calc_recommendation(score):
    if score >= 60:
        return "Acumular"
    if score <= 40:
        return "Reduzir"
    return "Manter"


def main():
    print("[STEP 1] Coletando dados...")
    snapshot = collect_all()

    print("\n[STEP 2] Gerando relatórios com o snapshot coletado...")
    reports = generate_all_reports(snapshot)

    if not reports:
        raise RuntimeError("Nenhum relatório foi gerado; mercado vazio no snapshot.")

    print("\n[STEP 3] Enviando relatórios ao Telegram...")
    for asset_report in reports:
        result = send(asset_report)
        if not result.get("ok"):
            raise RuntimeError(f"Telegram não confirmou envio: {result}")
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
        "date": snapshot["date"],
    }

    alerts = detect_regime_change(current_state)
    if alerts:
        print("\n[STEP 5] Enviando alertas de regime...")
        alert_header = "<b>ALERTA DE MUDANÇA DE REGIME</b>\n\n"
        alert_body = "\n".join(f"• {a}" for a in alerts)
        result = send(alert_header + alert_body)
        if not result.get("ok"):
            raise RuntimeError(f"Telegram não confirmou alerta: {result}")
        print(f"  [OK] {len(alerts)} alerta(s) enviado(s)")

    print("\n[CONCLUÍDO] Pipeline executado com sucesso!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERRO] {e}", file=sys.stderr)
        sys.exit(1)
