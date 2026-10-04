"""
One scraper per Seattle presenter. Each is a generator yielding event dicts
(see music_ingest.py for fields) and is registered in SCRAPERS by source name.

Scrapers are deliberately forgiving: a page that doesn't parse is skipped, and the
runner (music_ingest.run_scrapers) reports per-source counts so a site redesign
shows up as "0 events" rather than silently stale data.
"""

import json
import os
import re
import time
from datetime import datetime

from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15 BurrowOwlsMusic/1.0"
TIMEOUT = 25

# Anything matching these is not a concert (rehearsals, talks, parties…).
NON_CONCERT = re.compile(
    r"rehears|welcome party|conversation|meditation|lecture|workshop|masterclass|"
    r"open house|gala\b|auction|fundrais|class\b|introduction to|pre-concert talk|"
    r"late night session|karaoke|wine down|audition|tiny tots",
    re.I,
)

SCRAPERS = {}


def scraper(name):
    def deco(fn):
        SCRAPERS[name] = fn
        return fn
    return deco


def fetch(url, **kw):
    """GET with a small politeness delay; on 429 honour Retry-After once, then give up."""
    time.sleep(0.25)
    r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT, **kw)
    if r.status_code == 429:
        wait = r.headers.get("Retry-After", "")
        time.sleep(min(int(wait) if wait.isdigit() else 30, 90))
        r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT, **kw)
    r.raise_for_status()
    return r


def soup_of(url):
    return BeautifulSoup(fetch(url).text, "html.parser")


def text_lines(soup):
    """Visible text of the main content, one non-empty line per element."""
    s = BeautifulSoup(str(soup), "html.parser")
    for t in s(["script", "style", "svg", "nav", "header", "footer", "noscript"]):
        t.decompose()
    root = s.find("main") or s.body or s
    lines = (re.sub(r"\s+", " ", l).strip() for l in root.get_text("\n").split("\n"))  # \xa0 -> space
    return [l for l in lines if l]


def jsonld_events(soup):
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except ValueError:
            continue
        stack = [data]
        while stack:
            n = stack.pop()
            if isinstance(n, list):
                stack.extend(n)
            elif isinstance(n, dict):
                t = n.get("@type")
                t = t if isinstance(t, list) else [t]
                if any(isinstance(x, str) and x.endswith("Event") for x in t):
                    yield n
                stack.extend(v for v in n.values() if isinstance(v, (dict, list)))


def local_dt(iso: str):
    """'2027-04-18T16:00:00-8:00' -> naive 2027-04-18 16:00 (venue-local wall clock)."""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}))?", iso or "")
    if not m:
        return None
    y, mo, d, h, mi = m.groups()
    return datetime(int(y), int(mo), int(d), int(h or 19), int(mi or 30))


_MONTHS = "Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
_DATE_RE = re.compile(
    rf"\b(?P<mon>{_MONTHS})[a-z]*\.?\s+(?P<d>\d{{1,2}})(?:st|nd|rd|th)?(?:,?\s+(?P<y>\d{{4}}))?", re.I)
_TIME_RE = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s*([ap])\.?m\.?\b", re.I)


def parse_when(text, default_year=None):
    """First 'Month D[, YYYY]' plus optional 'H[:MM] pm' in text -> naive datetime, else None.
    Without a year, picks the next occurrence on/after today (seasons span new year)."""
    m = _DATE_RE.search(text or "")
    if not m:
        return None
    mon = _MONTHS.split("|").index(m.group("mon").title()[:3]) + 1
    day = int(m.group("d"))
    t = _TIME_RE.search(text[m.end():m.end() + 40]) or _TIME_RE.search(text[max(0, m.start() - 30):m.start()])
    hh, mm = 19, 30
    if t:
        hh = int(t.group(1)) % 12 + (12 if t.group(3).lower() == "p" else 0)
        mm = int(t.group(2) or 0)
    try:
        if m.group("y"):
            return datetime(int(m.group("y")), mon, day, hh, mm)
        today = datetime.now()
        dt = datetime(today.year, mon, day, hh, mm)
        return dt if dt.date() >= today.date() else datetime(today.year + 1, mon, day, hh, mm)
    except ValueError:
        return None


