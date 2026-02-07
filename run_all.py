from report_market import generate_market_report
from report_onchain import generate_onchain_report
from telegram_sender import send


def main():
    messages = []

    market_report = generate_market_report()
    if market_report:
        messages.append(market_report)

    onchain_report = generate_onchain_report()
    if onchain_report:
        messages.append(onchain_report)

    if not messages:
        raise RuntimeError("Nenhum relatório foi gerado")

    for msg in messages:
        send(msg)


if __name__ == "__main__":
    main()
