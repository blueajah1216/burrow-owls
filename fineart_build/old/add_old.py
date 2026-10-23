"""Select ~1100 top candidates (per-artist cap), fetch Commons image info + artist facts, append to ../base4.json."""
import json, re, sys, time, unicodedata, urllib.parse, collections, requests, warnings
warnings.filterwarnings("ignore"); sys.path.insert(0, "..")
from q3 import sparql, H
CAP, TARGET = 18, 1150
gal = json.load(open("../../data/fineart/gallery.json")); used = {p["id"] for p in gal["paintings"]}
b2 = json.load(open("../base2.json")); b3 = json.load(open("../base3.json")); b4 = json.load(open("../base4.json"))
have = {r.get("qid") for r in b2["paintings"] + b3["paintings"] + b4["paintings"]}
used |= {p["id"] for p in b4["paintings"]}
cands = [r for r in json.load(open("cands.json")) if r["qid"] not in have and r["arts"]]
cands = [r for r in cands if r["year"] >= int(sys.argv[1])] if len(sys.argv) > 1 else cands
cands.sort(key=lambda r: -r["sl"])
perart = collections.Counter(); sel = []
for r in cands:
    a = next(iter(r["arts"]))
    if perart[a] >= CAP: continue
    perart[a] += 1; sel.append(r)
    if len(sel) >= TARGET: break
print("selected", len(sel), "min sl", sel[-1]["sl"])
def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")
new = []
for r in sel:
    t = r["title"] if not re.match(r"^Q\d+$", r["title"]) else "Untitled"
    a = next(iter(r["arts"])); aname = r["arts"][a]
    sid = slug(t)[:55] or "untitled"; k = 2
    while sid in used: sid = f"{slug(t)[:44]}-{slug(aname.split()[-1] if aname else 'x')[:10]}" + ("" if k == 2 else f"-{k}"); k += 1
    used.add(sid)
    new.append({"id": sid, "qid": r["qid"], "title": t, "year": r["year"], "sl": r["sl"], "artist_ids": [a],
                "file": urllib.parse.unquote(r["img"].rsplit("/", 1)[1]).replace(" ", "_"), "med": ""})
aq = sorted({a for p in new for a in p["artist_ids"] if a not in gal["artists"] and a not in b4["artists"]})
print("new artists", len(aq))
for i in range(0, len(aq), 60):
    vals = " ".join("wd:" + q for q in aq[i:i + 60])
    Q = f"""SELECT ?a ?aL ?b ?dd ?bpL ?dpL WHERE {{ VALUES ?a {{ {vals} }} OPTIONAL {{ ?a rdfs:label ?aL FILTER(LANG(?aL)='en') }} OPTIONAL {{ ?a wdt:P569 ?b }} OPTIONAL {{ ?a wdt:P570 ?dd }}
      OPTIONAL {{ ?a wdt:P19 ?bp . ?bp rdfs:label ?bpL FILTER(LANG(?bpL)='en') }} OPTIONAL {{ ?a wdt:P20 ?dp . ?dp rdfs:label ?dpL FILTER(LANG(?dpL)='en') }} }}"""
    for b in sparql(Q):
        q = b["a"]["value"].rsplit("/", 1)[1]; o = b4["artists"].setdefault(q, {})
        if "aL" in b: o["name"] = b["aL"]["value"]
        if "b" in b: o.setdefault("birth", b["b"]["value"][:10])
        if "dd" in b: o.setdefault("death", b["dd"]["value"][:10])
        if "bpL" in b: o.setdefault("born_in", b["bpL"]["value"])
        if "dpL" in b: o.setdefault("died_in", b["dpL"]["value"])
    time.sleep(1)
info = {}; files = [p["file"] for p in new]
for i in range(0, len(files), 40):
    r = requests.get("https://commons.wikimedia.org/w/api.php", params={"action": "query", "format": "json", "titles": "|".join("File:" + f.replace("_", " ") for f in files[i:i + 40]), "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1280, "iiextmetadatafilter": "LicenseShortName"}, headers=H, timeout=60).json()
    for pg in r["query"]["pages"].values():
        if "imageinfo" in pg: info[pg["title"][5:].replace(" ", "_")] = pg["imageinfo"][0]
    time.sleep(.7)
ok = 0; skipped = []
for p in new:
    ii = info.get(p["file"])
    if not ii or not ii["mime"].startswith("image/") or ii["width"] < 900 and ii["height"] < 900: skipped.append(p["id"]); continue
    lic = ii.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "")
    p.update(w=ii["width"], h=ii["height"], thumb=ii.get("thumburl"), page=ii["descriptionurl"], lic=lic)
    b4["paintings"].append(p); ok += 1
print(ok, "added; skipped", len(skipped))
print("non-PD:", [(p["id"], p["lic"]) for p in new if p.get("lic") and p["lic"] not in ("Public domain", "CC0")][:40])
json.dump(b4, open("../base4.json", "w"), ensure_ascii=False)
ids0 = json.load(open("new_ids.json")) if len(sys.argv) > 1 else []
json.dump(ids0 + [p["id"] for p in new if p.get("w")], open("new_ids.json", "w"))
