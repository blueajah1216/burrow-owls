import json, requests, warnings, time, re
warnings.filterwarnings("ignore")
H={"User-Agent":"BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
def sparql(Q):
    for t in range(5):
        r=requests.get("https://query.wikidata.org/sparql",params={"query":Q,"format":"json"},headers=H,timeout=100)
        if r.status_code==200: return r.json()["results"]["bindings"]
        print("retry",r.status_code,r.text[:80]); time.sleep(8)
    raise SystemExit("failed")
allp=json.load(open("allp.json")); qids=[p["qid"] for p in allp]
pv={}   # painting -> (venue qid, label, kind)
for i in range(0,len(qids),150):
    vals=" ".join("wd:"+q for q in qids[i:i+150])
    for prop in ("P276","P195"):
        Q=f"SELECT ?p ?v ?vL WHERE {{ VALUES ?p {{ {vals} }} ?p wdt:{prop} ?v . ?v rdfs:label ?vL FILTER(LANG(?vL)='en') }}"
        for b in sparql(Q):
            q=b["p"]["value"].rsplit("/",1)[1]
            pv.setdefault(q,(b["v"]["value"].rsplit("/",1)[1],b["vL"]["value"]))
    print(i,len(pv),end="\r"); time.sleep(1)
print("\npaintings with venue",len(pv))
venues=sorted({v[0] for v in pv.values()})
vi={}
for i in range(0,len(venues),100):
    vals=" ".join("wd:"+q for q in venues[i:i+100])
    Q=f"""SELECT ?v ?locL ?ctryL WHERE {{ VALUES ?v {{ {vals} }}
      OPTIONAL {{ ?v wdt:P131 ?loc . ?loc rdfs:label ?locL FILTER(LANG(?locL)='en') }}
      OPTIONAL {{ ?v wdt:P17 ?c . ?c rdfs:label ?ctryL FILTER(LANG(?ctryL)='en') }} }}"""
    for b in sparql(Q):
        q=b["v"]["value"].rsplit("/",1)[1]; o=vi.setdefault(q,{})
        if "locL" in b: o.setdefault("loc",b["locL"]["value"])
        if "ctryL" in b: o.setdefault("country",b["ctryL"]["value"])
    time.sleep(1)
out={}
for q,(v,label) in pv.items():
    o={"venue":label}; x=vi.get(v,{})
    loc=x.get("loc","")
    m=re.search(r"arrondissement of (.+)$",loc)
    if m: loc=m.group(1)
    if loc and loc!=label: o["city"]=loc
    if x.get("country"): o["country"]=x["country"]
    out[q]=o
json.dump(out,open("loc.json","w"),ensure_ascii=False,indent=0)
print(len(out),"of",len(qids))
