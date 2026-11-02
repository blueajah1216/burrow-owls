import json, re
d = json.load(open("sel.json"))
BAD = re.compile(r"(PK-F|RP-F|D\d{4}|LCCN|page \d|Fargeprøver|Zonder titel|\bscan\b|\bcopy\b|verso|recto|album page|title page|\.tif)", re.I)
out = []
for r in d:
    if BAD.search(r["title"]): continue
    t = re.sub(r"\s*\(.*?\)\s*$", "", r["title"]).strip() or r["title"]
    r["title"] = t[:90]
    out.append(r)
json.dump(out, open("work.json", "w"), ensure_ascii=False)
print(len(d), len(out))
