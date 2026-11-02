import json, requests
H={"User-Agent":"BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
out=[];skip=0
while True:
    r=requests.get("https://openaccess-api.clevelandart.org/api/artworks/",params={"type":"Photograph","cc0":1,"has_image":1,"limit":1000,"skip":skip},headers=H,timeout=120).json()
    d=r["data"]
    if not d:break
    for a in d:
        im=(a.get("images") or {}).get("print") or (a.get("images") or {}).get("web") or {}
        out.append({"src":"cleveland","sid":str(a["id"]),"title":a["title"],"date":a.get("creation_date"),"y0":a.get("creation_date_earliest"),
          "artists":[c.get("description") for c in a.get("creators",[])],"tech":a.get("technique"),"desc":a.get("description"),"dyk":a.get("did_you_know"),
          "url":a["url"],"img":im.get("url"),"w":im.get("width"),"h":im.get("height"),"credit":a.get("creditline"),"hl":a.get("is_highlight"),"culture":a.get("culture")})
    skip+=len(d)
    if skip>=r["info"]["total"]:break
json.dump(out,open("c_cleveland.json","w"),ensure_ascii=False)
print(len(out))
import collections
print(collections.Counter((a["artists"][0] if a["artists"] else "?") for a in out).most_common(40))
