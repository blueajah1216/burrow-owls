"""Rank + choose candidates -> sel.json (ordered by year). Prints counts per era/source."""
import json, re, collections, sys
d = json.load(open("cand_all.json"))
def pk(w):
    w = re.sub(r"\(.*?\)", "", w or "").split(";")[0].strip()
    w = re.sub(r"<.*", "", w)
    p = w.split()
    return (p[0][0].lower() + " " + p[-1].lower()) if len(p) > 1 else w.lower()
# photographer weight: key -> (score, cap)
W = {}
def tier(names, score, cap):
    for n in names.split(","): W[n.strip()] = (score, cap)
tier("a stieglitz", 9, 30); tier("l hine", 9, 28); tier("j cameron", 9, 16); tier("j atget,e atget", 8, 16); tier("r fenton", 8, 12); tier("w talbot", 9, 14); tier("e curtis", 8, 14)
tier("t o'sullivan,a gardner,m brady,g barnard", 8, 10); tier("c watkins", 8, 10); tier("e muybridge", 9, 8); tier("h bayard", 8, 8); tier("d hill,d adamson", 8, 8); tier("g gray", 7, 8); tier("n niépce,l daguerre", 10, 3)
tier("c white,g käsebier,f day,f eugene,a coburn,h kühn,p strand,e steichen,a ulmann,f evans,p emerson,h robinson,o rejlander", 7, 10); tier("nadar,c marville,f beato,s bourne,j thomson,w jackson,j riis,a genthe", 7, 8)
tier("d lange,w evans,a rothstein,r lee,j delano,m wolcott,j vachon,e bubley,g parks,a palmer,b shahn,j collier", 7, 10); tier("s prokudin-gorsky,s prokudin-gorskii,s prokudin-gorski", 8, 14)
tier("r dayal,j burke,l rousselet,a braun,e baldus,é baldus,l tripe,c tripe,f frith,j greene,f bonfils,l fong,a beato,c nègre,m camp,e carjat,a disdéri,a bisson,b frères", 5, 5)
sel = []; cnt = collections.Counter()
rows = []
for r in d:
    if not r["y"] or r["y"] < 1826 or r["y"] > 2026: continue
    k = pk(r["who"]); r["pk"] = k
    sc, cap = W.get(k, (3 if r["who"] else 1, 3))
    if r["src"] in ("commons",) and (r.get("cat") or "").startswith(("cat:", "q:")): sc = max(sc, 6)
    r["rank"] = sc + r["score"]
    r["cap"] = cap
    rows.append(r)
rows.sort(key=lambda r: -r["rank"])
E = [(1826, 1850, 120), (1851, 1879, 300), (1880, 1909, 280), (1910, 1934, 220), (1935, 1949, 190), (1950, 1979, 140), (1980, 3000, 260)]
if len(sys.argv) > 1: E = [(a, b, int(n * float(sys.argv[1]))) for a, b, n in E]
for lo, hi, n in E:
    got = 0; per = collections.Counter()
    for r in rows:
        if got >= n: break
        if not (lo <= r["y"] <= hi): continue
        if per[r["pk"]] >= r["cap"] and r["pk"]: continue
        if r["src"] == "commons" and (r["w"] < 1400 or r["w"] / r["h"] > 2.4 or r["w"] / r["h"] < 0.4): continue
        per[r["pk"]] += 1; got += 1; sel.append(r)
    print(lo, hi, got, dict(collections.Counter(r["src"] for r in sel if lo <= r["y"] <= hi)))
sel.sort(key=lambda r: (r["y"], r["key"]))
json.dump(sel, open("sel.json", "w"), ensure_ascii=False)
print(len(sel))
