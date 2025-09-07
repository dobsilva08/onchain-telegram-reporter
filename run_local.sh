
#!/usr/bin/env bash
set -euo pipefail
python -m pip install --upgrade pip
pip install -r requirements.txt
python onchain_to_telegram.py --no-send
echo "PDF gerado na pasta ./out (sem enviar)."
