# 📊 On-Chain BTC Telegram Reporter

Sistema **determinístico e automatizado** de análise on-chain do Bitcoin, que coleta dados reais, constrói histórico, interpreta métricas de forma objetiva (sem IA) e envia relatórios diários e alertas para o Telegram.

> 🔒 100% sem IA  
> 📡 Dados on-chain reais  
> 🧠 Interpretação estatística baseada em histórico  
> 🤖 Execução automática via GitHub Actions  

---

## 🚀 O que este projeto faz

Todos os dias, o sistema:

1. 📥 **Coleta dados on-chain reais do Bitcoin**
2. 🗂️ **Armazena histórico local versionado (Git)**
3. 📈 **Calcula médias, variações percentuais e contexto histórico**
4. 🧠 **Interpreta os dados com lógica determinística**
5. 🧮 **Calcula Score On-Chain (0–100)**
6. 📊 **Define viés de mercado e recomendação**
7. 📲 **Envia relatório formatado para o Telegram**

---

## 📌 Métricas analisadas

### 1️⃣ Exchange Inflow (MA7)
- Média móvel de 7 dias de BTC entrando em exchanges
- Comparação com média histórica e percentil
- Indica pressão vendedora potencial

### 2️⃣ Exchange Netflow
- Entrada ou saída líquida de BTC das exchanges
- Forte indicador de acumulação ou distribuição

### 3️⃣ Reservas em Exchanges
- Total de BTC mantidos em exchanges
- Comparação com média histórica (ex: 180 dias)
- Indica escassez ou abundância estrutural

### 4️⃣ Fluxos de Baleias
- Depósitos recentes de grandes carteiras
- Whale Ratio (participação relativa de baleias)
- Separação clara entre:
  - Depósitos whales/miners
  - Concentração de fluxo

---

## 🧠 Interpretação e Score

O sistema gera automaticamente:

- **Score On-Chain:** 0 a 100  
- **Viés de Mercado:**  
  - Altista (Fraco / Moderado / Forte)  
  - Neutro  
  - Baixista  
- **Recomendação:**  
  - Acumular  
  - Manter  
  - Reduzir  

> ⚠️ O score **pode mudar mesmo com valores absolutos iguais**, pois depende do **histórico acumulado e do contexto estatístico**.

---

## 📲 Exemplo de relatório no Telegram

📊 Dados On-Chain BTC — 31/01/2026 — Diário

1️⃣ Exchange Inflow (MA7)
O Exchange Inflow (MA7) está significativamente abaixo da média histórica, em 3.200 BTC.

2️⃣ Exchange Netflow
O Exchange Netflow registra saída líquida de aproximadamente 4.850 BTC das exchanges.

3️⃣ Reservas em Exchanges
As reservas em exchanges seguem em 1.720.000 BTC, abaixo da média histórica, indicando redução de oferta.

4️⃣ Fluxos de Baleias
Os depósitos de baleias somaram cerca de 1.340 BTC nas últimas 24h.
O Whale Ratio encontra-se em 0.54, em nível moderado.

📌 Interpretação Executiva
• Score On-Chain: 100/100
• Viés de Mercado: Altista (Forte)
• Recomendação: Acumular


---

## 🗂️ Estrutura do projeto

.
├── .github/workflows/
│ └── run-onchain.yml # GitHub Actions (agendamento e execução)
├── collector.py # Coleta de dados on-chain reais
├── text_engine.py # Motor determinístico de interpretação
├── onchain_to_telegram.py # Geração do relatório e envio ao Telegram
├── metrics.json # Snapshot atual das métricas
├── history_metrics.json # Histórico de métricas (base estatística)
├── history.json # Histórico de score / recomendação
├── requirements.txt # Dependências Python
└── README.md # Documentação


---

## ⏰ Agendamento

O sistema roda automaticamente via **GitHub Actions**:

- 🕕 **06:00 BRT (09:00 UTC)**
- Periodicidade: diária
- Também pode ser executado manualmente

---

## 🔐 Variáveis de ambiente (obrigatórias)

Configure em **Settings → Secrets → Actions**:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

---

## 🧪 Fases implementadas

- ✅ Fase 1–4: Coleta e interpretação básica
- ✅ Fase 5: Histórico persistente
- ✅ Fase 6.1: Score dinâmico
- ✅ Fase 6.2: Comparação percentual (quando houver base)
- ✅ Fase 6.3: Separação Whale Flow + Whale Ratio
- ✅ Fase 6.4: Mensagens condicionais ao histórico
- ✅ Fase 6.5: Estabilidade do score e consolidação

---

## ⚠️ Observações importantes

- O sistema **não é um conselho financeiro**
- O foco é **contexto on-chain e leitura estrutural**
- Ideal para:
  - Investidores de médio/longo prazo
  - Análise macro de Bitcoin
  - Estudos quantitativos on-chain

---

## 🧠 Filosofia do projeto

> “Dados primeiro.  
> Interpretação objetiva.  
> Nenhuma IA opinativa.  
> Histórico acima de ruído.”

---

## 📌 Próximas evoluções (opcional)

- Alertas de mudança de regime
- Relatório semanal/mensal
- Exportação CSV
- Dashboard externo
- Multi-ativo (ETH, etc.)

---

## 👤 Autor

Projeto desenvolvido e arquitetado por **Douglas**  
com foco em **robustez, clareza e controle total da lógica**.




