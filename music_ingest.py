"""
Getting concerts into the /music database.

    flask music-import data/music/seattle.json      # JSON list (format below)
    flask music-import data/music/world.csv         # CSV with the same columns
    flask music-scrape                              # schema.org JSON-LD sources in data/music_sources.json
    flask music-demo                                # clearly-labelled sample data (source="demo")
    flask music-clear-demo

Event fields (JSON keys / CSV columns):
    title*, start* (ISO 8601 local time), category (symphonic|chamber|choral|solo|opera;
    guessed from title if absent), performers, program (list of {"composer","work"} in JSON,
    or "Composer: Work | Composer: Work" in CSV), venue, city, country, region
    ("seattle" puts it on the calendar), major (true => appears in world piece search),
    ticket_url, source, source_id (stable id so re-imports update instead of duplicate).
"""

import csv
import json
import os
import re
import threading
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

import music

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES_PATH = os.path.join(HERE, "data", "music_sources.json")

_CAT_RULES = [
    ("opera", r"\bopera\b|\brecital of (arias|songs)\b|\bliederabend\b"),
    ("choral", r"chanticleer|tallis scholars|vox luminis|cappella|sine nomine|\bchoir\b|\bchorus\b|\bchorale\b|\bchoral\b|\bcantata\b|\bvespers\b|\bmass\b|\brequiem\b"),
    ("symphonic", r"\bsymphon|concert des nations|\borchestra\b|\bphilharmonic\b|\bsinfonietta\b|\bpops\b"),
    ("chamber", r"\bquartet\b|\bquintet\b|\btrio\b|\bsextet\b|\boctet\b|\bensemble\b|\bchamber\b|\bduo\b"),
    ("solo", r"\brecital\b|\bsolo\b|\bpiano\b|\borgan\b|\bviolin\b|\bcello\b|\bguitar\b"),
]


def classify(*texts) -> str:
    blob = " ".join(t for t in texts if t).lower()
    for cat, pat in _CAT_RULES:
        if re.search(pat, blob):
            return cat
    return "chamber"


_PROG_LINE = re.compile(r"^\s*([A-Z][\w'’.\- ]{2,40}?)\s*[:–—-]\s*(.{3,200}?)\s*$")


def parse_program(text: str):
    """Best-effort 'Composer: Work' extraction from free text, one piece per line."""
    items = []
    for line in re.split(r"[\n|]+", text or ""):
        m = _PROG_LINE.match(line)
        if m:
            items.append({"composer": m.group(1).strip(), "work": m.group(2).strip()})
    return items


def upsert(db, rec: dict) -> bool:
    """Insert/update one event dict. Returns True if stored."""
    ME = music.MusicEvent
    title = (rec.get("title") or "").strip()
    start = rec.get("start")
    if isinstance(start, str):
        try:
            start = datetime.fromisoformat(start.replace("Z", "")).replace(tzinfo=None)
        except ValueError:
            return False
    if not title or not start:
        return False

    program = rec.get("program") or []
    if isinstance(program, str):
        program = parse_program(program)
    source = rec.get("source") or "import"
    source_id = str(rec.get("source_id") or f"{title}|{start.isoformat()}|{rec.get('venue', '')}")

    ev = ME.query.filter_by(source=source, source_id=source_id).first() or ME(source=source, source_id=source_id)
    cat = rec.get("category")
    ev.title = title[:400]
    ev.start = start
    ev.category = cat if cat in music.CATEGORY_LABELS else classify(title, rec.get("performers"))
    ev.performers = rec.get("performers")
    if program or not (ev.program_json and ev.program_json != "[]"):  # keep a known program if this fetch lacked one
        ev.program_json = json.dumps(program, ensure_ascii=False)
    ev.description = (rec.get("description") or "")[:600] or None
    ev.venue = rec.get("venue")
    ev.city = rec.get("city")
    ev.country = rec.get("country")
    ev.region = (rec.get("region") or "").lower() or None
    ev.major = str(rec.get("major", "")).lower() in ("1", "true", "yes")
    ev.ticket_url = rec.get("ticket_url")
    db.session.add(ev)
    return True


def import_file(db, path: str) -> int:
    n = 0
    if path.lower().endswith(".csv"):
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    else:
        with open(path, encoding="utf-8") as f:
            rows = json.load(f)
    for rec in rows:
        n += upsert(db, rec)
    db.session.commit()
    return n