def region_of(place):
    """Map venue/city text to (city, region). Only 'seattle' feeds the calendar."""
    p = (place or "").lower()
    for city, region in (("olympia", "olympia"), ("bellingham", "bellingham"), ("tacoma", "tacoma"),
                         ("portland", "portland"), ("vancouver", "vancouver")):
        if city in p:
            return city.title(), region
    for city in ("bellevue", "kirkland", "redmond", "edmonds", "shoreline", "renton", "everett", "bainbridge",
                 "kenmore", "issaquah", "mercer island", "burien", "lynnwood", "bothell", "kent", "auburn", "federal way"):
        if city in p:
            return city.title(), "seattle"  # greater Seattle region
    return "Seattle", "seattle"


def block_lines(soup):
    """Lines of paragraph-level text: inline tags (italic titles) are kept inside their line,
    <br> splits lines. Better than text_lines() for 'Composer – Work' program lists."""
    root = soup.find("main") or soup.body or soup
    out = []
    for t in root.find_all(["p", "li", "h1", "h2", "h3", "h4", "h5", "h6"]):
        if t.find(["p", "li"]):
            continue
        for br in t.find_all("br"):
            br.replace_with("\n")
        for l in t.get_text("").split("\n"):
            l = re.sub(r"\s+", " ", l).strip()
            if l:
                out.append(l)
    return out


_INSTR = (r"Piano|Cello|Violin|Viola|Soprano|Mezzo[- ]Soprano|Alto|Tenor|Baritone|Bass(?:-Baritone)?|Flute|Clarinet|Oboe|"
          r"Bassoon|Trumpet|Horn|Harp|Guitar|Organ|Percussion|Saxophone|Narrator|Conductor|Harpsichord|Theremin")


def dash_program(lines):
    """['Rossini – Overture to The Barber of Seville', ...] -> [{composer, work}]"""
    out = []
    for l in lines:
        m = re.match(r"^([A-Z][^–—]{2,45}?)\s+[–—]\s+(.+)$", l)
        if m:
            out.append({"composer": m.group(1).strip(), "work": m.group(2).strip()})
    return out


def sections(soup, split_tag):
    """Split a page on <split_tag> headings -> [(heading_text, [(enclosing_tag, text), ...])].
    Text nodes are in document order; enclosing_tag is the nearest h1-h6 ancestor name or None."""
    out, cur = [], None
    for node in soup.find_all(string=True):
        if node.parent.name in ("script", "style", "noscript"):
            continue
        txt = re.sub(r"\s+", " ", str(node)).strip()
        if not txt:
            continue
        h = node.find_parent(re.compile(r"^h[1-6]$"))
        if h is not None and h.name == split_tag:
            if cur is not None and cur[2] is h:
                cur[0] += " " + txt  # heading text split across nodes
                continue
            cur = [txt, [], h]
            out.append(cur)
            continue
        if cur is not None:
            cur[1].append((h.name if h else None, txt))
    return [(t, toks) for t, toks, _ in out]


def clean(s):
    return re.sub(r"\s+", " ", BeautifulSoup(s or "", "html.parser").get_text(" ")).strip()


# ------------------------------------------------------------------------------
# Early Music Seattle  (WordPress REST list + JSON-LD on each event page)
# ------------------------------------------------------------------------------

@scraper("Early Music Seattle")
def early_music_seattle():
    base = "https://earlymusicseattle.org"
    items = fetch(f"{base}/wp-json/wp/v2/events?per_page=100&_fields=link,title").json()
    seen = set()
    for it in items:
        url, title = it["link"], clean(it["title"]["rendered"])
        if url in seen or NON_CONCERT.search(title):
            continue
        seen.add(url)
        try:
            page = soup_of(url)
        except requests.RequestException:
            continue
        ld = next(jsonld_events(page), None)
        start = local_dt(ld.get("startDate")) if ld else None
        if not start:
            continue
        lines = text_lines(page)
        venue = None
        for i, l in enumerate(lines):
            if l == "Venue Information" and i + 1 < len(lines):
                venue = lines[i + 1]
                break
        tix = re.search(r"https://ci\.ovationtix\.com/36724/production/\d+", str(page))
        meta = page.find("meta", attrs={"name": "description"}) or page.find("meta", property="og:description")
        yield {
            "source": "Early Music Seattle",
            "source_id": url,
            "title": title,
            "start": start,
            "performers": title.split(":")[0].strip() if ":" in title else title,
            "description": clean(meta.get("content")) if meta else None,
            "venue": venue,
            "city": "Seattle",
            "country": "USA",
            "region": "seattle",
            "major": False,
            "ticket_url": tix.group(0) if tix else url,
        }


