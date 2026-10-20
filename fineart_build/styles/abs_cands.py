import json, re, sys, time, requests, warnings
warnings.filterwarnings("ignore"); sys.path.insert(0,"..")
from q3 import sparql, H
NAMES=["Wassily Kandinsky","Kazimir Malevich","Piet Mondrian","Paul Klee","Hilma af Klint","Robert Delaunay","Franz Marc","August Macke","Alexej von Jawlensky","Marianne von Werefkin","Kurt Schwitters","El Lissitzky","Theo van Doesburg","Lyubov Popova","Olga Rozanova","Alexandra Exter","Vladimir Tatlin","Ivan Kliun","Sophie Taeuber-Arp","Joaquín Torres-García","Arthur Dove","Marsden Hartley","Morgan Russell","Patrick Henry Bruce","John Marin","Joseph Stella","Umberto Boccioni","Luigi Russolo","Oscar Bluemner","Gino Severini","Albert Gleizes","Juan Gris","Georges Valmier","Vilmos Huszár","Bart van der Leck","Ilya Chashnik","Nikolai Suetin","Ivan Puni","Liubov Popova","Vasily Kandinsky"]
ROLE=re.compile(r"painter|artist|designer|architect|photographer",re.I)
Q={}
for n in NAMES:
    r=requests.get("https://www.wikidata.org/w/api.php",params={"action":"wbsearchentities","search":n,"language":"en","type":"item","limit":6,"format":"json"},headers=H,timeout=30).json()
    s=[x for x in r.get("search",[]) if ROLE.search(x.get("description",""))]
    if s: Q[n]=(s[0]["id"],s[0].get("label"),s[0].get("description","")[:50])
    time.sleep(.2)
print(len(Q)); print(json.dumps(Q,ensure_ascii=False,indent=0)[:2500])
json.dump(Q,open("abs_artists.json","w"),ensure_ascii=False)
ids=sorted({v[0] for v in Q.values()})
rows={}
for i in range(0,len(ids),15):
    vals=" ".join("wd:"+q for q in ids[i:i+15])
    qq=f"""SELECT ?p ?pLabel ?img ?inc ?sl ?artist ?artistLabel ?death WHERE {{
      VALUES ?artist {{ {vals} }} ?p wdt:P170 ?artist . VALUES ?type {{ wd:Q3305213 wd:Q93184 wd:Q11060274 }} ?p wdt:P31 ?type .
      ?p wdt:P18 ?img . ?p wikibase:sitelinks ?sl . OPTIONAL {{ ?p wdt:P571 ?inc }} OPTIONAL {{ ?artist wdt:P570 ?death }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }} LIMIT 3000"""
    for b in sparql(qq):
        q=b["p"]["value"].rsplit("/",1)[1]
        m=re.match(r"^(-?\d{4})",b["inc"]["value"]) if "inc" in b else None
        yr=int(m.group(1)) if m else None
        rows[q]={"qid":q,"title":b["pLabel"]["value"],"img":b["img"]["value"],"sl":int(b["sl"]["value"]),"year":yr,"artist":b["artistLabel"]["value"],"aq":b["artist"]["value"].rsplit("/",1)[1]}
    time.sleep(2)
out=[r for r in rows.values() if r["year"] and r["year"]<=1929]
out.sort(key=lambda r:(-r["sl"]))
json.dump(out,open("abs_cands.json","w"),ensure_ascii=False)
from collections import Counter
print(len(rows),"total;",len(out),"<=1929"); print(Counter(r["artist"] for r in out).most_common(40))
