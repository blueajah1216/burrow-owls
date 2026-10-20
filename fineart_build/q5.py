import json, requests, warnings, time
warnings.filterwarnings("ignore")
from q3 import sparql
JEW={"Q134741","Q964608","Q120993","Q158062","Q512596","Q160141","Q443136","Q266415","Q214666","Q211356","Q528460","Q979534","Q213596","Q215073","Q469063","Q215572","Q213735","Q281812","Q379150","Q473771","Q1273537","Q594345","Q359506","Q1498652","Q69651","Q6505783","Q2839882","Q1674765","Q213726","Q9374535","Q2580416","Q704208","Q4290523","Q215550"}
CAN={"Q2035136","Q289624","Q1133777","Q506000","Q609959","Q3786446","Q2775516","Q346483","Q1627994","Q2665846","Q11705308","Q2975556","Q260166","Q10320377","Q3335933","Q3526663","Q2856626","Q7345286","Q325835","Q2959390","Q680528","Q8017377","Q4354618","Q15520500","Q3101368","Q3295479","Q9285666","Q4348982","Q256448","Q2824895","Q56660294","Q2837691","Q4799009","Q18508732","Q3133062","Q15998516","Q5460580","Q527191","Q5588070","Q7176604","Q55770586","Q3106117","Q952000","Q3499926","Q919420"}
def fetch(name,qids,maxdeath,minyear=1700,maxyear=1929):
    out=[]
    L=sorted(qids)
    for i in range(0,len(L),25):
        vals=" ".join("wd:"+q for q in L[i:i+25])
        Q=f"""SELECT ?p ?pLabel ?img ?inc ?sl ?a ?aLabel ?death ?birth WHERE {{
          VALUES ?a {{ {vals} }}
          ?p wdt:P170 ?a . ?p wdt:P31 wd:Q3305213 . ?p wdt:P18 ?img . ?p wikibase:sitelinks ?sl .
          ?p wdt:P571 ?inc . FILTER(YEAR(?inc) >= {minyear} && YEAR(?inc) <= {maxyear})
          ?a wdt:P570 ?death . FILTER(YEAR(?death) <= {maxdeath})
          OPTIONAL {{ ?a wdt:P569 ?birth }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}"""
        out+=sparql(Q); time.sleep(1.5)
    json.dump(out,open(f"cand_{name}_art.json","w")); print(name,len(out))
fetch("jewish",JEW,1954); fetch("canada",CAN,1971)
