"""List image files in Commons categories (depth-limited) with license info -> cand_cat/<name>.json"""
import json, sys, time, requests, re, os
H={"User-Agent":"BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
def api(**p):
    p["format"]="json"
    for a in range(5):
        r=requests.get("https://commons.wikimedia.org/w/api.php",params=p,headers=H,timeout=60)
        if r.status_code==200: return r.json()
        time.sleep(4*(a+1))
    raise SystemExit("commons api failed")
def members(cat,typ):
    out=[];cont={}
    while True:
        r=api(action="query",list="categorymembers",cmtitle="Category:"+cat,cmtype=typ,cmlimit=500,**cont)
        out+= [m["title"] for m in r["query"]["categorymembers"]]
        if "continue" not in r: break
        cont=r["continue"]
    return out
def walk(cat,depth,seen):
    files=[]
    if cat in seen: return files
    seen.add(cat)
    files+= [f for f in members(cat,"file")]
    if depth>0:
        for sc in members(cat,"subcat"):
            files+=walk(sc[9:],depth-1,seen); time.sleep(.2)
    return files
def info(files):
    out={}
    for i in range(0,len(files),40):
        ch=files[i:i+40]
        r=api(action="query",titles="|".join(ch),prop="imageinfo",iiprop="url|size|mime|extmetadata",iiurlwidth=1280,iiextmetadatafilter="LicenseShortName|Artist|ObjectName|DateTimeOriginal|ImageDescription|Credit")
        for p in r["query"]["pages"].values():
            if "imageinfo" in p:
                ii=p["imageinfo"][0]; md=ii.get("extmetadata",{})
                g=lambda k:re.sub(r"<[^>]+>","",md.get(k,{}).get("value","")).strip()
                out[p["title"]]={"file":p["title"][5:].replace(" ","_"),"w":ii["width"],"h":ii["height"],"mime":ii["mime"],"thumb":ii.get("thumburl"),"page":ii["descriptionurl"],"lic":g("LicenseShortName"),"artist":g("Artist")[:90],"name":g("ObjectName")[:120],"date":g("DateTimeOriginal")[:40],"desc":g("ImageDescription")[:220]}
        time.sleep(.5)
    return out
if __name__=="__main__":
    name,cat,depth=sys.argv[1],sys.argv[2],int(sys.argv[3])
    files=sorted(set(walk(cat,depth,set())))
    print(name,len(files),"files")
    res=info(files)
    os.makedirs("cand_cat",exist_ok=True)
    json.dump(list(res.values()),open(f"cand_cat/{name}.json","w"),ensure_ascii=False)
    print("saved",len(res))