# ------------------------------------------------------------------------------
# Emerald City Music  (sitemap -> concert pages with "When?" / "Where?" blocks)
# ------------------------------------------------------------------------------

@scraper("Emerald City Music")
def emerald_city_music():
    sm = fetch("https://emeraldcitymusic.org/sitemap.xml").text
    urls = sorted(set(re.findall(r"<loc>(https://emeraldcitymusic\.org/concerts/[^<]+)</loc>", sm)))
    cutoff = datetime.now().replace(hour=0, minute=0)
    for url in urls:
        try:
            lines = text_lines(soup_of(url))
        except requests.RequestException:
            continue
        try:
            w = lines.index("When?")
            where = lines[lines.index("Where?") + 1]
        except ValueError:
            continue
        start = parse_when(lines[w + 1])
        if not start or start < cutoff:
            continue
        # Title is the line before "IN BRIEF"; performers sit between title/banner and "When?".
        try:
            b = lines.index("IN BRIEF")
        except ValueError:
            continue
        title = lines[b - 1]
        if NON_CONCERT.search(title):
            continue
        desc = lines[b + 1] if b + 1 < len(lines) else None
        head = lines[:w]
        names = []
        for l in reversed(head):
            if len(l) > 40 or l.lower().startswith(("you are viewing", "-this is")) or l in (title, "here"):
                break
            names.append(l)
        names = list(reversed(names))[:6]
        city, region = region_of(where)
        yield {
            "source": "Emerald City Music",
            "source_id": url,
            "title": title,
            "start": start,
            "performers": ", ".join(names) or "Emerald City Music",
            "description": desc,
            "venue": where.split(",")[0] if where else None,
            "city": city,
            "country": "USA",
            "region": region,
            "major": False,
            "category": "chamber",
            "ticket_url": url,
        }


# ------------------------------------------------------------------------------
# Seattle Choral Company  (h3 per concert, h5 date lines, "At" venue, "by" composer)
# ------------------------------------------------------------------------------

@scraper("Seattle Choral Company")
def seattle_choral_company():
    url = "https://www.seattlechoralcompany.org/current-season/"
    page = soup_of(url)
    tix = "https://www.seattlechoralcompany.org/shop/purchase-tickets/"
    for title, toks in sections(page, "h3"):
        dates = []
        for tag, txt in toks:
            if tag == "h5":
                for m in re.finditer(r"(?:(\w+)\s+—\s+)?((?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day,[^S]*?\d{4} at \d{1,2}(?::\d{2})? ?[ap]m)", txt):
                    dates.append((m.group(1), parse_when(m.group(2))))
        if not dates:
            continue
        venues = [toks[i + 1][1] for i, (_, t) in enumerate(toks[:-1]) if t == "At"]
        program = [{"composer": t[3:].strip(), "work": toks[i - 1][1]}
                   for i, (_, t) in enumerate(toks) if t.startswith("by ") and i > 0]
        works = "; ".join(f"{p['composer']}: {p['work']}" for p in program)
        for i, (city, start) in enumerate(dates):
            if not start:
                continue
            venue = venues[i] if i < len(venues) else (venues[-1] if venues else None)
            tail = next((t for _, t in toks if t.lower().startswith("in ") and len(t) < 30), "")
            c, region = region_of(city or tail)
            yield {
                "source": "Seattle Choral Company",
                "source_id": f"{url}#{slugify_(title)}-{start:%Y%m%d}",
                "title": title,
                "start": start,
                "performers": "Seattle Choral Company",
                "description": works or None,
                "program": program,
                "venue": venue,
                "city": (city or c.title()) if city else c,
                "country": "USA",
                "region": region,
                "category": "choral",
                "major": False,
                "ticket_url": tix,
            }


