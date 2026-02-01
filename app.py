import json
import os
import re
import time
from pathlib import Path
from uuid import uuid4

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
from models import db, Review, Artwork

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

# Needed for session cookies (unlocking uploads in the browser)
# Set this in Render -> Environment:
#   SECRET_KEY=<random long string>
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "")

# For Render persistence (recommended):
# - Add a Render Disk mounted at /var/data
# - Set:
#     DATABASE_URL=sqlite:////var/data/burrowowls.db
#     UPLOAD_ROOT=/var/data/uploads
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///burrowowls.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Limit uploads (8MB). Adjust if needed.
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

db.init_app(app)

with app.app_context():
    db.create_all()

# Upload storage root
UPLOAD_ROOT = os.environ.get("UPLOAD_ROOT", str(BASE_DIR / "uploads"))

# Shared family upload key (set on Render as env var UPLOAD_KEY).
# If not set, uploads are disabled (fail closed).
UPLOAD_KEY = os.environ.get("UPLOAD_KEY", "")

# How long an "unlock" lasts in the browser (seconds)
UNLOCK_TTL_SECONDS = 60 * 60 * 6  # 6 hours


# Ensure upload directories exist
os.makedirs(UPLOAD_ROOT, exist_ok=True)
for p in PEOPLE.keys():
    os.makedirs(os.path.join(UPLOAD_ROOT, p), exist_ok=True)


def session_upload_unlocked() -> bool:
    """
    Returns True if the user has recently unlocked uploads in this browser session.
    """
    ts = session.get("upload_unlocked_at")
    if not ts:
        return False
    try:
        ts = float(ts)
    except (TypeError, ValueError):
        return False
    return (time.time() - ts) < UNLOCK_TTL_SECONDS


def require_upload_auth():
    """
    Upload authorization:
    - Fail closed if UPLOAD_KEY isn't set (uploads disabled).
    - Accept either:
        1) A valid unlocked session, OR
        2) The correct key supplied in the form/header/query (backup)
    """
    if not UPLOAD_KEY:
        abort(403, "Uploads are disabled (UPLOAD_KEY not set).")

    if session_upload_unlocked():
        return

    provided = (
        request.form.get("upload_key")
        or request.headers.get("X-Upload-Key")
        or request.args.get("upload_key")
    )

    if provided != UPLOAD_KEY:
        abort(403, "Not allowed.")


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
# Routes: Book reviews
# -----------------------------
@app.get("/<person>/review/<book_slug>")
def review_edit(person, book_slug):
    person = get_person_or_404(person)

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


@app.post("/<person>/review/<book_slug>")
def review_save(person, book_slug):
    person = get_person_or_404(person)

    data = get_person_books(person)
    books = [{**b, "slug": slugify(b["title"])} for b in data["books"]]
    book = next((b for b in books if b["slug"] == book_slug), None)
    if not book:
        abort(404)

    rating_raw = request.form.get("rating", "").strip()
    rating = int(rating_raw) if rating_raw.isdigit() else None
    if rating is not None and (rating < 1 or rating > 5):
        rating = None

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
    review.review_text = text
    db.session.commit()

    return redirect(url_for("review_edit", person=person, book_slug=book_slug))


# -----------------------------
# Routes: Art gallery + uploads
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
    """
    Shows either:
    - a key entry box (locked), or
    - the upload form (unlocked)
    """
    person = get_person_or_404(person)

    data = get_person_books(person)
    books = [{**b, "slug": slugify(b["title"])} for b in data["books"]]

    uploads_disabled = (not UPLOAD_KEY)

    # If SECRET_KEY isn't set, sessions won't work reliably.
    # We'll still allow "manual key in the form on submit" (fallback),
    # but unlocking won't persist.
    session_ready = bool(app.config.get("SECRET_KEY"))

    unlocked = session_upload_unlocked() if session_ready else False

    return render_template(
        "art_upload.html",
        person_key=person,
        person_name=PEOPLE[person],
        year=data["year"],
        books=books,
        uploads_disabled=uploads_disabled,
        unlocked=unlocked,
        session_ready=session_ready,
    )


@app.post("/<person>/art/unlock")
def art_unlock(person):
    """
    User enters the upload key on the page. If correct, unlock uploads for this browser session.
    """
    person = get_person_or_404(person)

    if not UPLOAD_KEY:
        abort(403, "Uploads are disabled (UPLOAD_KEY not set).")

    provided = request.form.get("upload_key", "")
    if provided != UPLOAD_KEY:
        # Don't leak details. Just show locked again.
        return redirect(url_for("art_upload_form", person=person))

    # Only works if SECRET_KEY is set
    if not app.config.get("SECRET_KEY"):
        # Still allow upload submission with key in the upload form,
        # but session-based unlock can't persist.
        return redirect(url_for("art_upload_form", person=person))

    session["upload_unlocked_at"] = str(time.time())
    return redirect(url_for("art_upload_form", person=person))


@app.post("/<person>/art/upload")
def art_upload_save(person):
    person = get_person_or_404(person)

    # Require session unlock OR correct key provided (fallback)
    require_upload_auth()

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