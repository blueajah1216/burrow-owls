"""python3 addq.py Q1 Q2 ... -> append cand-like records for these items to extra_cands.json (needs P18 image)"""
import sys, json, re, os, time, requests, warnings
warnings.filterwarnings("ignore"); sys.path.insert(0,"..")
from q3 import sparql
ex=json.load(open("extra_cands.json")) if os.path.exists("extra_cands.json") else {}
qs=[q for q in sys.argv[1:] if q not in ex]
for i in range(0,len(qs),40):
    vals=" ".join("wd:"+q for q in qs[i:i+40])
    Q=f"""SELECT ?p ?pLabel ?img ?inc ?sl ?artist ?artistLabel ?death WHERE {{ VALUES ?p {{ {vals} }}
      ?p wdt:P18 ?img . ?p wikibase:sitelinks ?sl . OPTIONAL {{ ?p wdt:P571 ?inc }}
      OPTIONAL {{ ?p wdt:P170 ?artist . OPTIONAL {{ ?artist wdt:P570 ?death }} }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}"""
    for b in sparql(Q):
        q=b["p"]["value"].rsplit("/",1)[1]
        o=ex.setdefault(q,{"qid":q,"title":b["pLabel"]["value"],"img":b["img"]["value"],"sl":int(b["sl"]["value"]),"year":None,"artists":{},"evs":[]})
        if "inc" in b and o["year"] is None:
            m=re.match(r"^(-?\d{4})",b["inc"]["value"]); o["year"]=int(m.group(1)) if m else None
        if "artist" in b: o["artists"][b["artist"]["value"].rsplit("/",1)[1]]=[b["artistLabel"]["value"], b["death"]["value"][:4] if "death" in b else None]
    time.sleep(1)
missing=[q for q in qs if q not in ex]
json.dump(ex,open("extra_cands.json","w"),ensure_ascii=False)
for q in qs:
    if q in ex: r=ex[q]; print(q,r["year"],r["title"][:50],"|",", ".join(v[0] for v in r["artists"].values())[:30],"| sl",r["sl"])
print("MISSING (no image/painting):",missing)
