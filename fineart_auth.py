"""
Create your gallery: one username/password account for paintings, photography,
and music. Original painting favorites and public painting profiles are preserved.

Wired up from app.py with `init_auth(app, db)`; call it before db.create_all().

Config (env vars):
  SECRET_KEY            required in production (Flask sessions)
"""

import os
import re
import secrets
import time
import unicodedata
from collections import defaultdict, deque
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json

from flask import (Blueprint, abort, current_app, g, jsonify, redirect, render_template,
                   request, session, url_for)
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash

import fineart

bp = Blueprint("fineart_auth", __name__, url_prefix="/fineart")

USERNAME_RE = re.compile(r"^[a-z0-9_]{3,24}$")
MAX_FAVS = 3000
MAX_GALLERY = 6000
KINDS = ("painting", "photo", "music")
# pbkdf2 works on every Python build (scrypt is missing on some).
def hash_pw(pw):
    return generate_password_hash(pw, method="pbkdf2:sha256:600000")


# A throwaway hash so unknown usernames cost the same time as wrong passwords.
_DUMMY_HASH = hash_pw("not-a-real-password")

User = Favorite = SavedItem = Profile = DB = None  # defined in init_auth
_attempts = defaultdict(deque)  # key -> recent attempt timestamps (per-process)


def too_many(key, limit=8, window=600):
    """True if `key` has already used `limit` attempts in the last `window` seconds."""
    now = time.time()
    q = _attempts[key]
    while q and q[0] < now - window:
        q.popleft()
    if len(q) >= limit:
        return True
    q.append(now)
    return False


def safe_next(target):
    """Only allow redirects back to a path on this site."""
    if isinstance(target, str) and len(target) < 2000:
        from galleryhost import is_gallery_host, _strip
        if is_gallery_host():
            target = _strip(target)
        decoded = unquote(unquote(target))
        if is_gallery_host():
            # An encoded legacy prefix may also be stripped by the middleware.
            decoded = _strip(decoded)
        try:
            parsed = urlsplit(decoded)
        except ValueError:
            parsed = None
        if (parsed is not None and decoded.startswith("/") and not decoded.startswith("//")
                and not parsed.scheme and not parsed.netloc and "\\" not in decoded
                and not re.search(r"[\x00-\x1f\x7f]", decoded)
                and " " not in parsed.path):
            return target
    return public_url("fineart_auth.my_gallery")


def public_url(endpoint, **values):
    from galleryhost import is_gallery_host, _strip
    url = url_for(endpoint, **values)
    return _strip(url) if is_gallery_host() else url


def csrf_token():
    if not current_app.config.get("SECRET_KEY"):
        return ""
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(24)
    return session["csrf"]


def check_csrf():
    sent = request.form.get("csrf") or request.headers.get("X-CSRF-Token") or ""
    if not sent or not secrets.compare_digest(sent, session.get("csrf", "")):
        abort(400, "Session expired — please go back, refresh, and try again.")


def login_user(user):
    session.clear()
    session["uid"] = user.id
    session["csrf"] = secrets.token_urlsafe(24)
    session.permanent = True


