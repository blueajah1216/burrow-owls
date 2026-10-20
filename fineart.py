"""
theburrowowls.com/fineart — a gallery of 1,000 famous paintings for curious kids.

Standalone look (templates/fineart/*, static/fineart/*). Data lives in
data/fineart/gallery.json, built by fineart_build/build_data.py from Wikidata +
Wikimedia Commons (public-domain images) + hand-written descriptions.

Wired up from app.py with `init_fineart(app)`.
"""

import gzip
import json
import os
import random
from urllib.parse import quote, quote_plus
from datetime import date

from flask import Blueprint, Response, abort, redirect, render_template, request, url_for

bp = Blueprint("fineart", __name__, url_prefix="/fineart")

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "fineart", "gallery.json")

HISTORY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "fineart", "history.json")

_cache = {"mtime": None, "data": None}
_hcache = {"mtime": None, "data": None}


def load():
    """Load gallery.json, reloading if the file changed on disk."""
    mtime = os.path.getmtime(DATA_PATH)
    if _cache["mtime"] != mtime:
        with open(DATA_PATH, encoding="utf-8") as f:
            data = json.load(f)
        data["by_id"] = {p["id"]: p for p in data["paintings"]}
        by_artist = {}
        for p in data["paintings"]:
            for a in p["a"]:
                by_artist.setdefault(a, []).append(p)
        data["by_artist"] = by_artist
        data["col_by_slug"] = {c["slug"]: c for c in data.get("collections", [])}
        _cache.update(mtime=mtime, data=data)
    return _cache["data"]


def load_history():
    """history.json (eras + events); each event lists painting ids from gallery.json with a short note."""
    gal = load()
    key = (os.path.getmtime(HISTORY_PATH), _cache["mtime"])
    if _hcache["mtime"] != key:
        with open(HISTORY_PATH, encoding="utf-8") as f:
            h = json.load(f)
        by_id = gal["by_id"]
        ev_of = {}
        for i, e in enumerate(h["events"]):
            e["works"] = [w | {"p": by_id[w["id"]]} for w in e["items"] if w["id"] in by_id]
            e["cover"] = by_id.get(e.get("cover")) or next((w["p"] for w in e["works"] if not w["p"].get("n")), None)
            e["count"] = sum(1 for w in e["works"] if not w["p"].get("n"))
            for w in e["works"]:
                ev_of.setdefault(w["id"], []).append(e)
        h["events_by_slug"] = {e["slug"]: e for e in h["events"]}
        h["eras_by_id"] = {r["id"]: r for r in h["eras"]}
        h["event_of"] = ev_of
        _hcache.update(mtime=key, data=h)
    return _hcache["data"]


def era_label(y):
    """-490 -> '490 BC', 1789 -> '1789'."""
    return f"{-y} BC" if y < 0 else str(y)


def span_label(e):
    a, b = e["start"], e["end"]
    if a == b:
        return era_label(a)
    if a < 0 and b > 0:
        return f"{-a} BC – {b} AD"
    if a < 0 and b < 0:
        return f"{-a}–{-b} BC"
    return f"{a}–{b}"


STD_WIDTHS = (250, 330, 500, 960, 1280, 1920, 3840)


def original_url(p):
    """Un-resized Commons file URL, derived from the thumbnail URL."""
    if "/thumb/" not in p["u"]:
        return p["u"]  # Commons gave us the original already (image narrower than 1280px)
    return p["u"].replace("thumb.wikimedia.org/wikipedia/commons/thumb/", "upload.wikimedia.org/wikipedia/commons/").rsplit("/", 1)[0]


def img_url(p, width):
    """Wikimedia image URL for at most `width` px. Commons only serves standard thumbnail widths,
    so when the original is narrower than the request we use the original file itself."""
    if width < p["w"]:
        std = max((w for w in STD_WIDTHS if w <= width), default=STD_WIDTHS[0])
        return p["u"].replace("/1280px-", f"/{std}px-")
    return original_url(p) if p["u"].lower().split("?")[0].endswith((".jpg", ".jpeg", ".png")) and p["w"] <= 4000 else p["u"]


