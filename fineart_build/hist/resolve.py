import json, time, requests, os
from events import EV
H={"User-Agent":"BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
cache=json.load(open("qid_cache.json")) if os.path.exists("qid_cache.json") else {}
terms=sorted({t for e in EV for t in e[5]})
for i,t in enumerate(terms):
    if t in cache: continue
    for attempt in range(4):
        try:
            r=requests.get("https://www.wikidata.org/w/api.php",params={"action":"wbsearchentities","search":t,"language":"en","type":"item","limit":1,"format":"json"},headers=H,timeout=30)
            if r.status_code==429: time.sleep(5*(attempt+1)); continue
            j=r.json(); s=j.get("search",[])
            cache[t]=[s[0]["id"],s[0].get("label",""),s[0].get("description","")] if s else None
            break
        except Exception as ex: time.sleep(3)
    if i%40==0: json.dump(cache,open("qid_cache.json","w"),ensure_ascii=False); print(i,len(terms),end="\r")
    time.sleep(0.12)
json.dump(cache,open("qid_cache.json","w"),ensure_ascii=False)
print("\nunresolved:",[t for t in terms if not cache.get(t)])
