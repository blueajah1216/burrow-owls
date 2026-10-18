import json, requests, time, warnings, re
warnings.filterwarnings("ignore")
H={"User-Agent":"BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
d=json.load(open("base.json")); P=d["paintings"]
# missing artists
need=[a for r in P for a in r["artist_ids"] if a not in d["artists"]]
need=sorted(set(need))
if need:
    r=requests.get("https://www.wikidata.org/w/api.php",params={"action":"wbgetentities","ids":"|".join(need),"props":"labels|claims","languages":"en","format":"json"},headers=H).json()
    for q,e in r["entities"].items():
        def tm(p):
            try: return e["claims"][p][0]["mainsnak"]["datavalue"]["value"]["time"].lstrip("+")[:10]
            except: return None
        d["artists"][q]={"name":(e["labels"].get("en") or {"value":"?"})["value"],"birth":tm("P569"),"death":tm("P570")}
    print("added",need)
info={}
files=[r["file"] for r in P]
for i in range(0,len(files),40):
    chunk=files[i:i+40]
    r=requests.get("https://commons.wikimedia.org/w/api.php",params={"action":"query","format":"json","titles":"|".join("File:"+f for f in chunk),"prop":"imageinfo","iiprop":"url|size|mime|extmetadata","iiurlwidth":1280,"iiextmetadatafilter":"LicenseShortName|Credit"},headers=H,timeout=60).json()
    norm={n["to"]:n["from"] for n in r["query"].get("normalized",[])}
    for p in r["query"]["pages"].values():
        t=p["title"][5:].replace(" ","_")
        if "imageinfo" in p:
            ii=p["imageinfo"][0]; info[t]=ii
    time.sleep(0.5)
    print(i,len(info),end="\r")
ok=0
for r in P:
    ii=info.get(r["file"])
    if not ii: r["bad"]="noinfo"; continue
    if not ii["mime"].startswith("image/") or ii["mime"] in("image/tiff",) and False: pass
    r["w"],r["h"]=ii["width"],ii["height"]
    r["thumb"]=ii.get("thumburl"); r["page"]=ii["descriptionurl"]
    r["lic"]=ii.get("extmetadata",{}).get("LicenseShortName",{}).get("value","")
    ok+=1
print("\nok",ok,"bad",[r["title"] for r in P if r.get("bad")][:20])
json.dump(d,open("base2.json","w"),ensure_ascii=False)
import collections
print(collections.Counter(r.get("lic","?") for r in P).most_common(12))
print([ (r["title"],r["w"]) for r in P if r.get("w",9999)<800][:20])
print(P[0]["thumb"])
