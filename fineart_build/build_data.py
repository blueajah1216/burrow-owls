"""Merge Wikidata/Commons facts (base2.json, base3.json) with hand-written text in out/ into data/fineart/gallery.json."""
import json, glob, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
L = lambda f: json.load(open(f"{HERE}/{f}"))
b2, b3 = L("base2.json"), L("base3.json")
b4 = L("base4.json") if os.path.exists(f"{HERE}/base4.json") else {"paintings": [], "artists": {}}
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
if os.path.exists(f"{HERE}/out/locations_hist.json"): locs |= L("out/locations_hist.json")
if os.path.exists(f"{HERE}/out/fixes_hist.json"):
    for k, v in L("out/fixes_hist.json").items(): fixes.setdefault(k, {}).update(v)
NAMES = {"Q155626": "John Singer Sargent", "Q380494": "Charles Demuth", "Q44007": "Paul Klee", "Q45006": "Franz von Stuck", "Q466639": "Olga Boznańska", "Q7724": "August Strindberg",
         "Q3109429": "Nishikawa Sukenobu", "Q910913": "Kuroda Seiki", "Q983949": "Józef Chełmoński"}
text, arttext = {}, {}
for f in sorted(glob.glob(f"{HERE}/out/paintings_*.json")) + sorted(glob.glob(f"{HERE}/out/new_*.json")) + sorted(glob.glob(f"{HERE}/out/hist_[0-9]*.json")) + sorted(glob.glob(f"{HERE}/out/style_[0-9]*.json")) + sorted(glob.glob(f"{HERE}/out/old_[0-9]*.json")):
    for row in json.load(open(f)):
        if not row[3].startswith("Skip"): text[row[0]] = row[1:]
patch = L("out/text_patch.json")
for i, w in patch.items():
    if i in text: text[i][2] = w
for f in sorted(glob.glob(f"{HERE}/out/artists_*.json")) + sorted(glob.glob(f"{HERE}/out/hist_artists_*.json")) + sorted(glob.glob(f"{HERE}/out/style_artists_*.json")) + sorted(glob.glob(f"{HERE}/out/old_artists_*.json")):
    for row in json.load(open(f)): arttext[row[0]] = row[1]
extra = L("out/artist_extra.json") if os.path.exists(f"{HERE}/out/artist_extra.json") else {}
kids = {r[0]: r[1] for r in L("out/kids.json")}

# ---- artists
A = {}
for src in (b2["artists"], b3["artists"], b4["artists"]):
    for q, x in src.items():
        A.setdefault(q, {}).update({k: v for k, v in x.items() if v})
for q, n in NAMES.items():
    A.setdefault(q, {})["name"] = n
if os.path.exists(f"{HERE}/out/hist_artist_fix.json"):
    for q, v in L("out/hist_artist_fix.json").items():
        for k, val in v.items():
            if val is None: A.setdefault(q, {}).pop(k, None)
            else: A.setdefault(q, {})[k] = val
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
    if r.get("med"): o["m"] = r["med"]
    if r["id"] in locs:
        o["l"] = [("China" if x == "People's Republic of China" else x) for x in locs[r["id"]]]
    items.append((r, o))
for r in b2["paintings"]: add(r, False)
for r in b3["paintings"]: add(r, True)
for r in b4["paintings"]: add(r, True)
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

