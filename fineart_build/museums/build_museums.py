"""Build data/fineart/museums.json and static/fineart/world.json (simple SVG world map).
Coordinates come from the Wikipedia API (enwiki title -> coordinates). Cached in coords.json."""
import json, os, re, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from src_world import M

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
UA = {"User-Agent": "BurrowOwlsGallery/1.0 (blueajah@pm.me)"}
CACHE = os.path.join(HERE, "coords.json")

def get(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40))

coords = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
for m in M:
    if m["wiki"] in coords:
        continue
    u = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(dict(
        action="query", titles=m["wiki"], prop="coordinates|pageimages", piprop="thumbnail", pithumbsize=800,
        redirects=1, format="json"))
    pg = next(iter(get(u)["query"]["pages"].values()))
    c = (pg.get("coordinates") or [{}])[0]
    coords[m["wiki"]] = dict(lat=c.get("lat"), lon=c.get("lon"), img=(pg.get("thumbnail") or {}).get("source"), missing="missing" in pg)
    time.sleep(0.2)
MANUAL = dict(thyssen=(40.4160, -3.6949), **{"ng-prague": (50.1088, 14.4310), "shanghai-museum": (31.2281, 121.4753),
              "nmwa-tokyo": (35.7155, 139.7757), "nmfa-manila": (14.5877, 120.9808), "mbc": (14.6783, -17.4440)})
for m in M:
    if coords[m["wiki"]]["lat"] is None and m["slug"] in MANUAL:
        coords[m["wiki"]]["lat"], coords[m["wiki"]]["lon"] = MANUAL[m["slug"]]
json.dump(coords, open(CACHE, "w"), indent=1)
bad = [m["slug"] for m in M if coords[m["wiki"]]["lat"] is None]
print("no coords:", bad)

gal = json.load(open(os.path.join(ROOT, "data/fineart/gallery.json")))
norm = lambda s: re.sub(r"\W+", " ", (s or "").lower()).strip()
by_venue = {}
for p in gal["paintings"]:
    if p.get("l"):
        by_venue.setdefault(norm(p["l"][0]), []).append(p)
out = []
for m in M:
    c = coords[m["wiki"]]
    if c["lat"] is None:
        continue
    ids = []
    for a in m["aliases"]:
        ids += [p["id"] for p in by_venue.get(norm(a), [])]
    # highlights: match title (and loosely artist) to gallery paintings
    hl = []
    for t, a, y in m["highlights"]:
        hit = next((p for p in gal["paintings"] if norm(p["t"]) == norm(t)), None)
        hl.append(dict(title=t, artist=a, year=y, id=hit["id"] if hit else None))
    out.append(dict(slug=m["slug"], aliases=m["aliases"], name=m["name"], city=m["city"], country=m["country"], continent=m["continent"],
                    lat=round(c["lat"], 4), lon=round(c["lon"], 4), founded=m["founded"], desc=m["desc"], history=m["history"],
                    img=c["img"], wiki=m["wiki"].replace(" ", "_"), highlights=hl, works=list(dict.fromkeys(ids))))
json.dump(dict(museums=out), open(os.path.join(ROOT, "data/fineart/museums.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(len(out), "museums;", sum(1 for o in out if o["works"]), "with gallery works;", sum(len(o["works"]) for o in out), "works linked")
unmatched = [(v, len(ps)) for v, ps in by_venue.items() if len(ps) >= 5 and not any(norm(a) == v for m in M for a in m["aliases"])]
print("unmatched venues >=5:", sorted(unmatched, key=lambda x: -x[1]))
