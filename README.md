
# Automação — Dados On-Chain → BTC (GitHub Actions)

Este repositório roda diariamente, gera o relatório **Dados On-Chain — {data} — Diário — Nº {contador}** via OpenAI API,
salva em PDF e envia para o **Telegram** com o seu bot.

## Arquivos principais
- `onchain_to_telegram.py` — gera o texto com a OpenAI, cria o PDF e envia no Telegram.
- `.github/workflows/onchain.yml` — agenda diário e executa o script.
- `.env.onchain.example` — apenas um exemplo local (não subir com dados reais).
- `requirements.txt` — dependências mínimas (Somente `requests`).
- `tools/telegram_notify.py` — utilitário opcional de envio.
- `tools/.env.example` — exemplo de env para o utilitário opcional.

## Agendamento (cron)
- O workflow já está configurado para rodar **todos os dias às 09:00 UTC**, que corresponde a **06:00 BRT** (São Paulo).
- Para alterar, edite em `.github/workflows/onchain.yml`:
  ```yaml
  on:
    schedule:
      - cron: "0 9 * * *"
  ```

## Como configurar as SECRETS (NÃO COMMITAR SEGREDOS)
1. No GitHub do seu repositório: **Settings → Secrets and variables → Actions**.
2. Clique em **New repository secret** e crie **cada uma**:
   - `OPENAI_API_KEY` → sua chave da OpenAI
   - `TELEGRAM_BOT_TOKEN` → token do bot (via @BotFather)
   - `TELEGRAM_CHAT_ID` → chat de destino
3. (Opcional) Se quiser definir explicitamente o modelo:
   - `OPENAI_MODEL` → ex.: `gpt-5`

> Importante: **nunca** coloque segredos em arquivos `.env` ou `.yml` do repositório. Use **Secrets** do GitHub.

## Rodar manualmente
- Na aba **Actions** do GitHub, entre no workflow “On-chain diário” e clique em **Run workflow**.

## Como testar localmente (sem enviar)
1. Crie um `.env` local (NÃO COMMITAR) copiando de `.env.onchain.example` e preenchendo `OPENAI_API_KEY`.
2. Instale dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Rode apenas geração (sem enviar no Telegram):
   ```bash
   python onchain_to_telegram.py --no-send
   ```
4. O PDF sai em `out/`.

## Persistência do contador
- O workflow faz commit do `counters.json` após cada execução, para manter o **Nº**.
- Já deixamos `permissions: contents: write` no YAML e um passo que faz `git add/commit/push` se `counters.json` mudar.

## Estrutura sugerida do repositório
```
.
├── onchain_to_telegram.py
├── requirements.txt
├── .env.onchain.example
├── tools
│   ├── telegram_notify.py
│   └── .env.example
└── .github
    └── workflows
        └── onchain.yml

> **Somente BTC**: o prompt do `onchain_to_telegram.py` está ajustado para **Bitcoin**.

---

## Segredos (GitHub → Settings → *Secrets and variables* → **Actions**)

Obrigatórios:

- `TELEGRAM_BOT_TOKEN` → token do seu bot (criado no **@BotFather**)
- `TELEGRAM_CHAT_ID` → chat/grupo de destino (ex.: `-1001234567880` para grupos)
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

---

## Como roda por dentro

O passo de envio (exemplo) chama:

```bash
python onchain_to_telegram.py \
  --provider groq \
  --model llama-3.1-70b-versatile \
  --send-as message