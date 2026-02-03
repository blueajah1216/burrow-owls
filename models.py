from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)

    person = db.Column(db.String(50), nullable=False, index=True)
    book_slug = db.Column(db.String(200), nullable=False, index=True)

    title = db.Column(db.String(300), nullable=False)
    author = db.Column(db.String(300), nullable=True)

    finished_date = db.Column(db.Date, nullable=True)

    rating = db.Column(db.Integer, nullable=True)  # 1–10
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
    filename = db.Column(db.String(500), nullable=False)
    original_name = db.Column(db.String(500), nullable=True)
    mime_type = db.Column(db.String(100), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class BookMetadata(db.Model):
    __tablename__ = "book_metadata"

    id = db.Column(db.Integer, primary_key=True)

    book_slug = db.Column(db.String(200), nullable=False, unique=True, index=True)

    title = db.Column(db.String(300), nullable=False)
    author = db.Column(db.String(300), nullable=True)

    cover_url = db.Column(db.String(500), nullable=True)
    summary = db.Column(db.Text, nullable=True)

    source = db.Column(db.String(100), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SiteCounter(db.Model):
    __tablename__ = "site_counter"

    id = db.Column(db.Integer, primary_key=True)
    visits = db.Column(db.Integer, nullable=False, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AudiobookReview(db.Model):
    """
    Per-person dynamic audiobook reviews.
    Metadata is stored directly on the row (simpler than joins/caches).
    """
    __tablename__ = "audiobook_reviews"

    id = db.Column(db.Integer, primary_key=True)

    person = db.Column(db.String(50), nullable=False, index=True)

    # User input
    audible_url = db.Column(db.String(800), nullable=True)

    listened_date = db.Column(db.Date, nullable=True)
    rating = db.Column(db.Integer, nullable=True)  # 1–10
    review_text = db.Column(db.Text, nullable=True)

    # Auto-fetched metadata (best-effort)
    title = db.Column(db.String(400), nullable=True)
    author = db.Column(db.String(400), nullable=True)
    narrator = db.Column(db.String(400), nullable=True)
    release_date = db.Column(db.String(100), nullable=True)
    synopsis = db.Column(db.Text, nullable=True)
    cover_url = db.Column(db.String(800), nullable=True)

    source = db.Column(db.String(100), nullable=True)  # e.g., "audible"

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)