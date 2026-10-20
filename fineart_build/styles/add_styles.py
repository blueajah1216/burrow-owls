"""Add abstract-pick QIDs (from abs_cands.json) to ../base4.json (paintings + artists)."""
import json, re, sys, time, unicodedata, urllib.parse, requests, warnings
warnings.filterwarnings("ignore"); sys.path.insert(0,"..")
from q3 import sparql, H
from abstract_picks import SECTIONS
gal=json.load(open("../../data/fineart/gallery.json")); used={p["id"] for p in gal["paintings"]}
b2=json.load(open("../base2.json")); b3=json.load(open("../base3.json"))
have={r["qid"] for r in b2["paintings"]+b3["paintings"] if r.get("qid")}
b4=json.load(open("../base4.json")); used|={p["id"] for p in b4["paintings"]}
b4q={p.get("qid") for p in b4["paintings"] if p.get("qid")}
cand={r["qid"]:r for r in json.load(open("abs_cands.json"))}
want=[x for s in SECTIONS for x in s[2] if re.match(r"^Q\d+$",x) and x not in have and x not in b4q]
def slug(s):
    s=unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+","-",s).strip("-")
new=[]
for q in want:
    r=cand.get(q)
    if not r: print("no cand",q); continue
    t=r["title"] if not re.match(r"^Q\d+$",r["title"]) else "Untitled"
    sid=slug(t)[:55]; k=2
    while sid in used: sid=f"{slug(t)[:48]}-{slug(r['artist'].split()[-1])[:10]}" if k==2 else f"{slug(t)[:48]}-{k}"; k+=1
    used.add(sid)
    new.append({"id":sid,"qid":q,"title":t,"year":r["year"],"sl":r["sl"],"artist_ids":[r["aq"]],"file":urllib.parse.unquote(r["img"].rsplit("/",1)[1]).replace(" ","_"),"med":""})
aq=sorted({a for p in new for a in p["artist_ids"] if a not in gal["artists"] and a not in b4["artists"]})
for i in range(0,len(aq),60):
    vals=" ".join("wd:"+q for q in aq[i:i+60])
    Q=f"""SELECT ?a ?aL ?b ?dd ?bpL ?dpL WHERE {{ VALUES ?a {{ {vals} }} OPTIONAL {{ ?a rdfs:label ?aL FILTER(LANG(?aL)='en') }} OPTIONAL {{ ?a wdt:P569 ?b }} OPTIONAL {{ ?a wdt:P570 ?dd }}
      OPTIONAL {{ ?a wdt:P19 ?bp . ?bp rdfs:label ?bpL FILTER(LANG(?bpL)='en') }} OPTIONAL {{ ?a wdt:P20 ?dp . ?dp rdfs:label ?dpL FILTER(LANG(?dpL)='en') }} }}"""
    for b in sparql(Q):
        q=b["a"]["value"].rsplit("/",1)[1]; o=b4["artists"].setdefault(q,{})
        if "aL" in b: o["name"]=b["aL"]["value"]
        if "b" in b: o.setdefault("birth",b["b"]["value"][:10])
        if "dd" in b: o.setdefault("death",b["dd"]["value"][:10])
        if "bpL" in b: o.setdefault("born_in",b["bpL"]["value"])
        if "dpL" in b: o.setdefault("died_in",b["dpL"]["value"])
    time.sleep(1)
files=[p["file"] for p in new]; info={}
for i in range(0,len(files),40):
    r=requests.get("https://commons.wikimedia.org/w/api.php",params={"action":"query","format":"json","titles":"|".join("File:"+f.replace("_"," ") for f in files[i:i+40]),"prop":"imageinfo","iiprop":"url|size|mime|extmetadata","iiurlwidth":1280,"iiextmetadatafilter":"LicenseShortName"},headers=H,timeout=60).json()
    for pg in r["query"]["pages"].values():
        if "imageinfo" in pg: info[pg["title"][5:].replace(" ","_")]=pg["imageinfo"][0]
    time.sleep(.7)
ok=0
for p in new:
    ii=info.get(p["file"])
    if not ii or not ii["mime"].startswith("image/"): print("no image",p["id"]); continue
    p.update(w=ii["width"],h=ii["height"],thumb=ii.get("thumburl"),page=ii["descriptionurl"],lic=ii.get("extmetadata",{}).get("LicenseShortName",{}).get("value",""))
    b4["paintings"].append(p); ok+=1
print(ok,"added;",[ (p['id'],p['lic']) for p in new if p.get('lic') and p['lic'] not in ('Public domain','CC0')])
print("small:",[(p['id'],p['w']) for p in new if p.get('w',9999)<700])
json.dump(b4,open("../base4.json","w"),ensure_ascii=False)
