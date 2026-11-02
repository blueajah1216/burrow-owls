import json, requests, time, os
from concurrent.futures import ThreadPoolExecutor
H={"User-Agent":"BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
ids=[];off=0
while True:
    r=requests.get("https://collectionapi.metmuseum.org/public/collection/v1.1/search",params={"departmentId":19,"hasImages":"true","isPublicDomain":"true","q":"*","limit":1000,"offset":off},headers=H,timeout=60).json()
    b=r.get("objectIDs") or []
    if not b:break
    ids+=b;off+=len(b)
    if off>=r["total"]:break
print(len(ids),flush=True)
keep=("objectID","title","artistDisplayName","artistDisplayBio","artistNationality","objectDate","objectBeginDate","medium","isHighlight","primaryImage","primaryImageSmall","objectURL","creditLine","tags","culture","classification","objectName","city","country","period","dimensions")
def get(i):
    for t in range(4):
        try:
            r=requests.get(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{i}",headers=H,timeout=30)
            if r.status_code==200:
                d=r.json();return {k:d.get(k) for k in keep}
            time.sleep(2)
        except Exception: time.sleep(2)
out=[]
with ThreadPoolExecutor(6) as ex:
    for n,d in enumerate(ex.map(get,ids)):
        if d:out.append(d)
        if n%2000==0:print(n,flush=True)
json.dump(out,open("c_met.json","w"),ensure_ascii=False)
print("done",len(out))
