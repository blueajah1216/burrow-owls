"""python3 cfind.py "search terms" ... -> Commons file hits (title, size, license)"""
import sys, requests, re, time, warnings
warnings.filterwarnings("ignore")
H={"User-Agent":"BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
def api(**p):
    p["format"]="json"
    for a in range(4):
        r=requests.get("https://commons.wikimedia.org/w/api.php",params=p,headers=H,timeout=40)
        if r.status_code==200: return r.json()
        time.sleep(3)
for q in sys.argv[1:]:
    r=api(action="query",list="search",srsearch=q,srnamespace=6,srlimit=8)
    titles=[s["title"] for s in r["query"]["search"]]
    print("##",q)
    if not titles: continue
    r=api(action="query",titles="|".join(titles),prop="imageinfo",iiprop="size|mime|extmetadata",iiextmetadatafilter="LicenseShortName")
    for p in r["query"]["pages"].values():
        ii=p.get("imageinfo",[{}])[0]
        print("  ",p["title"][5:][:80],"|",ii.get("width"),"x",ii.get("height"),"|",ii.get("extmetadata",{}).get("LicenseShortName",{}).get("value",""))
    time.sleep(.3)
