import json, sys, time, warnings
warnings.filterwarnings("ignore"); sys.path.insert(0, "..")
from q3 import sparql
ids = json.load(open("new_ids.json")); P = {p["id"]: p for p in json.load(open("../base4.json"))["paintings"]}
qs = [P[i]["qid"] for i in ids]; F = {}
for i in range(0, len(qs), 80):
    vals = " ".join("wd:" + q for q in qs[i:i + 80])
    Q = f"""SELECT ?p (SAMPLE(?d) AS ?desc) (GROUP_CONCAT(DISTINCT ?gl; separator='; ') AS ?genre) (GROUP_CONCAT(DISTINCT ?dl; separator='; ') AS ?dep) (GROUP_CONCAT(DISTINCT ?ml; separator='; ') AS ?mat) WHERE {{
      VALUES ?p {{ {vals} }}
      OPTIONAL {{ ?p schema:description ?d FILTER(LANG(?d)='en') }}
      OPTIONAL {{ ?p wdt:P136 ?g . ?g rdfs:label ?gl FILTER(LANG(?gl)='en') }}
      OPTIONAL {{ ?p wdt:P180 ?dd . ?dd rdfs:label ?dl FILTER(LANG(?dl)='en') }}
      OPTIONAL {{ ?p wdt:P186 ?m . ?m rdfs:label ?ml FILTER(LANG(?ml)='en') }} }} GROUP BY ?p"""
    for b in sparql(Q):
        F[b["p"]["value"].rsplit("/", 1)[1]] = {k: b[k]["value"] for k in ("desc", "genre", "dep", "mat") if k in b and b[k]["value"]}
    print(i, len(F), end="\r"); time.sleep(1.5)
json.dump(F, open("facts.json", "w"), ensure_ascii=False)
