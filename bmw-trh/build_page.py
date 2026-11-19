#!/usr/bin/env python3
"""Zostaví zaheslovanú webovú stránku BMW trhu pre GitHub Pages.
Použitie: BMW_HESLO=... python3 build_page.py <vystup.html>
Dáta: out/sklad_dealerov.csv, out/jazdene_trh.csv, out/udalosti.csv
Šablóna: page/index.html (rovnaký obsah ako dashboard na claude.ai), page/shim.js, page/d3.min.js"""
import os, sys, csv, json, base64, secrets, datetime, zoneinfo, pathlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

HERE = pathlib.Path(__file__).parent
PAGE = HERE / "page"
pw = os.environ.get("BMW_HESLO", "").strip()
if not pw:
    sys.exit("Chýba heslo v premennej BMW_HESLO")
out_path = sys.argv[1]

def rows(name):
    with open(HERE / "out" / name, encoding="utf-8") as f:
        return [{k: (v if v != "" else None) for k, v in r.items()} for r in csv.DictReader(f)]

data = {"sklad": rows("sklad_dealerov.csv"), "jazdene": rows("jazdene_trh.csv"), "udalosti": rows("udalosti.csv")}
stamp = datetime.datetime.now(zoneinfo.ZoneInfo("Europe/Bratislava")).strftime("%-d. %-m. %Y %H:%M")
page = (PAGE / "index.html").read_text(encoding="utf-8")
page = page.replace("</header>", f'  <p class="bt-sub" id="aktualizovane">Aktualizované {stamp}</p>\n  </header>', 1)

head = """<!doctype html>
<html lang="sk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>BMW trh SK · LION CAR</title>
<style>
:root {
  color-scheme: light;
  --color-bg: #f4f5f7; --color-panel: #ffffff; --color-fg: #16191d; --color-fg-muted: #5d6570; --color-border-line: #dde1e6;
  --color-ok: #1a7f4b; --color-warn: #c98a12; --color-bad: #c0352b;
  --font-anthropic-sans: "Segoe UI", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif;
  --font-anthropic-serif: Georgia, "Times New Roman", serif;
  --cds-font-size-caption: 12px; --cds-font-size-body: 14px; --cds-font-size-heading: 17px; --cds-font-size-title: 30px; --cds-font-weight-medium: 600;
  --cds-gap-xs: 4px; --cds-gap-sm: 8px; --cds-gap-md: 14px; --cds-gap-lg: 22px; --cds-gap-xl: 32px;
  --cds-pad-xs: 4px; --cds-pad-sm: 8px; --cds-pad-md: 12px; --cds-pad-lg: 18px; --cds-pad-xl: 28px;
  --cds-radius: 8px;
  --cds-chart-muted: #b9c0c9; --cds-chart-grid: #eceef1; --cds-chart-axis: #9aa3ad; --cds-chart-reference: #7d8692;
  --cds-surface-popover: #ffffff; --cds-border: #d3d8de; --cds-shadow-popover: 0 6px 20px rgba(20,25,30,.12); --cds-text-secondary: #5d6570;
}
@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --color-bg: #121418; --color-panel: #1b1e23; --color-fg: #eceef1; --color-fg-muted: #9aa2ad; --color-border-line: #2e333a;
    --color-ok: #4cc38a; --color-warn: #e0a341; --color-bad: #f0796d;
    --cds-chart-muted: #4a515b; --cds-chart-grid: #262a30; --cds-chart-axis: #5f6772; --cds-chart-reference: #8a939e;
    --cds-surface-popover: #23272d; --cds-border: #3a4048; --cds-shadow-popover: 0 6px 20px rgba(0,0,0,.45); --cds-text-secondary: #9aa2ad;
  }
}
[hidden] { display: none !important; }
html, body { margin: 0; background: var(--color-bg); color: var(--color-fg); font-family: var(--font-anthropic-sans); font-size: 14px; }
#dash-root { max-width: 1400px; margin-inline: auto; padding: 28px clamp(12px, 3vw, 36px) 48px; box-sizing: border-box; }
.dash-select { font: inherit; font-size: 14px; color: var(--color-fg); background: var(--color-panel); border: 1px solid var(--color-border-line); border-radius: var(--cds-radius); padding: 7px 10px; min-width: 170px; }
</style>
</head>
<body>
<div id="dash-root">
"""
d3 = (PAGE / "d3.min.js").read_text(encoding="utf-8")
inner = (head
         + "<script>" + d3 + "</script>\n"
         + "<script>window.BMW_DATA=" + json.dumps(data, ensure_ascii=False).replace("</", "<\\/") + ";</script>\n"
         + "<script>" + (PAGE / "shim.js").read_text(encoding="utf-8") + "</script>\n"
         + page + "\n<script>dash.start();</script>\n</div>\n</body>\n</html>\n")

if os.environ.get("BMW_BEZ_HESLA") == "1":  # len na lokálny test
    pathlib.Path(out_path).write_text(inner, encoding="utf-8"); print("TEST bez hesla"); sys.exit()

