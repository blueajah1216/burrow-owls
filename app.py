import os
import re
from datetime import datetime, date
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    abort,
    send_from_directory,
    session,
)

from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

# ------------------------------------------------------------------------------
# App / Config
# ------------------------------------------------------------------------------

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(BASE_DIR, 'burrowowls.db')}",
)

UPLOAD_ROOT = os.environ.get(
    "UPLOAD_ROOT",
    os.path.join(BASE_DIR, "uploads"),
)

UPLOAD_KEY = os.environ.get("UPLOAD_KEY")  # shared family key
YEAR = 2026

app.config.update(
    SQLALCHEMY_DATABASE_URI=DATABASE_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY=os.environ.get("SECRET_KEY", None),
)

db = SQLAlchemy(app)

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

PEOPLE = {
    "richard": "Richard",
    "gillian": "Gillian",
    "felicity": "Felicity",
    "elisabeth": "Elisabeth",
    "penelope": "Penelope",
    "peregrine": "Peregrine",
}


def normalize_person(person: str):
    key = person.lower()
    if key not in PEOPLE:
        abort(404)
    return key, PEOPLE[key]


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def uploads_disabled() -> bool:
    return not bool(UPLOAD_KEY)


def is_unlocked() -> bool:
    return session.get("unlocked", False)


def require_unlock():
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if uploads_disabled():
                abort(403)
            if not is_unlocked():
                abort(403)
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def get_site_visits() -> int:
    path = os.path.join(BASE_DIR, "site_visits.txt")
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write("0")
    with open(path, "r+") as f:
        count = int(f.read().strip() or "0")
        count += 1
        f.seek(0)
        f.write(str(count))
        f.truncate()
    return count


# ------------------------------------------------------------------------------
# Models
# ------------------------------------------------------------------------------

class Audiobook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    person = db.Column(db.String(32), index=True, nullable=False)

    title = db.Column(db.String(256), nullable=False)
    slug = db.Column(db.String(256), index=True)

    author = db.Column(db.String(256))
    narrator = db.Column(db.String(256))
    release_date = db.Column(db.Date)

    listened_date = db.Column(db.Date)
    rating = db.Column(db.Integer)
    review_text = db.Column(db.Text)

    audible_url = db.Column(db.String(512))
    cover_url = db.Column(db.String(512))
    synopsis = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ------------------------------------------------------------------------------
# Startup
# ------------------------------------------------------------------------------

with app.app_context():
    db.create_all()


# ------------------------------------------------------------------------------
# Reading List (static for now)
# ------------------------------------------------------------------------------

READING_LISTS = {
    "richard": [
        {"title": "Napoleon", "slug": "napoleon"},
        {"title": "Herzog", "slug": "herzog"},
        {"title": "The Chosen", "slug": "the-chosen"},
    ],
}


def get_reading_list_books(person_key):
    return READING_LISTS.get(person_key, [])


# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------

@app.route("/")
def home():
    return redirect("/richard")


@app.route("/<person>")
def person_home(person):
    person_key, person_name = normalize_person(person)
    books = get_reading_list_books(person_key)

    return render_template(
        "person_home.html",
        person_key=person_key,
        person_name=person_name,
        year=YEAR,
        books=books,
        site_visits=get_site_visits(),
    )


# ------------------------------------------------------------------------------
# Unlock
# ------------------------------------------------------------------------------

@app.post("/<person>/unlock")
def unlock(person):
    if uploads_disabled():
        abort(403)

    key = request.form.get("upload_key", "")
    if key == UPLOAD_KEY:
        session["unlocked"] = True

    return redirect(request.referrer or f"/{person}")


# ------------------------------------------------------------------------------
# Audiobooks
# ------------------------------------------------------------------------------

@app.get("/<person>/audiobooks")
def audiobooks_list(person):
    person_key, person_name = normalize_person(person)
    books = get_reading_list_books(person_key)

    items = (
        Audiobook.query.filter_by(person=person_key)
        .order_by(Audiobook.listened_date.desc().nullslast())
        .all()
    )

    return render_template(
        "audiobooks_list.html",
        person_key=person_key,
        person_name=person_name,
        year=YEAR,
        books=books,
        items=items,
        unlocked=is_unlocked(),
        uploads_disabled=uploads_disabled(),
        session_ready=bool(app.config.get("SECRET_KEY")),
        site_visits=get_site_visits(),
    )


