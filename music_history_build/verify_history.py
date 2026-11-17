"""Content and route QA. Run with .venv/bin/python music_history_build/verify_history.py."""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "music-history-test"
os.environ["MUSIC_AUTOREFRESH"] = "0"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bs4 import BeautifulSoup
from app import app
from music_history import load_history


class HistoryChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()
        cls.data, cls.composers, cls.eras = load_history()

    def get(self, url):
        # Keep QA out of the family site's on-disk visitor counter.
        with patch("app.get_site_visits", return_value=0):
            response = self.client.get(url, base_url="https://thegreatgallery.art", follow_redirects=True)
        self.assertEqual(response.status_code, 200, url)
        return BeautifulSoup(response.data, "html.parser")

    def test_editorial_integrity(self):
        works = self.data["works"]
        self.assertEqual(len(works), 100)
        self.assertEqual(len({w["id"] for w in works}), 100)
        self.assertEqual(len(self.data["composers"]), 50)
        self.assertEqual(len(self.composers), 50)
        self.assertEqual(len(self.eras), 7)
        self.assertEqual([w["year"] for w in works], sorted(w["year"] for w in works))
        self.assertEqual([w["number"] for w in works], list(range(1, 101)))
        for work in works:
            self.assertIn(work["composer"], self.composers)
            era = self.eras[work["era"]]
            self.assertTrue(era["start"] <= work["year"] < era["end"])
            composer = self.composers[work["composer"]]
            self.assertGreaterEqual(work["year"], composer["birth"])
            self.assertLessEqual(work["year"], composer["death"] or 2026)
            for field in ["description", "importance", "listen"]:
                self.assertGreater(len(work[field]), 45, (work["id"], field))
        for composer in self.composers.values():
            self.assertIn(composer["era"], self.eras)
            self.assertTrue(composer["works"])
            self.assertGreater(len(composer["bio"]), 200)
            self.assertTrue(composer["source"]["url"].startswith("https://"))

    def test_every_reading_page_and_local_link(self):
        urls = ["/music/history", "/music/history?view=composers"]
        urls += [f'/music/history/pieces/{w["id"]}' for w in self.data["works"]]
        urls += [f'/music/history/composers/{c}' for c in self.composers]
        checked = set()
        with patch("music_ingest.refresh_if_stale") as refresh:
            for url in urls:
                soup = self.get(url)
                self.assertEqual(len(soup.select("h1")), 1, url)
                for link in soup.select("a[href]"):
                    target = link["href"].split("#")[0]
                    if target.startswith("/music/history") and target not in checked:
                        self.get(target)
                        checked.add(target)
            refresh.assert_not_called()

    def test_filters_without_javascript(self):
        soup = self.get("/music/history?q=beethoven")
        visible = [x for x in soup.select("[data-item]") if not x.has_attr("hidden")]
        # Search also finds the historical discussion of Beethoven in Brahms/Mahler.
        self.assertEqual(len(visible), 7)
        self.assertTrue(all("beethoven" in x["data-search"] for x in visible))
        soup = self.get("/music/history?view=composers&q=dvorak")
        visible = [x for x in soup.select("[data-item]") if not x.has_attr("hidden")]
        self.assertEqual(len(visible), 1)
        soup = self.get("/music/history?era=baroque")
        self.assertEqual(len([s for s in soup.select("[data-era]") if not s.has_attr("hidden")]), 1)
        soup = self.get("/music/history?q=does-not-exist")
        self.assertFalse(soup.select_one("#empty-state").has_attr("hidden"))
        self.assertTrue(all(x.has_attr("hidden") for x in soup.select("[data-item]")))
        soup = self.get("/music/history?era=bad&view=bad")
        self.assertEqual(len([x for x in soup.select("[data-item]") if not x.has_attr("hidden")]), 100)
        soup = self.get('/music/history?q=%22%3E%3Cscript%3Ealert(1)%3C/script%3E')
        self.assertFalse(any("alert(1)" in s.get_text() for s in soup.select("script")))

    def test_missing_pages_and_discovery(self):
        for path in ["/music/history/pieces/missing", "/music/history/composers/missing"]:
            self.assertEqual(self.client.get(path).status_code, 404)
        for path in ["/music", "/music/concerts", "/music/search", "/", "/photography"]:
            soup = self.get(path)
            self.assertTrue(soup.select('a[href="/music/history"]'), path)

    def test_gallery_host_music_routes(self):
        practice = self.get("/music")
        self.assertTrue(practice.select_one("#play"))
        self.assertEqual(len(practice.select(".song-option")), 92)
        self.assertEqual(practice.select_one(".music-history-invitation")["href"], "/music/history")
        self.assertTrue(practice.select('a[href="/music/concerts"]'))
        history = self.get("/music/history")
        self.assertIn("The Great Gallery", history.select_one("title").get_text())
        self.assertNotIn("The Burrow Owls", str(history))
        self.assertTrue(history.select('a[href="/music"], a[href="/music/"]'))
        self.assertTrue(history.select('a[href="/music/concerts"]'))
        self.assertTrue(history.select('a[href="/"]'))
        concerts = self.get("/music/concerts")
        self.assertIn("Seattle Classical Music", concerts.select_one("h1").get_text())
        self.assertNotIn("The Burrow Owls", str(concerts))
        search = self.get("/music/search?q=bach")
        self.assertTrue(search.select('a[href="/music/concerts"]'))
        library = self.client.get("/music/library.json", base_url="https://thegreatgallery.art")
        self.assertEqual(library.status_code, 200)
        self.assertEqual(len(library.json), 92)
        score = self.client.get("/music/sources/" + library.json[0]["source"], base_url="https://thegreatgallery.art")
        self.assertEqual(score.status_code, 200)
        self.assertIn("attachment", score.headers["Content-Disposition"])
        self.assertIn(b"X:", score.data)
        score.close()
        library.close()
        redirect = self.client.get("/fineart/music/history?q=bach", base_url="https://thegreatgallery.art")
        self.assertEqual(redirect.status_code, 301)
        self.assertEqual(redirect.headers["Location"], "/music/history?q=bach")
        www = self.client.get("/music/history", base_url="https://www.thegreatgallery.art")
        self.assertEqual(www.status_code, 301)
        self.assertEqual(www.headers["Location"], "https://thegreatgallery.art/music/history")


if __name__ == "__main__":
    unittest.main(verbosity=2)
