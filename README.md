# burrow-owls
Blog for my family

## Music practice — The Great Gallery

`thegreatgallery.art/music` (locally `/fineart/music`) is a blue choir practice
room for soprano, alto, tenor and bass. The separate Seattle calendar at `/music`
on the family site is unchanged. Painting and photography menus link to practice.

The songbook has 92 titles, including 18 Jewish songs and 22 world folk songs,
plus the original carols, hymns/spirituals, familiar children's tunes and four
anthem/patriotic songs. The Anthems collection includes O Canada (current English
lyrics) and The Star-Spangled Banner (first verse), with new practice harmonies.
Jewish and world collections
have shortcut buttons; search also matches origins, Hebrew titles, and alternate
spellings. The default song is Hava Nagila, and existing song links still work.
Thirty-five settings come from the Open Hymnal archive and retain their original
public-domain statements in `data/choir/sources/`. Fifteen simple new educational
harmonizations, 40 added folk-song settings and two added anthem settings are dedicated under CC0.
These are educational practice settings, not historical editions.
Jingle Bells and Oh! Susanna are explicitly chorus-only.
The library does not include recent copyrighted pop songs.

- `choir.py`, `templates/choir/`, `static/choir/`: routes, responsive page and player.
- `data/choir/library.json`: compiled score/credit catalog, served by Flask.
- `.venv/bin/python choir_build/build_library.py`: deterministic, offline rebuild.
- `choir_build/folk_manifest.json` and `folk_melodies.json`: reviewed melody
  references, source URLs/hashes, origin/search metadata, and pitch/rhythm inputs.
  `arrange_folk.py` adds new harmony without using source accompaniments. Original
  melody pitches and rhythms are checked against the generated soprano line;
  a few documented octave/key transpositions make high instrumental references
  more comfortable to sing. Traditional rounds receive new harmonies here.
  The new scores are educational Western SATB settings, not claims about how
  a culture traditionally performs its music. Goldfarb's 1918/1927 songs are
  identified as public domain in the United States.
- abcjs 6.7.2 is bundled locally under its MIT license in `static/choir/vendor/`.
- Web Audio plays guide tones from the same parsed MIDI note events used by the
  score. An audio-clock cursor follows playback; mute/solo, backing practice,
  40–120% tempo, seeking, pause, restart and looping work without remote samples.
- MIDI export includes all four parts at the original tempo; printing paginates
  between systems. Individual source scores and credits are available on the page.
- No microphone, recording, new database tables or new Python dependencies.

For regression checks, run a local Flask server on port 5057 and
`node choir_build/verify_browser.cjs` with the existing workspace Playwright and
installed Google Chrome. Set `CHOIR_TEST_URL` or `CHOIR_TEST_ARTIFACTS` to override
the URL or screenshot directory. It checks all 92 scores for four voices and
matching visual/audio duration, controls, filtering, MIDI and mobile overflow.
`node choir_build/verify_library.cjs` separately checks all source files and the
42 added melody transcriptions against their generated notes and rhythms.


## /music — Seattle classical concert calendar

Calendar (day / week / month) of classical concerts in the Seattle region, plus piece search
(`/music/search?q=beethoven+7`).

### Music Through History

`/music/history` is an editorial timeline of Western classical music: 100 landmark
works, 50 composer biographies, and seven era chapters. Switch to composers with
`?view=composers`; `?era=baroque` and `?q=bach` filter either view. Piece pages live at
`/music/history/pieces/<id>` and biographies at `/music/history/composers/<id>`.
The calendar features a history invitation, and the shared sidebar and music navigation
link to both the timeline and the composer directory.

Edit `data/music_history/history.json` directly. Preserve IDs to keep links stable.
Work `year` determines chronological order and era placement; `date` explains whether
the displayed year means composition, completion, publication, or premiere. Composer
chapters describe stylistic affiliations, so lifespans and individual works can cross
chapter boundaries. The selection is chronological rather than a ranked league table;
a complete collection or cycle counts as one entry. Each work has a description,
historical significance, and listening prompt. Biographies and selected work entries
link to further reading, including institutional program notes and composer catalogs.
Restart the app after editing the JSON because it is cached per worker.

Routes and data loading are in `music_history.py`, templates in `templates/music_history/`,
and styles and progressive filtering in `static/music_history/`. History requests do not
trigger concert scraping. No database migration or external API is needed. Recording
links open YouTube searches; they do not embed or host recordings.

