"""Assemble data/photo/gallery.json from fineart_build/photo/work.json + photo_build/texts/t*.json."""
import glob, hashlib, json, os, re, subprocess, sys, unicodedata
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), "texts"))
from meta import GENRES, ERAS, MILESTONES
from artists_a import A
from artists_b import B
from who import canon
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = json.load(open(os.path.join(ROOT, "fineart_build/photo/work.json")))
TH = "/private/tmp/claude-501/-Users-whitetower-dev-burrow-owls/717d435b-0809-4761-bc97-df7352efb381/scratchpad/thumbs"
H = {"User-Agent": "BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
OVERRIDE_WHO = {591: ("john-t-daniels", "John T. Daniels"), 828: ("louis-bachrach", "Louis Bachrach"), 1038: ("bob-sandberg", "Bob Sandberg"), 1050: ("rowland-scherman", "Rowland Scherman"),
                1130: ("nasa", "NASA and partners"), 1136: ("charles-c-ebbets", "Charles C. Ebbets")}
EXTRA_B = {"charles-c-ebbets": ("Charles C. Ebbets", 1905, 1978, "USA", "Charles Ebbets was a photographer who took the famous picture of ironworkers eating lunch on a beam above New York in 1932.")}

rows = {}
for f in sorted(glob.glob(os.path.join(os.path.dirname(__file__), "texts", "t0*.json"))):
    for r in json.load(open(f))["rows"]: rows[r[0]] = r

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:60]

def dims(url):
    f = f"{TH}/{hashlib.md5(url.encode()).hexdigest()}.jpg"
    if not os.path.exists(f):
        try: open(f, "wb").write(requests.get(url, headers=H, timeout=40).content)
        except Exception: return None
    out = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", f], capture_output=True, text=True).stdout
    w = re.search(r"pixelWidth: (\d+)", out); h = re.search(r"pixelHeight: (\d+)", out)
    return (int(w.group(1)), int(h.group(1))) if w and h else None

DEFAULT_BIO = {
    "commons": "A photographer who shares pictures freely on Wikimedia Commons.",
}
artists = {}; photos = []; used = set()
for idx in sorted(rows):
    gi, g, n, y, title, why, k = rows[idx][0], rows[idx][1], rows[idx][2], rows[idx][3], rows[idx][4], rows[idx][5], rows[idx][6]
    c = WORK[idx]
    y = y or c["y"]; t = title or c["title"]
    # photographer
    cw = OVERRIDE_WHO.get(idx) or canon(c["who"], t)
    a = []
    if cw:
        key, disp = cw
        if key in A: n_, b_, d_, bi_, bio_ = A[key]
        elif key in B: n_, b_, d_, bi_, bio_ = B[key]
        elif key in EXTRA_B: n_, b_, d_, bi_, bio_ = EXTRA_B[key]
        else:
            n_, b_, d_, bi_ = disp, None, None, ""
            bio_ = DEFAULT_BIO["commons"] if c["src"] == "commons" and y >= 1975 else f"{disp} is credited as the photographer of work held by {c['source']}."
        akey = re.sub(r"\W+", "-", key).strip("-")
        artists.setdefault(akey, {"n": n_, "b": b_, "d": d_, "bi": bi_, "bio": bio_})
        a = [akey]
    # image size
    w_, h_ = c["w"], c["h"]
    if not w_ or not h_:
        dd = dims(c["th"]); w_, h_ = dd if dd else (4, 3)
    hi = c["hi"]
    if "artic.edu/iiif" in hi and c["hw"]: hi = hi.split("/full/")[0] + f"/full/{c['hw']},/0/default.jpg"  # AIC refuses /full/full; an explicit width works
    pid = slug(t) + ("-" + slug(artists[a[0]]["n"].split()[-1]) if a else "")
    pid = pid[:70]; base = pid; i = 2
    while pid in used: pid = f"{base}-{i}"; i += 1
    used.add(pid)
    lic = c["lic"]
    by = ""
    if re.match(r"CC BY", lic or ""):
        by = (artists[a[0]]["n"] if a else re.sub(r"<[^>]+>", "", c.get("by") or "")[:80])
    photos.append(dict(id=pid, t=t, a=a, y=y, d=str(y), g=g, w=w_, h=h_, u=c["u"], th=c["th"], hi=hi, hw=c["hw"] or 0, hh=c["hh"] or 0, p=c["page"], s=c["source"],
                       cr=(c.get("credit") or ""), lic=("Public domain" if lic.startswith(("Public", "No ")) else lic), by=by, why=why, k=k, pr=(c.get("pr") or "")[:80] if c["src"] in ("aic", "cleveland") else "",
                       l=[], c=[], n=1 if n else 0, r=0, _idx=idx, _who=c["who"], _src=c["src"]))

