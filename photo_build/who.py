"""Normalise messy 'who' strings from Commons/museum metadata into (key, display name)."""
import html, re
from artists_a import A

def pk(x):
    p = x.split()
    return (p[0][0].lower() + " " + p[-1].lower()) if len(p) > 1 else x.lower()

RULES = [  # (regex on cleaned string, canonical key or display)
    (r"niépce|niepce", "n niépce"), (r"daguerre\b", "l daguerre"), (r"fox talbot|\btalbot\b", "w talbot"), (r"bayard", "h bayard"), (r"hill.*adamson|adamson|^david octavius hill", "d hill"),
    (r"cameron", "j cameron"), (r"fenton", "r fenton"), (r"\bnadar\b|tournachon", "nadar"), (r"brady|handy", "m brady"), (r"gardner", "a gardner"), (r"o.?sullivan", "t o'sullivan"),
    (r"barnard", "g barnard"), (r"watkins", "c watkins"), (r"muybridge", "e muybridge"), (r"jackson", None), (r"le gray|legray|gray, gustave", "g gray"), (r"marville", "c marville"),
    (r"beato", "f beato"), (r"bourne", "s bourne"), (r"john thomson", "j thomson"), (r"dayal", "r dayal"), (r"\briis\b", "j riis"), (r"\bhine\b", "l hine"), (r"curtis", "e curtis"),
    (r"stieglitz", "a stieglitz"), (r"steichen", "e steichen"), (r"käsebier|kasebier", "g käsebier"), (r"holland day", "f day"), (r"clarence h", "c white"), (r"atget", "e atget"),
    (r"emerson", "p emerson"), (r"henry peach robinson", "h robinson"), (r"rejlander", "o rejlander"), (r"carroll|dodgson", "l carroll"), (r"marey", "e marey"), (r"prokudin|прокудин", "s prokudin-gorsky"),
    (r"genthe", "a genthe"), (r"paul strand", "p strand"), (r"\blange\b", "d lange"), (r"walker evans|evans, walker", "w evans"), (r"rothstein", "a rothstein"), (r"russell lee|lee, russell", "r lee"),
    (r"delano", "j delano"), (r"wolcott", "m wolcott"), (r"vachon", "j vachon"), (r"bubley", "e bubley"), (r"gordon parks|parks, gordon", "g parks"), (r"palmer", "a palmer"),
    (r"ansel adams|adams, ansel", "a adams"), (r"coburn", "a coburn"), (r"man ray", "m ray"), (r"frederick h\. evans|evans, frederick", "f evans"),
]
SPECIAL = [  # (regex, (key, display))
    (r"nasa|jpl|hubble|webb|\besa\b|\beso\b|apollo|msfc|goddard|ingalls|schmaltz|stöckli|stockli|salzgeber_", ("nasa", "NASA and partners")),
    (r"u\.?s\.? navy|navy photo|cmdr|photographer.s mate", ("us-navy", "U.S. Navy photographers")),
    (r"air force|airmen", ("us-air-force", "U.S. Air Force photographers")),
    (r"national archives|archives", ("us-archives", "U.S. National Archives")),
]
def clean(s):
    s = html.unescape(s or "")
    s = re.sub(r"<[^>]*>", " ", s)
    s = re.split(r";|\n", s)[0]
    s = re.sub(r"\(.*?\)|\[.*?\]|https?://\S+|www\.\S+", "", s)
    s = re.sub(r"^(Creator|User|Photographer|Image by|Photo by|Autochrome by|Credit|Lt\.|Cmdr\.)[: ]*", "", s.strip(), flags=re.I)
    s = re.split(r" / | and the | & ", s)[0] if re.search(r"(NASA|Hine|Lange|Curtis|Cuerden)", s) is None else s
    return re.sub(r"\s+", " ", s).strip(" .,:/")

def canon(who, title=""):
    raw = html.unescape(who or "")
    low = clean(raw).lower()
    if not low or re.search(r"unknown|anonym|unattributed|not credited|photographer not", raw, re.I) and not re.search(r"[A-Z][a-z]+ [A-Z][a-z]+", re.sub(r"unknown|author|anonymous", "", raw)):
        return None
    for rx, tgt in SPECIAL:
        if re.search(rx, raw, re.I): return tgt
    if re.search(r"cuerden", raw, re.I):
        for rx, key in RULES:
            if re.search(rx, raw, re.I): return (key, A[key][0]) if key in A else None
        return None
    for rx, key in RULES:
        if key and re.search(rx, raw, re.I) and key in A: return (key, A[key][0])
    s = clean(raw)
    if not s or len(s) > 50: return None
    if "," in s and s.count(",") == 1: s = re.sub(r"^([^,]+), (.+)$", r"\2 \1", s)
    k = pk(s)
    if k in A: return (k, A[k][0])
    return (re.sub(r"\W+", "-", s.lower()).strip("-"), s)
