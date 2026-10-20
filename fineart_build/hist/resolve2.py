import json, time, requests, re
H={"User-Agent":"BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
cache=json.load(open("qid_cache.json"))
def search(t):
    for a in range(4):
        r=requests.get("https://www.wikidata.org/w/api.php",params={"action":"wbsearchentities","search":t,"language":"en","type":"item","limit":3,"format":"json"},headers=H,timeout=30)
        if r.status_code==200: return r.json().get("search",[])
        time.sleep(4*(a+1))
    return []
for t,v in list(cache.items()):
    if v: continue
    for q in (t, re.sub(r"\s*\(.*?\)","",t), t.replace(" (World War I)","")):
        s=search(q)
        if s: cache[t]=[s[0]["id"],s[0].get("label",""),s[0].get("description","")]; break
        time.sleep(.2)
    print(t,"->",cache[t])
json.dump(cache,open("qid_cache.json","w"),ensure_ascii=False)
