#!/usr/bin/env python3
"""Spracuje denné snímky (data/used/<den>.json, data/dealers/<den>.json),
porovná ich s predchádzajúcim stavom (state.json) a vytvorí súbory pre dashboard:
  out/jazdene_trh.csv   – jazdené BMW všetkých dealerov (portál BMW SK)
  out/sklad_dealerov.csv – všetky vozidlá z webov dealerov (nové/predv./manaž./jazdené)
  out/udalosti.csv      – kumulatívny denník: predané, nové v ponuke, rezervácie, zmeny cien
  state.json            – stav pre ďalšie porovnanie
Použitie: python3 build.py [YYYY-MM-DD] [cesta_k_state.json] [cesta_k_udalosti.csv]"""
import csv, json, re, sys, datetime, pathlib

ROOT = pathlib.Path(__file__).parent
day = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
STATE = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "state.json"
EVENTS_IN = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else ROOT / "out" / "udalosti.csv"
OUT = ROOT / "out"; OUT.mkdir(exist_ok=True)
LION = "LION CAR"

def model_family(title, series=""):
    t = (title or "").replace("BMW ", " ").strip()
    m = re.search(r"\b(iX\d|iX|X\d|XM|Z4|i[3-8]|M\d)\b", t)
    if m:
        return m.group(1)
    m = re.search(r"radu (\d)", series or "") or re.search(r"\b(?:Rad|rad|radu)\s*(\d)\b", t) \
        or re.search(r"\bM?(\d)\d\d[A-Za-z]*\b", t)
    if m:
        return f"Rad {m.group(1)}"
    return (series or t.split(" ")[0] or "Iné").replace("BMW radu ", "Rad ")

def version(title):
    t = re.sub(r"^(BMW|MINI)\s+", "", title or "").strip()
    t = re.sub(r"\b(Rad|rad)\s+\d\s*", "", t)
    t = re.sub(r"\s+(A/T|AT|Sedan|Touring|Gran Coup[eé]|Coup[eé]|Cabrio|Active Tourer|Gran Tourer|Sports Activity.*|M Sport.*|Luxury Line.*|xLine.*|Sport Line.*)$", "", t)
    return t.strip()

def fuel_norm(f):
    f = (f or "").lower()
    if "elektr" in f and "hybrid" not in f: return "Elektro"
    if "hybrid" in f or "plug" in f: return "Hybrid"
    if "diesel" in f or "nafta" in f: return "Diesel"
    if "benz" in f: return "Benzín"
    return f.capitalize() or "—"

def days(a, b):
    try:
        return (datetime.date.fromisoformat(b) - datetime.date.fromisoformat(a)).days
    except Exception:
        return ""

# ---------- načítanie snímok ----------
used = json.load(open(ROOT / "data" / "used" / f"{day}.json"))["cars"]
stock = json.load(open(ROOT / "data" / "dealers" / f"{day}.json"))["cars"]

# ---------- jazdené (portál) ----------
used_rows = []
for c in used:
    dealer = (c["dealer"] or "").replace(", s.r.o.", "").replace(" s.r.o.", "").replace(" s.r.o", "")
    dealer = re.sub(r"\s*-\s*Váš predaj.*", "", dealer).strip()
    used_rows.append({
        "vin": c["vin"], "dealer": dealer, "mesto": c["city"], "lion_car": "áno" if LION in (c["dealer"] or "") else "nie",
        "znacka": c["brand"], "model": model_family(c["title"], c["series"]) if c["brand"] == "BMW" else c["brand"],
        "verzia": version(c["title"]), "nazov": c["title"], "karoseria": c["body"], "kod_rady": c["seriesCode"],
        "palivo": fuel_norm(c["fuel"]), "kw": c["kw"], "k": c["hp"],
        "motorizacia": f"{version(c['title'])} · {c['kw']} kW",
        "rok": c["year"], "registracia": c["registration"], "km": c["km"],
        "cena": c["price"], "cena_novy": c["newPrice"] or "",
        "pokles_z_novej_pct": round(100 * (1 - c["price"] / c["newPrice"]), 1) if c.get("newPrice") and c.get("price") else "",
        "premium_selection": "áno" if c["premium"] else "nie", "odpocet_dph": "áno" if c["vat"] else "nie",
        "v_ponuke_od": c["created"], "dni_v_ponuke": days(c["created"], day),
        "rezervovane": "áno" if c["reserved"] else "nie",
    })

# ---------- sklad z webov dealerov ----------
OTHER = ("Volkswagen", "Škoda", "Audi", "Mercedes", "Toyota", "Ford", "Hyundai", "Kia", "Peugeot", "Seat", "Honda", "Volvo", "Porsche")
def brand_of(title):
    t = title or ""
    if re.search(r"\bMINI\b", t, re.I): return "MINI"
    for b in OTHER:
        if b.lower() in t.lower(): return b
    return "BMW"
