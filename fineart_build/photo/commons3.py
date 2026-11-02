"""Commons third sweep: more categories (deeper), skipping files already fetched -> c_commons3.json"""
import json, re, time, requests, warnings, collections
from concurrent.futures import ThreadPoolExecutor
warnings.filterwarnings("ignore")
H = {"User-Agent": "BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
API = "https://commons.wikimedia.org/w/api.php"
def call(**kw):
    kw.update(format="json")
    for t in range(5):
        try:
            r = requests.get(API, params=kw, headers=H, timeout=60)
            if r.status_code == 200: return r.json()
        except Exception: pass
        time.sleep(4 * (t + 1))
    return {}
OLD = {("File:" + a["title"]) for f in ("c_commons.json", "c_commons2.json") for a in json.load(open(f))}
CATS = [l.strip() for l in open("commons_cats3.txt") if l.strip()]
def members(cat, depth, cap):
    out = []; cont = {}
    while len(out) < cap:
        r = call(action="query", list="categorymembers", cmtitle="Category:" + cat, cmtype="file", cmlimit=200, **cont)
        out += [m["title"] for m in r.get("query", {}).get("categorymembers", [])]
        if "continue" not in r: break
        cont = r["continue"]; time.sleep(1.5)
    if depth:
        r = call(action="query", list="categorymembers", cmtitle="Category:" + cat, cmtype="subcat", cmlimit=60)
        for s in r.get("query", {}).get("categorymembers", [])[:25]:
            out += members(s["title"][9:], depth - 1, 120); time.sleep(1.5)
    return out
import os
titles = json.load(open("titles3.json")) if os.path.exists("titles3.json") else {}
for c in ([] if titles else CATS):
    m = [t for t in members(c, 2, 700) if t not in OLD and not t.lower().endswith((".svg", ".pdf", ".ogg", ".webm", ".ogv", ".djvu"))]
    print("CAT", c, len(m), flush=True)
    for t in m: titles.setdefault(t, "cat:" + c)
if not os.path.exists("titles3.json"): json.dump(titles, open("titles3.json", "w"))
per = collections.Counter(); keep = []
for t, c in titles.items():
    if per[c] >= 500: continue
    per[c] += 1; keep.append(t)
print(len(titles), len(keep), flush=True)
def batch(ch):
    for k in range(5):
        try:
            r = requests.get(API, params=dict(action="query", format="json", titles="|".join(ch), prop="imageinfo", iiprop="url|size|mime|extmetadata", iiurlwidth=1280,
                             iiextmetadatafilter="LicenseShortName|Artist|ImageDescription|DateTimeOriginal|Credit"), headers=H, timeout=60)
            if r.status_code == 200: return r.json()
        except Exception: pass
        time.sleep(3 * (k + 1))
    return {}
chunks = [keep[i:i + 50] for i in range(0, len(keep), 50)]
out = {}
with ThreadPoolExecutor(2) as ex:
    for n, r in enumerate(ex.map(batch, chunks)):
        for p in r.get("query", {}).get("pages", {}).values():
            ii = (p.get("imageinfo") or [None])[0]
            if not ii or not ii["mime"].startswith("image/") or ii["mime"] == "image/svg+xml": continue
            em = {k: re.sub(r"<[^>]+>", "", v.get("value", "")).strip() for k, v in (ii.get("extmetadata") or {}).items()} if isinstance(ii.get("extmetadata"), dict) else {}
            out[p["title"]] = {"src": "commons", "title": p["title"][5:], "cat": titles.get(p["title"]), "w": ii["width"], "h": ii["height"], "thumb": ii.get("thumburl"), "orig": ii["url"], "page": ii["descriptionurl"],
                               "lic": em.get("LicenseShortName", ""), "artist": em.get("Artist", ""), "desc": em.get("ImageDescription", ""), "date": em.get("DateTimeOriginal", ""), "usage": 0}
        print(n, len(chunks), len(out), flush=True); time.sleep(1)
json.dump(list(out.values()), open("c_commons3.json", "w"), ensure_ascii=False)
print("done", len(out))