Verification:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python music_history_build/verify_history.py
MUSIC_AUTOREFRESH=0 DATABASE_URL=sqlite:///:memory: SECRET_KEY=local-music-history-preview .venv/bin/python -m flask --app app run --host 127.0.0.1 --port 5058
# In another terminal, with the preview running:
node music_history_build/verify_browser.cjs
```

The route checks use an in-memory database and a mocked visitor counter. Browser
screenshots go to `/private/tmp/music-history-qa/`.

### Concert data

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

`fineart_auth.py` adds sign-up / log-in (username + password) so favorites sync across devices.
Tables `fa_users` and `fa_favorites` are created by `db.create_all()`. Anonymous visitors still use localStorage favorites.

Env vars on Render: `DATABASE_URL` (Postgres — SQLite files don't survive deploys) and `SECRET_KEY` (required).

### Gallery visitor analytics

Umami Cloud tracks public pages on **thegreatgallery.art** only: paintings, games,
photography and music practice. The private dashboard is at https://cloud.umami.is/.
The website ID in `galleryhost.py` is public; it is separate from the account ID.
`UMAMI_WEBSITE_ID` optionally overrides it; setting it to an empty value disables tracking.
The family site, Render preview hosts and account/profile pages have no tracker.
Search parameters, URL fragments and referrer queries are removed. No login IDs,
form contents, microphone data or session replay are sent. The tracker respects
Do Not Track and Umami's `localStorage['umami.disabled'] = '1'` opt-out.

Umami reports estimated unique visitors, approximate countries/regions/cities,
popular pages and visit duration. Visitors are browser/network estimates, not a
count of identifiable people. VPNs and blockers affect results. Standard visit
duration is based on event timestamps and can include gaps between events.
For time on a single practice page, `static/fineart/analytics.js` sends an
`engagement` event with numeric `seconds` and a `section` (paintings, photography,
games, music). Sum `seconds` in event data to see visible-page time; divide by
visits for a per-visit estimate. These are incremental batches every 60 seconds
and when a page is hidden or left, not cumulative totals. Hidden tabs add no time;
visible time does not prove attention. Final seconds may be lost on abrupt exit.
Engagement events count toward the plan's event limit and affect bounce/visit
duration metrics; pageview events remain separate. Counts begin after deployment.

QA: with Flask serving port 5057, run `node analytics_build/verify_browser.cjs`.
It loads the official tracker but intercepts all collection requests so test
visits do not appear in the live dashboard, and saves screenshots under
`/private/tmp/gallery-analytics-qa`.

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

## The Great Gallery — Photography (`/photography`)

A sister site to the paintings gallery: photographs from 1826 to today, traced through seven eras, with kid-friendly texts, photographer bios, collections and a timeline. Served at `thegreatgallery.art/photography` (and `/photography` on any host).

- `photography.py` — blueprint (`/photography`), data in `data/photo/gallery.json`, templates in `templates/photo/`, assets in `static/photo/` (green theme of the paintings CSS).
- Everything shown is public domain, CC0 or freely licensed (CC BY / BY-SA, with the credit shown). Images are hot-linked from their source (Art Institute of Chicago, Cleveland Museum of Art, Library of Congress, NASA, Wikimedia Commons); each page links to the source and a hi-res download.
- Build: `fineart_build/photo/*.py` fetch candidates (museum open-access APIs, NASA, Commons), `unify.py` merges them, `select_.py` + `freeze.py` choose `work.json`; texts are hand-written in `photo_build/texts/t*.py`; `photo_build/build_data.py` assembles the JSON (eras, milestones and photographer bios live in `photo_build/meta.py`, `artists_a.py`, `artists_b.py`).

## Backing up hi-res originals to Backblaze B2

`backup/backup_hires.py` copies the hi-res original of every photo (or painting) to a private B2 bucket as a fallback in case the external links break. It is not used by the site. Set `B2_KEY_ID`, `B2_APP_KEY`, `B2_BUCKET` and `B2_ENDPOINT`, then run `.venv/bin/python backup/backup_hires.py --site photo --dry-run` (sizes only) and again without `--dry-run` to upload. It is resumable, waits between downloads from the same host and stops on 403/429 instead of retrying.
