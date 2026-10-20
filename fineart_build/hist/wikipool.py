"""For each event: collect images used on the event's Wikipedia articles (terms), keep PD painting-like files. -> wp/<slug>.json"""
import json, re, sys, os, time, requests, warnings
from events import EV
warnings.filterwarnings("ignore")
H={"User-Agent":"BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
os.makedirs("wp",exist_ok=True)
def api(base,**p):
    p["format"]="json"
    for a in range(5):
        try:
            r=requests.get(base,params=p,headers=H,timeout=60)
            if r.status_code==200: return r.json()
        except Exception: pass
        time.sleep(4*(a+1))
    return {}
EN="https://en.wikipedia.org/w/api.php"; CM="https://commons.wikimedia.org/w/api.php"
SKIP=re.compile(r"flag|coat[_ ]of|map|icon|logo|symbol|commons-|wiki|stub|signature|\.svg|\.gif|\.webm|\.ogg|\.ogv|\.pdf|\.tif|portal|button|disambig|question|edit-|ambox|crystal|nuvola|folder|increase|decrease|steady|padlock|speaker|wikt|merge|split|cscr|flagicon|seal_of|emblem|statue|monument|memorial|grave|tomb|ruins|bust",re.I)
PAINT=re.compile(r"painting|drawing|print|illustration|engraving|woodcut|fresco|mural|miniature|poster|lithograph|etching|watercolo|tapestr|artworks|works by|oil on|mosaic|caricature|cartoon|sketch",re.I)
only=sys.argv[1:]
for slug,era,title,s,e,terms in EV:
    if only and slug not in only: continue
    if os.path.exists(f"wp/{slug}.json") and not only: continue
    count={}
    for i in range(0,len(terms),20):
        ts=terms[i:i+20]; cont={}
        while True:
            r=api(EN,action="query",titles="|".join(ts),prop="images",imlimit="max",redirects=1,**cont)
            for p in r.get("query",{}).get("pages",{}).values():
                for im in p.get("images",[]):
                    n=im["title"][5:]
                    if not SKIP.search(n) and re.search(r"\.(jpe?g|png)$",n,re.I): count[n]=count.get(n,0)+1
            if "continue" in r: cont={k:v for k,v in r["continue"].items()}
            else: break
            time.sleep(.2)
        time.sleep(.3)
    files=list(count)
    out=[]
    for i in range(0,len(files),40):
        r=api(CM,action="query",titles="|".join("File:"+f for f in files[i:i+40]),prop="imageinfo|categories",iiprop="size|mime|extmetadata",iiextmetadatafilter="LicenseShortName|Artist|ObjectName|DateTimeOriginal",cllimit="max")
        for p in r.get("query",{}).get("pages",{}).values():
            ii=p.get("imageinfo",[{}])[0]
            if not ii: continue
            md=ii.get("extmetadata",{}); g=lambda k:re.sub(r"<[^>]+>","",md.get(k,{}).get("value","")).strip()
            cats=[c["title"][9:] for c in p.get("categories",[])]
            lic=g("LicenseShortName")
            if ii.get("width",0)<800 or not re.search(r"public domain|^PD|CC0|no restrictions",lic,re.I): continue
            if not any(PAINT.search(c) for c in cats): continue
            out.append({"file":p["title"][5:].replace(" ","_"),"w":ii["width"],"h":ii["height"],"lic":lic,"artist":g("Artist")[:60],"name":g("ObjectName")[:90],"date":g("DateTimeOriginal")[:30],"n":count.get(p["title"][5:].replace("_"," "),count.get(p["title"][5:],1)),"cats":[c for c in cats if PAINT.search(c)][:3]})
        time.sleep(.4)
    out.sort(key=lambda x:-x["n"])
    json.dump(out,open(f"wp/{slug}.json","w"),ensure_ascii=False)
    print(slug,len(files),"files ->",len(out),flush=True)
