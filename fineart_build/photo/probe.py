import sys, json, time, warnings
warnings.filterwarnings("ignore"); sys.path.insert(0, "..")
from q3 import sparql
for lo, hi in [(1820,1860),(1860,1900),(1900,1930),(1930,1960),(1960,2000),(2000,2026)]:
    Q=f"""SELECT (COUNT(DISTINCT ?p) AS ?n) WHERE {{ ?p wdt:P31 wd:Q125191 . ?p wdt:P571 ?inc . FILTER(YEAR(?inc)>={lo} && YEAR(?inc)<{hi})
      ?p wdt:P18 ?img . ?p wikibase:sitelinks ?sl . FILTER(?sl>=2) }}"""
    print(lo,hi,sparql(Q)[0]["n"]["value"],flush=True); time.sleep(1)