# ---- Styles & movements
sys.path.insert(0, f"{HERE}/styles")
from styles_rules import STYLES
from abstract_picks import SECTIONS
STYLE_BLURBS = {
 "impressionism": ("Quick brushstrokes, sparkling light and everyday moments: the painters who stopped trying to hide their brushwork.", "In the 1860s and 70s a group of Paris painters left their studios and painted outside, catching the light of a single moment. Critics laughed and named them after one of Monet's paintings, Impression, Sunrise. Look for dabs of color that blend only when you step back."),
 "post-impressionism": ("Van Gogh's swirls, Cézanne's apples, Gauguin's flat color: artists who took Impressionism somewhere new.", "After Impressionism, painters wanted to say more than just how a moment looked. Van Gogh turned feelings into thick swirling brushstrokes, Cézanne built pictures from solid shapes, Seurat used tiny dots and Gauguin used flat, bold color."),
 "romanticism": ("Wild storms, misty mountains and big feelings: nature and imagination in charge.", "Romantic painters believed feelings mattered more than rules. They painted shipwrecks, thunderstorms, haunted ruins and lonely figures staring at huge landscapes, to make you feel how small and amazed a person can be."),
 "realism": ("Real people, real work, real life: painters who showed the world as it is.", "Realist painters decided that farmers, stone breakers and city crowds were as worthy of a big painting as kings and gods. They painted what they saw, with no prettying-up."),
 "neoclassicism": ("Heroes in togas, perfect poses and Greek and Roman stories: clear, balanced and carefully painted.", "In the late 1700s and 1800s artists copied the order and calm of ancient Greece and Rome. This collection covers Neoclassicism and the polished academic painters who followed, famous for smooth finish and big stories from history and myth."),
 "pre-raphaelites": ("Knights, maidens, mermaids and jewel-bright colors: dreamy Victorian storytelling.", "In 1848 a group of young English painters, the Pre-Raphaelite Brotherhood, wanted to paint with the honest detail and bright color of art before Raphael. They filled pictures with legends, poems and gorgeous flowers. Later painters carried on the dream."),
 "symbolism": ("Dreams, moods and mysteries: artists who painted ideas and feelings you can't quite name.", "Symbolist and Art Nouveau artists painted dreams, myths and moods, and swirled flowing lines through posters, jewelry and buildings. Look for gold, mysterious faces and curving, plant-like shapes."),
 "expressionism": ("Paint it how it feels: wild color, bold lines and strong emotion.", "Expressionist and Fauvist painters used color and shape to show feelings. Matisse and the Fauves, called wild beasts by a critic, painted in bright, flat color. In Germany and Austria, Expressionists turned anxiety, joy and energy into paint."),
 "hudson-river": ("Glowing mountains, waterfalls and endless skies: the great American landscape painters.", "In the 1800s painters of the Hudson River School showed America as a wild, glowing paradise, with huge skies, peaks and rivers. They traveled far to sketch the real places, then made giant pictures that made people proud of their land."),
 "ukiyo-e": ("Great waves, rainy bridges and kabuki stars: Japan's woodblock prints that stunned Europe.", "Ukiyo-e means pictures of the floating world. Artists drew a design, carvers cut it into wooden blocks and printers pressed the colors one at a time, making cheap prints for everyone. They inspired Monet and Van Gogh."),
 "renaissance": ("Leonardo, Raphael, Botticelli, Van Eyck, Dürer: the artists who brought back the beauty of the ancient world and learned to paint space, light and real people.", "Around 1400 painters and sculptors in Florence began to study nature, the human body and the rules of perspective, so that pictures looked like windows into the real world. Leonardo, Michelangelo and Raphael became legends, while in Flanders Jan van Eyck's oil paint caught every glint of a jewel. Look for calm triangles of figures, soft landscapes and faces full of feeling."),
 "baroque": ("Spotlights, storms of motion and big emotions: Caravaggio, Rubens, Velázquez and Artemisia Gentileschi.", "Baroque painters of the 1600s wanted to make you feel something. They used deep shadow and spotlights, twisting bodies and swirling clouds, and they painted saints and heroes as real, sweaty, passionate people. Look for the single beam of light, the diagonal lines and the moment right before something happens."),
 "dutch-golden-age": ("Rembrandt, Vermeer and Frans Hals: when the Netherlands was rich and painted its own homes, ships, tulips and faces.", "In the 1600s the Dutch Republic was one of the richest places on Earth, and ordinary merchants bought pictures for their homes. Painters turned to portraits, quiet rooms, stormy seas, ice-skating villages and still lifes of cheese and oysters. Look for window light, tiny details and clever hidden symbols."),
 "rococo": ("Pastel elegance, flirty swings and fancy portraits: art of the 1700s.", "The 1700s loved lightness: pink and blue colors, curling frills, picnics, portraits and glittering views of Venice. Look for playful details and fancy clothes."),
}
ABS_BLURB = "Pictures that don't show things, but color, shape and feeling: Kandinsky, Mondrian, Klee, Hilma af Klint and many more."
ABS_INTRO = "Abstract art is painting without a picture of something. Instead of a person, tree or boat, you get colors, lines and shapes that make you feel something, like music you can see. A few artists in the early 1900s, in Munich, Moscow, Paris and Stockholm, realized that paint didn't have to copy the world. This collection takes you from the painters who were nearly there, through the pioneers, to playful corners like Klee's cats and fish and Schwitters's collages made from trash. Try asking: what does this sound like? What would it feel like to step inside?"
qid2pid = {r["qid"]: o["id"] for r, o in items if r.get("qid")}
def abs_ids(lst):
    out = []
    for x in lst:
        pid = qid2pid.get(x, x) if re.match(r"^Q\d+$", x) else x
        if pid in byid and not byid[pid].get("n") and pid not in out: out.append(pid)
    return out
