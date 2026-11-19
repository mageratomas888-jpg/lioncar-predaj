# BMW trh SK – denný monitoring skladu dealerov

Vetva `bmw-trh-data` (nie `main`, aby sa nemenila webová stránka).

- `fetch_used.py` – jazdené BMW všetkých dealerov z portálu bezcakania.bmw.sk
- `fetch_dealers.py` – kompletná ponuka z webov 10 BMW dealerov (/ponuka-vozidiel)
- `build.py` – spracovanie, porovnanie so včerajškom (`state.json`), výstupy v `out/`
- `out/udalosti.csv` – denník: zmizlo z ponuky (predané), označené ako predané, nové, rezervované, zmena ceny
- `run_daily.sh` – celý denný beh

Dashboard: https://claude.ai/artifact/QnnkDQ84i9bTBSuKBU9QzB
