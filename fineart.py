"""
theburrowowls.com/fineart — a gallery of 1,000 famous paintings for curious kids.

Standalone look (templates/fineart/*, static/fineart/*). Data lives in
data/fineart/gallery.json, built by fineart_build/build_data.py from Wikidata +
Wikimedia Commons (public-domain images) + hand-written descriptions.

Wired up from app.py with `init_fineart(app)`.
"""

import json
import os
import random
from urllib.parse import quote, quote_plus
from datetime import date

from flask import Blueprint, abort, jsonify, redirect, render_template, request, url_for

bp = Blueprint("fineart", __name__, url_prefix="/fineart")

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "fineart", "gallery.json")

_cache = {"mtime": None, "data": None}


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
        _cache.update(mtime=mtime, data=data)
    return _cache["data"]


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


def lived(a):
    b, d = a.get("b") or "?", a.get("d") or "?"
    return f"{b}–{d}"


def init_fineart(app):
    app.jinja_env.globals.update(fa_img=img_url, fa_lived=lived, fa_prints=print_links, fa_map=map_url)
    app.register_blueprint(bp)


@bp.route("/")
def index():
    data = load()
    total = sum(1 for p in data["paintings"] if not p.get("n"))
    return render_template("fineart/index.html", genres=data["genres"], total=total)


@bp.route("/data.json")
def data_json():
    data = load()
    resp = jsonify({"genres": data["genres"], "artists": data["artists"], "paintings": data["paintings"]})
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
    same_artist = [x for x in data["by_artist"].get(p["a"][0], []) if x["id"] != pid][:12]
    like = [x for x in data["paintings"] if x["g"] == p["g"] and x["id"] != pid and not x.get("n")]
    like = sorted(like, key=lambda x: abs(x["y"] - p["y"]))[:12]
    return render_template(
        "fineart/painting.html", p=p, artists=artists, genre=data["genres"][p["g"]], genres=data["genres"],
        prev_p=prev_p, next_p=next_p, same_artist=same_artist, like=like, g=g,
    )


@bp.route("/artist/<aid>")
def artist(aid):
    data = load()
    a = data["artists"].get(aid)
    if not a:
        abort(404)
    works = data["by_artist"].get(aid, [])
    return render_template("fineart/artist.html", a=a | {"id": aid}, works=works, genres=data["genres"])


@bp.route("/today")
def today():
    data = load()
    pool = [p for p in data["paintings"][:300] if not p.get("n")]
    return redirect(url_for("fineart.painting", pid=pool[date.today().toordinal() % len(pool)]["id"]))
