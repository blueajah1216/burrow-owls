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
