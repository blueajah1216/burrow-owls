"""Merge Wikidata/Commons facts (base2.json, base3.json) with hand-written text in out/ into data/fineart/gallery.json."""
import json, glob, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
L = lambda f: json.load(open(f"{HERE}/{f}"))
b2, b3 = L("base2.json"), L("base3.json")
sel_d = L("sel.json"); SEL, POOL = sel_d["sel"], sel_d["pool"]

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
COLLECTIONS = [  # slug, group, emoji, name, blurb, intro
 ("kids","kids","🧒","Art for Kids","The 100 most fun paintings for young explorers: animals, fairy tales, circuses, storms and wonders.","Welcome, young explorers! These 100 paintings are picked for you: tigers in thunderstorms, mermaids, a giant wave, 42 cats and a spinning top. Each one has a little challenge — can you find what the painter hid?"),
 ("jewish","heritage","✡️","Jewish Artists","Paintings by Jewish artists across Europe and beyond, from Amsterdam to Montmartre to Jerusalem.","These painters came from Jewish families in Germany, the Netherlands, Poland, Russia, France, Italy and beyond. Some painted Jewish life and history; many painted whatever they loved — fishermen, gardens, city streets and friends. Together, they show how much Jewish artists helped shape modern art."),
 ("canada","heritage","🇨🇦","Canada","From Tom Thomson's wild north to Krieghoff's snowy Quebec: Canada's most important early paintings.","Canada's art begins with explorers and Indigenous portraits, grows through the snowy villages of Quebec and ends with the Group of Seven's wild north. Here are the paintings that taught Canadians to see their own land. Some paintings show Indigenous peoples as artists of the time saw them, so it's worth asking whose story is being told."),
 ("norway","heritage","🇳🇴","Norway","Fjords, Vikings, trolls and Munch: the great paintings of Norway.","Norway's painters gave the world dramatic fjords and misty mountains, the Vikings of the sagas, cozy farmhouse lights and the famously haunting art of Edvard Munch. Many of these artists also worked in Denmark and Germany, where Norwegian painters often trained."),
 ("usa","heritage","🇺🇸","United States","Great American paintings: wild landscapes, sea storms, Revolutionary heroes and the artists who made America look like itself.","From the Hudson River School's glowing wilderness to Winslow Homer's stormy seas, from Revolutionary War heroes to Mary Cassatt's quiet rooms, these are the great American paintings from the nation's first 150 years."),
 ("fr","world","🇫🇷","France","Impressionists, revolutionaries and the heart of modern art.","France gave us Impressionism, Romanticism and many of history's best-known paintings."),
 ("it","world","🇮🇹","Italy","Italian painters of the last 300 years, from Venice to Milan.","Italy's art after the Renaissance kept going: romantic lovers, sunlit Alpine peaks and shimmering portraits."),
 ("es","world","🇪🇸","Spain","Goya, Sorolla and the painters of Spain.","From Goya's court portraits and dark visions to Sorolla's dazzling beaches."),
 ("nl","world","🇳🇱","Netherlands","Van Gogh, the Hague School and Dutch painters.","The land of windmills, canals and Van Gogh's swirling skies."),
 ("de","world","🇩🇪","Germany","Romantic mountains, expressive colors and German painters.","Germany's painters gave us misty Romantic mountains, wild Expressionist colors and dreamlike modern art."),
 ("uk","world","🇬🇧","United Kingdom","Turner's storms, Pre-Raphaelite fairy tales and England's great portraits.","British painters loved storms, fairy tales, portraits and the English countryside."),
 ("ru","world","🇷🇺","Russia","Giant historical canvases, forests and snowy landscapes from Russia.","Russian painters made huge, emotional pictures of history, forests, rivers and the lives of ordinary people."),
 ("pl","world","🇵🇱","Poland","Poland's proud history in paint.","Polish painters kept their country's history alive in huge canvases, countryside scenes and portraits."),
 ("se","world","🇸🇪","Sweden","Midsummer dances, cozy homes and Nordic light.","Sweden's painters made sparkling summer pictures, family homes full of sunlight and scenes from Norse legends."),
 ("dk","world","🇩🇰","Denmark","The Danish Golden Age and the artists of Skagen.","Quiet Copenhagen rooms, sunny beaches at Skagen and some of the calmest paintings ever made."),
 ("fi","world","🇫🇮","Finland","Finnish heroes, forests and the Kalevala.","Finnish painters turned their national legends and lakeside forests into glowing pictures."),
 ("at","world","🇦🇹","Austria","Vienna's golden age of painting.","Austrian art sparkled in turn-of-the-century Vienna with gold leaf, bold lines and dreamy patterns."),
 ("be","world","🇧🇪","Belgium","Masks, Symbolists and Belgian painters.","Belgium's painters gave us carnival masks, mysterious Symbolist dreams and sunlit gardens."),
 ("ch","world","🇨🇭","Switzerland","Alpine peaks and playful modern art from Switzerland.","Mountains, myths and Paul Klee's playful lines."),
 ("jp","world","🇯🇵","Japan","Woodblock prints, folding screens and the painters of Japan.","Japan's artists gave the world The Great Wave, golden folding screens, puppies, cats and ghosts. This collection includes woodblock prints as well as paintings, since prints were one of Japan's great art forms."),
 ("cn","world","🇨🇳","China","Imperial court paintings from the Qing dynasty.","Huge scrolls, emperors on horseback and bustling cities from the court of the Qing emperors."),
 ("middle-east","world","🕌","Middle East","Painters from Turkey and Iran.","Ottoman and Persian painters who studied European techniques and painted their own world: palaces, courtyards and quiet moments."),
 ("mx","world","🇲🇽","Mexico","Volcano landscapes and folk traditions from Mexico.","Mexican painters celebrated their volcanoes, valleys and traditions like the Day of the Dead."),
 ("au","world","🇦🇺","Australia","Sunburnt landscapes, sheepshearers and the Heidelberg School.","Australian painters like Tom Roberts and Arthur Streeton painted the golden bush and the working people of the outback."),
 ("br","world","🇧🇷","Brazil","Brazil's great history paintings.","Painters of Brazil's independence, first Mass and famous battles."),
]

