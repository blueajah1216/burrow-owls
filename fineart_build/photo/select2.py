"""Second selection: add more photographs beyond work.json -> work2.json (indices start at 10000). Usage: select2.py [scale]"""
import json, re, collections, sys, importlib.util
spec = importlib.util.spec_from_file_location("sel1", "select_.py")
d = json.load(open("cand_all.json"))
old = {r["key"] for r in json.load(open("work.json"))}
PREFIX = json.load(open("work2_prefix.json"))
old |= {r["key"] for r in PREFIX}
BAD = re.compile(r"(PK-F|RP-F|D\d{4}|LCCN|page \d|Fargeprøver|Zonder titel|\bscan\b|\bcopy\b|verso|recto|album page|title page|\.tif|^(DSC|IMG|DSCN|_MG|IMGP|PXL|P\d{6,})|screenshot|\bmap of\b|logo|diagram|poster|postage|stamp|\bpainting\b|\bdrawing\b|\bengraving\b|\blithograph|illustration|\bcrop(ped)?\b|restored|colori[sz]ed|cleaned|\bdet\d|\bEAA\b|^untitled$|^\(.*\)$|unidentified|unknown)", re.I)
def pk(w):
    w = re.sub(r"\(.*?\)", "", w or "").split(";")[0].strip(); w = re.sub(r"<.*", "", w); p = w.split()
    return (p[0][0].lower() + " " + p[-1].lower()) if len(p) > 1 else w.lower()
famous = set("a stieglitz,l hine,j cameron,j atget,e atget,r fenton,w talbot,e curtis,t o'sullivan,a gardner,m brady,g barnard,c watkins,e muybridge,h bayard,d hill,d adamson,g gray,c white,g käsebier,f day,f eugene,a coburn,h kühn,p strand,e steichen,a ulmann,f evans,p emerson,h robinson,o rejlander,nadar,c marville,f beato,s bourne,j thomson,w jackson,j riis,a genthe,d lange,w evans,a rothstein,r lee,j delano,m wolcott,j vachon,e bubley,g parks,a palmer,b shahn,j collier,c mydans,s prokudin-gorsky,s prokudin-gorskii,f johnston,f frith,b abbott,i cunningham,e weston,m ray,r capa,t frissell,y karsh,c vechten".split(","))
rows = []
for r in d:
    if r["key"] in old or not r["y"] or r["y"] < 1826 or r["y"] > 2026: continue
    if BAD.search(r["title"] or "") or len(r["title"] or "") < 6: continue
    if r["src"] == "commons" and (r["w"] < 1400 or r["w"] / max(r["h"], 1) > 2.4 or r["w"] / max(r["h"], 1) < 0.4): continue
    r["pk"] = pk(r["who"]); rows.append(r)
sc = float(sys.argv[1]) if len(sys.argv) > 1 else 1
E = [(1826, 1850, 60), (1851, 1879, 350), (1880, 1909, 400), (1910, 1934, 350), (1935, 1949, 360), (1950, 1979, 160), (1980, 3000, 640)]
def rank(r):
    s = r["score"] + (3 if r["pk"] in famous else 0) + (1.5 if r["desc"] else 0) + (1 if r["src"] in ("aic", "cleveland") else 0)
    if r["src"] == "loc" and (r.get("q") or "").startswith(("fsac", "hs:", "photochrom", "usnwr")): s += 2
    if r["src"] == "commons" and (r.get("cat") or "").startswith("cat:"): s += 1
    return s
sel = []
STEMS = collections.Counter(); TAGS = collections.Counter()
def stem(r):
    w = re.findall(r"[a-zà-ÿ]+", re.sub(r"\[|\]", "", (r["title"] or "").lower()))
    return " ".join(w[:2])
for r in PREFIX: STEMS[stem(r)] += 1
for lo, hi, n in E:
    n = int(n * sc); per = collections.Counter(); got = 0; srcc = collections.Counter(); seen = set()
    pool = sorted([r for r in rows if lo <= r["y"] <= hi], key=lambda r: -rank(r))
    # round-robin by source to keep variety: take in rank order but cap each source at 55%
    for r in pool:
        if got >= n: break
        cap = 8 if r["pk"] in famous else 4
        if r["pk"] and per[r["pk"]] >= cap: continue
        if srcc[r["src"]] >= max(40, n * .55): continue
        tk = re.sub(r"\W+", "", (r["title"] or "").lower())[:28]
        if tk in seen: continue
        tg = (r.get("q") or "")[:3] if r["src"] == "loc" else ""
        if tg == "cw:" and TAGS[tg] >= 45: continue
        if tg in ("pho", "det"):
            parts = [x.strip().lower() for x in re.split(r"[.,]", r["title"] or "") if x.strip()]
            ctry = parts[-1] if parts else ""; cty = parts[-2] if len(parts) > 1 else ""
            if TAGS["pd"] >= 110 or TAGS["c:" + ctry] >= 6 or TAGS["y:" + cty] >= 2: continue
            TAGS["pd"] += 1; TAGS["c:" + ctry] += 1; TAGS["y:" + cty] += 1
        if STEMS[stem(r)] >= (2 if stem(r).startswith(("untitled", "camp of", "portrait of")) else 4): continue
        STEMS[stem(r)] += 1; TAGS[tg] += 1
        seen.add(tk); per[r["pk"]] += 1; srcc[r["src"]] += 1; got += 1; sel.append(r)
    print(lo, hi, got, "of pool", len(pool), dict(srcc))
sel.sort(key=lambda r: (r["y"], r["key"]))
out = []
for r in sel:
    t = re.sub(r"\s*\(.*?\)\s*$", "", r["title"]).strip() or r["title"]
    t = re.sub(r"\s*(LACMA|MET|NARA|NYPL|V&A|Brady-Handy)\b.*$", "", t).strip(" -_") or t
    t = re.sub(r"^[\[\(]|[\]\)]$", "", t).strip()
    r["title"] = t[:90]; out.append(r)
out = PREFIX + out
json.dump(out, open("work2.json", "w"), ensure_ascii=False)
print(len(out))
