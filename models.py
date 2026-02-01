from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    person = db.Column(db.String(50), nullable=False, index=True)
    book_slug = db.Column(db.String(200), nullable=False, index=True)

    title = db.Column(db.String(300), nullable=False)
    author = db.Column(db.String(300), nullable=True)

    rating = db.Column(db.Integer, nullable=True)  # 1–5
    review_text = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("person", "book_slug", name="uix_person_book"),
    )