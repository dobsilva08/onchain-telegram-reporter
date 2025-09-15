#!/usr/bin/env bash
set -euo pipefail

# ===== Config =====
VERSION="0.3.0"
DATE="$(date +%F)"  # data de hoje; ajuste se quiser fixar outra

# ===== README.md =====
cat > README.md <<MD
# Automação — Relatório On-Chain **BTC • ETH • SOL** (Telegram + GitHub Actions) — **v${VERSION}**

Gera e envia para o **Telegram** um relatório de **Dados On-Chain** em **texto**.

Há rotinas **diária**, **semanal** e **mensal**.  
Para **BTC** existem **watchdogs** que disparam se o horário principal falhar.  
Por padrão usamos **Groq / Llama-3**; também é possível usar **OpenAI**, **OpenRouter** ou **Anthropic**.

---

### Status — BTC
![On-chain diário](https://github.com/dobsilva08/onchain-telegram-reporter/actions/workflows/onchain.yml/badge.svg)
![Semanal](https://github.com/dobsilva08/onchain-telegram-reporter/actions/workflows/onchain-weekly.yml/badge.svg)
![Mensal](https://github.com/dobsilva08/onchain-telegram-reporter/actions/workflows/onchain-monthly.yml/badge.svg)
![Watchdog diário](https://github.com/dobsilva08/onchain-telegram-reporter/actions/workflows/watchdog.yml/badge.svg)
![Watchdog semanal](https://github.com/dobsilva08/onchain-telegram-reporter/actions/workflows/watchdog-weekly.yml/badge.svg)
![Watchdog mensal](https://github.com/dobsilva08/onchain-telegram-reporter/actions/workflows/watchdog-monthly.yml/badge.svg)

### Status — ETH
![ETH diário](https://github.com/dobsilva08/onchain-telegram-reporter/actions/workflows/onchain-eth.yml/badge.svg)
![ETH semanal](https://github.com/dobsilva08/onchain-telegram-reporter/actions/workflows/onchain-eth-weekly.yml/badge.svg)
![ETH mensal](https://github.com/dobsilva08/onchain-telegram-reporter/actions/workflows/onchain-eth-monthly.yml/badge.svg)

### Status — SOL
![SOL diário](https://github.com/dobsilva08/onchain-telegram-reporter/actions/workflows/onchain-sol.yml/badge.svg)
![SOL semanal](https://github.com/dobsilva08/onchain-telegram-reporter/actions/workflows/onchain-sol-weekly.yml/badge.svg)
![SOL mensal](https://github.com/dobsilva08/onchain-telegram-reporter/actions/workflows/onchain-sol-monthly.yml/badge.svg)

---

## Visão geral

- Título: **“Dados On-Chain — {MOEDA} — {data} — Diário/Semanal/Mensal — Nº {contador}”**  
- Envio: **mensagens** no Telegram (DM, grupo ou ambos)  
- Anti-duplicidade: selos em \`.sent/\` (BTC)  
- Contador: \`counters.json\` (commit automático)  
- Watchdogs: **apenas BTC** (garantem o disparo caso o agendamento principal não rode)

---

## Estrutura dos arquivos

\`\`\`
.
├── onchain_to_telegram.py            # BTC
├── onchain_to_telegram_eth.py        # ETH
├── onchain_to_telegram_sol.py        # SOL
├── requirements.txt
├── counters.json                     # atualizado automaticamente
├── .sent/                            # selos anti-duplicidade (BTC)
│   ├── done-daily-YYYY-MM-DD
│   ├── done-weekly-YYYY-Www
│   └── done-monthly-YYYY-MM
└── .github/workflows/
    ├── onchain.yml                   # BTC diário
    ├── onchain-weekly.yml            # BTC semanal
    ├── onchain-monthly.yml           # BTC mensal
    ├── watchdog.yml                  # BTC watchdog diário
    ├── watchdog-weekly.yml           # BTC watchdog semanal
    ├── watchdog-monthly.yml          # BTC watchdog mensal
    ├── onchain-eth.yml               # ETH diário
    ├── onchain-eth-weekly.yml        # ETH semanal
    ├── onchain-eth-monthly.yml       # ETH mensal
    ├── onchain-sol.yml               # SOL diário
    ├── onchain-sol-weekly.yml        # SOL semanal
    └── onchain-sol-monthly.yml       # SOL mensal
\`\`\`

> Os prompts de cada script já estão ajustados para **BTC**, **ETH** e **SOL** respectivamente.

---

## Segredos (GitHub → Settings → *Secrets and variables* → **Actions**)

**Obrigatórios (para qualquer moeda):**
- \`TELEGRAM_BOT_TOKEN\` → token do bot (criado no **@BotFather**)
- \`TELEGRAM_CHAT_ID\` → chat/grupo de destino (ex.: \`-1001234567890\`)
- **Um** provedor:
  - \`GROQ_API_KEY\` *(padrão recomendado)* **ou**
  - \`OPENAI_API_KEY\` **ou**
  - \`OPENROUTER_API_KEY\` **ou**
  - \`ANTHROPIC_API_KEY\`

**Opcionais por moeda (se quiser enviar para chats/tópicos diferentes):**
- \`ETH_TELEGRAM_CHAT_ID\`, \`ETH_TELEGRAM_TOPIC_ID\`
- \`SOL_TELEGRAM_CHAT_ID\`, \`SOL_TELEGRAM_TOPIC_ID\`

> Se não definir os IDs específicos por moeda, os scripts usam **\`TELEGRAM_CHAT_ID\`**.

---

## Agendamentos

### BTC — horários
| Workflow               | UTC                              | BRT (São Paulo)             | Obs. |
|------------------------|----------------------------------|-----------------------------|------|
| **Diário (principal)** | 09:15, 09:30, 09:45, 10:00       | 06:15, 06:30, 06:45, 07:00  | Janelas de backup |
| **Watchdog diário**    | 10:10                            | 07:10                       | Dispara se não houver selo do dia |
| **Semanal (sábado)**   | 10:05 (sábado)                   | 07:05 (sábado)              | Gera “semanal” |
| **Watchdog semanal**   | 10:25 (sábado)                   | 07:25 (sábado)              | Dispara se não houver selo |
| **Mensal (dia 1)**     | 10:10 (dia 1)                    | 07:10 (dia 1)               | Gera “mensal” |
| **Watchdog mensal**    | 10:30 (dia 1)                    | 07:30 (dia 1)               | Dispara se não houver selo |

### ETH — horários
Mesma janela do BTC (sem watchdogs):  
**Diário:** 09:15/09:30/09:45/10:00 UTC • **Semanal:** sáb 10:05 UTC • **Mensal:** dia 1 às 10:10 UTC.

### SOL — horários
Mesma janela do BTC (sem watchdogs):  
**Diário:** 09:15/09:30/09:45/10:00 UTC • **Semanal:** sáb 10:05 UTC • **Mensal:** dia 1 às 10:10 UTC.

> Horários podem ser ajustados editando o \`cron\` nos arquivos em \`.github/workflows/\`.

---

## Como roda por dentro

Exemplos de execução (chamados pelos workflows):

\`\`\`bash
# BTC
python onchain_to_telegram.py --provider groq --model llama-3.1-70b-versatile --send-as message

# ETH
python onchain_to_telegram_eth.py --provider groq --model llama-3.1-70b-versatile --send-as message --period daily

# SOL
python onchain_to_telegram_sol.py --provider groq --model llama-3.1-70b-versatile --send-as message --period daily
\`\`\`

Você pode trocar \`--provider/--model\` conforme o provedor e modelo disponíveis.

---

## Rodar manualmente

1. Vá em **Actions**.  
2. Abra o workflow desejado (**BTC/ETH/SOL** diário/semanal/mensal).  
3. Clique em **Run workflow**.

> Se “pular” dizendo que já enviou, é porque existe selo em \`.sent/\` (aplica ao BTC).  
> Para **testar de novo** no BTC, apague o selo correspondente:
> - diário: \`.sent/done-daily-YYYY-MM-DD\`
> - semanal: \`.sent/done-weekly-YYYY-Www\`
> - mensal: \`.sent/done-monthly-YYYY-MM\`

---

## Estrutura do relatório (resumo do prompt)

1) Exchange Inflow (MA7)  
2) Exchange Netflow (Total)  
3) Reservas em Exchanges  
4) Fluxos de Baleias (depósitos whales/miners + Whale Ratio)  
5) Resumo de Contexto Institucional  
6) Interpretação Executiva (5–8 bullets)  
7) Conclusão

> Em caso de quota/erro no provedor, o script envia um **esqueleto** para registro manual.

---

## Versão do projeto

**v${VERSION}** — mantenha esse número atualizado quando fizer melhorias visíveis (veja CHANGELOG).

---

## Licença

Livre uso. Sugestões e PRs são bem-vindos!
MD

# ===== CHANGELOG.md =====
cat > CHANGELOG.md <<MD
# Changelog
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/)
e versão conforme [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [${VERSION}] - ${DATE}
### Adicionado
- **ETH**: novo script \`onchain_to_telegram_eth.py\` + workflows (diário/semanal/mensal).
- **SOL**: novo script \`onchain_to_telegram_sol.py\` + workflows (diário/semanal/mensal).
- Fallback para \`TELEGRAM_CHAT_ID\` quando variáveis específicas por moeda não estiverem definidas.
- Documentação atualizada (README) e arquivo \`VERSION\`.

### Corrigido
- Ajustes de permissões/commit automático do \`counters.json\`.

[${VERSION}]: https://github.com/dobsilva08/onchain-telegram-reporter/releases/tag/v${VERSION}
MD

# ===== VERSION =====
echo "${VERSION}" > VERSION

# ===== Final =====
echo "✅ Atualizado com sucesso:"
printf " - README.md (v%s)\n" "${VERSION}"
printf " - CHANGELOG.md ([%s] - %s)\n" "${VERSION}" "${DATE}"
printf " - VERSION => %s\n" "${VERSION}"
echo
echo "💡 Dica: atualize também a descrição do repositório (Settings → About → Description):"
echo "On-Chain Telegram Reporter — Relatórios on-chain para BTC, ETH e SOL via GitHub Actions (diário/semanal/mensal). v${VERSION}"

# (Opcional) Faça o commit e a tag automaticamente:
# git add README.md CHANGELOG.md VERSION
# git commit -m "docs: atualiza README/CHANGELOG para v${VERSION}"
# git tag v${VERSION}
# git push && git push --tags
```0