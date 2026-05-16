# 🟠 OnChain Telegram Reporter

Sistema automatizado de monitoramento on-chain para criptomoedas com envio de relatórios premium via Telegram.

Projeto desenvolvido em Python utilizando APIs públicas gratuitas, GitHub Actions e automação serverless.

---

# 🚀 Features

✅ Relatórios automáticos via Telegram  
✅ Monitoramento BTC / ETH / SOL  
✅ Dados reais em tempo real  
✅ Pipeline automatizado via GitHub Actions  
✅ Whale Activity (estimado)  
✅ Whale Ratio (estimado)  
✅ Fear & Greed Index  
✅ Dominância BTC / ETH  
✅ Dados on-chain BTC  
✅ Histórico persistente  
✅ Score quantitativo automático  
✅ Visual premium estilo institucional  

---

# 📸 Exemplo do Relatório

```text
🟠 RELATÓRIO ON-CHAIN BTC
📅 Diário

📥 Exchange Inflow
📤 Exchange Netflow
🏦 Reservas em Exchanges
🐋 Whale Activity
📉 Whale Ratio
⚙️ Contexto da Rede
📊 Interpretação Executiva
```

---

# ⚙️ Stack Utilizada

- Python 3.11
- GitHub Actions
- Telegram Bot API
- CoinGecko API
- mempool.space API
- Alternative.me API

---

# 📂 Estrutura do Projeto

```text
onchain-telegram-reporter/
│
├── .github/
│   └── workflows/
│       └── run-onchain.yml
│
├── collector_unified.py
├── report_unified.py
├── alerts_engine.py
├── telegram_sender.py
├── run_all.py
├── requirements.txt
├── snapshot.json
├── history.json
└── README.md
```

---

# 📊 Métricas Monitoradas

## 📥 Exchange Inflow
- Volume 24h
- Fluxo recente

## 📤 Exchange Netflow
- Variação semanal
- Acumulação/distribuição

## 🏦 Reservas em Exchanges
- Market Cap
- Dominância
- Ranking

## 🐋 Whale Activity
- Grandes transações
- Depósitos institucionais
- Miner flow

## 📉 Whale Ratio
- Whale Ratio estimado
- Pressão vendedora

## ⚙️ Contexto da Rede
- Hashrate
- Fees
- Fear & Greed

## 📊 Interpretação Executiva
- Score quantitativo
- Viés de mercado
- Estratégia automática

---

# 🔧 Instalação Local

Clone o projeto:

```bash
git clone https://github.com/dobsilva08/onchain-telegram-reporter.git
```

Entre na pasta:

```bash
cd onchain-telegram-reporter
```

Instale dependências:

```bash
pip install -r requirements.txt
```

Execute:

```bash
python run_all.py
```

---

# 🔐 Variáveis de Ambiente

O projeto utiliza:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

Configure no GitHub Secrets:

```text
Settings → Secrets and variables → Actions
```

---

# 🤖 Automação

O sistema roda automaticamente via GitHub Actions utilizando cron schedule.

Exemplo:

```yaml
schedule:
  - cron: "15 9 * * *"
```

---

# 📡 APIs Utilizadas

## CoinGecko
- Preços
- Volume
- Market Cap
- Dominância

https://www.coingecko.com/en/api

---

## mempool.space
- Hashrate
- Fees
- Blocos
- Dados on-chain BTC

https://mempool.space/docs/api/rest

---

## Alternative.me
- Fear & Greed Index

https://alternative.me/crypto/fear-and-greed-index/

---

# 🧠 Roadmap

- [ ] Whale Alerts reais
- [ ] Dashboard Streamlit
- [ ] Gráficos automáticos PNG
- [ ] Relatório semanal
- [ ] Relatório mensal
- [ ] Banco SQLite/PostgreSQL
- [ ] Score multi-fator
- [ ] Alertas inteligentes
- [ ] Funding Rate
- [ ] Open Interest
- [ ] ETF Flows

---

# 📌 Objetivo do Projeto

Construir uma plataforma gratuita e automatizada de inteligência on-chain com foco em:

- automação
- análise quantitativa
- monitoramento institucional
- visual premium
- operação serverless

---

# ⚠️ Disclaimer

Este projeto possui caráter educacional e informativo.

Não constitui recomendação financeira.

---

# 👨‍💻 Autor

Douglas Silva

GitHub:
https://github.com/dobsilva08
