"""
The Great Gallery — Photography. A sister to /fineart: great photographs from 1826 to today,
traced through time, with kid-friendly texts.

Data: data/photo/gallery.json (built by photo_build/build_data.py).
Everything shown is public domain, CC0, or freely licensed with the credit displayed.
"""

import gzip
import json
import os
import random
from datetime import date
from urllib.parse import quote_plus

from flask import Blueprint, Response, abort, redirect, render_template, request, url_for

bp = Blueprint("photo", __name__, url_prefix="/photography")

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(ROOT, "data", "photo", "gallery.json")
_cache = {"mtime": None, "data": None}


def load():
    mtime = os.path.getmtime(DATA_PATH)
    if _cache["mtime"] != mtime:
        with open(DATA_PATH, encoding="utf-8") as f:
            data = json.load(f)
        data["by_id"] = {p["id"]: p for p in data["photos"]}
        by_artist = {}
        for p in data["photos"]:
            for a in p["a"]:
                by_artist.setdefault(a, []).append(p)
        data["by_artist"] = by_artist
        data["col_by_slug"] = {c["slug"]: c for c in data.get("collections", [])}
        for i, e in enumerate(data["eras"]):
            e["idx"] = i
            e["photos"] = [p for p in data["photos"] if e["start"] <= p["y"] <= e["end"] and not p.get("n")]
        for e in data["eras"]:
            picks = [data["by_id"][i] for i in e.get("pick_ids", []) if i in data["by_id"]] or sorted(e["photos"], key=lambda x: x["r"])[:8]
            e["picks"], e["cover"] = picks[:8], (picks[0] if picks else None)
        data["era_by_slug"] = {e["slug"]: e for e in data["eras"]}
        _cache.update(mtime=mtime, data=data, json_mtime=None)
    return _cache["data"]


def era_of(data, y):
    return next((e for e in data["eras"] if e["start"] <= y <= e["end"]), data["eras"][-1])


def card_ratio(p):
    return f"{min(max(p['w'] / p['h'], 0.55), 2.2):.3f}"


def lived(a):
    b, d = a.get("b"), a.get("d")
    if b is None and d is None:
        return "Photographer"
    return f"{b or '?'}–{d or '?'}"


def hires_info(p):
    mp = (p.get("hw") or 0) * (p.get("hh") or 0) / 1e6
    return dict(url=p.get("hi") or p["u"], page=p["p"], w=p.get("hw"), h=p.get("hh"), mp=round(mp, 1),
                in_w=round(p["hw"] / 300) if p.get("hw") else None, in_h=round(p["hh"] / 300) if p.get("hh") else None,
                level="high" if mp >= 8 else "good" if mp >= 3 else "low" if mp else "unknown", src=p["s"])


def print_links(p, artists):
    q = f"{p['t']} {artists[0]['n'] if artists else ''}".strip()
    return [
        {"tier": "Budget", "icon": "💵", "shop": "Etsy", "blurb": "Posters and simple prints from small sellers, usually the lowest prices.",
         "url": f"https://www.etsy.com/search?q={quote_plus(q + ' poster print')}"},
        {"tier": "Mid-range", "icon": "🖼️", "shop": "Fine Art America", "blurb": "Good printing on paper, canvas or metal, made to order, with framing options.",
         "url": f"https://fineartamerica.com/shop/prints?keyword={quote_plus(q)}"},
    ]


def collection_cards(data):
    out = []
    for c in data.get("collections", []):
        cover = data["by_id"].get(c.get("cover_id")) or next((data["by_id"][i] for i in c["ids"] if i in data["by_id"] and not data["by_id"][i].get("n")), None)
        out.append(c | {"cover": cover, "count": len(c["ids"])})
    return out


def init_photography(app):
    app.jinja_env.globals.update(ph_card_ratio=card_ratio, ph_lived=lived, ph_hires=hires_info, ph_prints=print_links)
    app.register_blueprint(bp)


# ---------------------------------------------------------------- pages

@bp.route("/")
def index():
    data = load()
    shown = [p for p in data["photos"] if not p.get("n")]
    cols = collection_cards(data)
    return render_template("photo/index.html", genres=data["genres"], eras=data["eras"], total=len(shown),
                           first=data["by_id"].get(data["first_id"]), cols=cols)


