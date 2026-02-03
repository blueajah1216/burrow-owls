import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import requests
from flask import (
    Flask,
    abort,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from people import PEOPLE
from models import db, Review, Artwork, BookMetadata, SiteCounter

# -----------------------------
# Paths & helpers
# -----------------------------
BASE_DIR = Path(__file__).parent
READING_LIST_PATH = BASE_DIR / "data" / "reading_lists.json"

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def load_reading_lists() -> dict:
    if not READING_LIST_PATH.exists():
        return {}
    return json.loads(READING_LIST_PATH.read_text(encoding="utf-8"))


def get_person_or_404(person: str) -> str:
    if person not in PEOPLE:
        abort(404)
    return person


def get_person_books(person: str) -> dict:
    lists = load_reading_lists()
    return lists.get(person, {"year": 2026, "books": []})


def allowed_image_file(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS


# -----------------------------
# Flask app setup
# -----------------------------
app = Flask(__name__)

# Needed for session cookies (unlocking writes in the browser)
# Set this in Render -> Environment: SECRET_KEY=<random long string>
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "")

# For Render persistence (recommended):
# - Add a Render Disk mounted at /var/data
# - Set:
#     DATABASE_URL=sqlite:////var/data/burrowowls.db
#     UPLOAD_ROOT=/var/data/uploads
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///burrowowls.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Limit uploads (8MB)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

db.init_app(app)

with app.app_context():
    db.create_all()

    # Ensure a single counter row exists (id=1)
    counter = SiteCounter.query.get(1)
    if counter is None:
        counter = SiteCounter(id=1, visits=0)
        db.session.add(counter)
        db.session.commit()

# Upload storage root
UPLOAD_ROOT = os.environ.get("UPLOAD_ROOT", str(BASE_DIR / "uploads"))

# Shared family key for *all write actions* (art uploads + review edits)
UPLOAD_KEY = os.environ.get("UPLOAD_KEY", "")

# How long unlock lasts in the browser
UNLOCK_TTL_SECONDS = 60 * 60 * 6  # 6 hours

# Ensure upload directories exist
os.makedirs(UPLOAD_ROOT, exist_ok=True)
for p in PEOPLE.keys():
    os.makedirs(os.path.join(UPLOAD_ROOT, p), exist_ok=True)


# -----------------------------
# Auth helpers
# -----------------------------
def session_unlocked() -> bool:
    ts = session.get("write_unlocked_at")
    if not ts:
        return False
    try:
        ts = float(ts)
    except (TypeError, ValueError):
        return False
    return (time.time() - ts) < UNLOCK_TTL_SECONDS


def require_write_auth():
    """
    Require write auth for review edits and art uploads.
    - Fail closed if UPLOAD_KEY is not set.
    - Allow if session is unlocked.
    - Otherwise allow if correct key provided in request (fallback).
    """
    if not UPLOAD_KEY:
        abort(403, "Writes are disabled (UPLOAD_KEY not set).")

    if session_unlocked():
        return

    provided = (
        request.form.get("upload_key")
        or request.headers.get("X-Upload-Key")
        or request.args.get("upload_key")
    )
    if provided != UPLOAD_KEY:
        abort(403, "Not allowed.")

@app.context_processor
def inject_site_counter():
    """
    Makes `site_visits` available in every template automatically.
    """
    try:
        counter = SiteCounter.query.get(1)
        return {"site_visits": int(counter.visits) if counter else 0}
    except Exception:
        return {"site_visits": 0}

@app.before_request
def count_visit_once_per_session():
    """
    Old-school visitor counter:
    - counts once per browser session (more like "people visited" than page views)
    - does NOT count static assets
    """
    # Don't count static files
    if request.path.startswith("/static/") or request.path.startswith("/uploads/"):
        return

    # Only count normal page GETs
    if request.method != "GET":
        return

    # Count only once per session
    if session.get("counted_visit"):
        return

    session["counted_visit"] = True

    try:
        counter = SiteCounter.query.get(1)
        if counter is None:
            counter = SiteCounter(id=1, visits=0)
            db.session.add(counter)

        counter.visits = (counter.visits or 0) + 1
        db.session.commit()
    except Exception:
        db.session.rollback()
        # Don't break the site if counting fails
        return

# -----------------------------
# Book metadata (Open Library)
# -----------------------------
def fetch_openlibrary_metadata(title: str, author: str | None):
    """
    Returns dict: {cover_url, summary} possibly None values.
    Uses Open Library Search + Work details.
    """
    # 1) Search
    params = {"title": title}
    if author:
        params["author"] = author

    r = requests.get("https://openlibrary.org/search.json", params=params, timeout=8)
    r.raise_for_status()
    data = r.json()
    docs = data.get("docs", [])
    if not docs:
        return {"cover_url": None, "summary": None}

    doc = docs[0]

    cover_url = None
    cover_i = doc.get("cover_i")
    if cover_i:
        cover_url = f"https://covers.openlibrary.org/b/id/{cover_i}-L.jpg"

    summary = None
    # 2) If there's a work key, try to fetch its description
    work_key = None
    key = doc.get("key")  # often like "/works/OLxxxxW"
    if isinstance(key, str) and key.startswith("/works/"):
        work_key = key

    if work_key:
        wr = requests.get(f"https://openlibrary.org{work_key}.json", timeout=8)
        if wr.ok:
            wj = wr.json()
            desc = wj.get("description")
            if isinstance(desc, str):
                summary = desc
            elif isinstance(desc, dict):
                summary = desc.get("value")

    return {"cover_url": cover_url, "summary": summary}


def get_or_update_book_metadata(book_slug: str, title: str, author: str | None):
    """
    Read cached metadata. If missing/empty, fetch from Open Library and store.
    """
    meta = BookMetadata.query.filter_by(book_slug=book_slug).first()
    if meta and (meta.cover_url or meta.summary):
        return meta

    # Create if missing
    if not meta:
        meta = BookMetadata(book_slug=book_slug, title=title, author=author, source="openlibrary")
        db.session.add(meta)

    try:
        fetched = fetch_openlibrary_metadata(title, author)
        meta.cover_url = fetched.get("cover_url")
        meta.summary = fetched.get("summary")
        meta.source = "openlibrary"
        db.session.commit()
    except Exception:
        # If Open Library is down, keep whatever we have and don't crash the page.
        db.session.rollback()

    return meta


# -----------------------------
# Routes: Home / Person pages
# -----------------------------
@app.get("/")
def index():
    return redirect(url_for("person_home", person="richard"))


@app.get("/<person>")
def person_home(person):
    person = get_person_or_404(person)
    data = get_person_books(person)
    books = [{**b, "slug": slugify(b["title"])} for b in data["books"]]
    return render_template(
        "person_home.html",
        person_key=person,
        person_name=PEOPLE[person],
        year=data["year"],
        books=books,
    )


@app.get("/<person>/reading-list")
def reading_list(person):
    person = get_person_or_404(person)
    data = get_person_books(person)
    books = [{**b, "slug": slugify(b["title"])} for b in data["books"]]
    return render_template(
        "reading_list.html",
        person_key=person,
        person_name=PEOPLE[person],
        year=data["year"],
        books=books,
    )


# -----------------------------
# Routes: Reviews (public view + protected edit)
# -----------------------------
@app.get("/<person>/review/<book_slug>")
def review_view(person, book_slug):
    person = get_person_or_404(person)

    data = get_person_books(person)
    books = [{**b, "slug": slugify(b["title"])} for b in data["books"]]
    book = next((b for b in books if b["slug"] == book_slug), None)
    if not book:
        abort(404)

    review = Review.query.filter_by(person=person, book_slug=book_slug).first()
    meta = get_or_update_book_metadata(book_slug, book["title"], book.get("author"))

    return render_template(
        "review_view.html",
        person_key=person,
        person_name=PEOPLE[person],
        year=data["year"],
        books=books,
        book=book,
        review=review,
        meta=meta,
        unlocked=session_unlocked(),
        uploads_disabled=(not UPLOAD_KEY),
        session_ready=bool(app.config.get("SECRET_KEY")),
    )


@app.get("/<person>/review/<book_slug>/edit")
def review_edit(person, book_slug):
    person = get_person_or_404(person)

    # Require session unlock (or key in query as fallback, but we keep UI clean)
    if not session_unlocked():
        return redirect(url_for("review_view", person=person, book_slug=book_slug))

    data = get_person_books(person)
    books = [{**b, "slug": slugify(b["title"])} for b in data["books"]]
    book = next((b for b in books if b["slug"] == book_slug), None)
    if not book:
        abort(404)

    review = Review.query.filter_by(person=person, book_slug=book_slug).first()

    return render_template(
        "review_edit.html",
        person_key=person,
        person_name=PEOPLE[person],
        year=data["year"],
        books=books,
        book=book,
        review=review,
    )


@app.post("/<person>/review/<book_slug>/edit")
def review_save(person, book_slug):
    person = get_person_or_404(person)

    # Enforce key/session for saving edits
    require_write_auth()

    data = get_person_books(person)
    books = [{**b, "slug": slugify(b["title"])} for b in data["books"]]
    book = next((b for b in books if b["slug"] == book_slug), None)
    if not book:
        abort(404)

    rating_raw = request.form.get("rating", "").strip()
    rating = int(rating_raw) if rating_raw.isdigit() else None
    if rating is not None and (rating < 1 or rating > 10):
        rating = None

    finished_raw = request.form.get("finished_date", "").strip()
    finished_date = None
    if finished_raw:
        try:
            finished_date = datetime.strptime(finished_raw, "%Y-%m-%d").date()
        except ValueError:
            finished_date = None

    text = request.form.get("review_text", "").strip()

    review = Review.query.filter_by(person=person, book_slug=book_slug).first()
    if review is None:
        review = Review(
            person=person,
            book_slug=book_slug,
            title=book["title"],
            author=book.get("author"),
        )
        db.session.add(review)

    review.rating = rating
    review.finished_date = finished_date
    review.review_text = text
    db.session.commit()

    return redirect(url_for("review_view.html", person=person, book_slug=book_slug))


@app.post("/<person>/unlock")
def unlock_writes(person):
    """
    Enter the family key on a page; unlock writes for this browser session.
    """
    person = get_person_or_404(person)
    if not UPLOAD_KEY:
        abort(403, "Writes are disabled (UPLOAD_KEY not set).")

    provided = request.form.get("upload_key", "")
    if provided != UPLOAD_KEY:
        return redirect(request.referrer or url_for("person_home", person=person))

    if not app.config.get("SECRET_KEY"):
        # Sessions won't persist without SECRET_KEY
        return redirect(request.referrer or url_for("person_home", person=person))

    session["write_unlocked_at"] = str(time.time())
    return redirect(request.referrer or url_for("person_home", person=person))


# -----------------------------
# Routes: Art gallery + uploads (still protected)
# -----------------------------
@app.get("/<person>/art")
def art_gallery(person):
    person = get_person_or_404(person)
    data = get_person_books(person)
    books = [{**b, "slug": slugify(b["title"])} for b in data["books"]]

    artworks = (
        Artwork.query.filter_by(person=person)
        .order_by(Artwork.created_at.desc())
        .all()
    )

    return render_template(
        "art_gallery.html",
        person_key=person,
        person_name=PEOPLE[person],
        year=data["year"],
        books=books,
        artworks=artworks,
    )


@app.get("/<person>/art/upload")
def art_upload_form(person):
    person = get_person_or_404(person)
    data = get_person_books(person)
    books = [{**b, "slug": slugify(b["title"])} for b in data["books"]]

    return render_template(
        "art_upload.html",
        person_key=person,
        person_name=PEOPLE[person],
        year=data["year"],
        books=books,
        uploads_disabled=(not UPLOAD_KEY),
        unlocked=session_unlocked(),
        session_ready=bool(app.config.get("SECRET_KEY")),
    )


@app.post("/<person>/art/upload")
def art_upload_save(person):
    person = get_person_or_404(person)

    require_write_auth()

    file = request.files.get("image")
    title = request.form.get("title", "").strip()

    if not file or file.filename == "":
        abort(400, "No file selected")

    if not allowed_image_file(file.filename):
        abort(400, "Unsupported file type")

    original = file.filename
    safe = secure_filename(original)
    ext = safe.rsplit(".", 1)[1].lower()

    stored = f"{uuid4().hex}.{ext}"
    person_dir = os.path.join(UPLOAD_ROOT, person)
    os.makedirs(person_dir, exist_ok=True)

    save_path = os.path.join(person_dir, stored)
    file.save(save_path)

    art = Artwork(
        person=person,
        title=title or None,
        filename=stored,
        original_name=original,
        mime_type=file.mimetype,
    )
    db.session.add(art)
    db.session.commit()

    return redirect(url_for("art_gallery", person=person))


@app.get("/uploads/<person>/<path:filename>")
def uploaded_file(person, filename):
    person = get_person_or_404(person)
    directory = os.path.join(UPLOAD_ROOT, person)
    return send_from_directory(directory, filename)