# --- fame rank
ICONS = ["Migrant Mother", "Earthrise", "View from the Window at Le Gras", "The Steerage", "Raising the Flag on Iwo Jima", "The Blue Marble", "Footprint on the Moon", "Buzz Aldrin Salutes the Flag", "Aldrin on the Moon",
         "Boulevard du Temple", "Self-Portrait", "The Horse in Motion", "Sallie Gardner at a Gallop", "Lunch Atop a Skyscraper", "The Tetons and the Snake River", "Kissing the War Goodbye", "The Pillars of Creation",
         "The Hubble Ultra Deep Field", "Addie Card, Age 12", "The Wright Brothers' First Flight", "Farmer Walking in a Dust Storm", "Allie Mae Burroughs", "Sadie Pfeifer, Cotton Mill Spinner", "Frederick Douglass",
         "Abraham Lincoln at Cooper Union", "A Harvest of Death, Gettysburg", "Into the Jaws of Death", "The Valley of the Shadow of Death", "Nikola Tesla in His Laboratory", "First View of the Yosemite Valley",
         "Fountain by Marcel Duchamp", "The Terminal", "Power House Mechanic", "The Cosmic Cliffs", "The Flatiron", "Jackie Robinson", "March on Washington", "Curiosity's First Selfie", "Bruce McCandless Floats Free",
         "Brig on the Water", "The Emir of Bukhara", "Leo Tolstoy in Color", "American Gothic, Washington, D.C.", "Mark Twain in Color", "Charles Darwin", "Sojourner Truth", "Harriet Tubman", "The Hindenburg Disaster",
         "Isadora Duncan at the Parthenon", "The Endurance at Night", "The Daguerreotype Camera", "The Pillars of Creation, 2014", "The Indian Ocean Tsunami", "The Green Comet", "Mount Everest", "Machu Picchu"]
by_title = {}
for p in photos: by_title.setdefault(p["t"], p)
ri = 0
for tname in ICONS:
    p = by_title.get(tname)
    if p and p["r"] == 0: ri += 1; p["r"] = ri
rest = sorted([p for p in photos if p["r"] == 0], key=lambda p: -(WORK[p["_idx"]].get("rank") or 0))
for p in rest: ri += 1; p["r"] = ri

# --- collections
def has(p, rx): return re.search(rx, p["t"] + " " + p["why"], re.I)
def who_is(p, *keys): return any(re.sub(r"\W+", "-", k.replace("_", " ")).strip("-") in p["a"] for k in keys)
CD = []
def col(slug_, name, emoji, blurb, intro, fn, cover=None, limit=None):
    ids = [p["id"] for p in sorted(photos, key=lambda p: (p["y"], p["r"])) if fn(p)]
    if limit: ids = ids[:limit]
    if len(ids) >= 6: CD.append(dict(slug=slug_, name=name, emoji=emoji, blurb=blurb, intro=intro, ids=ids, cover_id=cover))
