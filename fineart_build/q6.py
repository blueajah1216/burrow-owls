import json,time,warnings
warnings.filterwarnings("ignore")
from q3 import run
G={"sweden":"{?a wdt:P27 wd:Q34}.","denmark":"?a wdt:P27 wd:Q35 .","finland":"{ ?a wdt:P27 wd:Q33 } UNION { ?a wdt:P27 wd:Q62633 } .","austria":"{ ?a wdt:P27 wd:Q40 } UNION { ?a wdt:P27 wd:Q28513 } .","belgium":"?a wdt:P27 wd:Q31 .","switzerland":"?a wdt:P27 wd:Q39 .","australia":"?a wdt:P27 wd:Q408 .","hungary":"{ ?a wdt:P27 wd:Q28 } UNION { ?a wdt:P27 wd:Q171150 } .","czech":"{ ?a wdt:P27 wd:Q213 } UNION { ?a wdt:P27 wd:Q33946 } .","ukraine":"?a wdt:P27 wd:Q212 .","greece":"?a wdt:P27 wd:Q41 .","portugal":"?a wdt:P27 wd:Q45 .","ireland":"?a wdt:P27 wd:Q27 .","brazil":"?a wdt:P27 wd:Q155 .","argentina":"?a wdt:P27 wd:Q414 .","philippines":"?a wdt:P27 wd:Q928 ."}
for n,f in G.items():
    rows=run(n,f,2,limit=250)
    json.dump(rows,open(f"cand_{n}.json","w")); time.sleep(2)
