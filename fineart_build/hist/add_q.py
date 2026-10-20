"""python3 add_q.py slug:Qid ...  -> append QID picks (from cand/*.json + extra_cands.json) to base4.json + resolved.json"""
import json, re, sys, time, glob, unicodedata, urllib.parse, requests, warnings
warnings.filterwarnings("ignore"); sys.path.insert(0,"..")
from q3 import sparql, H
gal=json.load(open("../../data/fineart/gallery.json")); used={p["id"] for p in gal["paintings"]}
b2=json.load(open("../base2.json")); b3=json.load(open("../base3.json"))
qid2id={r["qid"]:r["id"] for r in b2["paintings"]+b3["paintings"] if r.get("qid") and r["id"] in used}
b4=json.load(open("../base4.json")); used|={p["id"] for p in b4["paintings"]}
R=json.load(open("resolved.json"))
cand={}
for f in glob.glob("cand/*.json"):
    for r in json.load(open(f)): cand.setdefault(r["qid"],r)
cand.update(json.load(open("extra_cands.json")))
def slug(s):
    s=unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+","-",s).strip("-")
for arg in sys.argv[1:]:
    ev,q=arg.split(":")
    if q in qid2id: R[ev].append({"gal":qid2id[q]}); print(ev,"gallery",qid2id[q]); continue
    r=cand[q]; sid=slug(r["title"])[:55]; k=2
    while sid in used: sid=f"{slug(r['title'])[:50]}-{k}"; k+=1
    used.add(sid)
    aids=list(r["artists"].keys())
    for a in aids:
        if a in b4["artists"] or a in gal["artists"]: continue
        qq=f"SELECT ?aL ?b ?dd ?bpL ?dpL WHERE {{ BIND(wd:{a} AS ?a) OPTIONAL {{ ?a rdfs:label ?aL FILTER(LANG(?aL)='en') }} OPTIONAL {{ ?a wdt:P569 ?b }} OPTIONAL {{ ?a wdt:P570 ?dd }} OPTIONAL {{ ?a wdt:P19 ?bp . ?bp rdfs:label ?bpL FILTER(LANG(?bpL)='en') }} OPTIONAL {{ ?a wdt:P20 ?dp . ?dp rdfs:label ?dpL FILTER(LANG(?dpL)='en') }} }}"
        o={}
        for b in sparql(qq):
            if "aL" in b: o["name"]=b["aL"]["value"]
            if "b" in b: o["birth"]=b["b"]["value"][:10]
            if "dd" in b: o["death"]=b["dd"]["value"][:10]
            if "bpL" in b: o["born_in"]=b["bpL"]["value"]
            if "dpL" in b: o["died_in"]=b["dpL"]["value"]
        b4["artists"][a]=o; time.sleep(1)
    f=urllib.parse.unquote(r["img"].rsplit("/",1)[1]).replace(" ","_")
    ii=requests.get("https://commons.wikimedia.org/w/api.php",params={"action":"query","format":"json","titles":"File:"+f.replace("_"," "),"prop":"imageinfo","iiprop":"url|size|mime|extmetadata","iiurlwidth":1280,"iiextmetadatafilter":"LicenseShortName"},headers=H).json()
    ii=list(ii["query"]["pages"].values())[0]["imageinfo"][0]
    rec={"id":sid,"qid":q,"title":r["title"],"year":r["year"],"sl":r["sl"],"artist_ids":aids,"file":f,"med":"","w":ii["width"],"h":ii["height"],"thumb":ii.get("thumburl"),"page":ii["descriptionurl"],"lic":ii.get("extmetadata",{}).get("LicenseShortName",{}).get("value","")}
    b4["paintings"].append(rec)
    R[ev].append({"new":{"qid":q,"title":r["title"],"year":r["year"],"artists":list(r["artists"].items()),"file":f,"id":sid}})
    print(ev,sid,rec["w"],rec["lic"],[b4["artists"].get(a,{}).get("name") for a in aids]); time.sleep(.6)
json.dump(b4,open("../base4.json","w"),ensure_ascii=False)
json.dump(R,open("resolved.json","w"),ensure_ascii=False,indent=0)
