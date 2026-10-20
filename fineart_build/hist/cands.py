import json, time, sys, os, requests, re
from events import EV
H={"User-Agent":"BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
cache=json.load(open("qid_cache.json"))
os.makedirs("cand",exist_ok=True)
def sparql(q):
    for a in range(5):
        r=requests.get("https://query.wikidata.org/sparql",params={"query":q,"format":"json"},headers=H,timeout=180)
        if r.status_code==200: return r.json()["results"]["bindings"]
        time.sleep(8*(a+1))
    raise SystemExit("sparql failed "+str(r.status_code))
only=sys.argv[1:]
for slug,era,title,s,e,terms in EV:
    if only and slug not in only: continue
    if os.path.exists(f"cand/{slug}.json") and not only: continue
    qs=sorted({cache[t][0] for t in terms if cache.get(t)})
    rows={}
    for i in range(0,len(qs),25):
        vals=" ".join("wd:"+q for q in qs[i:i+25])
        Q=f"""SELECT ?p ?pLabel ?img ?inc ?sl ?artist ?artistLabel ?death ?ev ?evLabel WHERE {{
          VALUES ?ev {{ {vals} }}
          {{ ?p wdt:P921 ?ev }} UNION {{ ?p wdt:P180 ?ev }} UNION {{ ?p wdt:P921 ?sub . ?sub wdt:P361 ?ev }} UNION {{ ?p wdt:P180 ?sub . ?sub wdt:P361 ?ev }}
          VALUES ?type {{ wd:Q3305213 wd:Q11060274 wd:Q93184 }} ?p wdt:P31 ?type .
          ?p wdt:P18 ?img . ?p wikibase:sitelinks ?sl .
          OPTIONAL {{ ?p wdt:P571 ?inc }} OPTIONAL {{ ?p wdt:P170 ?artist . OPTIONAL {{ ?artist wdt:P570 ?death }} }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}"""
        for b in sparql(Q):
            q=b["p"]["value"].rsplit("/",1)[1]
            o=rows.setdefault(q,{"qid":q,"title":b["pLabel"]["value"],"img":b["img"]["value"],"sl":int(b["sl"]["value"]),"year":None,"artists":{},"evs":set()})
            if "inc" in b and o["year"] is None:
                m=re.match(r"^(-?\d{4})",b["inc"]["value"]); o["year"]=int(m.group(1)) if m else None
            if "artist" in b: o["artists"][b["artist"]["value"].rsplit("/",1)[1]]=[b["artistLabel"]["value"], b["death"]["value"][:4] if "death" in b else None]
            o["evs"].add(b["evLabel"]["value"])
        time.sleep(1.5)
    out=[dict(v,evs=sorted(v["evs"])) for v in rows.values()]
    out.sort(key=lambda x:-x["sl"])
    json.dump(out,open(f"cand/{slug}.json","w"),ensure_ascii=False)
    print(slug,len(out),flush=True)
