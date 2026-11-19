#!/usr/bin/env python3
"""Stiahne ponuku vozidiel (nové, predvádzacie, manažérske, jazdené) z webov
všetkých BMW dealerov na Slovensku (rovnaká platforma /ponuka-vozidiel)
a uloží denný snímok do data/dealers/YYYY-MM-DD.json"""
import json, re, time, datetime, pathlib, sys, urllib.request, urllib.error
from bs4 import BeautifulSoup

DEALERS = [  # oficiálny zoznam BMW SK (dealer locator), predajné body.
    # Skupiny so spoločným skladom na webe (overené 19.11.2026 podľa VIN) sa sťahujú raz.
    ("LION CAR", "Banská Bystrica", "https://bmw-lioncar.sk"),
    ("Auto Palace Bratislava", "Bratislava", "https://autopalacebratislava.sk"),
    ("Bavaria BA + TT", "Bratislava / Trnava", "https://bavariabratislava.sk"),
    ("Dunauto DS", "Dunajská Streda", "https://bmw.dunauto.com"),
    ("RIJA - Bavaria", "Nitra", "https://rijabavaria.sk"),
    ("T.O.B. + MD-Bavaria", "Trenčín / Žilina", "https://tob-bmw.sk"),
    ("Regnum PO + KE", "Prešov / Košice", "https://regnum-bavaria.sk"),
]
# zrkadlové weby (rovnaký sklad): bavariatt.sk, bmw-zilina.sk, regnum-kosice.sk
OUT = pathlib.Path(__file__).parent / "data" / "dealers"
UA = {"User-Agent": "LionCar-market-monitor/1.0"}
KIND = {"new": "Nové", "demo": "Predvádzacie", "manager": "Manažérske", "used": "Jazdené"}

def get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
            return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise

def num(s):
    s = re.sub(r"[^\d]", "", s or "")
    return int(s) if s else None

def txt(el):
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)) if el else ""

def parse_card(card, base):
    cls = card.get("class", [])
    a = card.select_one("h2 a")
    href = a["href"] if a else ""
    cid = card.select_one("[car-id]")
    kind = next((k for k in KIND if k in cls), "other")
    stickers = [txt(s) for s in card.select(".stickers .sticker")]
    def row(sel):
        r = card.select_one(sel)
        return num(txt(r.select_one(".value"))) if r else None
    action = card.select_one(".prices .row.action")
    no_vat = num(txt(action.select_one(".dph")).replace("bez DPH", "")) if action and action.select_one(".dph") else None
    tags = {t: txt(card.select_one(f".tag.{t}")) for t in ("registration", "mileage", "fuel", "power", "vin", "availability")}
    kw = re.search(r"(\d+)\s*kW", tags["power"])
    title = txt(a)
    return {
        "carId": cid["car-id"] if cid else href.rsplit("-", 1)[-1],
        "url": base + href if href.startswith("/") else href,
        "title": title,
        "brand": "MINI" if title.upper().startswith("MINI") else ("BMW" if title.upper().startswith("BMW") else title.split(" ")[0]),
        "kind": KIND.get(kind, "Iné"),
        "onStock": "stock" in cls, "onWay": "way" in cls,
        "sold": any(s.lower() == "predané" for s in stickers),
        "reserved": any(s.lower() == "rezervované" for s in stickers),
        "stickers": stickers,
        "price": row(".prices .row.action"), "priceNoVat": no_vat,
        "listPrice": row(".prices .row.price"), "discount": row(".prices .row.sale"),
        "registration": tags["registration"], "km": num(tags["mileage"]),
        "fuel": tags["fuel"], "kw": int(kw.group(1)) if kw else None,
        "vin": tags["vin"].replace(" ", "") or None, "availability": tags["availability"],
    }

def fetch_dealer(name, city, base):
    cars, seen, page = [], set(), 1
    while page < 60:
        html = get(f"{base}/ponuka-vozidiel" + (f"/page:{page}" if page > 1 else ""))
        if html is None:
            break
        soup = BeautifulSoup(html, "html.parser")
        new = 0
        for card in soup.select("#filter_content > .cell.item"):
            c = parse_card(card, base)
            if c["carId"] in seen:
                continue
            seen.add(c["carId"]); new += 1
            c.update(dealer=name, city=city)
            cars.append(c)
        if new == 0:
            break
        page += 1
        time.sleep(1.5)
    return cars

def main():
    allcars, status = [], {}
    for name, city, base in DEALERS:
        try:
            cars = fetch_dealer(name, city, base)
            status[name] = len(cars)
            allcars += cars
            print(f"{name}: {len(cars)}")
        except Exception as e:
            status[name] = f"CHYBA: {e}"
            print(f"{name}: CHYBA {e}", file=sys.stderr)
    OUT.mkdir(parents=True, exist_ok=True)
    day = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1))).date().isoformat()
    (OUT / f"{day}.json").write_text(json.dumps({"date": day, "status": status, "cars": allcars},
                                                ensure_ascii=False, indent=0))
    print(f"{day}: spolu {len(allcars)} vozidiel")

if __name__ == "__main__":
    main()