def slugify_(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def composers_to_program(text):
    """'Reena Esmail (Winter Breviary), Morten Lauridsen, …' -> [{composer, work}]"""
    items, depth, buf = [], 0, ""
    for ch in text:
        depth += ch == "("
        depth -= ch == ")"
        if ch == "," and depth == 0:
            items.append(buf)
            buf = ""
        else:
            buf += ch
    items.append(buf)
    out = []
    for it in items:
        m = re.match(r"\s*(?:contemporary [\w ]+? composers\s+)?([^()]+?)\s*(?:\((.*?)\))?\s*$", it)
        if m and m.group(1).strip():
            out.append({"composer": m.group(1).strip(" .,"), "work": (m.group(2) or "").strip()})
    return out


# ------------------------------------------------------------------------------
# Seattle Pro Musica  (h2 per concert; "Day, Month D, YYYY — 3:00 pm & 7:00 pm" then venue)
# ------------------------------------------------------------------------------

@scraper("Seattle Pro Musica")
def seattle_pro_musica():
    url = "https://www.seattlepromusica.org/season"
    tix = url
    for title, toks in sections(soup_of(url), "h2"):
        body = " ".join(t for _, t in toks)
        if NON_CONCERT.search(title + " " + body) or "sponsors" in title.lower():
            continue
        title = re.sub(r"\s+", " ", title)
        dates = list(re.finditer(
            r"((?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day,\s+\w+ \d{1,2},\s+\d{4})\s*[—–-]\s*"
            r"((?:\d{1,2}(?::\d{2})?\s*[ap]m(?:\s*&\s*)?)+)", body))
        fc = re.search(r"Featured composers:\s*(.*?)(?=(?:Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day,|$)", body)
        program = composers_to_program(fc.group(1)) if fc else []
        desc = body[: dates[0].start()].strip() if dates else ""
        desc = re.sub(r"Featured composers:.*", "", desc).strip()
        for i, m in enumerate(dates):
            end = dates[i + 1].start() if i + 1 < len(dates) else len(body)
            place = body[m.end():end].strip()
            venue = re.split(r"\s\d", place, 1)[0].strip() or None
            for tm in re.findall(r"\d{1,2}(?::\d{2})?\s*[ap]m", m.group(2)):
                start = parse_when(f"{m.group(1)} {tm}")
                if not start:
                    continue
                c, region = region_of(place)
                yield {
                    "source": "Seattle Pro Musica",
                    "source_id": f"{url}#{slugify_(title)}-{start:%Y%m%d%H%M}",
                    "title": title,
                    "start": start,
                    "performers": "Seattle Pro Musica",
                    "description": desc[:500] or None,
                    "program": program,
                    "venue": venue,
                    "city": c,
                    "country": "USA",
                    "region": region,
                    "category": "choral",
                    "major": False,
                    "ticket_url": tix,
                }


# ------------------------------------------------------------------------------
# Benaroya Hall / Seattle Symphony
#
# One JSON endpoint (the one the site's own calendar page calls) lists everything in the
# hall: the Symphony plus guests (Seattle Chamber Music Society, Music of Remembrance,
# Seattle Philharmonic, Seattle Classic Guitar Society, …). The site sits behind a Queue-it
# waiting room during big on-sales; we never bypass it — we wait and retry, and if it
# doesn't clear we yield what we have (detail pages are optional extras).
# ------------------------------------------------------------------------------

BH = "https://benaroyahall.org"
BH_API = BH + "/umbraco/api/performances/GetGridCalendarShows"


def _queued(resp):
    return "<title>Queue-it</title>" in resp.text[:3000]


def bh_detail(path, tries=3, wait=8):
    for i in range(tries):
        r = fetch(BH + path)
        if not _queued(r):
            return BeautifulSoup(r.text, "html.parser")
        if i < tries - 1:
            time.sleep(wait)
    return None


def bh_parse_detail(soup):
    """-> (performers_text, program[]) from a Benaroya event page's Artists / Program lists."""
    lines = text_lines(soup)
    stops = {"Doors Open", "Run Time", "Pre-Concert Talk", "Dates & Times", "Promo code", "Buy Tickets",
             "Performers", "Artists", "Program", "Tickets from", "Read Full Details"}
    try:
        a = lines.index("Artists") + 1
    except ValueError:
        artists = []
    else:
        artists, chunk = [], []
        for l in lines[a:]:
            if l in stops:
                break
            chunk.append(l)
        artists = [(chunk[i], chunk[i + 1]) for i in range(0, len(chunk) - 1, 2)]
    program = []
    if "Program" in lines:
        chunk = []
        for l in lines[lines.index("Program") + 1:]:
            if l in stops or l.lower().startswith(("intermission", "run time")):
                break
            chunk.append(l)
        program = [{"composer": chunk[i], "work": chunk[i + 1]} for i in range(0, len(chunk) - 1, 2)]
    names = []
    for name, role in artists:
        names.append(name if role in ("Orchestra", "Chorus", "Ensemble", "Quartet") else f"{name}, {role.lower()}")
    return ", ".join(names), program


def bh_category(ev):
    slug = (ev.get("learnMoreUrl") or "").lower()
    venue = ev.get("venue") or ""
    if "-recital-" in slug:
        return "solo"
    if "-octave-" in slug or "Raisbeck" in venue:
        return "chamber"
    if "symphonic" in slug or "pops" in slug or "families" in slug:
        return "symphonic"
    from music_ingest import classify
    cat = classify(ev["title"])
    if cat == "chamber" and ev.get("brand") == "Seattle Symphony":
        return "symphonic"
    if cat == "chamber" and "Taper" in venue and not re.search(r"quartet|trio|duo|quintet|recital", ev["title"], re.I):
        return "symphonic"
    return cat


BROCHURE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "seattle_symphony_season.json")


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def load_brochure():
    """Season brochure data (see music_brochure.py) -> (by_title, by_date). Empty if absent."""
    try:
        with open(BROCHURE_PATH, encoding="utf-8") as f:
            items = json.load(f)
    except (OSError, ValueError):
        return {}, {}
    by_date = {}
    for it in items:
        for d in it["dates"]:
            by_date.setdefault(d, []).append(it)
    return {_norm(it["title"]): it for it in items}, by_date


