"""Venue (P276 else P195), city, country for the new works -> ../out/locations_hist.json {id: [venue, city, country]}"""
import json, re, sys, time, warnings
warnings.filterwarnings("ignore"); sys.path.insert(0, "..")
from q3 import sparql
ids = json.load(open("new_ids.json")); b4 = {p["id"]: p for p in json.load(open("../base4.json"))["paintings"]}
q2id = {b4[i]["qid"]: i for i in ids}; qids = list(q2id)
pv = {}; alt = {}
BAD = re.compile(r"^(room|hall|salle|sala|gallery of|paintings in|italian painting|italy|france|spain|germany|netherlands|.*collection$|.*storage$|.*\d.*|.*chapel.*|.*palace.*|.*castle.*)", re.I)
for prop in ("P276", "P195"):
    for i in range(0, len(qids), 150):
        vals = " ".join("wd:" + q for q in qids[i:i + 150])
        for b in sparql(f"SELECT ?p ?v ?vL WHERE {{ VALUES ?p {{ {vals} }} ?p wdt:{prop} ?v . ?v rdfs:label ?vL FILTER(LANG(?vL)='en') }}"):
            q = b["p"]["value"].rsplit("/", 1)[1]
            cur = (b["v"]["value"].rsplit("/", 1)[1], b["vL"]["value"])
            if q not in pv or (BAD.match(pv[q][1]) and not BAD.match(cur[1])): pv[q] = cur
        time.sleep(1)
print("with venue", len(pv), "of", len(qids))
venues = sorted({v[0] for v in pv.values()}); vi = {}
for i in range(0, len(venues), 100):
    vals = " ".join("wd:" + q for q in venues[i:i + 100])
    Q = f"""SELECT ?v ?locL ?ctryL WHERE {{ VALUES ?v {{ {vals} }}
      OPTIONAL {{ ?v wdt:P131 ?loc . ?loc rdfs:label ?locL FILTER(LANG(?locL)='en') }}
      OPTIONAL {{ ?v wdt:P17 ?c . ?c rdfs:label ?ctryL FILTER(LANG(?ctryL)='en') }} }}"""
    for b in sparql(Q):
        q = b["v"]["value"].rsplit("/", 1)[1]; o = vi.setdefault(q, {})
        if "locL" in b: o.setdefault("loc", b["locL"]["value"])
        if "ctryL" in b: o.setdefault("country", b["ctryL"]["value"])
    time.sleep(1)
out = json.load(open("../out/locations_hist.json")) if __import__("os").path.exists("../out/locations_hist.json") else {}
for q, (v, label) in pv.items():
    x = vi.get(v, {}); loc = x.get("loc", "")
    m = re.search(r"arrondissement of (.+)$", loc)
    if m: loc = m.group(1)
    out[q2id[q]] = [label, loc if loc != label else "", x.get("country", "")]
json.dump(out, open("../out/locations_hist.json", "w"), ensure_ascii=False)
import collections
print(collections.Counter(v[0] for k, v in out.items() if k in set(ids)).most_common(60))
