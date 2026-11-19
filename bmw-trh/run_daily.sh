#!/usr/bin/env bash
# Denný beh BMW trhu SK: stiahne ponuku, porovná so včerajškom (state.json),
# aktualizuje out/*.csv a out/udalosti.csv. Spúšťa sa z koreňa vetvy bmw-trh-data.
set -euo pipefail
cd "$(dirname "$0")"
DAY=$(TZ=Europe/Bratislava date +%F)
python3 -c "import bs4" 2>/dev/null || pip install --quiet --break-system-packages beautifulsoup4
python3 fetch_used.py
python3 fetch_dealers.py
python3 build.py "$DAY"
rm -rf data   # surové snímky sa necommitujú, stačí state.json + out/
echo "HOTOVO ${DAY}"