ITER = 600000
salt, iv = secrets.token_bytes(16), secrets.token_bytes(12)
key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(pw.encode())
ct = AESGCM(key).encrypt(iv, inner.encode("utf-8"), None)
b64 = lambda b: base64.b64encode(b).decode()

gate = """<!doctype html>
<html lang="sk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>BMW trh SK · LION CAR</title>
<style>
:root { color-scheme: light; --bg: #f4f5f7; --panel: #fff; --fg: #16191d; --muted: #5d6570; --line: #dde1e6; --bad: #c0352b; --accent: #1f5fae; }
@media (prefers-color-scheme: dark) { :root { color-scheme: dark; --bg: #121418; --panel: #1b1e23; --fg: #eceef1; --muted: #9aa2ad; --line: #2e333a; --bad: #f0796d; --accent: #6ea3e6; } }
[hidden] { display: none !important; }
html, body { margin: 0; height: 100%; background: var(--bg); color: var(--fg); font: 15px "Segoe UI", system-ui, -apple-system, Arial, sans-serif; }
.wrap { min-height: 100%; display: grid; place-items: center; padding: 24px 16px; box-sizing: border-box; }
.card { width: 100%; max-width: 380px; background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 28px; box-sizing: border-box; display: flex; flex-direction: column; gap: 14px; }
h1 { font: 400 24px Georgia, "Times New Roman", serif; margin: 0; }
p { margin: 0; color: var(--muted); font-size: 13px; line-height: 1.5; }
label { font-size: 13px; color: var(--muted); display: flex; flex-direction: column; gap: 6px; }
input[type=password] { font: inherit; padding: 9px 11px; border: 1px solid var(--line); border-radius: 8px; background: var(--bg); color: var(--fg); }
.row { flex-direction: row; align-items: center; gap: 8px; }
button { font: inherit; font-weight: 600; padding: 10px; border: 0; border-radius: 8px; background: var(--fg); color: var(--bg); cursor: pointer; }
button:disabled { opacity: .6; cursor: progress; }
input:focus-visible, button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.err { color: var(--bad); font-size: 13px; min-height: 1.2em; }
</style>
</head>
<body>
<div class="wrap">
  <form class="card" id="f" autocomplete="on">
    <h1>BMW trh Slovensko</h1>
    <p>LION CAR · interný prehľad skladu a predajov BMW dealerov. Zadajte heslo.</p>
    <input type="text" name="username" value="bmw-trh" autocomplete="username" hidden>
    <label for="pw">Heslo<input type="password" id="pw" autocomplete="current-password" required autofocus></label>
    <label class="row" for="rem"><input type="checkbox" id="rem" checked> Zapamätať na tomto zariadení</label>
    <button type="submit" id="go">Otvoriť dashboard</button>
    <div class="err" id="err" role="alert"></div>
  </form>
</div>
<script>
const P = { s: "%SALT%", iv: "%IV%", ct: "%CT%", it: %ITER% };
const KEY = 'bmw-trh-heslo';
const u8 = (b) => Uint8Array.from(atob(b), (c) => c.charCodeAt(0));
async function open(pw) {
  const base = await crypto.subtle.importKey('raw', new TextEncoder().encode(pw), 'PBKDF2', false, ['deriveKey']);
  const key = await crypto.subtle.deriveKey({ name: 'PBKDF2', salt: u8(P.s), iterations: P.it, hash: 'SHA-256' }, base, { name: 'AES-GCM', length: 256 }, false, ['decrypt']);
  const html = new TextDecoder().decode(await crypto.subtle.decrypt({ name: 'AES-GCM', iv: u8(P.iv) }, key, u8(P.ct)));
  document.open(); document.write(html); document.close();
}
const f = document.getElementById('f'), go = document.getElementById('go'), err = document.getElementById('err');
f.addEventListener('submit', async (e) => {
  e.preventDefault();
  const pw = document.getElementById('pw').value;
  const rem = document.getElementById('rem').checked;
  go.disabled = true; go.textContent = 'Otváram…'; err.textContent = '';
  try {
    await open(pw);
    try { if (rem) localStorage.setItem(KEY, pw); else localStorage.removeItem(KEY); } catch (x) {}
  } catch (x) {
    go.disabled = false; go.textContent = 'Otvoriť dashboard';
    err.textContent = 'Nesprávne heslo. Skúste to znova.';
  }
});
(async () => { let s = null; try { s = localStorage.getItem(KEY); } catch (x) {} if (s) { try { await open(s); } catch (x) { try { localStorage.removeItem(KEY); } catch (y) {} } } })();
</script>
</body>
</html>
"""
gate = gate.replace("%SALT%", b64(salt)).replace("%IV%", b64(iv)).replace("%CT%", b64(ct)).replace("%ITER%", str(ITER))
pathlib.Path(out_path).write_text(gate, encoding="utf-8")
print("OK", len(gate) // 1024, "KB", stamp)
