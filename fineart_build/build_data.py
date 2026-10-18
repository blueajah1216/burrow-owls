"""Merge base2.json (Wikidata/Commons facts) with hand-written text in out/ into data/fineart/gallery.json."""
import json, glob, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(f"{HERE}/base2.json"))
P, A = d["paintings"], d["artists"]

GENRES = [
    {"key": "portraits",  "name": "Portraits",            "emoji": "🖼️", "color": "#ff8fa3", "blurb": "Faces from long ago that still seem to look back at you."},
    {"key": "landscapes", "name": "Landscapes & Cities",  "emoji": "🏔️", "color": "#7ee0a5", "blurb": "Mountains, meadows, streets and skies."},
    {"key": "seas",       "name": "Seas & Ships",         "emoji": "⛵", "color": "#5fd3ff", "blurb": "Storms, sailors, harbors and endless waves."},
    {"key": "life",       "name": "Everyday Life",        "emoji": "☕", "color": "#ffd166", "blurb": "Ordinary moments that became extraordinary."},
    {"key": "myth",       "name": "Myths & Legends",      "emoji": "🐉", "color": "#c79bff", "blurb": "Gods, heroes, monsters and magic."},
    {"key": "history",    "name": "History & Battles",    "emoji": "⚔️", "color": "#ff9f6b", "blurb": "Great events frozen in paint."},
    {"key": "faith",      "name": "Faith & Scripture",    "emoji": "🕊️", "color": "#f4e29a", "blurb": "Stories from the Bible and sacred traditions."},
    {"key": "still",      "name": "Still Life & Animals", "emoji": "🍎", "color": "#ff7b6b", "blurb": "Flowers, fruit, horses, hounds and more."},
    {"key": "dreams",     "name": "Dreams & Big Ideas",   "emoji": "🌀", "color": "#8da2ff", "blurb": "Symbols, feelings and wild new ways of seeing."},
]

text, arttext = {}, {}
for f in sorted(glob.glob(f"{HERE}/out/paintings_*.json")):
    for row in json.load(open(f)):
        text[row[0]] = row[1:]
for f in sorted(glob.glob(f"{HERE}/out/artists_*.json")):
    for row in json.load(open(f)):
        arttext[row[0]] = row[1]

fixes = json.load(open(f"{HERE}/out/fixes.json"))
NAMES = {"Q155626": "John Singer Sargent", "Q380494": "Charles Demuth", "Q44007": "Paul Klee", "Q45006": "Franz von Stuck", "Q466639": "Olga Boznańska", "Q7724": "August Strindberg"}
for q, n in NAMES.items():
    if q in A: A[q]["name"] = n
for r in P:
    for k, v in fixes.get(r["id"], {}).items():
        r[{"t": "title", "y": "year"}.get(k, k)] = v

def yr(s): return int(s[:4]) if s and re.match(r"^-?\d{4}", s) else None
paintings = []
for rank, r in enumerate(P):
    t = text.get(r["id"])
    if not t and "--all" not in sys.argv and "--preview" not in sys.argv: continue
    g, n, why = (t if t else [8, 0, "(description coming soon)"])
    o = {"id": r["id"], "t": r["title"], "a": r["artist_ids"], "y": r["year"], "g": g - 1, "w": r["w"], "h": r["h"],
         "u": r["thumb"].split("?")[0], "p": r["page"], "m": (r["collection"] or [""])[0], "why": why, "r": rank}
    if n: o["n"] = 1
    paintings.append(o)
used = {a for p in paintings for a in p["a"]}
artists = {}
for a in used:
    x = A[a]
    artists[a] = {"n": x["name"], "b": yr(x.get("birth")), "d": yr(x.get("death")), "bi": x.get("born_in", ""), "di": x.get("died_in", ""),
                  "bio": arttext.get(a, "(biography coming soon)")}
os.makedirs(f"{HERE}/../data/fineart", exist_ok=True)
json.dump({"genres": GENRES, "artists": artists, "paintings": paintings}, open(f"{HERE}/../data/fineart/gallery.json", "w"), ensure_ascii=False, separators=(",", ":"))
print(len(paintings), "paintings", len(artists), "artists; missing text:", sum(1 for r in P if r["id"] not in text), "paintings,", sum(1 for a in used if a not in arttext), "artists")