def brochure_for(e, by_title, by_date):
    """Match a Benaroya feed event to its brochure entry: same title, else the only brochure
    concert on that date (titles differ, e.g. 'Leila Josefowicz Returns' vs the feed's title)."""
    hit = by_title.get(_norm(e["title"]))
    if hit:
        return hit
    if (e.get("brand") or "") == "Seattle Symphony":
        same_day = by_date.get(e["start"][:10], [])
        words = lambda t: {w for w in re.findall(r"[a-z]+", t.lower()) if len(w) > 3}
        close = [it for it in same_day if len(words(it["title"]) & words(e["title"])) >= 2]
        if len(close) == 1:  # titles differ ("Leila Josefowicz Returns") but share >=2 real words
            return close[0]
    return None


def brochure_performers(it):
    out = []
    for p in it.get("performers", []):
        m = re.match(r"^(.*?)\s+(conductor|piano|violin|viola|cello|bass|soprano|mezzo-soprano|alto|tenor|baritone|"
                     r"bass-baritone|flute|saxophone|clarinet|oboe|trumpet|horn|harp|guitar|organ|percussion|vocals|"
                     r"timpani|narrator|host)$", p, re.I)
        out.append(f"{m.group(1)}, {m.group(2).lower()}" if m else p)
    return ", ".join(out)