@app.get("/<person>/audiobooks/new")
@require_unlock()
def audiobook_new(person):
    person_key, person_name = normalize_person(person)
    books = get_reading_list_books(person_key)

    return render_template(
        "audiobook_edit.html",
        person_key=person_key,
        person_name=person_name,
        year=YEAR,
        books=books,
        audiobook=None,
        is_new=True,
        unlocked=True,
        uploads_disabled=uploads_disabled(),
        session_ready=True,
        site_visits=get_site_visits(),
    )


@app.post("/<person>/audiobooks/new")
@require_unlock()
def audiobook_create(person):
    person_key, _ = normalize_person(person)

    title = request.form["title"].strip()
    ab = Audiobook(
        person=person_key,
        title=title,
        slug=slugify(title),
        author=request.form.get("author"),
        narrator=request.form.get("narrator"),
        audible_url=request.form.get("audible_url"),
        review_text=request.form.get("review_text"),
    )

    rating = request.form.get("rating")
    if rating and rating.isdigit():
        ab.rating = int(rating)

    if request.form.get("listened_date"):
        ab.listened_date = date.fromisoformat(
            request.form["listened_date"]
        )

    db.session.add(ab)
    db.session.commit()

    return redirect(f"/{person_key}/audiobooks/{ab.id}")


@app.get("/<person>/audiobooks/<int:audiobook_id>")
def audiobook_view(person, audiobook_id):
    person_key, person_name = normalize_person(person)
    books = get_reading_list_books(person_key)

    ab = Audiobook.query.filter_by(
        person=person_key, id=audiobook_id
    ).first_or_404()

    return render_template(
        "audiobook_view.html",
        person_key=person_key,
        person_name=person_name,
        year=YEAR,
        books=books,
        audiobook=ab,
        unlocked=is_unlocked(),
        uploads_disabled=uploads_disabled(),
        session_ready=bool(app.config.get("SECRET_KEY")),
        site_visits=get_site_visits(),
    )


@app.get("/<person>/audiobooks/<int:audiobook_id>/edit")
@require_unlock()
def audiobook_edit(person, audiobook_id):
    person_key, person_name = normalize_person(person)
    books = get_reading_list_books(person_key)

    ab = Audiobook.query.filter_by(
        person=person_key, id=audiobook_id
    ).first_or_404()

    return render_template(
        "audiobook_edit.html",
        person_key=person_key,
        person_name=person_name,
        year=YEAR,
        books=books,
        audiobook=ab,
        is_new=False,
        unlocked=True,
        uploads_disabled=uploads_disabled(),
        session_ready=True,
        site_visits=get_site_visits(),
    )


@app.post("/<person>/audiobooks/<int:audiobook_id>/edit")
@require_unlock()
def audiobook_save(person, audiobook_id):
    person_key, _ = normalize_person(person)

    ab = Audiobook.query.filter_by(
        person=person_key, id=audiobook_id
    ).first_or_404()

    ab.title = request.form["title"].strip()
    ab.author = request.form.get("author")
    ab.narrator = request.form.get("narrator")
    ab.review_text = request.form.get("review_text")
    ab.audible_url = request.form.get("audible_url")

    rating = request.form.get("rating")
    if rating and rating.isdigit():
        ab.rating = int(rating)

    if request.form.get("listened_date"):
        ab.listened_date = date.fromisoformat(
            request.form["listened_date"]
        )

    db.session.commit()
    return redirect(f"/{person_key}/audiobooks/{ab.id}")


# ------------------------------------------------------------------------------
# Static uploads (art)
# ------------------------------------------------------------------------------

@app.route("/uploads/<path:filename>")
def uploads(filename):
    return send_from_directory(UPLOAD_ROOT, filename)


# ------------------------------------------------------------------------------
# Run
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)