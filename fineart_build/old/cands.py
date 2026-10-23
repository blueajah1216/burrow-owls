"""Candidate paintings made 1426-1725, per 5 years, ranked by Wikipedia sitelinks. -> cands.json"""
import json, re, sys, time, warnings
warnings.filterwarnings("ignore"); sys.path.insert(0, "..")
from q3 import sparql
rows = {}
for y in range(1426, 1726, 5):
    Q = f"""SELECT ?p ?pLabel ?img ?inc ?sl ?a ?aLabel ?death WHERE {{
      ?p wdt:P31 wd:Q3305213 . ?p wdt:P571 ?inc . FILTER(YEAR(?inc) >= {y} && YEAR(?inc) < {y+5})
      ?p wdt:P18 ?img . ?p wikibase:sitelinks ?sl . FILTER(?sl >= 3)
      OPTIONAL {{ ?p wdt:P170 ?a . OPTIONAL {{ ?a wdt:P570 ?death }} }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }} ORDER BY DESC(?sl) LIMIT 400"""
    n = 0
    for b in sparql(Q):
        q = b["p"]["value"].rsplit("/", 1)[1]
        m = re.match(r"^(-?\d{4})", b["inc"]["value"])
        r = rows.setdefault(q, {"qid": q, "title": b["pLabel"]["value"], "img": b["img"]["value"], "sl": int(b["sl"]["value"]),
                                "year": int(m.group(1)) if m else None, "arts": {}})
        if "a" in b: r["arts"][b["a"]["value"].rsplit("/", 1)[1]] = b.get("aLabel", {}).get("value", "")
        n += 1
    print(y, n, len(rows), flush=True); time.sleep(1.5)
json.dump(list(rows.values()), open("cands.json", "w"), ensure_ascii=False)
