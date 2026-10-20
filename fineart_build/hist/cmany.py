"""python3 cmany.py "query" [limit] -> Commons file hits that look like paintings (PD, >=900px)"""
import sys, requests, re, time, warnings
warnings.filterwarnings("ignore")
H={"User-Agent":"BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
def api(**p):
    p["format"]="json"
    for a in range(4):
        r=requests.get("https://commons.wikimedia.org/w/api.php",params=p,headers=H,timeout=40)
        if r.status_code==200: return r.json()
        time.sleep(3)
q=sys.argv[1]; lim=int(sys.argv[2]) if len(sys.argv)>2 else 40
r=api(action="query",list="search",srsearch=q+" filetype:bitmap",srnamespace=6,srlimit=lim)
titles=[s["title"] for s in r["query"]["search"]]
out=[]
for i in range(0,len(titles),40):
    r=api(action="query",titles="|".join(titles[i:i+40]),prop="imageinfo",iiprop="size|mime|extmetadata",iiextmetadatafilter="LicenseShortName")
    for p in r["query"]["pages"].values():
        ii=p.get("imageinfo",[{}])[0]; lic=ii.get("extmetadata",{}).get("LicenseShortName",{}).get("value","")
        if ii.get("width",0)>=900 and re.search(r"public domain|PD|CC0",lic,re.I): out.append((p["title"][5:],ii["width"],ii["height"],lic))
print("##",q,len(out),"of",len(titles))
for t,w,h,l in out: print("  ",t[:92],"|",w,"x",h)
