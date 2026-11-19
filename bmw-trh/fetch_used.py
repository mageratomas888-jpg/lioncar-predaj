#!/usr/bin/env python3
"""Stiahne kompletnú ponuku jazdených BMW všetkých SK dealerov z bezcakania.bmw.sk
a uloží denný snímok do data/used/YYYY-MM-DD.json"""
import json, time, datetime, pathlib, urllib.request, sys

API = "https://bezcakania.bmw.sk/jazdene/api/v1/ems/bmw-used-sk_SK/search"
OUT = pathlib.Path(__file__).parent / "data" / "used"
PAGE = 50

def post(body):
    req = urllib.request.Request(API, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json",
                                          "User-Agent": "LionCar-market-monitor/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def L(x):
    return (x or {}).get("label", "") if isinstance(x, dict) else ""

def slim(v):
    d = v.get("dealer") or {}
    return {
        "id": v.get("id"), "vin": v.get("vin17"), "isNew": v.get("isNew"),
        "brand": L(v.get("brand")), "series": L(v.get("series")), "body": L(v.get("bodyType")),
        "seriesCode": v.get("seriesCode"), "modelCode": v.get("modelCode"), "title": v.get("title"),
        "year": v.get("productionYear"), "registration": (v.get("registration") or "")[:10],
        "km": v.get("mileage"), "fuel": L(v.get("fuel")), "kw": v.get("powerKW"), "hp": v.get("powerHP"),
        "ccm": v.get("capacity"), "gear": L(v.get("transmission")), "color": L(v.get("color")),
        "warranty": v.get("warranty"), "vat": v.get("vatReclaimable"),
        "newPrice": v.get("newPrice"), "optionsPrice": v.get("optionsPrice"), "price": v.get("transactionalPrice"),
        "premium": any(c.get("label") == "bmw-premiumselection" for c in v.get("campaigns") or []),
        "dealerId": d.get("id"), "dealer": d.get("name"), "city": d.get("city"),
        "created": (v.get("created") or "")[:10], "ageMonths": v.get("age"),
        "reserved": v.get("reserved"), "reservationStatus": v.get("reservationStatus"),
    }

def main():
    rows, skip = [], 0
    while True:
        j = post({"$match": {}, "$skip": skip, "$limit": PAGE})
        lst = j.get("$list", [])
        rows += [slim(v) for v in lst]
        total = j["$count"]["$total"]
        skip += PAGE
        if not lst or skip >= total:
            break
        time.sleep(1)
    if len(rows) != total:
        print(f"VAROVANIE: stiahnuté {len(rows)} z {total}", file=sys.stderr)
    OUT.mkdir(parents=True, exist_ok=True)
    day = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1))).date().isoformat()
    (OUT / f"{day}.json").write_text(json.dumps({"date": day, "total": total, "cars": rows},
                                                ensure_ascii=False, indent=0))
    print(f"{day}: {len(rows)} jazdených áut uložených")

if __name__ == "__main__":
    main()
