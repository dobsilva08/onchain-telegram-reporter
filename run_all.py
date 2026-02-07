from telegram_sender import send
from market_report import generate_market_report

def main():
    message = generate_market_report()

    if not message or not isinstance(message, str):
        raise RuntimeError("Relatório vazio ou inválido — nada para enviar ao Telegram")

    send(message)

if __name__ == "__main__":
    main()