col("kids", "Photos for Kids", "🧒", "Animals, space, firsts and funny faces, with a challenge to find something in each.", "These are the photographs kids tend to love: animals up close, rockets and rovers, the very first pictures ever taken, and a few surprises. Each one has a \"look closer\" challenge.",
    lambda p: not p["n"] and p["g"] != 4 and (p["g"] == 6 or (p["g"] == 7 and p["y"] >= 1955) or has(p, r"first photograph|oldest|\bdog\b|\bcat\b|baby|babies|elephant|first selfie|Wright")), cover=None)
col("first-photographs", "The First Photographs", "🪞", "Silver plates, paper negatives and the people who were brave enough to sit still.", "These pictures were made in the first twenty-five years of photography, between 1826 and 1850, when making a single picture could take hours of sunshine and a lot of chemistry.", lambda p: p["y"] <= 1850)
col("civil-war", "The American Civil War", "🎖️", "Brady, Gardner, O'Sullivan and Barnard carried cameras to the battlefields.", "The Civil War was the first big American war to be photographed. Cameras were too slow to catch the fighting, so photographers recorded camps, ruins and the places where battles had been fought.", lambda p: 1861 <= p["y"] <= 1866 and (p["g"] == 4 or who_is(p, "m_brady", "a_gardner", "g_barnard", "t o'sullivan") or has(p, "Lincoln")) and "Yosemite" not in p["t"])
col("american-west", "Photographing the American West", "🌄", "Watkins, Jackson, O'Sullivan and Adams showed Americans their own wild lands.", "Before there were highways and airplanes, photographers hauled huge cameras by mule to Yosemite, Yellowstone and the deserts. Their pictures helped people see why wild places were worth protecting.",
    lambda p: has(p, r"Yosemite|Yellowstone|Teton|Sierra Nevada|Kings River|Carson Desert|Taos|Canyon de Chelly|El Capitan|Colorado|national park"))
