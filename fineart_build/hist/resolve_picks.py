"""Resolve picks_a/picks_b into resolved.json: per event -> list of {gal:id,note} | {new:{...}}"""
import json, re, glob, urllib.parse, sys, os, requests, time, warnings
warnings.filterwarnings("ignore")
from events import EV
from picks_a import A
from picks_b import B
H={"User-Agent":"BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
PICKS={**A,**B}
gal=json.load(open("../../data/fineart/gallery.json")); by_id={p["id"]:p for p in gal["paintings"]}
def fname(url): return urllib.parse.unquote(url.rsplit("/",1)[1]).replace(" ","_")
file2id={fname(p["p"]):p["id"] for p in gal["paintings"]}
b2=json.load(open("../base2.json")); b3=json.load(open("../base3.json"))
qid2id={r["qid"]:r["id"] for r in b2["paintings"]+b3["paintings"] if r.get("qid") and r["id"] in by_id}
# file index
idx={}
for f in glob.glob("wp/*.json"):
    for r in json.load(open(f)): idx.setdefault(r["file"],r)
for f in glob.glob("cand_cat/*.json"):
    for r in json.load(open(f)): idx.setdefault(r["file"],r)
cand={}
for f in glob.glob("cand/*.json"):
    for r in json.load(open(f)): cand.setdefault(r["qid"],r)
if os.path.exists("extra_cands.json"): cand.update(json.load(open("extra_cands.json")))
def commons_exists(name):
    r=requests.get("https://commons.wikimedia.org/w/api.php",params={"action":"query","titles":"File:"+name.replace("_"," "),"prop":"imageinfo","format":"json"},headers=H,timeout=30).json()
    p=list(r["query"]["pages"].values())[0]
    return "imageinfo" in p
def match_file(pre):
    if pre in idx: return pre
    cs=[k for k in idx if k.startswith(pre)]
    if len(cs)==1: return cs[0]
    if len(cs)>1: return ("AMBIG",cs[:4])
    if commons_exists(pre): return pre
    r=requests.get("https://commons.wikimedia.org/w/api.php",params={"action":"query","list":"allpages","apnamespace":6,"apprefix":pre.replace("_"," "),"aplimit":5,"format":"json"},headers=H,timeout=30).json()
    pg=[p["title"][5:].replace(" ","_") for p in r["query"]["allpages"]]
    if len(pg)==1: return pg[0]
    if len(pg)>1: return ("AMBIG",pg)
    return None
out={}; errs=[]
order=[e[0] for e in EV]
for slug in order:
    items=[]; seen=set()
    for p in PICKS.get(slug,[]):
        if isinstance(p,str) and re.match(r"^Q\d+$",p):
            if p in qid2id: d={"gal":qid2id[p]}
            else:
                r=cand.get(p)
                if not r: errs.append((slug,p,"no cand record")); continue
                d={"new":{"qid":p,"title":r["title"],"year":r["year"],"artists":list(r["artists"].items()),"file":fname(r["img"])}}
        elif isinstance(p,str):
            if p not in by_id: errs.append((slug,p,"unknown gallery id")); continue
            d={"gal":p}
        elif len(p)==2:
            if p[0] not in by_id: errs.append((slug,p[0],"unknown gallery id")); continue
            d={"gal":p[0],"note":p[1]}
        else:
            f=match_file(p[0])
            if f is None: errs.append((slug,p[0],"file not found")); continue
            if isinstance(f,tuple): errs.append((slug,p[0],"ambiguous "+str(f[1]))); continue
            if f in file2id: d={"gal":file2id[f]}
            else: d={"new":{"qid":None,"title":p[1],"year":p[3],"artist_name":p[2],"med":p[4] if len(p)>4 else "","file":f}}
        key=d.get("gal") or d["new"]["file"]
        if key in seen: continue
        seen.add(key); items.append(d)
    out[slug]=items
json.dump(out,open("resolved.json","w"),ensure_ascii=False,indent=0)
print("events",len(out),"items",sum(len(v) for v in out.values()),"new",sum(1 for v in out.values() for d in v if "new" in d))
for e in errs: print("ERR",e)
for s,v in out.items(): print(f"{s:26s} {len(v):2d}  new={sum(1 for d in v if 'new' in d)}")
