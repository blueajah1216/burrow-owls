"""
theburrowowls.com/music — classical concert aggregator.

1. Seattle calendar (day / week / month) of classical concerts.
2. Piece search: where in the world is a work being performed this season.

Wired up from app.py with `init_music(app, db, ctx_fn)`.
Data comes in through music_ingest.py (JSON/CSV import, scrapers, demo seed).
"""

import calendar
import json
import re
import unicodedata
from datetime import date, datetime, timedelta

from flask import Blueprint, render_template, request

bp = Blueprint("music", __name__, url_prefix="/music")

CATEGORIES = [
    ("symphonic", "Symphonic"),
    ("chamber", "Chamber"),
    ("choral", "Choral"),
    ("solo", "Solo"),
    ("opera", "Opera & Vocal"),
]
CATEGORY_LABELS = dict(CATEGORIES)

REGION_SEATTLE = "seattle"

MusicEvent = None  # set by init_music
ScrapeLog = None


# ------------------------------------------------------------------------------
# Text normalisation for piece search
# ------------------------------------------------------------------------------

_ORDINALS = {
    "first": "1", "second": "2", "third": "3", "fourth": "4", "fifth": "5",
    "sixth": "6", "seventh": "7", "eighth": "8", "ninth": "9", "tenth": "10",
}
_STOP = {"no", "nr", "number", "in", "the", "of", "a", "op", "opus", "for", "and"}
_ROMAN = {"i": "1", "ii": "2", "iii": "3", "iv": "4", "v": "5",
          "vi": "6", "vii": "7", "viii": "8", "ix": "9", "x": "10"}


