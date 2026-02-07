from report_market import generate_market_report
from report_onchain import generate_onchain_report
from telegram_sender import send


def main():
    reports = []

    market_report = generate_market_report()
    if market_report:
        reports.append(market_report)

    onchain_report = generate_onchain_report()
    if onchain_report:
        reports.append(onchain_report)

    if not reports:
        raise RuntimeError("Nenhum relatório foi gerado")

    final_message = "\n\n".join(reports)
    send(final_message)


if __name__ == "__main__":
    main()
