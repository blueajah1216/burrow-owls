"""Offline regression checks for the Benaroya feed and its deployment fallback."""
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "benaroya-test"
os.environ["MUSIC_AUTOREFRESH"] = "0"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests
from app import app, db
import music
import music_ingest
import music_scrapers as scrapers


def event(event_id=1, **extra):
    return dict({"id": event_id, "start": "2030-01-15T19:30:00.0000000",
                 "title": "Mozart’s Requiem with Xian", "brand": "Seattle Symphony",
                 "genre": "Classical", "description": "A concert with chorus and orchestra.",
                 "venue": "S. Mark Taper Foundation Auditorium", "isPast": False,
                 "learnMoreUrl": "/pdps/symphonic-5/", "buyPageUrl": "/book/1"}, **extra)


def response(payload=None, text="<title>Calendar</title>", url=scrapers.BH + "/calendar/"):
    r = Mock()
    r.text, r.url, r.status_code = text, url, 200
    r.json.return_value = payload
    return r


class BenaroyaChecks(unittest.TestCase):
    def test_bundled_snapshot_contains_real_symphony_and_guest_concerts(self):
        snapshot = json.loads((Path(__file__).resolve().parents[1] / "data/snapshots/benaroya_hall.json").read_text())
        records = snapshot["events"]
        self.assertEqual(len(records), 163)
        self.assertEqual(len({r["source_id"] for r in records}), len(records))
        self.assertEqual(sum(r["major"] for r in records), 119)
        self.assertTrue(any(not r["major"] for r in records))
        for rec in records:
            self.assertEqual(rec["region"], "seattle")
            self.assertEqual(rec["source"], "Benaroya Hall")
            self.assertIn("Benaroya Hall", rec["venue"])
            self.assertTrue(rec["ticket_url"].startswith(scrapers.BH + "/"))
            self.assertGreaterEqual(rec["start"], snapshot["exported"][:10])
        requiem = [r for r in records if r["title"] == "Mozart’s Requiem with Xian"]
        self.assertEqual([r["start"] for r in requiem],
            ["2026-11-19T19:30:00", "2026-11-21T20:00:00", "2026-11-22T14:00:00"])
        self.assertTrue(all(any("Requiem" in p["work"] for p in r["program"]) for r in requiem))

    def test_session_starts_at_public_calendar_before_post_feed(self):
        session = Mock()
        session.get.return_value = response()
        session.post.return_value = response([event()])
        with patch.object(scrapers.time, "sleep"):
            rows = scrapers.bh_calendar_events(session, datetime(2026, 11, 17))
        self.assertEqual(len(rows), 1)  # duplicate IDs across month windows are one performance
        self.assertEqual(session.method_calls[0][0], "get")
        self.assertEqual(session.get.call_args.args[0], scrapers.BH + "/calendar/")
        self.assertEqual(session.post.call_count, 7)
        self.assertEqual(session.post.call_args.args[0], scrapers.BH_API)
        self.assertEqual(session.post.call_args.kwargs["data"]["start"], "2027-11-01T00:00:00.000Z")

    def test_waiting_room_and_blocked_access_stop_requests(self):
        session = Mock()
        session.get.return_value = response(text="<title>Queue-it</title>")
        with patch.object(scrapers.time, "sleep"), self.assertRaises(RuntimeError):
            scrapers.bh_calendar_events(session, datetime.now())
        session.post.assert_not_called()
        for status in [403, 429]:
            session = Mock()
            r = response()
            r.status_code = status
            r.raise_for_status.side_effect = requests.HTTPError(response=r)
            session.get.return_value = r
            with patch.object(scrapers.time, "sleep"), self.assertRaises(requests.HTTPError):
                scrapers.bh_calendar_events(session, datetime.now())
            self.assertEqual(session.get.call_count, 1)
            session.post.assert_not_called()

    def test_concert_filter_includes_symphony_and_untagged_guests(self):
        cases = [
            (event(), True),
            (event(genre=None, title="The Sound of Remembrance: A Mosaic Requiem"), True),
            (event(genre="Pop Culture", title="Holiday Pops with Megan Hilty"), True),
            (event(genre="Movies", title="The Snowman"), True),
            (event(brand="Benaroya Hall", title="Seattle Men's Chorus", genre=None), True),
            (event(brand="Benaroya Hall", title="David Templeton in Concert", genre=None), True),
            (event(brand="Benaroya Hall", title="National Geographic Live", genre="Talks"), False),
            (event(title="Open Rehearsal with Xian"), False),
            (event(title="Laffont District Auditions"), False),
            (event(hideInSearchResults=True), False),
        ]
        for item, expected in cases:
            self.assertEqual(scrapers.bh_is_concert(item), expected, item["title"])

    def test_distinct_performances_keep_dates_and_local_times(self):
        rows = [event(), event(2, start="2030-01-17T20:00:00.0000000"),
                event(3, brand="Benaroya Hall", title="Balourdet Quartet", genre="Chamber"),
                event(4, isPast=True)]
        with patch.object(scrapers, "bh_calendar_events", return_value=rows), \
             patch.object(scrapers, "bh_detail", return_value=None), \
             patch.object(scrapers, "load_brochure", return_value=({}, {})):
            records = list(scrapers._benaroya_hall(Mock()))
        self.assertEqual(len(records), 3)
        self.assertEqual(records[0]["start"], datetime(2030, 1, 15, 19, 30))
        self.assertEqual(records[1]["start"], datetime(2030, 1, 17, 20))
        self.assertNotEqual(records[0]["source_id"], records[1]["source_id"])
        self.assertTrue(all(r["region"] == "seattle" and "Benaroya Hall" in r["venue"] for r in records))
        self.assertTrue(records[0]["major"])
        self.assertFalse(records[2]["major"])
        self.assertEqual(records[0]["ticket_url"], scrapers.BH + "/book/1")
        self.assertIn("Seattle Symphony", records[0]["performers"])

    def test_empty_or_invalid_feed_is_a_failure_not_silent_success(self):
        for payload in [[], {"error": "unavailable"}]:
            session = Mock()
            session.get.return_value = response()
            session.post.return_value = response(payload)
            with patch.object(scrapers.time, "sleep"), self.assertRaises(RuntimeError):
                scrapers.bh_calendar_events(session, datetime.now())

    def test_snapshot_seed_and_failed_live_refresh_keep_events(self):
        context = app.app_context()
        context.push()
        temp = tempfile.TemporaryDirectory()
        try:
            music.MusicEvent.query.filter_by(source="Benaroya Hall").delete()
            db.session.commit()
            future = (datetime.now() + timedelta(days=10)).replace(hour=19, minute=30, second=0, microsecond=0)
            record = dict(source="Benaroya Hall", source_id="snapshot-test", title="Seattle Symphony fixture",
                          start=future.isoformat(), category="symphonic", performers="Seattle Symphony",
                          venue="Benaroya Hall", region="seattle", major=True)
            with patch.object(music_ingest, "SNAP_DIR", temp.name):
                music_ingest.export_snapshot("Benaroya Hall", [record])
                self.assertEqual(music_ingest.seed_missing_snapshot(db, "Benaroya Hall"), 1)
                stored = music.MusicEvent.query.filter_by(source_id="snapshot-test").one()
                stored.title = "Newer live title"
                db.session.commit()
                self.assertEqual(music_ingest.seed_missing_snapshot(db, "Benaroya Hall"), 0)
                self.assertEqual(stored.title, "Newer live title")
                with patch.dict(scrapers.SCRAPERS, {"Benaroya Hall": Mock(side_effect=RuntimeError("venue unavailable"))}):
                    result = list(music_ingest.run_scrapers(db, ["Benaroya Hall"]))
                self.assertEqual(result, [("Benaroya Hall", 1, None)])
                self.assertEqual(music.MusicEvent.query.filter_by(source="Benaroya Hall").count(), 1)
                log = music.ScrapeLog.query.filter_by(source="Benaroya Hall").order_by(music.ScrapeLog.ran_at.desc()).first()
                self.assertIn("served snapshot", log.error)
        finally:
            music.MusicEvent.query.filter_by(source="Benaroya Hall").delete()
            db.session.commit()
            db.session.remove()
            context.pop()
            temp.cleanup()


if __name__ == "__main__":
    unittest.main(verbosity=2)