col("depression", "The Great Depression", "🌾", "The government sent photographers across America to record hard times.", "In the 1930s, a Farm Security Administration photography unit hired Dorothea Lange, Walker Evans and others to record what the Depression and the Dust Bowl did to American families.", lambda p: 1934 <= p["y"] <= 1943 and p["g"] in (0, 3, 2, 8) and p["_src"] in ("commons", "loc") and has(p, r"Depression|Dust|farm|Farm Security|government|mill|Pie Town|Alabama|Oklahoma|California|Hale"))
col("color-before-color-film", "Color Before Color Film", "🌈", "Autochromes, photochroms and three-filter color from a century ago.", "Color photographs are older than you think. The Lumière brothers' Autochrome plates, Prokudin-Gorsky's three-color process and the Swiss photochrom all gave people glimpses of the world in color long before color film.", lambda p: p["y"] < 1950 and has(p, r"Autochrome|Prokudin|photochrom|in color|color photograph|color picture"))
col("women-photographers", "Women Behind the Camera", "📸", "Cameron, Käsebier, Lange, Abbott and more.", "Women were making great photographs from the start. Julia Margaret Cameron began at 48, Gertrude Käsebier ran New York's busiest portrait studio, and Dorothea Lange gave the Depression a face.", lambda p: who_is(p, "j_cameron", "g_käsebier", "d_lange", "m_wolcott", "e_bubley", "berenice-abbott", "toni-frissell", "imogen-cunningham", "a_atkins"))
col("child-labor", "Lewis Hine and the Children of Work", "🏭", "Photographs that helped change the law.", "Between 1908 and 1920 Lewis Hine photographed children working in mills, mines and streets for the National Child Labor Committee. His pictures helped end child labor in the United States.", lambda p: who_is(p, "l_hine"))
col("photo-secession", "Photography as Art", "🎨", "Stieglitz, Steichen, Käsebier, White and Coburn argued that photographs could be art.", "Around 1900, Alfred Stieglitz and a circle of friends began to insist that photographs could be as beautiful as paintings. They made soft, dreamy pictures, then sharp, modern ones.", lambda p: who_is(p, "a_stieglitz", "e_steichen", "g_käsebier", "c_white", "a_coburn", "f_day", "p_strand", "c_white", "f_evans", "frederick-h-evans", "james-craig-annan"))
col("paris", "Paris Through the Lens", "🗼", "Marville, Atget, Nadar and the streets of the City of Light.", "Paris has been photographed since the very beginning. Marville recorded streets before they were torn down, Atget photographed it at dawn, and Nadar took portraits and the first aerial pictures.", lambda p: has(p, r"Paris|Montmartre|Eiffel|Louvre") and p["y"] < 1950)
col("egypt-and-the-nile", "Egypt and the Nile", "🏺", "Sphinxes, temples and Nile travelers' cameras.", "Photographers have been going to Egypt since the 1840s. Du Camp, Frith and Greene hauled cameras up the Nile to photograph temples that were half buried in sand.", lambda p: has(p, r"Egypt|Nile|Sphinx|Nubia|Thebes|Kom Ombo|Medinet|Abu Simbel|Ramses"))
col("asia-through-the-lens", "Asia Through the Lens", "🏯", "India, China, Burma and Japan in the 1800s.", "Photographers like Felice Beato, Samuel Bourne, John Thomson and Raja Deen Dayal made some of the first photographs of India, China and Southeast Asia.", lambda p: has(p, r"India|China|Beijing|Burma|Ceylon|Japan|Lucknow|Shimla|Hyderabad|Pagan|Himalaya") and p["y"] < 1925)
col("space", "Out of This World", "🚀", "From the Moon to the edge of the universe.", "Cameras went to space almost as soon as people did. These photographs, from the first moonwalk to the Webb Space Telescope, show our planet and the cosmos as no one had seen them before.", lambda p: p["g"] == 7 and p["y"] >= 1946)
col("animals-and-nature", "Animals and Nature", "🦋", "Birds, bugs, crystals and creatures, up close.", "Modern cameras can freeze a hummingbird or show the eye of a fly. These photographs from Wikimedia Commons show wild things in sharp detail.", lambda p: p["g"] == 6 and p["y"] >= 1975)
col("famous-faces", "Faces of History", "🧑‍🎤", "Lincoln, Douglass, Darwin, Tubman, Edison, Tolstoy and others.", "Photographs let us look into the eyes of people who lived long ago. These portraits show writers, inventors, leaders and rebels as they really looked.",
    lambda p: has(p, r"^(Abraham Lincoln|Frederick Douglass|Harriet Tubman|Sojourner Truth|Charles Darwin|Thomas Edison|Mark Twain|Leo Tolstoy|Edgar Allan Poe|Alexander Graham Bell|Charles Baudelaire|Alexandre Dumas|Geronimo|Chief Joseph|George Sand|Giuseppe Garibaldi|Babe Ruth|Jackie Robinson|Gustave Doré|Sarah Bernhardt|Auguste Rodin|Georgia O|Lewis Carroll|Andrew Jackson|Alfred, Lord Tennyson|Sir John Herschel|Emperor Bao Dai|Yuri Gagarin|Richard Strauss|H\. G\. Wells|Ezra Pound|Isadora)"))
col("civil-rights-and-freedom", "Faces of Freedom", "✊", "Douglass, Truth, Tubman, Parks, Robinson and the March on Washington.", "People who fought for freedom and equality, from a man who escaped slavery to the crowds who marched on Washington.", lambda p: has(p, r"Frederick Douglass|Sojourner Truth|Harriet Tubman|Tuskegee|March on Washington|Jackie Robinson|American Gothic|Manzanar|Eliza|Tuskegee"))
col("cities", "City Lights and Skyscrapers", "🏙️", "From horse-drawn streets to the Empire State Building.", "As cities grew taller and busier, photographers followed. Stieglitz, Strand, Abbott and Hine showed how new skyscrapers and crowds changed the way people lived.", lambda p: p["g"] == 2 and p["y"] >= 1880 and has(p, r"New York|skyscraper|Fifth Avenue|Flatiron|Empire State|Wall Street|Chicago|Manhattan|Times Square"))
col("war-and-peace", "Wars and Their Aftermath", "🕊️", "From the Crimean War to D-Day.", "Photographers have followed armies since 1855. These pictures show soldiers, ruins and the moments when wars ended, and some are hard to look at.", lambda p: p["g"] == 4)
col("moon", "To the Moon", "🌙", "The Moon, from Apollo to Orion.", "People have looked at the Moon for as long as there have been people. These photographs show the Moon up close, from the first Apollo pictures to the newest spacecraft.", lambda p: has(p, r"Moon|Apollo|lunar") and p["g"] == 7)
for c in CD:
    for pid in c["ids"]: next(p for p in photos if p["id"] == pid)["c"].append(c["slug"])
