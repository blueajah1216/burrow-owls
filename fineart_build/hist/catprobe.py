import sys, requests, time, warnings
warnings.filterwarnings("ignore")
H={"User-Agent":"BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
def api(**p):
    p["format"]="json"
    for a in range(4):
        r=requests.get("https://commons.wikimedia.org/w/api.php",params=p,headers=H,timeout=40)
        if r.status_code==200: return r.json()
        time.sleep(3)
for q in sys.argv[1:]:
    r=api(action="query",list="search",srsearch=q,srnamespace=14,srlimit=6)
    titles=[s["title"] for s in r["query"]["search"]]
    if not titles: print("##",q,"-> none"); continue
    r=api(action="query",titles="|".join(titles),prop="categoryinfo")
    print("##",q)
    for p in r["query"]["pages"].values():
        ci=p.get("categoryinfo",{}); print("   ",p["title"][9:][:70],"| files",ci.get("files",0),"subcats",ci.get("subcats",0))
    time.sleep(.3)
