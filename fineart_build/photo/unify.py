"""Merge all candidate files into cand_all.json with one schema.
Fields: key, src, sid, title, who (photographer string), y, date, th, u, hi, hw, hh, w, h, page, lic, by, source, pr, place, desc, score"""
import json, re, collections, hashlib
def yr(s):
    m = re.search(r"(1[89]\d\d|20[0-2]\d)", s or "")
    return int(m.group(1)) if m else None
ACCEPT = re.compile(r"^(Public domain|No (known )?restrictions|CC0|PD|CC BY(-SA)? \d\.\d)", re.I)
out = []
# --- Cleveland
for a in json.load(open("c_cleveland.json")):
    if not a["img"]: continue
    web = a["img"].replace("_print.jpg", "_web.jpg")
    w, h = int(a["w"] or 0), int(a["h"] or 0)
    sc = 3 if a.get("hl") else 0
    out.append(dict(key="cle-" + a["sid"], src="cleveland", sid=a["sid"], title=a["title"], who="; ".join(re.sub(r"\s*\(.*", "", x) for x in a["artists"] if x), y=a["y0"] and int(a["y0"]), date=a["date"],
                    th=web, u=web, hi=a["img"], hw=w, hh=h, w=w, h=h, page=a["url"], lic="CC0 (public domain)", by="", source="Cleveland Museum of Art", credit=a["credit"], pr=a["tech"],
                    place="", desc=" ".join(x for x in [a.get("desc") or "", a.get("dyk") or ""] if x)[:900], score=sc))
# --- NGA (excluded: hotlinks not reliable)
NGA_ON = False
for a in (json.load(open("c_nga.json")) if NGA_ON else []):
    base = a["iiif"]
    w, h = int(a["w"] or 0), int(a["h"] or 0)
    if min(w, h) < 700: continue
    y = int(a["y0"]) if a["y0"] and a["y0"].lstrip("-").isdigit() else yr(a["date"])
    out.append(dict(key="nga-" + a["sid"], src="nga", sid=a["sid"], title=a["title"], who=re.sub(r"^(.*), (.*)$", r"\2 \1", a["artist"]) if a["artist"] and "," in a["artist"] and not a["artist"].startswith(("American", "British", "French", "Unknown")) else "", y=y, date=a["date"],
                    th=base + "/full/!600,600/0/default.jpg", u=base + "/full/!1400,1400/0/default.jpg", hi=base + "/full/full/0/default.jpg", hw=w, hh=h, w=w, h=h,
                    page="https://www.nga.gov/artworks/" + a["sid"], lic="CC0 (public domain)", by="", source="National Gallery of Art, Washington", credit=a["credit"], pr=a["tech"], place="", desc="", score=0))
# --- AIC
for a in json.load(open("c_aic.json")):
    iid = a["image_id"]; base = f"https://www.artic.edu/iiif/2/{iid}"
    w, h = int(a["w"] or 0), int(a["h"] or 0)
    if w and min(w, h) < 500: continue
    desc = re.sub(r"<[^>]+>", "", a.get("description") or a.get("short_description") or "")[:800]
    out.append(dict(key="aic-%s" % a["id"], src="aic", sid=str(a["id"]), title=a["title"], who=(a.get("artist_title") or "").replace("Unknown", ""), y=a.get("date_start") or yr(a["date_display"]), date=a["date_display"],
                    th=base + "/full/600,/0/default.jpg", u=base + "/full/1200,/0/default.jpg", hi=base + "/full/full/0/default.jpg", hw=w, hh=h, w=w, h=h, page="https://www.artic.edu/artworks/%s" % a["id"],
                    lic="CC0 (public domain)", by="", source="Art Institute of Chicago", credit=a["credit_line"], pr=a["medium_display"], place=a.get("place_of_origin") or "", desc=desc, score=min((a.get("pageviews") or 0) / 60.0, 6)))
