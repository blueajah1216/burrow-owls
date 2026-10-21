"""
Accounts for /fineart: sign up with a username + password, or "Sign in with Google".
Signed-in visitors get their favorite paintings saved to their account (synced with
the localStorage favorites that logged-out visitors already have).

Wired up from app.py with `init_auth(app, db)`; call it before db.create_all().

Config (env vars):
  SECRET_KEY            required in production (Flask sessions)
  GOOGLE_CLIENT_ID      } optional; the Google button only appears when both are set
  GOOGLE_CLIENT_SECRET  }
  GOOGLE_REDIRECT_URI   optional override of the callback URL
                        (default: https://<host>/fineart/auth/google/callback)
"""

import os
import re
import secrets
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta

from flask import (Blueprint, abort, current_app, g, jsonify, redirect, render_template,
                   request, session, url_for)
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash

import fineart

bp = Blueprint("fineart_auth", __name__, url_prefix="/fineart")

USERNAME_RE = re.compile(r"^[a-z0-9_]{3,24}$")
MAX_FAVS = 3000
# pbkdf2 works on every Python build (scrypt is missing on some).
def hash_pw(pw):
    return generate_password_hash(pw, method="pbkdf2:sha256:600000")


# A throwaway hash so unknown usernames cost the same time as wrong passwords.
_DUMMY_HASH = hash_pw("not-a-real-password")

User = Favorite = Profile = DB = None  # defined in init_auth
oauth = None
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
    if target and target.startswith("/") and not target.startswith("//") and "\\" not in target:
        return target
    return url_for("fineart.index")


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


def google_enabled():
    return bool(os.environ.get("GOOGLE_CLIENT_ID") and os.environ.get("GOOGLE_CLIENT_SECRET"))


def init_auth(app, db):
    global User, Favorite, Profile, DB, oauth
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
        username = db.Column(db.String(24), unique=True, nullable=True)  # lowercase; Google users have none
        display_name = db.Column(db.String(60), nullable=False)
        password_hash = db.Column(db.String(255), nullable=True)
        google_sub = db.Column(db.String(64), unique=True, nullable=True)
        email = db.Column(db.String(255), nullable=True)  # from Google only; never used to link accounts
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        favorites = db.relationship("_Favorite", backref="user", cascade="all, delete-orphan", lazy="dynamic")

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

    User, Favorite, Profile = _User, _Favorite, _Profile

    if google_enabled():
        from authlib.integrations.flask_client import OAuth
        oauth = OAuth(app)
        oauth.register(
            name="google",
            client_id=os.environ["GOOGLE_CLIENT_ID"],
            client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )

    @app.before_request
    def _load_user():
        g.fa_user = None
        if request.path.startswith("/fineart") and session.get("uid"):
            g.fa_user = db.session.get(User, session["uid"])
            if g.fa_user is None:
                session.pop("uid", None)

    @app.context_processor
    def _inject():
        if not request.path.startswith("/fineart"):
            return {}
        return dict(fa_current=getattr(g, "fa_user", None), fa_csrf=csrf_token, fa_google=google_enabled())

    @app.after_request
    def _no_store_for_accounts(resp):
        if request.path.startswith("/fineart/") and (request.path.startswith("/fineart/api/") or
                                                      request.path.split("/")[2:3] in (["login"], ["signup"], ["account"])):
            resp.headers["Cache-Control"] = "no-store"
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
    error = "Google sign-in didn't work. Please try again." if request.args.get("error") == "google" else None
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
    return redirect(url_for("fineart.index"))


@bp.route("/account")
def account():
    _ready()
    if not g.fa_user:
        return redirect(url_for("fineart_auth.login", next=request.path))
    prof = _session().get(Profile, g.fa_user.id)
    return render_template("fineart/account.html", count=g.fa_user.favorites.count(), is_public=bool(prof and prof.public))


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
    return redirect(url_for("fineart_auth.account"))


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
    return redirect(url_for("fineart_auth.account"))


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
    return redirect(url_for("fineart.index"))


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


# ---------------------------------------------------------------- Google

@bp.route("/auth/google")
def google_start():
    _ready()
    if not oauth:
        abort(404)
    session["oauth_next"] = safe_next(request.args.get("next"))
    redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI") or url_for("fineart_auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@bp.route("/auth/google/callback")
def google_callback():
    _ready()
    if not oauth:
        abort(404)
    nxt = safe_next(session.get("oauth_next"))
    try:
        token = oauth.google.authorize_access_token()
        info = token.get("userinfo") or {}
    except Exception:
        return redirect(url_for("fineart_auth.login", error="google"))
    sub = info.get("sub")
    if not sub:
        return redirect(url_for("fineart_auth.login", error="google"))
    s = _session()
    u = User.query.filter_by(google_sub=sub).first()
    if not u:
        name = (info.get("name") or info.get("given_name") or "Art lover").strip()[:60]
        u = User(google_sub=sub, display_name=name, email=info.get("email"))
        s.add(u)
        s.commit()
    login_user(u)
    return redirect(nxt)


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
