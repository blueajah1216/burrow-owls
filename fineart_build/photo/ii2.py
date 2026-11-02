import json, re, time, requests, collections, warnings
from concurrent.futures import ThreadPoolExecutor
warnings.filterwarnings("ignore")
H = {"User-Agent": "BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
T = json.load(open("titles2.json"))
per = collections.Counter(); keep = []
for t, c in T.items():
    if per[c] >= (400 if c.startswith("q:") else 160): continue
    per[c] += 1; keep.append(t)
print(len(T), len(keep), flush=True)
def batch(ch):
    for k in range(5):
        try:
            r = requests.get("https://commons.wikimedia.org/w/api.php", params=dict(action="query", format="json", titles="|".join(ch), prop="imageinfo", iiprop="url|size|mime|extmetadata", iiurlwidth=1280,
                             iiextmetadatafilter="LicenseShortName|Artist|ImageDescription|DateTimeOriginal|Credit"), headers=H, timeout=60)
            if r.status_code == 200: return r.json()
        except Exception: pass
        time.sleep(3 * (k + 1))
    return {}
chunks = [keep[i:i + 50] for i in range(0, len(keep), 50)]
out = {}
with ThreadPoolExecutor(3) as ex:
    for n, r in enumerate(ex.map(batch, chunks)):
        for p in r.get("query", {}).get("pages", {}).values():
            ii = (p.get("imageinfo") or [None])[0]
            if not ii or not ii["mime"].startswith("image/") or ii["mime"] == "image/svg+xml": continue
            em = {k: re.sub(r"<[^>]+>", "", v.get("value", "")).strip() for k, v in ii.get("extmetadata", {}).items()}
            out[p["title"]] = {"src": "commons", "title": p["title"][5:], "cat": T.get(p["title"]), "w": ii["width"], "h": ii["height"], "thumb": ii.get("thumburl"), "orig": ii["url"], "page": ii["descriptionurl"],
                               "lic": em.get("LicenseShortName", ""), "artist": em.get("Artist", ""), "desc": em.get("ImageDescription", ""), "date": em.get("DateTimeOriginal", ""), "usage": 0}
        print(n, len(chunks), len(out), end="\r", flush=True)
json.dump(list(out.values()), open("c_commons2.json", "w"), ensure_ascii=False)
print("\ndone", len(out))
