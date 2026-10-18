"""Resolve each venue to a real city by walking P131 (located in) until we hit a city/town/commune."""
import json, requests, warnings, time
warnings.filterwarnings("ignore")
H={"User-Agent":"BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
def sparql(Q):
    for t in range(5):
        r=requests.get("https://query.wikidata.org/sparql",params={"query":Q,"format":"json"},headers=H,timeout=100)
        if r.status_code==200: return r.json()["results"]["bindings"]
        time.sleep(8)
    raise SystemExit("fail")
g=json.load(open("../data/fineart/gallery.json")); d=json.load(open("base2.json")); l=json.load(open("loc.json"))
ids={p["id"]:p["qid"] for p in d["paintings"]}
# need venue QIDs again: re-query painting->venue qid
qs=[ids[p["id"]] for p in g["paintings"]]
pv={}
for i in range(0,len(qs),150):
    vals=" ".join("wd:"+q for q in qs[i:i+150])
    for prop in ("P276","P195"):
        for b in sparql(f"SELECT ?p ?v WHERE {{ VALUES ?p {{ {vals} }} ?p wdt:{prop} ?v }}"):
            pv.setdefault(b["p"]["value"].rsplit("/",1)[1],b["v"]["value"].rsplit("/",1)[1])
    time.sleep(1)
CITYTYPES={"Q515","Q1549591","Q5119","Q1637706","Q484170","Q15284","Q747074","Q262166","Q22865","Q3957","Q2039348","Q532","Q1093829","Q200250","Q70208","Q6465","Q2074737","Q3184121","Q494721","Q17431399","Q123705","Q1187580","Q2989398","Q42744322","Q15127012","Q1907114"}
info={}  # node -> {label, parents:set, types:set}
frontier=set(pv.values()); seen=set()
for level in range(6):
    nodes=sorted(frontier-seen); seen|=set(nodes)
    if not nodes: break
    nxt=set()
    for i in range(0,len(nodes),100):
        vals=" ".join("wd:"+q for q in nodes[i:i+100])
        Q=f"""SELECT ?n ?nL ?par ?t WHERE {{ VALUES ?n {{ {vals} }}
          OPTIONAL {{ ?n rdfs:label ?nL FILTER(LANG(?nL)='en') }}
          OPTIONAL {{ ?n wdt:P131 ?par }} OPTIONAL {{ ?n wdt:P31 ?t }} OPTIONAL {{ ?n wdt:P17 ?c }} }}"""
        for b in sparql(Q):
            n=b["n"]["value"].rsplit("/",1)[1]; o=info.setdefault(n,{"label":"","par":[],"types":set()})
            if "nL" in b: o["label"]=b["nL"]["value"]
            if "par" in b:
                pq=b["par"]["value"].rsplit("/",1)[1]
                if pq not in o["par"]: o["par"].append(pq); nxt.add(pq)
            if "t" in b: o["types"].add(b["t"]["value"].rsplit("/",1)[1])
        time.sleep(1)
    frontier=nxt; print("level",level,len(info),end="\r")
def city(v):
    # BFS up the chain for first ancestor (not the venue itself) with a city-like type
    q=[(p,1) for p in info.get(v,{}).get("par",[])]; seenl=set()
    while q:
        n,dpt=q.pop(0)
        if n in seenl or dpt>6: continue
        seenl.add(n); o=info.get(n)
        if not o: continue
        if o["types"]&CITYTYPES: return o["label"]
        q+= [(p,dpt+1) for p in o["par"]]
    return None
res={}
for pid,v in pv.items():
    res[pid]={"venue_q":v,"city2":city(v)}
json.dump(res,open("loc2.json","w"),ensure_ascii=False)
print("\nresolved",sum(1 for r in res.values() if r["city2"]),"of",len(res))
