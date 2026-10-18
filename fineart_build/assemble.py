import json, re, unicodedata, urllib.parse, hashlib, collections
r1=json.load(open("raw1.json")); r2=json.load(open("raw2.json"))
paint={}
for b in r1:
    q=b["p"]["value"]
    y=int(b["inc"]["value"][:4]) if not b["inc"]["value"].startswith("-") else 0
    if y>1929 or y<1726: continue
    d=paint.setdefault(q,{"qid":q.rsplit("/",1)[1],"title":b["pLabel"]["value"],"sl":int(b["sl"]["value"]),"year":y,"artists":[],"img":b["img"]["value"]})
    a=b["artist"]["value"]
    if a not in d["artists"]: d["artists"].append(a)
    d["year"]=min(d["year"],y)
rows=sorted(paint.values(),key=lambda d:-d["sl"])
rows=[r for r in rows if not re.match(r"^Q\d+$",r["title"]) and "origine du monde" not in r["title"].lower()]
print(len(rows))
rows=rows[:1000]
def slug(s):
    s=unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+","-",s).strip("-")
used=set()
for r in rows:
    s=slug(r["title"])[:60]; 
    while s in used: s+="-"+slug(r["artists"] and r2["artists"][r["artists"][0]]["name"] or "x")[:12] if s+"-" not in used else "-2"
    used.add(s); r["id"]=s
    r["genres"]=r2["genre"].get("http://www.wikidata.org/entity/"+r["qid"],[])
    r["movement"]=r2["movement"].get("http://www.wikidata.org/entity/"+r["qid"],[])
    r["collection"]=r2["collection"].get("http://www.wikidata.org/entity/"+r["qid"],[])
    fn=urllib.parse.unquote(r["img"].rsplit("/",1)[1]).replace(" ","_")
    r["file"]=fn
    r["artist_ids"]=[a.rsplit("/",1)[1] for a in r["artists"]]
    del r["artists"],r["img"]
arts={k.rsplit("/",1)[1]:v for k,v in r2["artists"].items()}
used_a={a for r in rows for a in r["artist_ids"]}
print("artists used",len(used_a), "missing", [a for a in used_a if a not in arts][:10])
json.dump({"paintings":rows,"artists":{a:arts[a] for a in used_a if a in arts}},open("base.json","w"),ensure_ascii=False,indent=0)
c=collections.Counter(g for r in rows for g in r["genres"]); print(c.most_common(40))
print(collections.Counter(len(r["genres"]) for r in rows))
print(collections.Counter(r["year"]//25*25 for r in rows))
