"""Append extra picks to base4.json + resolved.json without disturbing existing ids."""
import json, re, sys, time, unicodedata, requests, warnings
warnings.filterwarnings("ignore"); sys.path.insert(0,"..")
from q3 import sparql, H
EX=[
 ("caesar","Victor_Honoré_Janssens_-_The_death_of_Caesar.jpg","The Death of Caesar","Victor Honoré Janssens",1700,""),
 ("charlemagne","Charlemagne_et_Louis_le_Pieux.jpg","Charlemagne and Louis the Pious","?Anonymous illuminator (French chronicle)",1400,"Illuminated manuscript"),
]
gal=json.load(open("../../data/fineart/gallery.json")); used={p["id"] for p in gal["paintings"]}
b4=json.load(open("../base4.json")); used|={p["id"] for p in b4["paintings"]}
R=json.load(open("resolved.json"))
def slug(s):
    s=unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+","-",s).strip("-")
def exact(pre):
    r=requests.get("https://commons.wikimedia.org/w/api.php",params={"action":"query","list":"allpages","apnamespace":6,"apprefix":pre.replace("_"," "),"aplimit":5,"format":"json"},headers=H).json()
    pg=[p["title"][5:].replace(" ","_") for p in r["query"]["allpages"]]
    return pg
out=[]
for ev,pre,title,artist,year,med in EX:
    pg=exact(pre)
    if len(pg)!=1: print("PREFIX PROBLEM",pre,pg); continue
    f=pg[0]
    ii=requests.get("https://commons.wikimedia.org/w/api.php",params={"action":"query","format":"json","titles":"File:"+f.replace("_"," "),"prop":"imageinfo","iiprop":"url|size|mime|extmetadata","iiurlwidth":1280,"iiextmetadatafilter":"LicenseShortName"},headers=H).json()
    pgs=list(ii["query"]["pages"].values())[0]["imageinfo"][0]
    sid=slug(title)[:55]; k=2
    while sid in used: sid=f"{slug(title)[:50]}-{k}"; k+=1
    used.add(sid)
    aid=None
    if artist.startswith("?"): aid="x-"+slug(artist[1:])[:40]; b4["artists"].setdefault(aid,{"name":artist[1:],"synthetic":True})
    else:
        r=requests.get("https://www.wikidata.org/w/api.php",params={"action":"wbsearchentities","search":artist,"language":"en","type":"item","limit":5,"format":"json"},headers=H).json()
        aid=next((s["id"] for s in r["search"] if re.search(r"painter|artist|illustrator",s.get("description",""),re.I)),None)
        if aid and aid not in b4["artists"]:
            q=f"SELECT ?aL ?b ?dd ?bpL ?dpL WHERE {{ BIND(wd:{aid} AS ?a) OPTIONAL {{ ?a rdfs:label ?aL FILTER(LANG(?aL)='en') }} OPTIONAL {{ ?a wdt:P569 ?b }} OPTIONAL {{ ?a wdt:P570 ?dd }} OPTIONAL {{ ?a wdt:P19 ?bp . ?bp rdfs:label ?bpL FILTER(LANG(?bpL)='en') }} OPTIONAL {{ ?a wdt:P20 ?dp . ?dp rdfs:label ?dpL FILTER(LANG(?dpL)='en') }} }}"
            o={}
            for b in sparql(q):
                if "aL" in b: o["name"]=b["aL"]["value"]
                if "b" in b: o["birth"]=b["b"]["value"][:10]
                if "dd" in b: o["death"]=b["dd"]["value"][:10]
                if "bpL" in b: o["born_in"]=b["bpL"]["value"]
                if "dpL" in b: o["died_in"]=b["dpL"]["value"]
            b4["artists"][aid]=o
        if not aid: aid="x-"+slug(artist); b4["artists"].setdefault(aid,{"name":artist,"synthetic":True})
    rec={"id":sid,"qid":None,"title":title,"year":year,"sl":0,"artist_ids":[aid],"file":f,"med":med,"w":pgs["width"],"h":pgs["height"],"thumb":pgs.get("thumburl"),"page":pgs["descriptionurl"],"lic":pgs.get("extmetadata",{}).get("LicenseShortName",{}).get("value","")}
    b4["paintings"].append(rec)
    R[ev].append({"new":{"qid":None,"title":title,"year":year,"artist_name":artist,"med":med,"file":f,"id":sid}})
    print(ev,sid,rec["w"],rec["lic"],aid)
    time.sleep(.5)
json.dump(b4,open("../base4.json","w"),ensure_ascii=False)
json.dump(R,open("resolved.json","w"),ensure_ascii=False,indent=0)