def print_links(p, artists):
    """Three search links (budget / mid-range / high-end) for prints of a painting.

    These are search pages, not product pages: we can't vouch for any one listing, and they never go stale."""
    q = f"{p['t']} {artists[0]['n'] if artists else ''}".strip()
    return [
        {"tier": "Budget", "icon": "💵", "shop": "Etsy", "blurb": "Posters and simple prints from small sellers, usually the lowest prices.",
         "url": f"https://www.etsy.com/search?q={quote_plus(q + ' poster print')}"},
        {"tier": "Mid-range", "icon": "🖼️", "shop": "Fine Art America", "blurb": "Good printing on paper, canvas or metal, made to order, with framing options.",
         "url": f"https://fineartamerica.com/shop/prints?keyword={quote_plus(q)}"},
        {"tier": "High-end", "icon": "🏛️", "shop": "Meisterdrucke", "blurb": "Museum-grade giclée prints on archival paper or canvas, the closest to the real thing.",
         "url": f"https://www.meisterdrucke.us/suche/{quote(q)}.html"},
    ]


def map_url(loc):
    return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(f"{loc[0]} {loc[1]}")


def card_ratio(p):
    """CSS aspect-ratio for grid cards; very long scrolls and panoramas are cropped so they don't become slivers."""
    return f"{min(max(p['w'] / p['h'], 0.55), 2.2):.3f}"


def lived(a):
    b, d = a.get("b"), a.get("d")
    if b is None and d is None:
        return "Unknown or anonymous artist"
    return f"{b or '?'}–{d or '?'}"


def collection_cards(data):
    """Collections with a cover painting (first non-nude one) for the home page and index."""
    out = []
    for c in data.get("collections", []):
        cover = next((data["by_id"][i] for i in c["ids"] if i in data["by_id"] and not data["by_id"][i].get("n")), None)
        out.append(c | {"cover": cover, "count": len(c["ids"])})
    return out


def init_fineart(app):
    app.jinja_env.globals.update(fa_span=span_label, fa_img=img_url, fa_lived=lived, fa_ar=card_ratio, fa_prints=print_links, fa_map=map_url)
    app.register_blueprint(bp)


@bp.route("/")
def index():
    data = load()
    total = sum(1 for p in data["paintings"] if not p.get("n"))
    cols = collection_cards(data)
    teaser = []
    if os.path.exists(HISTORY_PATH):
        evs = {e["slug"]: e for e in load_history()["events"]}
        teaser = [evs[k] for k in ("persian-wars", "caesar", "reformation", "french-revolution", "wwi") if k in evs and evs[k]["cover"]]
    return render_template("fineart/index.html", hist_teaser=teaser, genres=data["genres"], total=total, kids=next((c for c in cols if c["slug"] == "kids"), None),
                           heritage=[c for c in cols if c["group"] == "heritage"], world=[c for c in cols if c["group"] == "world"])


@bp.route("/data.json")
def data_json():
    data = load()
    if _cache.get("json_mtime") != _cache["mtime"]:
        raw = json.dumps({"genres": data["genres"], "artists": data["artists"], "paintings": data["paintings"]}, ensure_ascii=False, separators=(",", ":")).encode()
        _cache.update(json_mtime=_cache["mtime"], json_raw=raw, json_gz=gzip.compress(raw, 6))
    resp = Response(_cache["json_raw"], mimetype="application/json")
    if "gzip" in request.headers.get("Accept-Encoding", ""):
        resp = Response(_cache["json_gz"], mimetype="application/json")
        resp.headers["Content-Encoding"] = "gzip"
    resp.headers["Vary"] = "Accept-Encoding"
    resp.headers["Cache-Control"] = "public, max-age=600"
    return resp


@bp.route("/random")
def random_painting():
    data = load()
    pool = [p for p in data["paintings"] if not p.get("n")]
    g = request.args.get("g")
    if g is not None and g.isdigit():
        pool = [p for p in pool if p["g"] == int(g)] or pool
    return redirect(url_for("fineart.painting", pid=random.choice(pool)["id"], g=g))


