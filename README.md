# burrow-owls
Blog for my family


## /music — Seattle classical concert calendar

Calendar (day / week / month) of classical concerts in the Seattle region, plus piece search
(`/music/search?q=beethoven+7`).

Data comes from per-presenter scrapers in `music_scrapers.py` (one function per source, registered with
`@scraper("Name")`). Current sources: Benaroya Hall (Seattle Symphony + guest presenters such as Seattle
Chamber Music Society, Music of Remembrance, Seattle Philharmonic), Early Music Seattle, Emerald City Music,
Seattle Choral Company, Seattle Pro Musica, Philharmonia Northwest, Cascade Symphony Orchestra,
UW School of Music.

    flask music-scrape                  # run every scraper (a few minutes; Benaroya's detail pages are slow)
    flask music-scrape "Early Music Seattle"
    flask music-import file.json|csv    # hand-curated events (format at top of music_ingest.py)
    flask music-demo / music-clear-demo # fake sample data for UI work

The web app refreshes automatically in a background thread when data is >24h old (disable with
`MUSIC_AUTOREFRESH=0`). A scraper that fails or returns nothing never deletes that source's existing events.

To add a presenter: write a generator yielding event dicts (see `music_ingest.upsert`) and decorate it with
`@scraper`. Prefer, in order: an official feed (.ics / JSON API the site's own calendar calls), schema.org
JSON-LD, then HTML parsing. Be polite (fetch() sleeps and honours 429s) and never bypass a waiting room or login.


## /fineart — The Great Gallery

A standalone-styled (blue + gold) gallery of ~1,350 famous public-domain paintings from 1700–1929, grouped into 9
"rooms" (genres) and 23 "collections" (Art for Kids, Jewish artists, Canada, Norway, USA, and a dozen+ other countries), each with a kid-friendly "why it's great" paragraph and a short artist bio.

- Collections are built from `fineart_build/select_cols.py` (Wikidata nationality/ethnicity + per-artist caps, ranked by fame) and the
  hand-picked `out/kids.json` (100 paintings, each with a "look closer" prompt). New works are `base3.json` + `out/new_*.json`;
  extra bios in `out/artists_03.json`; `out/text_patch.json` corrects blurbs after visual review; `out/fixes.json` holds title/year fixes,
  `n` (hide as mature) and `drop` flags. Rebuild everything with `python3 fineart_build/build_data.py`.
- `fineart.py` — Flask blueprint (`/fineart`, `/collections`, `/collection/<slug>`, `/fineart/p/<id>`, `/fineart/artist/<id>`, `/random`, `/today`, `/data.json`).
- `data/fineart/gallery.json` — the compiled dataset the site serves (rebuild with `python3 fineart_build/build_data.py`).
- `fineart_build/` — how the data was made: `base2.json` (Wikidata facts + Wikimedia Commons image info, ranked by
  number of Wikipedia language editions as a "fame" score), `out/*.json` (hand-written text; a painting with no entry
  is left out of the site), `out/fixes.json` (title/year corrections). `images.py`/`assemble.py` are the fetch steps.
- Images are hotlinked from Wikimedia Commons thumbnails (500/960/1280/1920px); each painting links to its Commons page.
- Each painting page also shows where it hangs (`out/locations.json`, built by `loc.py` → `loc2.py` → `loc3.py` from Wikidata's
  collection/location data plus hand-checked fixes) and three print-shop search links (budget Etsy, mid-range Fine Art America,
  high-end Meisterdrucke; see `print_links()` in `fineart.py`).
- Paintings that show nudity are flagged (`n`) and hidden unless the visitor ticks "Include nudes".

### /fineart accounts

`fineart_auth.py` adds sign-up / log-in (username + password, or Google) so favorites sync across devices.
Tables `fa_users` and `fa_favorites` are created by `db.create_all()`. Anonymous visitors still use localStorage favorites.

Env vars on Render: `DATABASE_URL` (Postgres — SQLite files don't survive deploys), `SECRET_KEY` (required), and for Google
`GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` (authorized redirect URI: `https://theburrowowls.com/fineart/auth/google/callback`).

### /fineart/history — Art Through History

A tree-shaped timeline (`/fineart/history`) of 43 events from the Persian Wars to the Moon landing and the Vietnam War, each with an event page (`/fineart/history/<slug>`) of ~10–18 artworks; paintings link back to their events ("Part of history").
Data: `data/fineart/history.json`, built by `fineart_build/build_data.py` from `fineart_build/hist/` (`events.py`, `events_text.py`, `picks_a.py`/`picks_b.py`, `resolved.json`) plus `base4.json` and the hand-written text in `fineart_build/out/hist_*.json`.
Works after 1929 are limited to public-domain sources (US-government art and photographs, NASA, Canadian war art), so the later events lean on those.

### /fineart collections: styles & movements

`fineart_build/styles/` holds `styles_rules.py` (artist/period rules for Impressionism, Romanticism, etc., capped per artist) and `abstract_picks.py` (the six sections of the Abstract Art collection). `build_data.py` turns them into `group: "styles"` collections; new abstract works are added by `styles/add_styles.py` into `base4.json`, with text in `out/style_*.json`.

## Museums (`/fineart/museums`)

A world map of ~107 great art museums with continent zoom, plus a page per museum (`/fineart/museum/<slug>`)
with a description, history, top pieces and the gallery's paintings held there.

- Source text: `fineart_build/museums/src_*.py` (hand-written; `aliases` must match the gallery's venue strings, `l[0]`).
- `python3 fineart_build/museums/build_museums.py` fetches coordinates and photos from Wikipedia (cached in `coords.json`),
  links gallery paintings by venue, and writes `data/fineart/museums.json`.
- `fineart_build/museums/build_map.py` turns world-atlas TopoJSON (download `countries-110m.json` into that folder first)
  into `static/fineart/world.json`, the simple SVG map used by `static/fineart/museums.js`.

## Old masters (1426–1725)

About 1,000 paintings from 600 to 300 years ago (Early Renaissance through the early Rococo) were added from Wikidata/Commons
by `fineart_build/old/`: `cands.py` (candidates by year, ranked by Wikipedia sitelinks) → `add_old.py` (per-artist cap, Commons image
info, artists; drops CC BY / BY-SA photos) → `loc_old.py` (venues) → hand-written texts in `out/old_NN.json` (from `t00.py`–`t09.py`) and
bios in `out/old_artists_NN.json` (`a00.py`–`a02.py`), then `build_data.py`. Style collections for the era (Renaissance, Baroque,
Dutch Golden Age) live in `styles/styles_rules.py`.