fixes = L("out/fixes.json"); locs = L("out/locations.json")
NAMES = {"Q155626": "John Singer Sargent", "Q380494": "Charles Demuth", "Q44007": "Paul Klee", "Q45006": "Franz von Stuck", "Q466639": "Olga Boznańska", "Q7724": "August Strindberg",
         "Q3109429": "Nishikawa Sukenobu", "Q910913": "Kuroda Seiki", "Q983949": "Józef Chełmoński"}
text, arttext = {}, {}
for f in sorted(glob.glob(f"{HERE}/out/paintings_*.json")) + sorted(glob.glob(f"{HERE}/out/new_*.json")):
    for row in json.load(open(f)):
        if not row[3].startswith("Skip"): text[row[0]] = row[1:]
patch = L("out/text_patch.json")
for i, w in patch.items():
    if i in text: text[i][2] = w
for f in sorted(glob.glob(f"{HERE}/out/artists_*.json")):
    for row in json.load(open(f)): arttext[row[0]] = row[1]
extra = L("out/artist_extra.json") if os.path.exists(f"{HERE}/out/artist_extra.json") else {}
kids = {r[0]: r[1] for r in L("out/kids.json")}

# ---- artists
A = {}
for src in (b2["artists"], b3["artists"]):
    for q, x in src.items():
        A.setdefault(q, {}).update({k: v for k, v in x.items() if v})
for q, n in NAMES.items():
    A.setdefault(q, {})["name"] = n
def yr(s): return int(s[:4]) if s and re.match(r"^-?\d{4}", s) else None

# ---- paintings
items = []
def add(r, new):
    t = text.get(r["id"])
    if not t and "--all" not in sys.argv: return
    if fixes.get(r["id"], {}).get("drop"): return
    g, n, why = t if t else [9, 0, "(description coming soon)"]
    for k, v in fixes.get(r["id"], {}).items():
        if k == "n": n = v
        else: r[{"t": "title", "y": "year"}.get(k, k)] = v
    o = {"id": r["id"], "t": r["title"], "a": r["artist_ids"], "y": r["year"], "g": g - 1, "w": r["w"], "h": r["h"],
         "u": r["thumb"].split("?")[0], "p": r["page"], "m": "", "why": why, "sl": r["sl"]}
    if n: o["n"] = 1
    if r["id"] in locs:
        o["l"] = [("China" if x == "People's Republic of China" else x) for x in locs[r["id"]]]
    items.append((r, o))
for r in b2["paintings"]: add(r, False)
for r in b3["paintings"]: add(r, True)
items.sort(key=lambda x: (-x[1]["sl"], x[1]["y"]))
paintings = []
for rank, (r, o) in enumerate(items):
    o["r"] = rank; del o["sl"]; paintings.append(o)
byid = {p["id"]: p for p in paintings}
qid2id = {r["qid"]: o["id"] for r, o in items}

# ---- collections
cols = []
for slug, group, emoji, name, blurb, intro in COLLECTIONS:
    if slug == "kids":
        ids = [i for i in kids if i in byid and not byid[i].get("n")]
    else:
        ids = [qid2id[q] for q in SEL.get({"jp": "japan", "cn": "china", "mx": "mexico"}.get(slug, slug), []) if q in qid2id and not byid[qid2id[q]].get("n")]
    if len(ids) < 8 and group == "world": continue
    cols.append({"slug": slug, "group": group, "emoji": emoji, "name": name, "blurb": blurb, "intro": intro, "ids": ids})
    for i in ids:
        byid[i].setdefault("c", []).append(slug)
for i, k in kids.items():
    if i in byid: byid[i]["k"] = k

used = {a for p in paintings for a in p["a"]}
artists = {}
for a in used:
    x = A[a]
    bio = arttext.get(a, "(biography coming soon)") + (" " + extra[a] if a in extra else "")
    artists[a] = {"n": x.get("name", a), "b": yr(x.get("birth")), "d": yr(x.get("death")), "bi": x.get("born_in", ""), "di": x.get("died_in", ""), "bio": bio}
os.makedirs(f"{HERE}/../data/fineart", exist_ok=True)
json.dump({"genres": GENRES, "collections": cols, "artists": artists, "paintings": paintings}, open(f"{HERE}/../data/fineart/gallery.json", "w"), ensure_ascii=False, separators=(",", ":"))
print(len(paintings), "paintings,", len(artists), "artists,", len(cols), "collections;", {c["slug"]: len(c["ids"]) for c in cols})
print("missing bios:", [artists[a]["n"] for a in artists if "coming soon" in artists[a]["bio"]])