@scraper("Benaroya Hall")
def benaroya_hall():
    events = {}
    now = datetime.now()
    for k in range(0, 14, 2):  # the API returns ~3 months from `start`; step by 2 and de-dupe
        y, mo = divmod(now.month - 1 + k, 12)
        start = f"{now.year + y}-{mo + 1:02d}-01T00:00:00.000Z"
        payload = dict(keywordId="", genre="", seriesKeywordId="", audienceKeywordId="",
                       accessibilityKeywordId="", timeSlot="", locationKeywordId="", programs="",
                       query="", selectedFilters="[]", start=start, end=start)
        r = requests.post(BH_API, data=payload, headers={"User-Agent": UA}, timeout=60)
        r.raise_for_status()
        for e in r.json():
            events[e["id"]] = e
    by_title, by_date = load_brochure()
    details = {}
    deadline = time.time() + 420  # total budget for detail pages; events still publish without them
    for e in sorted(events.values(), key=lambda e: e["start"]):
        bro = brochure_for(e, by_title, by_date)
        # Classical by the site's genre tag, or a Symphony concert whose brochure entry has a program
        classical = "Classical" in (e.get("genre") or "") or (
            (e.get("brand") or "") == "Seattle Symphony" and bro and bro["program"]
            and "Pop Culture" not in (e.get("genre") or ""))
        if not classical or NON_CONCERT.search(e["title"]) or e.get("isPast"):
            continue
        start = local_dt(e["start"])
        if not start or start < now.replace(hour=0, minute=0):
            continue
        path = e.get("learnMoreUrl")
        if path and path not in details and time.time() < deadline:
            try:
                soup = bh_detail(path)
                details[path] = bh_parse_detail(soup) if soup else ("", [])
            except requests.RequestException:
                details[path] = ("", [])
        artists, program = details.get(path, ("", []))
        if bro and not program:  # the printed season brochure is authoritative when the web page lacked a program
            program = bro["program"]
        if bro and not artists:
            artists = brochure_performers(bro)
        brand = e.get("brand") or ""
        host = brand if brand == "Seattle Symphony" and "Seattle Symphony" not in artists else ""
        performers = ", ".join(x for x in (host, artists) if x) or re.split(r"\s+presents?:?\s*", e["title"], 1)[0]
        yield {
            "source": "Benaroya Hall",
            "source_id": str(e["id"]),
            "title": e["title"],
            "start": start,
            "performers": performers,
            "description": clean(e.get("description"))[:500],
            "program": program,
            "category": bh_category(e),
            "venue": f"{e.get('venue') or ''}, Benaroya Hall".strip(", "),
            "city": "Seattle",
            "country": "USA",
            "region": "seattle",
            "major": brand == "Seattle Symphony",
            "ticket_url": BH + (e.get("buyPageUrl") or path or ""),
        }


# ------------------------------------------------------------------------------
# Philharmonia Northwest  (season page -> /concert-N-2026-27/ pages, uppercase header block)
# ------------------------------------------------------------------------------

@scraper("Philharmonia Northwest")
def philharmonia_northwest():
    base = "https://philharmonianw.org"
    season = soup_of(f"{base}/2026-27-season/")
    urls, names = [], {}
    for a in season.find_all("a", href=re.compile(r"/concert-\d+-")):
        if a["href"] not in urls:
            urls.append(a["href"])
        t = clean(a.get_text())
        if ":" in t and a["href"] not in names:  # "Concert 1: The Art of Defiance"
            names[a["href"]] = t.split(":", 1)[1].strip()
    for url in urls:
        try:
            lines = block_lines(soup_of(url))
        except requests.RequestException:
            continue
        di = next((i for i, l in enumerate(lines)
                   if re.match(r"(MON|TUES|WEDNES|THURS|FRI|SATUR|SUN)DAY,", l)), None)
        if di is None:
            continue
        start = parse_when(lines[di])
        head = []
        for l in reversed(lines[:di]):
            if l != l.upper():
                break
            head.append(l)
        head.reverse()
        if not start or len(head) < 2:
            continue
        title, venue, people = names.get(url) or head[0].title(), head[-1].title(), head[1:-1]
        people = [re.sub(r"^With ", "", p.title()).replace(", Piano", ", piano").replace(", Conductor", ", conductor")
                  for p in people]
        prog_i = next((i for i, l in enumerate(lines) if l.upper().startswith("PROGRAM")), None)
        program = []
        if prog_i is not None:
            end = next((i for i in range(prog_i + 1, len(lines)) if re.match(r"(Note:|SUBSCRIPTIONS)", lines[i])), len(lines))
            program = dash_program(lines[prog_i + 1:end])
        c, region = region_of(venue)
        yield {
            "source": "Philharmonia Northwest",
            "source_id": url,
            "title": title,
            "start": start,
            "performers": "; ".join(["Philharmonia Northwest"] + people),
            "program": program,
            "description": "; ".join(f"{p['composer']}: {p['work']}" for p in program) or None,
            "category": "symphonic",
            "venue": venue,
            "city": c,
            "country": "USA",
            "region": region,
            "major": False,
            "ticket_url": "https://app.arts-people.com/index.php?ticketing=pnw",
        }


