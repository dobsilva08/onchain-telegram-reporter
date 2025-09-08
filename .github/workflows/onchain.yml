name: On-chain diário

on:
  schedule:
    # 09:15 UTC = 06:15 BRT
    - cron: "15 9 * * *"
  workflow_dispatch: {}

permissions:
  contents: write

concurrency:
  group: onchain-diario
  cancel-in-progress: false

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests

      - name: Send on-chain report as Telegram message
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: |
          # Use um modelo bem disponível; mude para gpt-5 quando tiver acesso
          python onchain_to_telegram.py --model gpt-4o-mini --send-as message

      - name: Persist counter (counters.json)
        run: |
          if [ -f counters.json ]; then
            git config user.name "github-actions[bot]"
            git config user.email "github-actions[bot]@users.noreply.github.com"
            git add counters.json
            git diff --cached --quiet || git commit -m "chore: bump counter [skip ci]"
            git push
          fi