sections = [{"title": t, "blurb": b, "ids": abs_ids(l)} for t, b, l in SECTIONS]
sections = [s_ for s_ in sections if s_["ids"]]
all_abs = [i for s_ in sections for i in s_["ids"]]
cols.append({"slug": "abstract", "group": "styles", "emoji": "🌀", "name": "Abstract Art", "blurb": ABS_BLURB, "intro": ABS_INTRO, "ids": list(dict.fromkeys(all_abs)), "sections": sections, "featured": True, "cover_id": "several-circles", "covers": ["several-circles", "the-ten-largest-no-3-youth", "composition-with-large-red-plane-yellow-black-grey-and-", "fish-magic"]})
for i in dict.fromkeys(all_abs): byid[i].setdefault("c", []).append("abstract")
for slug, emoji, name, names, (y0, y1) in STYLES:
    cap = 12 if slug in ("impressionism", "post-impressionism", "romanticism", "realism", "neoclassicism", "rococo") else 15
    per, ids = {}, []
    for p in sorted(paintings, key=lambda p: p["r"]):
        if p.get("n") or not (y0 <= p["y"] <= y1): continue
        a0 = artists_pre.get(p["a"][0], {}).get("n", "") if False else A.get(p["a"][0], {}).get("name", "")
        if not any(n.lower() in a0.lower() for n in names): continue
        if per.get(a0, 0) >= cap: continue
        per[a0] = per.get(a0, 0) + 1; ids.append(p["id"])
        if len(ids) >= 90: break
    if len(ids) < 8: continue
    blurb, intro = STYLE_BLURBS[slug]
    cols.append({"slug": slug, "group": "styles", "emoji": emoji, "name": name, "blurb": blurb, "intro": intro, "ids": ids})
    for i in ids: byid[i].setdefault("c", []).append(slug)

used = {a for p in paintings for a in p["a"]}
artists = {}
for a in used:
    x = A[a]
    bio = arttext.get(a, "(biography coming soon)") + (" " + extra[a] if a in extra else "")
    artists[a] = {"n": x.get("name", a), "b": yr(x.get("birth")), "d": yr(x.get("death")), "bi": x.get("born_in", ""), "di": x.get("died_in", ""), "bio": bio}
# ---- Art Through History
def build_history():
    sys.path.insert(0, f"{HERE}/hist")
    from events import ERAS, EV
    from events_text import T
    R = L("hist/resolved.json")
    notes = L("out/hist_notes.json") if os.path.exists(f"{HERE}/out/hist_notes.json") else {}
    covers = L("hist/covers.json") if os.path.exists(f"{HERE}/hist/covers.json") else {}
    def span_ok(p): return 1000 <= p["w"] and 0.7 <= p["w"] / p["h"] <= 2.2
    events = []
    for slug, era, title, start, end, _terms in EV:
        items = []
        for d in R.get(slug, []):
            pid = d.get("gal") or d["new"]["id"]
            if pid not in byid: continue
            note = d.get("note") or notes.get(f"{slug}/{pid}") or ""
            if not note:  # fall back to the first sentence of the painting's own description
                first = re.split(r"(?<=[.!?])\s+", byid[pid]["why"].strip())[0]
                note = first if len(first) <= 230 else ""
            items.append({"id": pid, **({"note": note} if note else {})})
        pool = [i for i in items if not byid[i["id"]].get("n")]
        cover = covers.get(slug) if covers.get(slug) in byid else next((i["id"] for i in pool if span_ok(byid[i["id"]])), pool[0]["id"] if pool else None)
        events.append({"slug": slug, "era": era, "title": title, "start": start, "end": end, "summary": T[slug][0], "why": T[slug][1], "cover": cover, "items": items})
    eras = [{"id": i, "name": n, "sub": s, "color": c} for i, n, s, c in ERAS]
    json.dump({"eras": eras, "events": events}, open(f"{HERE}/../data/fineart/history.json", "w"), ensure_ascii=False, separators=(",", ":"))
    print("history:", len(events), "events,", sum(len(e["items"]) for e in events), "items;", "short:", [(e["slug"], len(e["items"])) for e in events if sum(1 for i in e["items"]) < 10])

os.makedirs(f"{HERE}/../data/fineart", exist_ok=True)
json.dump({"genres": GENRES, "collections": cols, "artists": artists, "paintings": paintings}, open(f"{HERE}/../data/fineart/gallery.json", "w"), ensure_ascii=False, separators=(",", ":"))
print(len(paintings), "paintings,", len(artists), "artists,", len(cols), "collections;", {c["slug"]: len(c["ids"]) for c in cols})
print("missing bios:", [artists[a]["n"] for a in artists if "coming soon" in artists[a]["bio"]])
build_history()
