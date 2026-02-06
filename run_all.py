from report_market import generate_market_report
from report_onchain import generate_onchain_report
from telegram_sender import send

def main():
    send(generate_market_report())
    send(generate_onchain_report())

if __name__ == "__main__":
    main()