@bp.route("/p/<pid>")
def painting(pid):
    data = load()
    p = data["by_id"].get(pid)
    if not p:
        abort(404)
    g = request.args.get("g")
    gi = int(g) if g and g.isdigit() else None
    seq = [x for x in data["paintings"] if (gi is None or x["g"] == gi) and (not x.get("n") or x is p)]
    try:
        i = next(k for k, x in enumerate(seq) if x["id"] == pid)
        prev_p, next_p = seq[i - 1] if i > 0 else None, seq[i + 1] if i + 1 < len(seq) else None
    except StopIteration:
        prev_p = next_p = None
    artists = [data["artists"][a] | {"id": a} for a in p["a"] if a in data["artists"]]
    same_artist = [x for x in data["by_artist"].get(p["a"][0], []) if x["id"] != pid and not x.get("n")][:12]
    like = [x for x in data["paintings"] if x["g"] == p["g"] and x["id"] != pid and not x.get("n")]
    like = sorted(like, key=lambda x: abs(x["y"] - p["y"]))[:12]
    cols = [data["col_by_slug"][s] for s in p.get("c", []) if s in data["col_by_slug"]]
    events = load_history()["event_of"].get(pid, []) if os.path.exists(HISTORY_PATH) else []
    return render_template(
        "fineart/painting.html", p=p, cols=cols, artists=artists, genre=data["genres"][p["g"]], genres=data["genres"],
        prev_p=prev_p, next_p=next_p, same_artist=same_artist, like=like, g=g, events=events,
    )


@bp.route("/artist/<aid>")
def artist(aid):
    data = load()
    a = data["artists"].get(aid)
    if not a:
        abort(404)
    works = data["by_artist"].get(aid, [])
    return render_template("fineart/artist.html", a=a | {"id": aid}, works=works, genres=data["genres"])


@bp.route("/collections")
def collections():
    data = load()
    cols = collection_cards(data)
    return render_template("fineart/collections.html", kids=next((c for c in cols if c["slug"] == "kids"), None),
                           heritage=[c for c in cols if c["group"] == "heritage"], world=[c for c in cols if c["group"] == "world"])


@bp.route("/collection/<slug>")
def collection(slug):
    data = load()
    c = data["col_by_slug"].get(slug)
    if not c:
        abort(404)
    works = [data["by_id"][i] for i in c["ids"] if i in data["by_id"]]
    others = [x for x in collection_cards(data) if x["slug"] != slug]
    return render_template("fineart/collection.html", c=c, works=works, artists=data["artists"], genres=data["genres"], others=others)


@bp.route("/today")
def today():
    data = load()
    pool = [p for p in data["paintings"] if p.get("k") and not p.get("n")]  # always something cheerful
    return redirect(url_for("fineart.painting", pid=pool[date.today().toordinal() % len(pool)]["id"]))


# ---------------------------------------------------------------- Art Through History

@bp.route("/history")
def history():
    data, h = load(), load_history()
    eras = [r | {"events": [e for e in h["events"] if e["era"] == r["id"]]} for r in h["eras"]]
    return render_template("fineart/history.html", eras=eras, total=sum(e["count"] for e in h["events"]), n_events=len(h["events"]))


@bp.route("/history/<slug>")
def history_event(slug):
    data, h = load(), load_history()
    e = h["events_by_slug"].get(slug)
    if not e:
        abort(404)
    i = h["events"].index(e)
    prev_e = h["events"][i - 1] if i > 0 else None
    next_e = h["events"][i + 1] if i + 1 < len(h["events"]) else None
    era = h["eras_by_id"][e["era"]]
    eras = [r | {"events": [x for x in h["events"] if x["era"] == r["id"]]} for r in h["eras"]]
    return render_template("fineart/history_event.html", e=e, era=era, eras=eras, prev_e=prev_e, next_e=next_e, artists=data["artists"])
