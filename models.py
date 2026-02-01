from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)

    person = db.Column(db.String(50), nullable=False, index=True)
    book_slug = db.Column(db.String(200), nullable=False, index=True)

    title = db.Column(db.String(300), nullable=False)
    author = db.Column(db.String(300), nullable=True)

    # NEW:
    finished_date = db.Column(db.Date, nullable=True)

    rating = db.Column(db.Integer, nullable=True)  # 1–5
    review_text = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("person", "book_slug", name="uix_person_book"),
    )


class Artwork(db.Model):
    __tablename__ = "artworks"

    id = db.Column(db.Integer, primary_key=True)

    person = db.Column(db.String(50), nullable=False, index=True)

    title = db.Column(db.String(300), nullable=True)
    filename = db.Column(db.String(500), nullable=False)       # stored filename on disk
    original_name = db.Column(db.String(500), nullable=True)   # original upload name
    mime_type = db.Column(db.String(100), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class BookMetadata(db.Model):
    """
    Cached metadata pulled from Open Library:
      - cover_url
      - summary
    Cached by book_slug.
    """
    __tablename__ = "book_metadata"

    id = db.Column(db.Integer, primary_key=True)

    book_slug = db.Column(db.String(200), nullable=False, unique=True, index=True)

    title = db.Column(db.String(300), nullable=False)
    author = db.Column(db.String(300), nullable=True)

    cover_url = db.Column(db.String(500), nullable=True)
    summary = db.Column(db.Text, nullable=True)

    source = db.Column(db.String(100), nullable=True)  # e.g., "openlibrary"
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)