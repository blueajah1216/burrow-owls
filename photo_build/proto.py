import json, re, sys
sys.path.insert(0, "photo_build")
from meta import GENRES, ERAS, MILESTONES
c = json.load(open("fineart_build/photo/cand_all.json"))
import random
random.seed(3)
pool = [r for r in c if r["y"] and r["w"] >= 1000 and r["src"] in ("aic", "cleveland", "nasa", "commons", "loc")]
sel = []
for e in ERAS:
    rows = [r for r in pool if e["start"] <= r["y"] <= e["end"]]
    random.shuffle(rows); sel += rows[:14]
artists = {}; photos = []
for i, r in enumerate(sel):
    a = []
    if r["who"]:
        aid = re.sub(r"\W+", "-", r["who"].split(";")[0].lower())[:30]
        artists.setdefault(aid, {"n": r["who"].split(";")[0][:50], "b": None, "d": None, "bi": "", "bio": "Bio coming soon."}); a = [aid]
    photos.append(dict(id=r["key"], t=r["title"][:80], a=a, y=r["y"], d=r["date"], g=i % 9, w=r["w"] or 1000, h=r["h"] or 800, u=r["u"], th=r["th"], hi=r["hi"], hw=r["hw"], hh=r["hh"], p=r["page"],
                       s=r["source"], cr=r["credit"], lic=r["lic"], by=r["by"][:80], why=(r["desc"] or "A great photograph.")[:300], k="What do you notice first?", l=[r["place"]] if r["place"] else [], c=["demo"], pr=r["pr"], r=i))
cols = [{"slug": "demo", "name": "Demo", "emoji": "🎞️", "blurb": "test", "intro": "A test collection.", "ids": [p["id"] for p in photos[:20]]}]
eras = []
for e in ERAS: eras.append({k: e[k] for k in ("slug", "name", "emoji", "start", "end", "blurb", "intro", "pr_note")})
json.dump(dict(genres=GENRES, eras=eras, milestones=[{"y": y, "text": t} for y, t in MILESTONES], artists=artists, photos=photos, collections=cols, first_id=photos[0]["id"]), open("data/photo/gallery.json", "w"), ensure_ascii=False)
print(len(photos))
