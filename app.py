import os
import re
from datetime import datetime, date
import requests
from bs4 import BeautifulSoup
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
# API
# ------------------------------------------------------------------------------

@app.get("/api/fetch-metadata")
@require_unlock()
def fetch_metadata():
    url = request.args.get("url")
    if not url:
        return {"error": "Missing URL"}, 400

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        return {"error": str(e)}, 500

    soup = BeautifulSoup(resp.content, "html.parser")
    data = {}

    # Title
    # <h1 ...>Title</h1>
    h1 = soup.find("h1")
    if h1:
        data["title"] = h1.get_text(strip=True)
        # Optional: remove " Audiobook" suffix if you like, or keep it
        # data["title"] = re.sub(r" Audiobook$", "", data["title"], flags=re.IGNORECASE)

    # Helper to find text by label
    def get_text_by_label(label_text):
        label = soup.find(string=re.compile(label_text))
        if label:
            # Case 1: The value is in the same text element or parent element (e.g. "By: Author Name")
            # label.parent is usually the tag containing the text
            parent = label.parent
            if parent:
                full_text = parent.get_text(" ", strip=True)
                # "By: Matt Dinniman"
                # Check if this text actually contains the label + value
                if ":" in full_text:
                    # check if the part before colon roughly matches label
                    params = full_text.split(":", 1)
                    if len(params) == 2:
                        return params[1].strip()
            
            # Case 2: Value is in a sibling or defined container
            container = label.find_parent(["li", "div", "tr"])
            if container:
                full_text = container.get_text(" ", strip=True)
                if ":" in full_text:
                    _, val = full_text.split(":", 1)
                    return val.strip()
                return full_text
            
            return label.find_next(string=True).strip()
        return None

    # Helper to get links helper
    def get_links_after_label(label_pattern):
        # Find element containing the label (e.g., "By:", "Narrated by:")
        # Then find following <a> tags within a reasonable container
        label = soup.find(string=re.compile(label_pattern))
        if label:
            # Go up to a container (li or div)
            container = label.find_parent(["li", "div"], class_=lambda x: x != "bc-modal-header" if x else True) 
            if container:
                links = container.find_all("a")
                if links:
                    return ", ".join(l.get_text(strip=True) for l in links)
        return None

    # Author
    # Often in <li class="authorLabel">...</li>
    author_li = soup.find("li", class_="authorLabel")
    if author_li:
        data["author"] = ", ".join(t.get_text(strip=True) for t in author_li.find_all("a"))
    else:
        # Fallback: look for "By:" or "Author:"
        # Start with links
        val = get_links_after_label(r"By:|Author:")
        if val:
            data["author"] = val
        else:
            # Try text
            data["author"] = get_text_by_label(r"By:|Author:")

    # Narrator
    # Often in <li class="narratorLabel">...</li>
    narrator_li = soup.find("li", class_="narratorLabel")
    if narrator_li:
        data["narrator"] = ", ".join(t.get_text(strip=True) for t in narrator_li.find_all("a"))
    else:
        val = get_links_after_label(r"Narrated by:")
        if val:
            data["narrator"] = val
        else:
             data["narrator"] = get_text_by_label(r"Narrated by:")

    # Release Date
    # <li class="releaseDateLabel">...</li>
    release_li = soup.find("li", class_="releaseDateLabel")
    if release_li:
        text = release_li.get_text(strip=True)
        if ":" in text:
            date_str = text.split(":", 1)[1].strip()
            try:
                # Try parsing standard US format MM-DD-YY
                dt = datetime.strptime(date_str, "%m-%d-%y")
                data["release_date"] = dt.strftime("%Y-%m-%d")
            except ValueError:
                pass
    else:
        # Fallback
        label = soup.find(string=re.compile(r"Release date:"))
        if label:
            # Often "Release date: 05-18-21"
            full_text = label.find_parent(["li", "div"]).get_text(strip=True) if label.find_parent(["li", "div"]) else label
            # Extract date
            # simple regex for date pattern
            match = re.search(r"(\d{2}-\d{2}-\d{2,4})", full_text)
            if match:
                date_str = match.group(1)
                try:
                    # Fix 2-digit year if needed (though %y does that)
                    dt = datetime.strptime(date_str, "%m-%d-%y" if len(date_str.split("-")[2])==2 else "%m-%d-%Y")
                    data["release_date"] = dt.strftime("%Y-%m-%d")
                except ValueError:
                    pass

    return data


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