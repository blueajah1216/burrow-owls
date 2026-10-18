import requests, json, sys
Q = """
SELECT ?p ?pLabel ?img ?inc ?sl ?artist ?artistLabel ?death ?birth WHERE {
  ?p wdt:P31 wd:Q3305213; wdt:P18 ?img; wdt:P170 ?artist; wikibase:sitelinks ?sl.
  ?p wdt:P571 ?inc.
  FILTER(YEAR(?inc) >= 1726 && YEAR(?inc) <= 1930)
  FILTER(?sl >= 8)
  ?artist wdt:P570 ?death. FILTER(YEAR(?death) <= 1954)
  OPTIONAL{?artist wdt:P569 ?birth}
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY DESC(?sl) LIMIT 3000
"""
r = requests.get("https://query.wikidata.org/sparql", params={"query":Q,"format":"json"},
  headers={"User-Agent":"BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}, timeout=120)
print(r.status_code, len(r.text))
d = r.json()["results"]["bindings"]
json.dump(d, open("raw1.json","w"))
seen=set()
rows=[]
for b in d:
    k=b["p"]["value"]
    if k in seen: continue
    seen.add(k); rows.append(b)
print(len(rows))
for b in rows[:25]: print(b["sl"]["value"], b["pLabel"]["value"], "|", b["artistLabel"]["value"], b["inc"]["value"][:4])
print(rows[-1]["sl"]["value"])
