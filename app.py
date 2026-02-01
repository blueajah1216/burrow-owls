import json
import re
from pathlib import Path

from flask import Flask, abort, render_template, request, redirect, url_for
from models import db, Review
from people import PEOPLE

BASE_DIR = Path(__file__).parent
READING_LIST_PATH = BASE_DIR / "data" / "reading_lists.json"

def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")

def load_reading_lists() -> dict:
    return json.loads(READING_LIST_PATH.read_text(encoding="utf-8"))

app = Flask(__name__)

# IMPORTANT on Render: use a persistent disk if you want SQLite to persist across deploys.
# For now, this works, but DB may reset on redeploy unless you attach a disk.
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///burrowowls.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.get("/")
def index():
    # Nice landing page: redirect to Richard for now
    return redirect(url_for("person_home", person="richard"))

def get_person_or_404(person: str) -> str:
    if person not in PEOPLE:
        abort(404)
    return person

def get_person_books(person: str):
    lists = load_reading_lists()
    return lists.get(person, {"year": 2026, "books": []})

@app.get("/<person>")
def person_home(person):
    person = get_person_or_404(person)
    data = get_person_books(person)
    # sidebar books: include slug for review links
    books = [
        {**b, "slug": slugify(b["title"])}
        for b in data["books"]
    ]
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