def init_auth(app, db):
    global User, Favorite, SavedItem, Profile, DB
    DB = db

    # Behind Render's proxy: trust X-Forwarded-Proto/Host so external URLs are https.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    if not app.config.get("SECRET_KEY") and not os.environ.get("RENDER"):
        app.config["SECRET_KEY"] = "dev-only-not-for-production"  # local development
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=bool(os.environ.get("RENDER")),
        PERMANENT_SESSION_LIFETIME=timedelta(days=90),
    )

    class _User(db.Model):
        __tablename__ = "fa_users"
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(24), unique=True, nullable=True)  # lowercase
        display_name = db.Column(db.String(60), nullable=False)
        password_hash = db.Column(db.String(255), nullable=True)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        favorites = db.relationship("_Favorite", backref="user", cascade="all, delete-orphan", lazy="dynamic")
        saved_items = db.relationship("_SavedItem", backref="user", cascade="all, delete-orphan", lazy="dynamic")
        profile = db.relationship("_Profile", cascade="all, delete-orphan", uselist=False)

    class _Favorite(db.Model):
        __tablename__ = "fa_favorites"
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey("fa_users.id"), nullable=False, index=True)
        painting_id = db.Column(db.String(120), nullable=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        __table_args__ = (db.UniqueConstraint("user_id", "painting_id", name="uix_fa_user_painting"),)

    class _Profile(db.Model):
        """Opt-in public profile. No row (or public=False) means the user is private."""
        __tablename__ = "fa_profiles"
        user_id = db.Column(db.Integer, db.ForeignKey("fa_users.id", ondelete="CASCADE"), primary_key=True)
        public = db.Column(db.Boolean, nullable=False, default=False)

    class _SavedItem(db.Model):
        """Photo and music saves; the original painting table stays intact."""
        __tablename__ = "fa_saved_items"
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey("fa_users.id"), nullable=False, index=True)
        kind = db.Column(db.String(20), nullable=False)
        item_id = db.Column(db.String(120), nullable=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        __table_args__ = (db.UniqueConstraint("user_id", "kind", "item_id", name="uix_fa_user_saved_item"),)

    User, Favorite, SavedItem, Profile = _User, _Favorite, _SavedItem, _Profile

    @app.before_request
    def _load_user():
        g.fa_user = None
        if request.path.startswith(("/fineart", "/photography", "/music")) and session.get("uid"):
            g.fa_user = db.session.get(User, session["uid"])
            if g.fa_user is None:
                session.pop("uid", None)

    @app.context_processor
    def _inject():
        if not request.path.startswith(("/fineart", "/photography", "/music")):
            return {}
        user = getattr(g, "fa_user", None)
        ids = gallery_ids(user) if user else {kind: [] for kind in KINDS}
        g.gallery_ids = ids
        return dict(fa_current=user, fa_csrf=csrf_token, gallery_ids=ids,
                    gallery_total=sum(map(len, ids.values())),
                    gallery_saved=lambda kind, item_id: item_id in ids.get(kind, []))

    @app.after_request
    def _no_store_for_accounts(resp):
        if (request.path.startswith("/fineart/api/") or request.endpoint in (
                "fineart_auth.login", "fineart_auth.signup", "fineart_auth.account", "fineart_auth.my_gallery")
                or (getattr(g, "fa_user", None) and resp.mimetype == "text/html")):
            resp.headers["Cache-Control"] = "private, no-store"
        if resp.mimetype == "text/html":
            resp.vary.add("Cookie")
        if request.endpoint in ("fineart_auth.account", "fineart_auth.my_gallery"):
            resp.headers["X-Robots-Tag"] = "noindex, nofollow"
        return resp

    app.register_blueprint(bp)


def _ready():
    if not current_app.config.get("SECRET_KEY"):
        abort(503, "Accounts aren't switched on yet (the server needs a SECRET_KEY).")


def _session():
    return DB.session


# ---------------------------------------------------------------- pages

@bp.route("/signup", methods=["GET", "POST"])
def signup():
    _ready()
    nxt = safe_next(request.values.get("next"))
    if g.fa_user:
        return redirect(nxt)
    error, form = None, {}
    if request.method == "POST":
        check_csrf()
        username = (request.form.get("username") or "").strip().lower()
        display = (request.form.get("display_name") or "").strip()[:60]
        pw, pw2 = request.form.get("password") or "", request.form.get("password2") or ""
        form = dict(username=username, display_name=display)
        if too_many("signup:" + (request.remote_addr or ""), limit=10, window=3600):
            error = "Too many sign-ups from this network. Please try again later."
        elif not USERNAME_RE.match(username):
            error = "Usernames are 3–24 characters: letters, numbers and underscores."
        elif len(pw) < 8:
            error = "Passwords need at least 8 characters."
        elif len(pw) > 200:
            error = "That password is too long."
        elif pw != pw2:
            error = "The two passwords don't match."
        elif User.query.filter_by(username=username).first():
            error = "That username is taken — try another."
        else:
            s = _session()
            u = User(username=username, display_name=display or username, password_hash=hash_pw(pw))
            s.add(u)
            try:
                s.commit()
            except Exception:  # lost a race on the unique username
                s.rollback()
                error = "That username is taken — try another."
            else:
                login_user(u)
                return redirect(nxt)
    return render_template("fineart/signup.html", error=error, form=form, next=nxt), (400 if error else 200)


@bp.route("/login", methods=["GET", "POST"])
def login():
    _ready()
    nxt = safe_next(request.values.get("next"))
    if g.fa_user:
        return redirect(nxt)
    error = None
    username = ""
    if request.method == "POST":
        check_csrf()
        username = (request.form.get("username") or "").strip().lower()
        pw = request.form.get("password") or ""
        if too_many(f"login:{request.remote_addr}:{username}") or too_many("login-ip:" + (request.remote_addr or ""), limit=40):
            error = "Too many tries. Please wait a few minutes and try again."
        else:
            u = User.query.filter_by(username=username).first() if username else None
            ok = check_password_hash(u.password_hash if u and u.password_hash else _DUMMY_HASH, pw)
            if u and u.password_hash and ok:
                login_user(u)
                return redirect(nxt)
            error = "That username and password don't match."
    return render_template("fineart/login.html", error=error, username=username, next=nxt), (401 if request.method == "POST" and error else 200)


@bp.route("/logout", methods=["POST"])
def logout():
    check_csrf()
    session.clear()
    return redirect(public_url("fineart.index"))


@bp.route("/account")
def account():
    _ready()
    if not g.fa_user:
        return redirect(public_url("fineart_auth.login", next=safe_next(request.full_path.rstrip("?"))))
    prof = _session().get(Profile, g.fa_user.id)
    ids = gallery_ids(g.fa_user)
    return render_template("fineart/account.html", counts={k: len(v) for k, v in ids.items()},
                           is_public=bool(prof and prof.public), message=request.args.get("updated"))


@bp.route("/account/name", methods=["POST"])
def account_name():
    _ready()
    check_csrf()
    if not g.fa_user:
        abort(401)
    name = (request.form.get("display_name") or "").strip()[:60]
    if name:
        g.fa_user.display_name = name
        _session().commit()
    return redirect(public_url("fineart_auth.account", updated="name"))


@bp.route("/account/public", methods=["POST"])
def account_public():
    _ready()
    check_csrf()
    if not g.fa_user:
        abort(401)
    s = _session()
    prof = s.get(Profile, g.fa_user.id) or Profile(user_id=g.fa_user.id)
    prof.public = request.form.get("public") == "1"
    s.add(prof)
    s.commit()
    return redirect(public_url("fineart_auth.account", updated="privacy"))


@bp.route("/account/delete", methods=["POST"])
def account_delete():
    _ready()
    check_csrf()
    if not g.fa_user:
        abort(401)
    s = _session()
    s.delete(g.fa_user)
    s.commit()
    session.clear()
    return redirect(public_url("fineart.index"))


@bp.post("/account/password")
def account_password():
    _ready()
    if not g.fa_user:
        abort(401)
    check_csrf()
    current = request.form.get("current_password") or ""
    password = request.form.get("password") or ""
    confirmation = request.form.get("password2") or ""
    error = None
    if not check_password_hash(g.fa_user.password_hash or _DUMMY_HASH, current):
        error = "Your current password doesn't match."
    elif not 8 <= len(password) <= 200:
        error = "Choose a new password with 8–200 characters."
    elif password != confirmation:
        error = "The two new passwords don't match."
    if error:
        prof = _session().get(Profile, g.fa_user.id)
        return render_template("fineart/account.html", error=error, message=None,
                               counts={k: len(v) for k, v in gallery_ids(g.fa_user).items()},
                               is_public=bool(prof and prof.public)), 400
    user = g.fa_user
    user.password_hash = hash_pw(password)
    _session().commit()
    login_user(user)
    return redirect(public_url("fineart_auth.account", updated="password"))


# ---------------------------------------------------------------- unified personal gallery

def gallery_ids(user):
    ids = {kind: [] for kind in KINDS}
    if user:
        ids["painting"] = _fav_ids(user)
        for item in user.saved_items.order_by(SavedItem.created_at, SavedItem.id):
            if item.kind in ids:
                ids[item.kind].append(item.item_id)
    return ids


@lru_cache(maxsize=1)
def _practice_catalog(mtime):
    path = Path(__file__).parent / "data" / "choir" / "library.json"
    return {"practice:" + song["id"]: song for song in json.loads(path.read_text())}


def gallery_catalog():
    if not hasattr(g, "gallery_catalog"):
        import photography
        from music_history import load_history
        history, composers, eras = load_history()
        practice_path = Path(__file__).parent / "data" / "choir" / "library.json"
        g.gallery_catalog = {
            "painting": fineart.load()["by_id"],
            "photo": {key: p for key, p in photography.load()["by_id"].items() if not p.get("n")},
            "music": {w["id"]: w for w in history["works"]} | _practice_catalog(practice_path.stat().st_mtime),
        }
    return g.gallery_catalog


def _gallery_item(kind, item_id):
    item = gallery_catalog().get(kind, {}).get(item_id)
    base = dict(kind=kind, id=item_id, thumbnail=None, mature=False, href=None,
                title="Saved item no longer available", creator="", date="", label="Saved item")
    if item is None:
        return base
    if kind in ("painting", "photo"):
        import photography
        data = fineart.load() if kind == "painting" else photography.load()
        base.update(title=item["t"], creator=" & ".join(data["artists"][a]["n"] for a in item["a"] if a in data["artists"]),
                    date=item.get("d") or str(item["y"]), mature=bool(item.get("n")),
                    label="Painting" if kind == "painting" else "Photograph",
                    href=public_url("fineart.painting" if kind == "painting" else "photo.photo", pid=item_id))
        if not base["mature"]:
            base["thumbnail"] = fineart.img_url(item, 500) if kind == "painting" else item["th"]
    elif item_id.startswith("practice:"):
        base.update(title=item["title"], creator=item.get("origin") or item["category"], label="Practice song",
                    href=public_url("choir.index", song=item["id"]), date="Four-part singing")
    else:
        from music_history import load_history
        history, composers, eras = load_history()
        base.update(title=item["title"], creator=composers[item["composer"]]["name"], date=item["date"],
                    label=item["form"], href=public_url("music.history_piece", slug=item_id))
    return base


def _normal_text(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(c))


@bp.get("/my-gallery")
def my_gallery():
    _ready()
    if not g.fa_user:
        return redirect(public_url("fineart_auth.login", next=safe_next(request.full_path.rstrip("?"))))
    records = [("painting", f.painting_id, f.created_at) for f in g.fa_user.favorites]
    records += [(f.kind, f.item_id, f.created_at) for f in g.fa_user.saved_items if f.kind in KINDS]
    records.sort(key=lambda row: (row[2], row[0], row[1]), reverse=True)
    counts = {kind: sum(row[0] == kind for row in records) for kind in KINDS}
    selected = request.args.get("kind", "all")
    if selected not in (*KINDS, "all"):
        selected = "all"
    query = request.args.get("q", "").strip()[:100]
    items = [_gallery_item(kind, item_id) for kind, item_id, _ in records if selected in ("all", kind)]
    terms = _normal_text(query).split()
    if terms:
        items = [item for item in items if all(term in _normal_text(" ".join(
            (item["title"], item["creator"], item["label"]))) for term in terms)]
    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1
    pages = max(1, (len(items) + 59) // 60)
    page = min(page, pages)
    return render_template("gallery/collection.html", counts=counts, total=len(records),
                           items=items[(page - 1) * 60:page * 60], filtered_total=len(items),
                           selected=selected, query=query, page=page, pages=pages)


def _parse_changes(body):
    if not isinstance(body, dict):
        abort(400, "Expected a JSON object.")
    operations = []
    for action in ("add", "remove"):
        values = body.get(action, {})
        if not isinstance(values, dict) or any(kind not in KINDS for kind in values):
            abort(400, "Choose paintings, photography, or music.")
        result = {}
        for kind, ids in values.items():
            if not isinstance(ids, list) or len(ids) > MAX_FAVS or any(not isinstance(i, str) or len(i) > 120 for i in ids):
                abort(400, "Expected a list of saved-item IDs.")
            result[kind] = list(dict.fromkeys(ids))
        operations.append(result)
    return operations


def _apply_gallery_changes(add, remove):
    s = _session()
    catalog = gallery_catalog()
    have = {kind: set(ids) for kind, ids in gallery_ids(g.fa_user).items()}
    for kind, ids in remove.items():
        if kind == "painting":
            Favorite.query.filter(Favorite.user_id == g.fa_user.id, Favorite.painting_id.in_(ids)).delete(synchronize_session=False)
        else:
            SavedItem.query.filter(SavedItem.user_id == g.fa_user.id, SavedItem.kind == kind, SavedItem.item_id.in_(ids)).delete(synchronize_session=False)
        have[kind].difference_update(ids)
    total = sum(map(len, have.values()))
    painting_rows, item_rows = [], []
    for kind, ids in add.items():
        for item_id in ids:
            if (item_id in have[kind] or item_id not in catalog[kind] or item_id in remove.get(kind, [])
                    or total >= MAX_GALLERY or len(have[kind]) >= MAX_FAVS):
                continue
            if kind == "painting":
                painting_rows.append(dict(user_id=g.fa_user.id, painting_id=item_id))
            else:
                item_rows.append(dict(user_id=g.fa_user.id, kind=kind, item_id=item_id))
            have[kind].add(item_id)
            total += 1
    # Native conflict handling keeps simultaneous tabs idempotent, including imports.
    if DB.engine.dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert
    for model, rows, columns in (
            (Favorite, painting_rows, ["user_id", "painting_id"]),
            (SavedItem, item_rows, ["user_id", "kind", "item_id"])):
        if rows:
            s.execute(insert(model).values(rows).on_conflict_do_nothing(index_elements=columns))
    s.commit()


@bp.route("/api/gallery", methods=["GET", "POST"])
def api_gallery():
    _ready()
    if not g.fa_user:
        return jsonify(error="Log in to save your gallery across devices."), 401
    if request.method == "POST":
        check_csrf()
        add, remove = _parse_changes(request.get_json(silent=True))
        _apply_gallery_changes(add, remove)
    ids = gallery_ids(g.fa_user)
    return jsonify(ids=ids, counts={kind: len(values) for kind, values in ids.items()})


@bp.post("/gallery/save")
def save_item():
    _ready()
    nxt = safe_next(request.form.get("next"))
    if not g.fa_user:
        return redirect(public_url("fineart_auth.login", next=nxt), code=303)
    check_csrf()
    kind, item_id = request.form.get("kind"), request.form.get("id", "")
    if kind not in KINDS or len(item_id) > 120:
        abort(400)
    remove = request.form.get("action") == "remove"
    if not remove and item_id not in gallery_catalog()[kind]:
        abort(404)
    _apply_gallery_changes({} if remove else {kind: [item_id]}, {kind: [item_id]} if remove else {})
    return redirect(nxt, code=303)


# ---------------------------------------------------------------- Art Lovers (opt-in public profiles)

@bp.route("/lovers")
def lovers():
    _ready()
    rows = (_session().query(User, DB.func.count(Favorite.id))
            .join(Profile, Profile.user_id == User.id).filter(Profile.public.is_(True))
            .outerjoin(Favorite, Favorite.user_id == User.id).group_by(User.id)
            .order_by(DB.func.count(Favorite.id).desc(), User.display_name).all())
    return render_template("fineart/lovers.html", rows=[(u, n) for u, n in rows if n])


@bp.route("/lovers/<int:uid>")
def lover(uid):
    _ready()
    u = _session().get(User, uid)
    prof = _session().get(Profile, uid) if u else None
    if not u or not (prof and prof.public):
        abort(404)
    data = fineart.load()
    works = [data["by_id"][i] for i in _fav_ids(u) if i in data["by_id"] and not data["by_id"][i].get("n")]
    return render_template("fineart/lover.html", u=u, works=works, artists=data["artists"])


# ---------------------------------------------------------------- favorites API

def _fav_ids(user):
    return [f.painting_id for f in user.favorites.order_by(Favorite.created_at)]


@bp.route("/api/favorites", methods=["GET", "POST"])
def api_favorites():
    """GET -> {"ids": [...]}.  POST {"add": [...], "remove": [...]} -> the new full list."""
    if not g.fa_user:
        return jsonify(error="login required"), 401
    if request.method == "GET":
        return jsonify(ids=_fav_ids(g.fa_user))
    check_csrf()
    body = request.get_json(silent=True) or {}
    valid = fineart.load()["by_id"]
    add = [i for i in (body.get("add") or []) if isinstance(i, str) and i in valid][:MAX_FAVS]
    remove = [i for i in (body.get("remove") or []) if isinstance(i, str)][:MAX_FAVS]
    s = _session()
    have = set(_fav_ids(g.fa_user))
    for pid in add:
        if pid not in have and len(have) < MAX_FAVS:
            s.add(Favorite(user_id=g.fa_user.id, painting_id=pid))
            have.add(pid)
    if remove:
        Favorite.query.filter(Favorite.user_id == g.fa_user.id, Favorite.painting_id.in_(remove)).delete(synchronize_session=False)
    s.commit()
    return jsonify(ids=_fav_ids(g.fa_user))