@bp.route("/data.json")
def data_json():
    data = load()
    if _cache.get("json_mtime") != _cache["mtime"]:
        raw = json.dumps({"genres": data["genres"], "artists": data["artists"], "photos": data["photos"], "eras": [{k: e[k] for k in ("slug", "name", "start", "end")} for e in data["eras"]]},
                         ensure_ascii=False, separators=(",", ":")).encode()
        _cache.update(json_mtime=_cache["mtime"], json_raw=raw, json_gz=gzip.compress(raw, 6))
    resp = Response(_cache["json_raw"], mimetype="application/json")
    if "gzip" in request.headers.get("Accept-Encoding", ""):
        resp = Response(_cache["json_gz"], mimetype="application/json")
        resp.headers["Content-Encoding"] = "gzip"
    resp.headers["Vary"] = "Accept-Encoding"
    resp.headers["Cache-Control"] = "public, max-age=600"
    return resp


@bp.route("/random")
def random_photo():
    data = load()
    pool = [p for p in data["photos"] if not p.get("n")]
    return redirect(url_for("photo.photo", pid=random.choice(pool)["id"]))


@bp.route("/today")
def today():
    data = load()
    pool = [p for p in data["photos"] if p.get("k") and not p.get("n")]
    return redirect(url_for("photo.photo", pid=pool[date.today().toordinal() % len(pool)]["id"]))


@bp.route("/p/<pid>")
def photo(pid):
    data = load()
    p = data["by_id"].get(pid)
    if not p:
        abort(404)
    artists = [data["artists"][a] | {"id": a} for a in p["a"] if a in data["artists"]]
    era = era_of(data, p["y"])
    pool = [x for x in data["photos"] if x["id"] != pid and not x.get("n")]
    same_artist = [x for x in data["by_artist"].get(p["a"][0], []) if x["id"] != pid and not x.get("n")][:8] if p["a"] else []
    near = sorted(pool, key=lambda x: abs(x["y"] - p["y"]) + (0 if x["g"] == p["g"] else 12))[:8]
    series = [x for x in era["photos"]]
    i = next((k for k, x in enumerate(series) if x["id"] == pid), None)
    prev_p = series[i - 1] if i else None
    next_p = series[i + 1] if i is not None and i + 1 < len(series) else None
    cols = [data["col_by_slug"][c] for c in p.get("c", []) if c in data["col_by_slug"]]
    return render_template("photo/photo.html", p=p, artists=artists, genre=data["genres"][p["g"]], era=era, cols=cols,
                           same_artist=same_artist, near=near, prev_p=prev_p, next_p=next_p)


@bp.route("/photographer/<aid>")
def photographer(aid):
    data = load()
    a = data["artists"].get(aid)
    if not a:
        abort(404)
    works = [w for w in data["by_artist"].get(aid, []) if not w.get("n")]
    return render_template("photo/photographer.html", a=a | {"id": aid}, works=works)


@bp.route("/photographers")
def photographers():
    data = load()
    rows = sorted(((data["artists"][a], a, [w for w in ws if not w.get("n")]) for a, ws in data["by_artist"].items() if a in data["artists"]),
                  key=lambda r: (r[0].get("b") or 9999, r[0]["n"]))
    rows = [r for r in rows if r[2]]
    return render_template("photo/photographers.html", rows=rows)


@bp.route("/collections")
def collections():
    data = load()
    return render_template("photo/collections.html", cols=collection_cards(data))


@bp.route("/collection/<slug>")
def collection(slug):
    data = load()
    c = data["col_by_slug"].get(slug)
    if not c:
        abort(404)
    works = [data["by_id"][i] for i in c["ids"] if i in data["by_id"] and not data["by_id"][i].get("n")]
    others = [x for x in collection_cards(data) if x["slug"] != slug]
    return render_template("photo/collection.html", c=c, works=works, artists=data["artists"], others=others)


@bp.route("/timeline")
def timeline():
    data = load()
    return render_template("photo/timeline.html", eras=data["eras"], milestones=data["milestones"], artists=data["artists"])


@bp.route("/era/<slug>")
def era(slug):
    data = load()
    e = data["era_by_slug"].get(slug)
    if not e:
        abort(404)
    ms = [m for m in data["milestones"] if e["start"] <= m["y"] <= e["end"]]
    return render_template("photo/era.html", e=e, eras=data["eras"], ms=ms, artists=data["artists"])
