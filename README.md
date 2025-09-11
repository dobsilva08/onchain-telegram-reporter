# Automação — Relatório On-Chain **BTC** (Telegram + GitHub Actions)

Gera e envia para o **Telegram** um relatório de **Dados On-Chain do Bitcoin** em **texto** (sem PDF).  
Há rotinas **diária**, **semanal** e **mensal**, com **watchdogs** que disparam se o horário principal falhar.

Por padrão usamos **Groq / Llama-3**; também é possível usar **OpenAI**, **OpenRouter** ou **Anthropic**.

---

![On-chain diário](https://github.com/dobsilva08/onchain-telegram-reporter/actions/workflows/onchain.yml/badge.svg)
![Semanal](https://github.com/dobsilva08/onchain-telegram-reporter/actions/workflows/onchain-weekly.yml/badge.svg)
![Mensal](https://github.com/dobsilva08/onchain-telegram-reporter/actions/workflows/onchain-monthly.yml/badge.svg)
![Watchdog diário](https://github.com/dobsilva08/onchain-telegram-reporter/actions/workflows/watchdog.yml/badge.svg)
![Watchdog semanal](https://github.com/dobsilva08/onchain-telegram-reporter/actions/workflows/watchdog-weekly.yml/badge.svg)
![Watchdog mensal](https://github.com/dobsilva08/onchain-telegram-reporter/actions/workflows/watchdog-monthly.yml/badge.svg)

---

## Visão geral

- Relatório: **“Dados On-Chain — {data} — Diário/Semanal/Mensal — Nº {contador}”**  
- Envio: **mensagens** no Telegram (DM, grupo ou ambos)  
- Anti-duplicidade: selos em `.sent/`  
- Contador: `counters.json` (commit automático)  
- Watchdogs: garantem o disparo caso o agendamento principal não rode

---

## Estrutura dos arquivos

    .
    ├── onchain_to_telegram.py           # gera o texto e envia ao Telegram (BTC)
    ├── requirements.txt                 # dependências (requests)
    ├── counters.json                    # atualizado automaticamente
    ├── .sent/                           # “selos” para evitar reenvio (gerado)
    │   ├── done-daily-YYYY-MM-DD
    │   ├── done-weekly-YYYY-Www
    │   └── done-monthly-YYYY-MM
    └── .github/workflows/
        ├── onchain.yml                  # diário (com janelas de backup)
        ├── onchain-weekly.yml           # semanal (sábado)
        ├── onchain-monthly.yml          # mensal (dia 1)
        ├── watchdog.yml                 # watchdog diário
        ├── watchdog-weekly.yml          # watchdog semanal
        └── watchdog-monthly.yml         # watchdog mensal

> **Somente BTC**: o prompt do `onchain_to_telegram.py` está ajustado para **Bitcoin**.

---

## Segredos (GitHub → Settings → *Secrets and variables* → **Actions**)

Obrigatórios:

- `TELEGRAM_BOT_TOKEN` → token do seu bot (criado no **@BotFather**)  
- `TELEGRAM_CHAT_ID` → chat/grupo de destino (ex.: `-1001234567890` para grupos)  
- **Um** provedor de LLM (o padrão é Groq):
  - `GROQ_API_KEY` *(padrão)* **ou**
  - `OPENAI_API_KEY` **ou**
  - `OPENROUTER_API_KEY` **ou**
  - `ANTHROPIC_API_KEY`

> Coloque o **bot dentro do grupo** (ideal como **admin**) para poder postar.

---

## Agendamentos

### Tabela de horários

| Workflow               | UTC                              | BRT (São Paulo)             | Obs. |
|------------------------|----------------------------------|-----------------------------|------|
| **Diário (principal)** | 09:15, 09:30, 09:45, 10:00       | 06:15, 06:30, 06:45, 07:00  | Janelas de backup |
| **Watchdog diário**    | 10:10                            | 07:10                       | Dispara se não houver selo `.sent` do dia |
| **Semanal (sábado)**   | 10:05 (sábado)                   | 07:05 (sábado)              | Gera “semanal” |
| **Watchdog semanal**   | 10:25 (sábado)                   | 07:25 (sábado)              | Dispara se não houver selo semanal |
| **Mensal (dia 1)**     | 10:10 (dia 1)                    | 07:10 (dia 1)               | Gera “mensal” |
| **Watchdog mensal**    | 10:30 (dia 1)                    | 07:30 (dia 1)               | Dispara se não houver selo mensal |

Os crons estão nos arquivos dentro de `.github/workflows/`. Edite os `cron:` caso precise ajustar.

### Cron snippets (referência)

- **Diário** (`.github/workflows/onchain.yml`)

        on:
          schedule:
            - cron: "15 9 * * *"   # 06:15 BRT
            - cron: "30 9 * * *"   # 06:30 BRT
            - cron: "45 9 * * *"   # 06:45 BRT
            - cron: "0 10 * * *"   # 07:00 BRT
          workflow_dispatch: {}

- **Watchdog diário** (`.github/workflows/watchdog.yml`)

        on:
          schedule:
            - cron: "10 10 * * *"  # 07:10 BRT
          workflow_dispatch: {}

- **Semanal** (`.github/workflows/onchain-weekly.yml`)

        on:
          schedule:
            - cron: "5 10 * * 6"   # sáb 07:05 BRT
          workflow_dispatch: {}

- **Watchdog semanal** (`.github/workflows/watchdog-weekly.yml`)

        on:
          schedule:
            - cron: "25 10 * * 6"  # sáb 07:25 BRT
          workflow_dispatch: {}

- **Mensal** (`.github/workflows/onchain-monthly.yml`)

        on:
          schedule:
            - cron: "10 10 1 * *"  # dia 1, 07:10 BRT
          workflow_dispatch: {}

- **Watchdog mensal** (`.github/workflows/watchdog-monthly.yml`)

        on:
          schedule:
            - cron: "30 10 1 * *"  # dia 1, 07:30 BRT
          workflow_dispatch: {}

---

## Como roda por dentro

O passo de envio (exemplo) chama:

    python onchain_to_telegram.py \
      --provider groq \
      --model llama-3.1-70b-versatile \
      --send-as message

Você pode trocar `--provider/--model` conforme o provedor e modelo disponíveis.

---

## Rodar manualmente

1. Vá em **Actions**.  
2. Abra o workflow desejado (**On-chain diário**, **On-chain semanal**, **On-chain mensal**).  
3. Clique em **Run workflow**.

> Se “pular” dizendo que já enviou, é porque existe selo em `.sent/`.  
> Para **testar de novo**, apague o selo e rode novamente:
> - diário: `.sent/done-daily-YYYY-MM-DD`  
> - semanal: `.sent/done-weekly-YYYY-Www`  
> - mensal: `.sent/done-monthly-YYYY-MM`

---

## Rodar localmente (opcional)

    # .env local (não commitar)
    GROQ_API_KEY=...
    TELEGRAM_BOT_TOKEN=...
    TELEGRAM_CHAT_ID=...

    pip install -r requirements.txt
    python onchain_to_telegram.py --provider groq --model llama-3.1-70b-versatile --send-as message

---

## Estrutura do relatório (resumo do prompt)

1) Exchange Inflow (MA7)  
2) Exchange Netflow (Total)  
3) Reservas em Exchanges  
4) Fluxos de Baleias (depósitos whales/miners + Whale Ratio)  
5) Resumo de Contexto Institucional  
6) Interpretação Executiva (5–8 bullets)  
7) Conclusão

> Se o LLM falhar/quota, é enviado um **esqueleto** para registro manual.

---

## Dicas rápidas

- **Nada chegou no grupo?** cheque `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`, se o bot está no grupo (ideal admin) e veja os logs do passo “Send on-chain report”.  
- **Erro de modelo/quota:** troque `--model`/`--provider` ou ajuste as chaves.  
- **Duplicidade:** os selos em `.sent/` previnem reenvio. Apague somente para testes manuais.

---

## Licença

Livre uso. Sugestões e PRs são bem-vindos!