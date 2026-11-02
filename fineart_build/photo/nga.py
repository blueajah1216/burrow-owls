import csv, json, collections, sys
csv.field_size_limit(10**9)
objs = {}
for r in csv.DictReader(open("nga/objects.csv", encoding="utf-8")):
    if r["classification"] == "Photograph": objs[r["objectid"]] = r
print(len(objs))
imgs = {}
for r in csv.DictReader(open("nga/published_images.csv", encoding="utf-8")):
    o = r["depictstmsobjectid"]
    if o in objs and r["openaccess"] == "1" and r["viewtype"] == "primary": imgs[o] = r
print(len(imgs))
out = []
for o, im in imgs.items():
    r = objs[o]
    out.append({"src": "nga", "sid": o, "title": r["title"], "date": r["displaydate"], "y0": r["beginyear"], "y1": r["endyear"], "artist": r["attributioninverted"], "tech": r["medium"],
                "credit": r["creditline"], "wikidata": r["wikidataid"], "iiif": im["iiifurl"], "w": im["width"], "h": im["height"], "acc": r["accessionnum"], "uuid": r["uuid"]})
json.dump(out, open("c_nga.json", "w"), ensure_ascii=False)
c = collections.Counter(a["artist"] for a in out)
print(c.most_common(60))
