🟠 Repórter do Telegram OnChain
Sistema automatizado de monitoramento on-chain para criptomoedas com envio de relatórios premium via Telegram.

Projeto desenvolvido em Python utilizando APIs públicas gratuitas, GitHub Actions e automação serverless.

🚀 Características
✅ Relatórios automáticos via Telegram
✅ Monitoramento BTC / ETH / SOL
✅ Dados reais em tempo real
✅ Pipeline automatizado via GitHub Actions
✅ Whale Activity (estimado)
✅ Whale Ratio (estimado)
✅ Índice de Medo & Ganância
✅ Dominância BTC / ETH
✅ Dados on-chain BTC
✅ Histórico persistente
✅ Score quantitativo automático
✅ Visual premium estilo institucional

📸 Exemplo do Relatório
🟠 RELATÓRIO ON-CHAIN BTC
📅 Diário

📥 Exchange Inflow
📤 Exchange Netflow
🏦 Reservas em Exchanges
🐋 Whale Activity
📉 Whale Ratio
⚙️ Contexto da Rede
📊 Interpretação Executiva
⚙️ Stack Utilizada
Python 3.11
Ações no GitHub
Telegram Bot API
CoinGecko API
mempool.space API
Alternative.me API
📂 Estrutura do Projeto
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
📊 Métricas Monitoradas
📥 Entrada de Troca
Volume 24h
Fluxo recente
📤 Exchange Netflow
Variação semanal
Acumulação/distribuição
🏦 Reservas em Exchanges
Capitalização de Mercado
Dominância
Classificação
🐋 Atividade de Baleias
Grandes transações
Depósitos institucionais
Fluxo minerador
📉 Proporção de Baleias
Razão da Baleia estimado
Pressão vendedora
⚙️ Contexto da Rede
Taxa de Hash
Taxas
Medo e Ganância
📊 Interpretação Executiva
Pontuação quantitativa
Viés de mercado
Estratégia automática
🔧 Instalação Local
Clone o projeto:

git clone https://github.com/dobsilva08/onchain-telegram-reporter.git
Entre na massa:

cd onchain-telegram-reporter
Instale dependências:

pip install -r requirements.txt
Execute:

python run_all.py
🔐 Variáveis de Ambiente
O projeto utiliza:

TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
Não configure segredos do GitHub:

Settings → Secrets and variables → Actions
🤖 Automação
O sistema roda automaticamente via GitHub Actions utilizando cron Agenda.

Exemplo:

schedule:
  - cr>: "15 9 * * *"
📡 APIs Utilizadas
CoinGecko
Preços
Volume
Capitalização de Mercado
Dominância
https://www.coingecko.com/en/api

mempool.space
Taxa de Hash
Taxas
Blocos
Dados on-chain BTC
https://mempool.space/docs/api/rest

Alternative.me
Índice de Medo e Ganância
https://alternative.me/crypto/fear-and-greed-index/

🧠 Roteiro
Alertas de Baleia reais
Dashboard Streamlit
Gráficos automáticos PNG
Relatório semanal
Relatório mensal
Banco SQLite/PostgreSQL
Partitura multi-fator
Alertas inteligentes
Taxa de Financiamento
Interesse Aberto
Fluxos de ETFs
📌 Objetivo do Projeto
Construir uma plataforma gratuita e automatizada de inteligência on-chain com foco em:

Automação
análise quantitativa
Monitoramento Institucional
Visual Premium
Operação serverless
⚠️ Aviso legal
Este projeto possui caráter educacional e informativo.

Não constitui recomendação financeira.

💻 Autor
Douglas Silva

GitHub: https://github.com/dobsilva08