stock_rows = []
for c in stock:
    c["brand"] = brand_of(c["title"])
    lp, pr = c.get("listPrice"), c.get("price")
    stock_rows.append({
        "vin": c["vin"], "dealer": c["dealer"], "mesto": c["city"], "lion_car": "áno" if c["dealer"] == LION else "nie",
        "typ": c["kind"], "dostupnost": "na sklade" if c["onStock"] else ("na ceste" if c["onWay"] else c["availability"]),
        "stav": "predané" if c["sold"] else ("rezervované" if c["reserved"] else "v ponuke"),
        "znacka": c["brand"], "model": model_family(c["title"]) if c["brand"] == "BMW" else c["brand"],
        "verzia": version(c["title"]), "nazov": c["title"], "palivo": fuel_norm(c["fuel"]), "kw": c["kw"] or "",
        "motorizacia": f"{version(c['title'])} · {c['kw']} kW" if c["kw"] else version(c["title"]),
        "rok": c["registration"], "km": c["km"] if c["km"] is not None else "",
        "cena": pr or "", "cena_bez_dph": c.get("priceNoVat") or "", "cennikova_cena": lp or "",
        "zlava": c.get("discount") or (lp - pr if lp and pr and lp > pr else ""),
        "zlava_pct": round(100 * (lp - pr) / lp, 1) if lp and pr and lp > pr else "",
        "url": c["url"],
    })

# ---------- porovnanie so včerajškom ----------
state = json.loads(STATE.read_text()) if STATE.exists() else {"used": {}, "stock": {}, "last_day": None}
events = []
if EVENTS_IN.exists():
    events = list(csv.DictReader(open(EVENTS_IN, encoding="utf-8")))
    events = [e for e in events if e["datum"] != day]  # opakovaný beh v ten istý deň
    limit = (datetime.date.fromisoformat(day) - datetime.timedelta(days=180)).isoformat()
    events = [e for e in events if e["datum"] >= limit]  # denník drží posledných 180 dní

def diff(src, rows, key_state):
    prev = state[key_state]
    cur = {}
    first_run = not prev
    for r in rows:
        k = f"{r['dealer']}|{r['vin']}"
        p = prev.get(k)
        sold_flag = r.get("stav") == "predané"
        res_flag = r.get("rezervovane") == "áno" or r.get("stav") == "rezervované"
        cur[k] = {"first_seen": p["first_seen"] if p else (r.get("v_ponuke_od") or day), "cena": r["cena"],
                  "sold": sold_flag, "reserved": res_flag, "nazov": r["nazov"], "model": r["model"],
                  "dealer": r["dealer"], "vin": r["vin"], "typ": r.get("typ", "Jazdené")}
        if first_run:
            continue
        base = {"datum": day, "zdroj": src, "dealer": r["dealer"], "vin": r["vin"], "nazov": r["nazov"],
                "model": r["model"], "typ": r.get("typ", "Jazdené"), "cena_pred": "", "cena_po": r["cena"],
                "dni_v_ponuke": days(cur[k]["first_seen"], day)}
        if not p:
            events.append({**base, "udalost": "Nové v ponuke"})
            continue
        if sold_flag and not p.get("sold"):
            events.append({**base, "udalost": "Označené ako predané"})
        elif res_flag and not p.get("reserved"):
            events.append({**base, "udalost": "Rezervované"})
        if p.get("cena") and r["cena"] and p["cena"] != r["cena"]:
            events.append({**base, "udalost": "Zmena ceny", "cena_pred": p["cena"]})
    if not first_run:
        for k, p in prev.items():
            if k not in cur:
                events.append({"datum": day, "zdroj": src, "dealer": p["dealer"], "vin": p["vin"], "nazov": p["nazov"],
                               "model": p["model"], "typ": p.get("typ", ""), "cena_pred": p["cena"], "cena_po": "",
                               "dni_v_ponuke": days(p["first_seen"], day),
                               "udalost": "Zmizlo z ponuky (predané)" if not p.get("sold") else "Odstránené (už predané)"})
    state[key_state] = cur
    return first_run

fr1 = diff("Portál BMW (jazdené)", used_rows, "used")
fr2 = diff("Weby dealerov", stock_rows, "stock")
for r in stock_rows:  # dni v ponuke podľa prvého videnia
    r["prvy_krat_videne"] = state["stock"][f"{r['dealer']}|{r['vin']}"]["first_seen"]
    r["dni_v_ponuke"] = days(r["prvy_krat_videne"], day)
state["last_day"] = day

def write(name, rows, fields=None):
    fields = fields or (list(rows[0].keys()) if rows else [])
    with open(OUT / name, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); w.writeheader(); w.writerows(rows)

write("jazdene_trh.csv", used_rows)
write("sklad_dealerov.csv", stock_rows)
EV_FIELDS = ["datum", "zdroj", "udalost", "dealer", "model", "nazov", "typ", "vin", "cena_pred", "cena_po", "dni_v_ponuke"]
events.sort(key=lambda e: (e["datum"], e["zdroj"], e["dealer"]), reverse=True)
write("udalosti.csv", events, EV_FIELDS)
STATE.write_text(json.dumps(state, ensure_ascii=False))
print(f"{day}: jazdené {len(used_rows)}, sklad {len(stock_rows)}, udalosti spolu {len(events)}"
      + (" (prvý beh – východiskový stav, udalosti od zajtra)" if fr1 and fr2 else ""))
