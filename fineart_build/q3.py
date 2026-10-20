"""Fetch candidate paintings for heritage collections. Output: cand_<group>.json"""
import json, requests, warnings, time, sys
warnings.filterwarnings("ignore")
H={"User-Agent":"BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
def sparql(Q):
    for t in range(5):
        r=requests.get("https://query.wikidata.org/sparql",params={"query":Q,"format":"json"},headers=H,timeout=170)
        if r.status_code==200: return r.json()["results"]["bindings"]
        print("retry",r.status_code,r.text[:100]); time.sleep(10)
    return []
GROUPS={
 "norway":"?a wdt:P27 wd:Q20 .",
 "canada":"?a wdt:P27 wd:Q16 .",
 "usa":"?a wdt:P27 wd:Q30 .",
 "jewish":"{ ?a wdt:P172 wd:Q7325 } UNION { ?a wdt:P140 wd:Q9268 } .",
 "japan":"?a wdt:P27 wd:Q17 .",
 "china":"{ ?a wdt:P27 wd:Q148 } UNION { ?a wdt:P27 wd:Q8733 } UNION { ?a wdt:P27 wd:Q29520 } .",
 "turkey":"{ ?a wdt:P27 wd:Q43 } UNION { ?a wdt:P27 wd:Q12560 } .",
 "egypt":"?a wdt:P27 wd:Q79 .",
 "iran":"{ ?a wdt:P27 wd:Q794 } UNION { ?a wdt:P27 wd:Q2735232 } .",
 "lebanon":"?a wdt:P27 wd:Q822 .",
 "india":"{ ?a wdt:P27 wd:Q668 } UNION { ?a wdt:P27 wd:Q129286 } .",
 "mexico":"?a wdt:P27 wd:Q96 .",
}
def run(name,filt,minsl,limit=600,types="wd:Q3305213"):
    Q=f"""SELECT ?p ?pLabel ?img ?inc ?sl ?a ?aLabel ?death ?birth WHERE {{
      {filt}
      ?p wdt:P170 ?a . ?p wdt:P31 ?ty . VALUES ?ty {{ {types} }}
      ?p wdt:P18 ?img . ?p wikibase:sitelinks ?sl . FILTER(?sl >= {minsl})
      OPTIONAL {{ ?p wdt:P571 ?inc }} ?a wdt:P570 ?death . FILTER(YEAR(?death) <= 1954)
      OPTIONAL {{ ?a wdt:P569 ?birth }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }} ORDER BY DESC(?sl) LIMIT {limit}"""
    rows=sparql(Q); print(name,len(rows)); return rows
if __name__=="__main__":
    for name,filt in GROUPS.items():
        if len(sys.argv)>1 and name not in sys.argv[1:]: continue
        types="wd:Q3305213"
        if name in("japan","china"): types="wd:Q3305213 wd:Q11060274 wd:Q22669139 wd:Q184296 wd:Q1278452"
        rows=run(name,filt,1 if name in("norway","canada","japan","china","turkey","egypt","iran","lebanon","india","mexico") else 3,types=types)
        json.dump(rows,open(f"cand_{name}.json","w"))
        time.sleep(2)
