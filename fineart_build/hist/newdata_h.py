"""Build ../base4.json: new paintings needed by the history events (not already in gallery.json).
Reads picks.py (PICKS: slug -> [qid | gallery-id | dict for commons-only]) and cand/*.json for Wikidata facts."""
import json, re, unicodedata, urllib.parse, time, glob, requests, warnings, sys
warnings.filterwarnings("ignore")
sys.path.insert(0, "..")
from q3 import sparql, H
from picks import PICKS
gal = json.load(open("../../data/fineart/gallery.json")); used = {p["id"] for p in gal["paintings"]}
b2 = json.load(open("../base2.json")); b3 = json.load(open("../base3.json"))
have = {r["qid"] for r in b2["paintings"] + b3["paintings"] if r.get("qid")}
have_ids = {p["id"] for p in gal["paintings"]}
cand = {}
for f in glob.glob("cand/*.json"):
    for r in json.load(open(f)): cand.setdefault(r["qid"], r)
extra = json.load(open("extra_cands.json")) if glob.glob("extra_cands.json") else {}   # qid -> cand-like record (manual additions)
cand |= extra
def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")
want = []
for slug_, picks in PICKS.items():
    for k in picks:
        if isinstance(k, str) and re.match(r"^Q\d+$", k) and k not in have and k not in [w for w in want]: want.append(k)
print(len(want), "new qids")
P = []
for q in want:
    r = cand.get(q)
    if not r: print("no cand record for", q); continue
    base = slug(r["title"])[:55] or q.lower(); sid = base
    if sid in used: sid = f"{base}-{slug(list(r['artists'].values())[0][0] if r['artists'] else '')[:14]}".rstrip("-")
    n = 2
    while sid in used: sid = f"{base}-{n}"; n += 1
    used.add(sid)
    fn = urllib.parse.unquote(r["img"].rsplit("/", 1)[1]).replace(" ", "_")
    P.append({"id": sid, "qid": q, "title": r["title"], "year": r["year"], "sl": r["sl"], "artist_ids": list(r["artists"].keys()), "file": fn})
aq = sorted({a for p in P for a in p["artist_ids"]})
A = {}
for i in range(0, len(aq), 80):
    vals = " ".join("wd:" + q for q in aq[i:i + 80])
    Q = f"""SELECT ?a ?aL ?b ?dd ?bpL ?dpL WHERE {{ VALUES ?a {{ {vals} }}
      OPTIONAL {{ ?a rdfs:label ?aL FILTER(LANG(?aL)='en') }} OPTIONAL {{ ?a wdt:P569 ?b }} OPTIONAL {{ ?a wdt:P570 ?dd }}
      OPTIONAL {{ ?a wdt:P19 ?bp . ?bp rdfs:label ?bpL FILTER(LANG(?bpL)='en') }} OPTIONAL {{ ?a wdt:P20 ?dp . ?dp rdfs:label ?dpL FILTER(LANG(?dpL)='en') }} }}"""
    for b in sparql(Q):
        q = b["a"]["value"].rsplit("/", 1)[1]; o = A.setdefault(q, {})
        if "aL" in b: o.setdefault("name", b["aL"]["value"])
        if "b" in b: o.setdefault("birth", b["b"]["value"][:10])
        if "dd" in b: o.setdefault("death", b["dd"]["value"][:10])
        if "bpL" in b: o.setdefault("born_in", b["bpL"]["value"])
        if "dpL" in b: o.setdefault("died_in", b["dpL"]["value"])
    time.sleep(1)
# synthetic (commons-only) picks: dicts with id,title,year,artist_ids,file and artists in extra_artists.json
for slug_, picks in PICKS.items():
    for k in picks:
        if isinstance(k, dict) and k["id"] not in have_ids and k["id"] not in {p["id"] for p in P}:
            P.append({"id": k["id"], "qid": None, "title": k["title"], "year": k["year"], "sl": k.get("sl", 0), "artist_ids": k["artist_ids"], "file": k["file"], "med": k.get("med", "")})
if glob.glob("extra_artists.json"):
    for q, x in json.load(open("extra_artists.json")).items(): A.setdefault(q, {}).update(x)
files = [p["file"] for p in P]; info = {}
for i in range(0, len(files), 40):
    chunk = files[i:i + 40]
    r = requests.get("https://commons.wikimedia.org/w/api.php", params={"action": "query", "format": "json", "titles": "|".join("File:" + f for f in chunk), "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1280, "iiextmetadatafilter": "LicenseShortName"}, headers=H, timeout=60).json()
    for pg in r["query"]["pages"].values():
        if "imageinfo" in pg: info[pg["title"][5:].replace(" ", "_")] = pg["imageinfo"][0]
    time.sleep(0.7)
out = []; bad = []
for p in P:
    ii = info.get(p["file"])
    if not ii or not ii["mime"].startswith("image/"): bad.append(p["id"]); continue
    p["w"], p["h"] = ii["width"], ii["height"]; p["thumb"] = ii.get("thumburl"); p["page"] = ii["descriptionurl"]
    p["lic"] = ii.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "")
    out.append(p)
print(len(out), "with images; no image info:", bad)
import collections; print(collections.Counter(p["lic"] for p in out).most_common(15))
json.dump({"paintings": out, "artists": A}, open("../base4.json", "w"), ensure_ascii=False)
