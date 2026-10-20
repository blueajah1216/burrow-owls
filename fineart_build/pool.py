import json, glob, re, requests, warnings, time
warnings.filterwarnings("ignore")
from q3 import sparql
base=json.load(open("base2.json")); gal=json.load(open("../data/fineart/gallery.json"))
galids={p["id"] for p in gal["paintings"]}
pool={}
def add(qid,title,sl,year,aq,al,img,src,have=False,pid=None):
    o=pool.setdefault(qid,{"qid":qid,"title":title,"sl":sl,"year":year,"artists":[],"img":img,"src":set(),"have":have,"id":pid})
    if aq not in [a[0] for a in o["artists"]]: o["artists"].append((aq,al))
    o["src"].add(src); o["sl"]=max(o["sl"],sl)
for p in base["paintings"]:
    if p["id"] in galids:
        for a in p["artist_ids"]: add(p["qid"],p["title"],p["sl"],p["year"],a,base["artists"][a]["name"],None,"have",True,p["id"])
for f in glob.glob("cand_*.json"):
    src=f[5:-5].replace("_art","")
    for b in json.load(open(f)):
        q=b["p"]["value"].rsplit("/",1)[1]
        if re.match(r"^Q\d+$",b["pLabel"]["value"]): continue
        yr=int(b["inc"]["value"][:4]) if "inc" in b and not b["inc"]["value"].startswith("-") else None
        if yr is None or yr<1700 or yr>1929: continue
        if q in pool and pool[q]["have"]: pool[q]["src"].add(src); continue
        add(q,b["pLabel"]["value"],int(b["sl"]["value"]),yr,b["a"]["value"].rsplit("/",1)[1],b["aLabel"]["value"],b["img"]["value"],src)
SPECIAL=["Q252485","Q3565037","Q5826309","Q21127606","Q83562223","Q17227585","Q18173386","Q79937255"]
vals=" ".join("wd:"+q for q in SPECIAL)
for b in sparql(f"""SELECT ?p ?pLabel ?img ?inc ?sl ?a ?aLabel ?death ?birth WHERE {{ VALUES ?p {{ {vals} }} ?p wdt:P170 ?a . ?p wdt:P18 ?img . ?p wikibase:sitelinks ?sl . OPTIONAL {{ ?p wdt:P571 ?inc }} SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}"""):
    q=b["p"]["value"].rsplit("/",1)[1]; yr=int(b["inc"]["value"][:4]) if "inc" in b else 1830
    add(q,b["pLabel"]["value"],int(b["sl"]["value"])+30,yr,b["a"]["value"].rsplit("/",1)[1],b["aLabel"]["value"],b["img"]["value"],"special")
print(len(pool),"pool;",sum(1 for p in pool.values() if p["have"]),"existing")
aq=sorted({a[0] for p in pool.values() for a in p["artists"]})
meta={}
for i in range(0,len(aq),80):
    vals=" ".join("wd:"+q for q in aq[i:i+80])
    Q=f"""SELECT ?a ?aL ?cL ?bcL ?eL WHERE {{ VALUES ?a {{ {vals} }}
      OPTIONAL {{ ?a rdfs:label ?aL FILTER(LANG(?aL)='en') }}
      OPTIONAL {{ ?a wdt:P27 ?c . ?c rdfs:label ?cL FILTER(LANG(?cL)='en') }}
      OPTIONAL {{ ?a wdt:P19/wdt:P17 ?bc . ?bc rdfs:label ?bcL FILTER(LANG(?bcL)='en') }}
      OPTIONAL {{ ?a wdt:P172 ?e . ?e rdfs:label ?eL FILTER(LANG(?eL)='en') }} }}"""
    for b in sparql(Q):
        q=b["a"]["value"].rsplit("/",1)[1]; m=meta.setdefault(q,{"name":"","cit":set(),"born":set(),"eth":set()})
        if "aL" in b: m["name"]=b["aL"]["value"]
        if "cL" in b: m["cit"].add(b["cL"]["value"])
        if "bcL" in b: m["born"].add(b["bcL"]["value"])
        if "eL" in b: m["eth"].add(b["eL"]["value"])
    time.sleep(1)
for m in meta.values():
    for k in("cit","born","eth"): m[k]=sorted(m[k])
for p in pool.values(): p["src"]=sorted(p["src"])
json.dump({"pool":pool,"meta":meta},open("pool.json","w"),ensure_ascii=False)
print(len(meta),"artists")
