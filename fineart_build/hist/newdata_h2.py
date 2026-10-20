"""resolved.json -> ../base4.json (facts for new history paintings + their artists)."""
import json, re, unicodedata, time, requests, warnings, sys, os
warnings.filterwarnings("ignore"); sys.path.insert(0,"..")
from q3 import sparql, H
R=json.load(open("resolved.json"))
gal=json.load(open("../../data/fineart/gallery.json")); used={p["id"] for p in gal["paintings"]}
gart={a["n"].lower():q for q,a in gal["artists"].items()}
def slug(s):
    s=unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+","-",s).strip("-")
cache=json.load(open("artist_q_cache.json")) if os.path.exists("artist_q_cache.json") else {}
ROLE=re.compile(r"painter|artist|illustrator|photographer|engraver|printmaker|draughtsman|draftsman|sculptor|caricaturist|lithographer|miniaturist|cartoonist|poster|muralist|illuminator|etcher",re.I)
def find_artist(name):
    key=name.lower()
    if key in gart: return gart[key]
    if key in cache: return cache[key]
    r=requests.get("https://www.wikidata.org/w/api.php",params={"action":"wbsearchentities","search":name,"language":"en","type":"item","limit":8,"format":"json"},headers=H,timeout=30).json()
    q=None
    for s in r.get("search",[]):
        if ROLE.search(s.get("description","")) and s.get("label","").lower()==key: q=s["id"]; break
    if not q:
        for s in r.get("search",[]):
            if ROLE.search(s.get("description","")): q=s["id"]; break
    cache[key]=q; time.sleep(.25); return q
P=[]; seenfile={}; A={}; synth={}
for slug_,items in R.items():
    for d in items:
        if "new" not in d: continue
        n=d["new"]
        if n["file"] in seenfile: d["new"]["id"]=seenfile[n["file"]]; continue
        base=slug(n["title"])[:55] or "work"; sid=base
        if sid in used: sid=(base+"-"+slug(n.get("artist_name") or (n["artists"][0][1][0] if n.get("artists") else ""))[:14]).rstrip("-")
        k=2
        while sid in used: sid=f"{base}-{k}"; k+=1
        used.add(sid); seenfile[n["file"]]=sid; n["id"]=sid
        aids=[]
        if n.get("artists"):
            aids=[q for q,_ in n["artists"]]
        else:
            nm=n["artist_name"]
            if nm.startswith("?"):
                sy="x-"+slug(nm[1:])[:40]; synth[sy]=nm[1:]; aids=[sy]
            else:
                q=find_artist(nm)
                if q: aids=[q]; A.setdefault(q,{}).setdefault("name",nm)
                else:
                    sy="x-"+slug(nm)[:40]; synth[sy]=nm; aids=[sy]
        P.append({"id":sid,"qid":n.get("qid"),"title":n["title"],"year":n["year"],"sl":0,"artist_ids":aids,"file":n["file"],"med":n.get("med","")})
json.dump(cache,open("artist_q_cache.json","w"))
print(len(P),"new paintings;",len(synth),"synthetic artists")
aq=sorted({a for p in P for a in p["artist_ids"] if a.startswith("Q")})
for i in range(0,len(aq),80):
    vals=" ".join("wd:"+q for q in aq[i:i+80])
    Q=f"""SELECT ?a ?aL ?b ?dd ?bpL ?dpL WHERE {{ VALUES ?a {{ {vals} }}
      OPTIONAL {{ ?a rdfs:label ?aL FILTER(LANG(?aL)='en') }} OPTIONAL {{ ?a wdt:P569 ?b }} OPTIONAL {{ ?a wdt:P570 ?dd }}
      OPTIONAL {{ ?a wdt:P19 ?bp . ?bp rdfs:label ?bpL FILTER(LANG(?bpL)='en') }} OPTIONAL {{ ?a wdt:P20 ?dp . ?dp rdfs:label ?dpL FILTER(LANG(?dpL)='en') }} }}"""
    for b in sparql(Q):
        q=b["a"]["value"].rsplit("/",1)[1]; o=A.setdefault(q,{})
        if "aL" in b: o["name"]=b["aL"]["value"]
        if "b" in b: o.setdefault("birth",b["b"]["value"][:10])
        if "dd" in b: o.setdefault("death",b["dd"]["value"][:10])
        if "bpL" in b: o.setdefault("born_in",b["bpL"]["value"])
        if "dpL" in b: o.setdefault("died_in",b["dpL"]["value"])
    time.sleep(1)
for sy,nm in synth.items(): A[sy]={"name":nm,"synthetic":True}
# images
files=[p["file"] for p in P]; info={}
for i in range(0,len(files),40):
    chunk=files[i:i+40]
    r=requests.get("https://commons.wikimedia.org/w/api.php",params={"action":"query","format":"json","titles":"|".join("File:"+f.replace("_"," ") for f in chunk),"prop":"imageinfo","iiprop":"url|size|mime|extmetadata","iiurlwidth":1280,"iiextmetadatafilter":"LicenseShortName"},headers=H,timeout=60).json()
    norm={n["to"]:n["from"] for n in r["query"].get("normalized",[])}
    for pg in r["query"]["pages"].values():
        if "imageinfo" in pg: info[pg["title"][5:].replace(" ","_")]=pg["imageinfo"][0]
    time.sleep(.7)
out=[]; bad=[]
for p in P:
    ii=info.get(p["file"])
    if not ii or not ii["mime"].startswith("image/"): bad.append((p["id"],p["file"])); continue
    p["w"],p["h"]=ii["width"],ii["height"]; p["thumb"]=ii.get("thumburl"); p["page"]=ii["descriptionurl"]
    p["lic"]=ii.get("extmetadata",{}).get("LicenseShortName",{}).get("value",""); out.append(p)
print(len(out),"with images; missing:",bad)
import collections; print(collections.Counter(p["lic"] for p in out).most_common(12))
print("small:",[(p["id"],p["w"]) for p in out if p["w"]<700])
json.dump({"paintings":out,"artists":A},open("../base4.json","w"),ensure_ascii=False)
json.dump(R,open("resolved.json","w"),ensure_ascii=False,indent=0)