# ------------------------------------------------------------------------------
# schema.org JSON-LD scraper (works for any presenter whose pages publish Event data)
# ------------------------------------------------------------------------------

def _walk(node):
    if isinstance(node, list):
        for x in node:
            yield from _walk(x)
    elif isinstance(node, dict):
        yield node
        for v in node.values():
            if isinstance(v, (list, dict)):
                yield from _walk(v)


def scrape_jsonld(src: dict):
    """src: {name, url, region, city, country, major, default_category?, venue?}"""
    resp = requests.get(src["url"], timeout=30, headers={"User-Agent": "BurrowOwlsMusic/1.0 (+https://theburrowowls.com/music)"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except ValueError:
            continue
        for node in _walk(data):
            types = node.get("@type")
            types = types if isinstance(types, list) else [types]
            if not any(t and t.endswith("Event") for t in types):
                continue
            loc = node.get("location") if isinstance(node.get("location"), dict) else {}
            addr = loc.get("address") if isinstance(loc.get("address"), dict) else {}
            offers = node.get("offers")
            offers = offers[0] if isinstance(offers, list) and offers else offers
            performer = node.get("performer")
            names = [p.get("name") for p in (performer if isinstance(performer, list) else [performer]) if isinstance(p, dict)]
            desc = BeautifulSoup(node.get("description") or "", "html.parser").get_text("\n")
            yield {
                "source": src["name"],
                "source_id": node.get("url") or node.get("@id") or f"{node.get('name')}|{node.get('startDate')}",
                "title": node.get("name"),
                "start": node.get("startDate"),
                "performers": "; ".join(n for n in names if n) or src["name"],
                "program": parse_program(desc),
                "category": src.get("default_category"),
                "venue": loc.get("name") or src.get("venue"),
                "city": addr.get("addressLocality") or src.get("city"),
                "country": src.get("country"),
                "region": src.get("region"),
                "major": src.get("major", False),
                "ticket_url": (offers or {}).get("url") if isinstance(offers, dict) else node.get("url"),
            }


# ------------------------------------------------------------------------------
# Demo data — obviously fake performers/dates relative to today, flagged by source="demo"
# ------------------------------------------------------------------------------

def demo_records():
    base = datetime.now().replace(hour=19, minute=30, second=0, microsecond=0)

    def at(days, hour=19, minute=30):
        return (base + timedelta(days=days)).replace(hour=hour, minute=minute)

    def r(i, days, title, perf, cat, prog, venue, city, country, region=None, major=True, hour=19):
        return dict(source="demo", source_id=f"demo-{i}", title=title, start=at(days, hour), category=cat,
                    performers=perf, program=[{"composer": c, "work": w} for c, w in prog], venue=venue,
                    city=city, country=country, region=region, major=major,
                    ticket_url="https://example.com/tickets")

    B7 = ("Beethoven", "Symphony No. 7 in A major, Op. 92")
    return [
        r(1, 2, "[Sample] Beethoven 7", "Sample Symphony Orchestra; A. Conductor", "symphonic",
          [("Mozart", "Piano Concerto No. 21"), B7], "Sample Hall", "Seattle", "USA", "seattle"),
        r(2, 5, "[Sample] Late Quartets", "Sample String Quartet", "chamber",
          [("Beethoven", "String Quartet No. 14 in C-sharp minor, Op. 131")], "Sample Recital Room", "Seattle", "USA", "seattle", False),
        r(3, 9, "[Sample] Bach Motets", "Sample Chamber Choir", "choral",
          [("Bach", "Jesu, meine Freude, BWV 227")], "Sample Church", "Seattle", "USA", "seattle", False, 20),
        r(4, 12, "[Sample] Piano Recital", "B. Pianist", "solo",
          [("Beethoven", "Piano Sonata No. 23 in F minor, Op. 57 'Appassionata'"), ("Schumann", "Kreisleriana")],
          "Sample Recital Room", "Seattle", "USA", "seattle", False, 15),
        r(5, 20, "[Sample] Vienna Beethoven", "Sample Philharmonic Vienna", "symphonic", [B7], "Sample Musikverein", "Vienna", "Austria"),
        r(6, 31, "[Sample] Berlin Beethoven", "Sample Philharmonic Berlin", "symphonic", [B7], "Sample Philharmonie", "Berlin", "Germany"),
        r(7, 45, "[Sample] London Beethoven", "Sample Symphony London", "symphonic", [B7], "Sample Barbican", "London", "UK"),
    ]


def _log_run(db, name, count, error, t0):
    try:
        db.session.add(music.ScrapeLog(source=name, count=count, error=error,
                                       seconds=(datetime.now() - t0).total_seconds()))
        db.session.commit()
        old = music.ScrapeLog.query.filter_by(source=name).order_by(music.ScrapeLog.ran_at.desc()).offset(20).all()
        for o in old:
            db.session.delete(o)
        db.session.commit()
    except Exception:
        db.session.rollback()


def run_scrapers(db, names=None):
    """Run registered scrapers. Yields (name, count, error). One failing site never
    stops the others; a scraper that returns nothing never wipes that site's data."""
    import music_scrapers

    for name, fn in music_scrapers.SCRAPERS.items():
        if names and name not in names:
            continue
        t0 = datetime.now()
        try:
            recs = list(fn())
            seen = set()
            for rec in recs:
                if upsert(db, rec):
                    seen.add(str(rec["source_id"]))
            if seen:  # drop future events that vanished from the site (cancelled/moved)
                ME = music.MusicEvent
                for ev in ME.query.filter(ME.source == name, ME.start >= datetime.now()).all():
                    if ev.source_id not in seen:
                        db.session.delete(ev)
            db.session.commit()
            _log_run(db, name, len(seen), None, t0)
            yield name, len(seen), None
        except Exception as e:
            db.session.rollback()
            _log_run(db, name, 0, f"{type(e).__name__}: {e}"[:500], t0)
            yield name, 0, f"{type(e).__name__}: {e}"


REFRESH_EVERY = timedelta(hours=24)
_STAMP = os.path.join(HERE, "music_last_scrape.txt")
_LOCK = os.path.join(HERE, "music_scrape.lock")


def _last_scrape():
    try:
        with open(_STAMP) as f:
            return datetime.fromisoformat(f.read().strip())
    except (OSError, ValueError):
        return None


def refresh_if_stale(app, db):
    """Kick off a background scrape if the data is >24h old. Safe to call on every request:
    a lock file keeps multiple gunicorn workers from scraping at once, and a stale lock
    (crashed worker) expires after 30 minutes. Disable with MUSIC_AUTOREFRESH=0."""
    if os.environ.get("MUSIC_AUTOREFRESH", "1") == "0":
        return False
    last = _last_scrape()
    if last and datetime.now() - last < REFRESH_EVERY:
        return False
    try:
        if os.path.exists(_LOCK) and datetime.now().timestamp() - os.path.getmtime(_LOCK) < 1800:
            return False
        fd = os.open(_LOCK, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
        os.close(fd)
    except OSError:
        return False

    def work():
        try:
            with app.app_context():
                for name, n, err in run_scrapers(db):
                    app.logger.info("music scrape %s: %s", name, err or f"{n} events")
            with open(_STAMP, "w") as f:
                f.write(datetime.now().isoformat())
        finally:
            try:
                os.remove(_LOCK)
            except OSError:
                pass

    threading.Thread(target=work, name="music-scrape", daemon=True).start()
    return True


def register_cli(app, db):
    import click

    @app.cli.command("music-import")
    @click.argument("path")
    def _import(path):
        click.echo(f"imported {import_file(db, path)} events")

    @app.cli.command("music-scrape")
    @click.argument("names", nargs=-1)
    def _scrape(names):
        """Run the per-presenter scrapers (all, or the named ones)."""
        for name, n, err in run_scrapers(db, names or None):
            click.echo(f"{name}: {'FAILED (' + err + ')' if err else str(n) + ' events'}")
        if not names:
            with open(_STAMP, "w") as f:
                f.write(datetime.now().isoformat())

    @app.cli.command("music-demo")
    def _demo():
        for rec in demo_records():
            upsert(db, rec)
        db.session.commit()
        click.echo("demo data loaded")

    @app.cli.command("music-clear-demo")
    def _clear():
        music.MusicEvent.query.filter_by(source="demo").delete()
        db.session.commit()
        click.echo("demo data removed")