def _unaccent(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def tokenize(text: str) -> set:
    """Lowercase, unaccent, map '7th'/'seventh' -> '7', drop filler words."""
    text = _unaccent(text or "").lower()
    text = re.sub(r"['’]s\b", "", text)  # Beethoven's -> Beethoven
    text = re.sub(r"(\d+)(st|nd|rd|th)\b", r"\1", text)
    out = set()
    for tok in re.findall(r"[a-z0-9]+", text):
        tok = _ORDINALS.get(tok, tok)
        if tok in _STOP:
            continue
        # singular/plural: "symphonies" / "symphony", "sonatas" / "sonata"
        if tok.endswith("ies") and len(tok) > 4:
            tok = tok[:-3] + "y"
        elif tok.endswith("s") and len(tok) > 4:
            tok = tok[:-1]
        out.add(tok)
    return out


def _roman_tokens(text: str) -> set:
    return {_ROMAN[t] for t in re.findall(r"\b[ivx]+\b", (text or "").lower()) if t in _ROMAN}


def concert_season(today: date = None):
    """Concert year runs 1 Sep – 31 Aug."""
    today = today or date.today()
    start_year = today.year if today.month >= 9 else today.year - 1
    return date(start_year, 9, 1), date(start_year + 1, 8, 31)


def season_label(today: date = None) -> str:
    s, e = concert_season(today)
    return f"{s.year}–{str(e.year)[2:]}"


# ------------------------------------------------------------------------------
# Calendar helpers
# ------------------------------------------------------------------------------

def _parse_date(s: str, default: date) -> date:
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return default


def _window(view: str, anchor: date):
    """Return (start_date, end_date_inclusive, prev_anchor, next_anchor, title)."""
    if view == "day":
        return (anchor, anchor, anchor - timedelta(days=1), anchor + timedelta(days=1),
                anchor.strftime("%A, %B %-d, %Y"))
    if view == "week":
        start = anchor - timedelta(days=(anchor.weekday() + 1) % 7)  # Sunday start
        end = start + timedelta(days=6)
        title = f"{start.strftime('%b %-d')} – {end.strftime('%b %-d, %Y')}"
        return start, end, start - timedelta(days=7), start + timedelta(days=7), title
    # month grid, padded to full weeks (Sunday start)
    first = anchor.replace(day=1)
    last = anchor.replace(day=calendar.monthrange(anchor.year, anchor.month)[1])
    start = first - timedelta(days=(first.weekday() + 1) % 7)
    end = last + timedelta(days=(5 - last.weekday()) % 7)
    prev_m = (first - timedelta(days=1)).replace(day=1)
    next_m = last + timedelta(days=1)
    return start, end, prev_m, next_m, first.strftime("%B %Y")


def program_of(ev):
    try:
        return json.loads(ev.program_json or "[]")
    except ValueError:
        return []


# ------------------------------------------------------------------------------
# Search
# ------------------------------------------------------------------------------

def search_piece(query: str, include_all: bool, include_past: bool):
    """Return events whose program contains every token of the query."""
    q_tokens = tokenize(query)
    # "Beethoven VII" -> 7 (lone "i" left alone: too ambiguous)
    q_tokens = {_ROMAN[t] if t in _ROMAN and t != "i" else t for t in q_tokens}
    if not q_tokens:
        return []
    s_start, s_end = concert_season()
    q = MusicEvent.query.filter(
        MusicEvent.start >= datetime.combine(s_start, datetime.min.time()),
        MusicEvent.start <= datetime.combine(s_end, datetime.max.time()),
    )
    if not include_past:
        q = q.filter(MusicEvent.start >= datetime.now())
    if not include_all:
        q = q.filter(MusicEvent.major.is_(True))

    hits = []
    for ev in q.order_by(MusicEvent.start).all():
        best = None
        for item in program_of(ev):
            composer = item.get("composer", "")
            work = item.get("work", "")
            toks = tokenize(f"{composer} {work}") | _roman_tokens(work)
            if q_tokens <= toks:
                # prefer tighter matches (less extra words) for ranking
                score = len(toks) - len(q_tokens)
                if best is None or score < best[0]:
                    best = (score, item)
        if best:
            hits.append((best[0], ev, best[1]))
    hits.sort(key=lambda h: (h[0], h[1].start))
    return [(ev, item) for _, ev, item in hits]


def group_by_place(hits):
    """[(country, [(city, [(event, item)])])], countries/cities alphabetical,
    events chronological. Seattle first within the US is not forced."""
    tree = {}
    for ev, item in hits:
        tree.setdefault(ev.country or "Unknown", {}).setdefault(ev.city or "Unknown", []).append((ev, item))
    return [
        (country, sorted(cities.items()))
        for country, cities in sorted(tree.items())
    ]


# ------------------------------------------------------------------------------
# Init
# ------------------------------------------------------------------------------

def init_music(app, db, ctx_fn):
    """Define the model on the app's db and register routes.

    ctx_fn() -> dict of base-template context (person_key, year, books, ...).
    """
    global MusicEvent

    class _MusicEvent(db.Model):
        __tablename__ = "music_events"

        id = db.Column(db.Integer, primary_key=True)
        source = db.Column(db.String(100), nullable=False, index=True)
        source_id = db.Column(db.String(300), nullable=False)

        title = db.Column(db.String(400), nullable=False)
        start = db.Column(db.DateTime, nullable=False, index=True)  # local time at venue
        category = db.Column(db.String(20), nullable=False, index=True)
        performers = db.Column(db.Text, nullable=True)       # "Seattle Symphony; Ludovic Morlot, cond."
        program_json = db.Column(db.Text, nullable=True)     # [{"composer":..., "work":...}]
        description = db.Column(db.Text, nullable=True)      # short blurb: what's being played

        venue = db.Column(db.String(300), nullable=True)
        city = db.Column(db.String(120), nullable=True, index=True)
        country = db.Column(db.String(120), nullable=True)
        region = db.Column(db.String(60), nullable=True, index=True)  # "seattle" drives the calendar
        major = db.Column(db.Boolean, default=False, index=True)      # major performer -> search results

        ticket_url = db.Column(db.String(1000), nullable=True)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        __table_args__ = (db.UniqueConstraint("source", "source_id", name="uix_music_source"),)

    MusicEvent = _MusicEvent

    class _ScrapeLog(db.Model):
        """One row per scraper per run: lets us see remotely which sources work in production."""
        __tablename__ = "music_scrape_log"
        id = db.Column(db.Integer, primary_key=True)
        source = db.Column(db.String(100), nullable=False, index=True)
        ran_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
        count = db.Column(db.Integer, default=0)
        error = db.Column(db.Text, nullable=True)
        seconds = db.Column(db.Float, nullable=True)

    global ScrapeLog
    ScrapeLog = _ScrapeLog

    # create_all() doesn't add columns to an existing table; do it ourselves.
    with app.app_context():
        db.create_all()
        cols = {c["name"] for c in db.inspect(db.engine).get_columns("music_events")}
        if "description" not in cols:
            db.session.execute(db.text("ALTER TABLE music_events ADD COLUMN description TEXT"))
            db.session.commit()

    @bp.before_request
    def _auto_refresh():
        import music_ingest
        if request.endpoint != "music.music_status":
            music_ingest.refresh_if_stale(app, db)

    @bp.get("")
    @bp.get("/")
    def music_home():
        today = date.today()
        view = request.args.get("view", "month")
        if view not in ("day", "week", "month"):
            view = "month"
        anchor = _parse_date(request.args.get("date"), today)
        cats = [c for c in request.args.getlist("cat") if c in CATEGORY_LABELS]

        start, end, prev_a, next_a, title = _window(view, anchor)
        q = MusicEvent.query.filter(
            MusicEvent.region == REGION_SEATTLE,
            MusicEvent.start >= datetime.combine(start, datetime.min.time()),
            MusicEvent.start <= datetime.combine(end, datetime.max.time()),
        )
        if cats:
            q = q.filter(MusicEvent.category.in_(cats))
        events = q.order_by(MusicEvent.start).all()

        by_day = {}
        for ev in events:
            by_day.setdefault(ev.start.date(), []).append(ev)

        days = [start + timedelta(days=i) for i in range((end - start).days + 1)]
        weeks = [days[i:i + 7] for i in range(0, len(days), 7)] if view == "month" else []

        return render_template(
            "music_calendar.html",
            **ctx_fn(),
            view=view, anchor=anchor, today=today, title=title,
            prev_a=prev_a, next_a=next_a, cats=cats,
            categories=CATEGORIES, category_labels=CATEGORY_LABELS,
            by_day=by_day, days=days, weeks=weeks, total=len(events),
            program_of=program_of,
            demo=any(e.source == "demo" for e in events),
        )

    @bp.get("/search")
    def music_search():
        query = (request.args.get("q") or "").strip()
        include_all = request.args.get("all") == "1"
        include_past = request.args.get("past") == "1"
        hits = search_piece(query, include_all, include_past) if query else []
        return render_template(
            "music_search.html",
            **ctx_fn(),
            query=query, include_all=include_all, include_past=include_past,
            hits=hits, grouped=group_by_place(hits), season=season_label(),
            category_labels=CATEGORY_LABELS, now=datetime.now(),
            demo=any(ev.source == "demo" for ev, _ in hits),
        )

    @bp.get("/status")
    def music_status():
        """Per-source health: events stored, latest scrape result/error. Handy for debugging production."""
        from sqlalchemy import func
        now = datetime.now()
        stored = {r[0]: (r[1], r[2]) for r in db.session.query(
            MusicEvent.source, func.count(MusicEvent.id),
            func.sum(db.case((MusicEvent.start >= now, 1), else_=0))).group_by(MusicEvent.source)}
        rows = []
        for src in sorted(set(stored) | {l.source for l in ScrapeLog.query.all()}):
            last = ScrapeLog.query.filter_by(source=src).order_by(ScrapeLog.ran_at.desc()).first()
            rows.append(dict(
                source=src, stored=stored.get(src, (0, 0))[0], upcoming=int(stored.get(src, (0, 0))[1] or 0),
                last_run=last.ran_at.isoformat(timespec="seconds") + "Z" if last else None,
                last_count=last.count if last else None, last_error=last.error if last else None,
                seconds=round(last.seconds, 1) if last and last.seconds else None))
        import music_ingest
        stamp = music_ingest._last_scrape()
        return {"server_time_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                "last_full_scrape": stamp.isoformat(timespec="seconds") if stamp else None,
                "scrape_running": __import__("os").path.exists(music_ingest._LOCK),
                "sources": rows}

    app.register_blueprint(bp)
    return MusicEvent