# ------------------------------------------------------------------------------
# Cascade Symphony Orchestra  (Edmonds / Lynnwood; /casc_concert/<slug>/ pages)
# ------------------------------------------------------------------------------

@scraper("Cascade Symphony Orchestra")
def cascade_symphony():
    base = "https://cascadesymphony.org"
    home = soup_of(base + "/")
    urls = []
    for a in home.find_all("a", href=re.compile(r"/casc_concert/")):
        if a["href"] not in urls:
            urls.append(a["href"])
    for url in urls:
        try:
            lines = block_lines(soup_of(url))
        except requests.RequestException:
            continue
        di = next((i for i, l in enumerate(lines) if re.match(rf"({_MONTHS})[a-z]* \d{{1,2}}, \d{{4}}$", l)), None)
        if di is None or di + 1 >= len(lines):
            continue
        start = parse_when(f"{lines[di]} {lines[di + 1]}")
        if not start:
            continue
        m = re.match(r".*\bat ([A-Z].*)$", lines[di + 1])
        venue = m.group(1).strip() if m else None
        title = lines[0]
        rest = lines[di + 2:]
        program = dash_program(rest)
        people = [l for l in rest if re.match(rf"^[A-Z][^,–]+, (?:{_INSTR})$", l)
                  or re.search(r"\b(Chorale|Chorus|Choir)\b", l) and len(l) < 40]
        c, region = region_of(venue)
        yield {
            "source": "Cascade Symphony Orchestra",
            "source_id": url,
            "title": title,
            "start": start,
            "performers": "; ".join(["Cascade Symphony Orchestra"] + people),
            "program": program,
            "description": clean(rest[0])[:400] if rest else None,
            "category": classify_title(title),
            "venue": venue,
            "city": c,
            "country": "USA",
            "region": region,
            "major": False,
            "ticket_url": url,
        }


def classify_title(title):
    if re.search(r"chamber|quartet|trio|quintet", title, re.I):
        return "chamber"
    if re.search(r"requiem|mass\b|chorale|chorus|choral", title, re.I):
        return "choral"
    return "symphonic"


# ------------------------------------------------------------------------------
# Generic iCalendar (.ics) reader — for any presenter that publishes a feed
# ------------------------------------------------------------------------------

def ical_events(text):
    """Yield dicts of VEVENT properties (unfolded + unescaped). DTSTART as naive local datetime
    when it carries a TZID or is floating (the feeds we use are venue-local)."""
    text = re.sub(r"\r?\n[ \t]", "", text)  # unfold
    for block in re.findall(r"BEGIN:VEVENT\r?\n(.*?)END:VEVENT", text, re.S):
        ev = {}
        for line in block.splitlines():
            if ":" not in line:
                continue
            key, val = line.split(":", 1)
            name = key.split(";")[0].upper()
            val = (val.replace("\\n", "\n").replace("\\N", "\n").replace("\\,", ",")
                      .replace("\\;", ";").replace("\\\\", "\\"))
            ev.setdefault(name, val)
            if name == "DTSTART":
                ev["_dtstart_params"] = key
        raw = ev.get("DTSTART", "")
        m = re.match(r"(\d{4})(\d{2})(\d{2})(?:T(\d{2})(\d{2})(?:\d{2})?)?(Z)?$", raw)
        if not m:
            continue
        y, mo, d, hh, mm, z = m.groups()
        dt = datetime(int(y), int(mo), int(d), int(hh or 19), int(mm or 30))
        if z:  # UTC -> Pacific (the only zone we serve); good enough for display
            from datetime import timedelta
            dt = dt - timedelta(hours=7 if 3 < dt.month < 11 else 8)
        ev["start"] = dt
        yield ev