# cover for collections: pick most famous
by_id = {p["id"]: p for p in photos}
for c in CD:
    c["cover_id"] = min(c["ids"], key=lambda i: by_id[i]["r"])

# --- eras
eras = []
PICKS = [["View from the Window at Le Gras", "Boulevard du Temple", "Self-Portrait", "Newhaven Fishwife", "Earliest Known Photograph of a Living Animal", "Chouteau's Pond, St. Louis", "Frederick Douglass", "Winter Trees Reflected in a Pond"],
         ["The Valley of the Shadow of Death", "A Harvest of Death, Gettysburg", "Abraham Lincoln at Cooper Union", "First View of the Yosemite Valley", "Brig on the Water", "Sojourner Truth", "Sir John Herschel", "The Horse in Motion"],
         ["The Steerage", "Addie Card, Age 12", "Old Faithful", "The Terminal", "Bandits' Roost", "Sun Rays — Paula, Berlin", "The Wright Brothers' First Flight", "Nikola Tesla in His Laboratory"],
         ["The Emir of Bukhara", "Isadora Duncan at the Parthenon", "Power House Mechanic", "Fountain by Marcel Duchamp", "Lunch Atop a Skyscraper", "The Endurance at Night", "Boulevard Haussmann", "Georgia O'Keeffe"],
         ["Migrant Mother", "Raising the Flag on Iwo Jima", "Kissing the War Goodbye", "Into the Jaws of Death", "American Gothic, Washington, D.C.", "The Hindenburg Disaster", "Allie Mae Burroughs", "Farmer Walking in a Dust Storm"],
         ["Earthrise", "Footprint on the Moon", "Buzz Aldrin Salutes the Flag", "The Blue Marble", "Jackie Robinson", "March on Washington", "Yuri Gagarin", "Self-Portrait on Geary Street"],
         ["The Pillars of Creation, 2014", "The Cosmic Cliffs", "The Hubble Ultra Deep Field", "Curiosity's First Selfie", "Earthset from Orion", "The Indian Ocean Tsunami", "The Green Comet", "Machu Picchu"]]
for e, picks in zip(ERAS, PICKS):
    ids = [by_title[t]["id"] for t in picks if t in by_title]
    eras.append(dict(slug=e["slug"], name=e["name"], emoji=e["emoji"], start=e["start"], end=e["end"], blurb=e["blurb"], intro=e["intro"], pr_note=e["pr_note"], pick_ids=ids))

for p in photos:
    for k_ in ("_idx", "_who", "_src"): p.pop(k_)
first = by_title.get("View from the Window at Le Gras")
out = dict(genres=GENRES, eras=eras, milestones=[{"y": y, "text": t} for y, t in MILESTONES], artists=artists, photos=photos, collections=CD, first_id=first["id"] if first else photos[0]["id"])
os.makedirs(os.path.join(ROOT, "data/photo"), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, "data/photo/gallery.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(len(photos), "photos", len(artists), "artists", len(CD), "collections")
for c in CD: print(" ", c["slug"], len(c["ids"]))
import collections
print(collections.Counter(next(e["slug"] for e in eras if e["start"] <= p["y"] <= e["end"]) for p in photos))
