"""Build base3.json: the new paintings needed by the collections (not already in gallery.json)."""
import json,re,unicodedata,urllib.parse,time,requests,warnings
warnings.filterwarnings("ignore")
from q3 import sparql,H
d=json.load(open("sel.json")); sel,pool=d["sel"],d["pool"]
gal=json.load(open("../data/fineart/gallery.json")); used={p["id"] for p in gal["paintings"]}
newq=sorted({q for v in sel.values() for q in v if not pool[q]["have"]},key=lambda q:-pool[q]["sl"])
def slug(s):
    s=unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+","-",s).strip("-")
P=[]
for q in newq:
    p=pool[q]
    base=slug(p["title"])[:55] or q.lower()
    sid=base
    if sid in used: sid=f"{base}-{slug(p['artists'][0][1])[:14]}"
    n=2
    while sid in used: sid=f"{base}-{n}"; n+=1
    used.add(sid)
    img=p["img"]
    if not img: continue
    fn=urllib.parse.unquote(img.rsplit("/",1)[1]).replace(" ","_")
    P.append({"id":sid,"qid":q,"title":p["title"],"year":p["year"],"sl":p["sl"],"artist_ids":[a[0] for a in p["artists"]],"file":fn,"cc":p["cc"],"jew":p["jew"]})
print(len(P),"new paintings")
# artist details
aq=sorted({a for p in P for a in p["artist_ids"]})
have=set(gal["artists"].keys()) if False else set()
A={}
for i in range(0,len(aq),80):
    vals=" ".join("wd:"+q for q in aq[i:i+80])
    Q=f"""SELECT ?a ?aL ?b ?dd ?bpL ?dpL WHERE {{ VALUES ?a {{ {vals} }}
      OPTIONAL {{ ?a rdfs:label ?aL FILTER(LANG(?aL)='en') }} OPTIONAL {{ ?a wdt:P569 ?b }} OPTIONAL {{ ?a wdt:P570 ?dd }}
      OPTIONAL {{ ?a wdt:P19 ?bp . ?bp rdfs:label ?bpL FILTER(LANG(?bpL)='en') }} OPTIONAL {{ ?a wdt:P20 ?dp . ?dp rdfs:label ?dpL FILTER(LANG(?dpL)='en') }} }}"""
    for b in sparql(Q):
        q=b["a"]["value"].rsplit("/",1)[1]; o=A.setdefault(q,{})
        if "aL" in b: o.setdefault("name",b["aL"]["value"])
        if "b" in b: o.setdefault("birth",b["b"]["value"][:10])
        if "dd" in b: o.setdefault("death",b["dd"]["value"][:10])
        if "bpL" in b: o.setdefault("born_in",b["bpL"]["value"])
        if "dpL" in b: o.setdefault("died_in",b["dpL"]["value"])
    time.sleep(1)
# Commons imageinfo
files=[p["file"] for p in P]; info={}
for i in range(0,len(files),40):
    chunk=files[i:i+40]
    r=requests.get("https://commons.wikimedia.org/w/api.php",params={"action":"query","format":"json","titles":"|".join("File:"+f for f in chunk),"prop":"imageinfo","iiprop":"url|size|mime|extmetadata","iiurlwidth":1280,"iiextmetadatafilter":"LicenseShortName"},headers=H,timeout=60).json()
    for pg in r["query"]["pages"].values():
        if "imageinfo" in pg: info[pg["title"][5:].replace(" ","_")]=pg["imageinfo"][0]
    time.sleep(0.6)
out=[]
for p in P:
    ii=info.get(p["file"])
    if not ii or not ii["mime"].startswith("image/"): continue
    p["w"],p["h"]=ii["width"],ii["height"]; p["thumb"]=ii.get("thumburl"); p["page"]=ii["descriptionurl"]
    p["lic"]=ii.get("extmetadata",{}).get("LicenseShortName",{}).get("value","")
    out.append(p)
print(len(out),"with images")
json.dump({"paintings":out,"artists":A},open("base3.json","w"),ensure_ascii=False)