def ical_text(html):
    """Description HTML -> plain text, <br>/<p> as newlines."""
    html = re.sub(r"</?(?:h\d|p|div|li|tr)[^>]*>|<br\s*/?>", "\n", html or "")
    soup = BeautifulSoup(html, "html.parser")
    return "\n".join(l.strip() for l in soup.get_text().split("\n"))


_NAME = re.compile(r"^[A-ZÀ-Ý][\w.\'’-]*(?: (?:[A-ZÀ-Ý][\w.\'’-]*|van|von|de|der|di|da|du|la|le|del|dos)){0,4}$")
_PROG_ROW = re.compile(r"^([A-ZÀ-Ý][^,()–—]{2,40}?)\s*(?:,|\s[-–—]\s)\s*(.+?)(?:\s+\(\d{4}(?:[-–]\d{2,4})?\))?$")


def comma_program(text):
    """'Composer, Work (year)' lines under a 'Program' heading -> [{composer, work}]"""
    lines = text.split("\n")
    try:
        i = next(i for i, l in enumerate(lines) if l.strip().lower() in ("program", "program:", "programme"))
    except StopIteration:
        return []
    out = []
    for l in lines[i + 1:]:
        l = l.strip()
        if not l or re.match(r"^(i{1,3}|iv|v|vi{0,3}|ix|x)\.|^(short pause|intermission|-intermission|personnel)", l, re.I):
            continue
        if re.match(r"^(about|notes?|program notes|artists?|biograph)", l, re.I) or len(l) > 160:
            break  # prose (notes/bios) starts here
        m = _PROG_ROW.match(l)
        if m and _NAME.match(m.group(1).strip()) and len(m.group(2)) <= 140 and not m.group(2).endswith("."):
            out.append({"composer": m.group(1).strip(), "work": m.group(2).strip()})
    return out


# ------------------------------------------------------------------------------
# UW School of Music / Meany  (official calendar.ics)
# ------------------------------------------------------------------------------

@scraper("UW School of Music")
def uw_school_of_music():
    from music_ingest import classify
    text = fetch("https://music.washington.edu/calendar.ics").text
    cutoff = datetime.now().replace(hour=0, minute=0)
    for ev in ical_events(text):
        cats = ev.get("CATEGORIES", "")
        title = clean(ev.get("SUMMARY"))
        title = re.sub(r"^[:\s]+", "", title)
        if ("Performances" not in cats or ev["start"] < cutoff or NON_CONCERT.search(title)
                or re.search(r"cancel|postpone|jazz|late night show", title, re.I)):
            continue
        venue, tix = None, ev.get("URL")
        try:  # the feed has no location; the event page does (line after the date line)
            page = soup_of(ev["URL"])
            lines = text_lines(page)
            di = next((i for i, l in enumerate(lines) if re.match(r"\w+day, ", l)), None)
            if di is not None and di + 1 < len(lines) and len(lines[di + 1]) > 3 and lines[di + 1] != "Buy Tickets":
                venue = lines[di + 1].replace("—", " – ")
            a = page.find("a", string=re.compile("Buy Tickets", re.I))
            if a and a.get("href"):
                tix = urljoin("https://music.washington.edu", a["href"])
        except (requests.RequestException, KeyError, TypeError):
            pass
        desc = ical_text(ev.get("DESCRIPTION"))
        program = comma_program(desc)
        first = next((l for l in desc.split("\n") if len(l) > 40), "")
        cat = classify(title, cats)
        if re.search(r"recital|faculty|student", title + cats, re.I) and cat == "chamber":
            cat = "solo" if re.search(r"recital", title, re.I) else cat
        yield {
            "source": "UW School of Music",
            "source_id": ev.get("UID") or f"{title}|{ev['start']:%Y%m%d%H%M}",
            "title": title,
            "start": ev["start"],
            "performers": re.sub(r"^[^:]+:\s*", "", title) if ":" in title else "UW School of Music",
            "description": first[:400] or None,
            "program": program,
            "category": cat,
            "venue": venue or "University of Washington",
            "city": "Seattle",
            "country": "USA",
            "region": "seattle",
            "major": False,
            "ticket_url": tix or "https://music.washington.edu/events",
        }