# --- LoC
for a in json.load(open("c_loc.json")):
    b = a["base"]
    c = a.get("contrib") or []
    who = c[0].replace(", photographer", "") if isinstance(c, list) and c else (c if isinstance(c, str) else "")
    if "," in who: who = re.sub(r"^([^,]+), ([^,]+).*$", r"\2 \1", who)
    out.append(dict(key="loc-" + a["sid"], src="loc", sid=a["sid"], title=a["title"], who=who.title() if who.islower() else who, y=yr(a["date"]), date=a["date"], th=b + "r.jpg", u=b + "v.jpg", hi=b.replace("/service/", "/master/") + "u.tif",
                    hw=0, hh=0, w=0, h=0, page=a["url"], lic="No known restrictions (public domain)", by="", source="Library of Congress", credit="Library of Congress, Prints & Photographs Division", pr=a.get("medium") or "",
                    place=", ".join(a.get("loc") or []) if isinstance(a.get("loc"), list) else "", desc=" ".join(a.get("notes") or [])[:500], score=2, q=a.get("q")))
NU = json.load(open('nasa_urls.json'))
# --- NASA
for a in json.load(open("c_nasa.json")):
    sid = a["sid"]; base = f"https://images-assets.nasa.gov/image/{sid}/{sid}"
    nu = NU.get(sid, {})
    if "~medium" not in nu: continue
    out.append(dict(key="nasa-" + re.sub(r"\W+", "-", sid).lower(), src="nasa", sid=sid, title=a["title"], who=a.get("photographer") or "NASA", y=yr(a["date"]), date=a["date"][:10], th=base + "~medium.jpg", u=base + ("~large.jpg" if "~large" in nu else "~medium.jpg"), hi=base + "~orig" + nu.get("~orig", ".jpg"),
                    hw=0, hh=0, w=0, h=0, page=a["page"], lic="Public domain (NASA)", by="", source="NASA Image and Video Library", credit=a.get("center") or "NASA", pr="", place="", desc=re.sub(r"<[^>]+>", "", a["desc"])[:700], score=3, q=a["q"]))
# --- Commons
for f in ("c_commons.json", "c_commons2.json"):
    try: rows = json.load(open(f))
    except Exception: continue
    for a in rows:
        if not ACCEPT.match(a["lic"] or "") or a["w"] < 1000 or a["h"] < 600 and a["w"] < 1600: continue
        if f == "c_commons.json":  # Featured pictures: keep modern photographs only (the 'history'/'arts' sets are full of paintings and prints)
            if a.get("cat") in ("history", "the arts", "objects"): continue
            y_ = yr(a.get("date") or "") or yr(a["title"])
            if not y_ or y_ < 1975: continue
        t = re.sub(r"\.(jpe?g|png|tiff?)$", "", a["title"], flags=re.I).replace("_", " ")
        th = a["thumb"]
        if th and re.search(r"/\d+px-", th): th5 = re.sub(r"/\d+px-", "/500px-", th)
        else: th5 = th
        d = a.get("date") or ""
        out.append(dict(key="cm-" + hashlib.md5(a["title"].encode()).hexdigest()[:8], src="commons", sid=a["title"], title=t, who=a["artist"][:80], y=yr(d) or yr(t) or yr(a["desc"]), date=d[:30], th=th5, u=th, hi=a["orig"], hw=a["w"], hh=a["h"], w=a["w"], h=a["h"],
                        page=a["page"], lic=a["lic"], by=a["artist"][:120], source="Wikimedia Commons", credit="", pr="", place="", desc=a["desc"][:600], score=min(a["usage"], 500) / 40 + (2 if (a.get("cat") or "").startswith("q:") else 0), cat=a.get("cat")))
# dedupe by normalized title+year
seen = {}; res = []
for r in sorted(out, key=lambda r: -r["score"]):
    k = (re.sub(r"\W+", "", r["title"].lower())[:40], r["y"])
    if k in seen: continue
    seen[k] = 1; res.append(r)
json.dump(res, open("cand_all.json", "w"), ensure_ascii=False)
print(len(out), len(res), collections.Counter(r["src"] for r in res))
