"""Commons Featured Pictures (modern, mostly CC-licensed) + hand-picked iconic files -> c_commons.json"""
import json, re, sys, time, requests, warnings
warnings.filterwarnings("ignore")
H = {"User-Agent": "BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
API = "https://commons.wikimedia.org/w/api.php"
CATS = ["landscapes", "nature", "people", "cityscapes", "astronomy", "history", "geology", "transport", "culture", "architecture", "religion", "the arts", "agriculture", "objects"]
def call(**kw):
    kw.update(format="json")
    for t in range(4):
        try:
            return requests.get(API, params=kw, headers=H, timeout=60).json()
        except Exception as e: time.sleep(3)
    return {}
titles = {}
for c in CATS:
    off = 0; n = 0
    while off < 1200:
        r = call(action="query", list="search", srsearch=f'deepcategory:"Featured pictures of {c}" filemime:jpeg', srnamespace=6, srlimit=50, sroffset=off)
        s = r.get("query", {}).get("search", [])
        if not s: break
        for x in s: titles.setdefault(x["title"], c); n += 1
        off += 50
        if "continue" not in r: break
        time.sleep(.3)
    print(c, n, len(titles), flush=True)
extra = [l.strip() for l in open("commons_titles.txt")] if len(sys.argv) > 1 else []
for t in extra:
    if t: titles.setdefault("File:" + t.replace("File:", ""), "iconic")
out = {}
tl = list(titles)
for i in range(0, len(tl), 40):
    ch = tl[i:i + 40]
    r = call(action="query", titles="|".join(ch), prop="imageinfo|globalusage", iiprop="url|size|mime|extmetadata", iiurlwidth=1280,
             iiextmetadatafilter="LicenseShortName|Artist|ImageDescription|DateTimeOriginal|Credit|Restrictions|AttributionRequired|UsageTerms", gulimit=500, guprop="url")
    for p in r.get("query", {}).get("pages", {}).values():
        ii = (p.get("imageinfo") or [None])[0]
        if not ii or not ii["mime"].startswith("image/"): continue
        em = {k: re.sub(r"<[^>]+>", "", v.get("value", "")).strip() for k, v in ii.get("extmetadata", {}).items()}
        out[p["title"]] = {"src": "commons", "title": p["title"][5:], "cat": titles.get(p["title"]), "w": ii["width"], "h": ii["height"], "thumb": ii.get("thumburl"), "orig": ii["url"],
                           "page": ii["descriptionurl"], "lic": em.get("LicenseShortName", ""), "artist": em.get("Artist", ""), "desc": em.get("ImageDescription", ""), "date": em.get("DateTimeOriginal", ""),
                           "usage": len(p.get("globalusage", []))}
    print(i, len(out), end="\r", flush=True); time.sleep(.4)
json.dump(list(out.values()), open("c_commons.json", "w"), ensure_ascii=False)
print("\ndone", len(out))
