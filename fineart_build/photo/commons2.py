"""Commons: photographer/collection categories + iconic-photo searches -> c_commons2.json"""
import json, re, sys, time, requests, warnings
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
CATS = [l.strip() for l in open("commons_cats.txt") if l.strip() and not l.startswith("#")]
QUERIES = [l.strip() for l in open("commons_queries.txt") if l.strip() and not l.startswith("#")]
titles = {}
def members(cat, depth=1, cap=250):
    out = []; cont = {}
    while len(out) < cap:
        r = call(action="query", list="categorymembers", cmtitle="Category:" + cat, cmtype="file", cmlimit=200, **cont)
        out += [m["title"] for m in r.get("query", {}).get("categorymembers", [])]
        if "continue" not in r: break
        cont = r["continue"]
    if depth:
        r = call(action="query", list="categorymembers", cmtitle="Category:" + cat, cmtype="subcat", cmlimit=60)
        for s in r.get("query", {}).get("categorymembers", [])[:15]:
            out += members(s["title"][9:], depth - 1, 30); time.sleep(.2)
    return out
for c in CATS:
    m = members(c)
    print("CAT", c, len(m), flush=True)
    for t in m: titles.setdefault(t, "cat:" + c)
for q in QUERIES:
    r = call(action="query", list="search", srsearch=q + " filemime:jpeg", srnamespace=6, srlimit=3)
    s = r.get("query", {}).get("search", [])
    print("Q", q, [x["title"][5:60] for x in s[:2]], flush=True)
    for x in s[:2]: titles.setdefault(x["title"], "q:" + q)
    time.sleep(.3)
json.dump(titles, open('titles2.json','w'))
out = {}
tl = list(titles)
for i in range(0, len(tl), 40):
    ch = tl[i:i + 40]
    r = call(action="query", titles="|".join(ch), prop="imageinfo", iiprop="url|size|mime|extmetadata", iiurlwidth=1280,
             iiextmetadatafilter="LicenseShortName|Artist|ImageDescription|DateTimeOriginal|Credit")
    for p in r.get("query", {}).get("pages", {}).values():
        ii = (p.get("imageinfo") or [None])[0]
        if not ii or not ii["mime"].startswith("image/") or ii["mime"] == "image/svg+xml": continue
        em = {k: re.sub(r"<[^>]+>", "", v.get("value", "")).strip() for k, v in ii.get("extmetadata", {}).items()}
        out[p["title"]] = {"src": "commons", "title": p["title"][5:], "cat": titles.get(p["title"]), "w": ii["width"], "h": ii["height"], "thumb": ii.get("thumburl"), "orig": ii["url"],
                           "page": ii["descriptionurl"], "lic": em.get("LicenseShortName", ""), "artist": em.get("Artist", ""), "desc": em.get("ImageDescription", ""), "date": em.get("DateTimeOriginal", ""),
                           "usage": 0}
    print(i, len(out), end="\r", flush=True); time.sleep(.5)
json.dump(list(out.values()), open("c_commons2.json", "w"), ensure_ascii=False)
print("\ndone", len(out))
