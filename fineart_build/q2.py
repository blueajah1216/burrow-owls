import requests, json, warnings
warnings.filterwarnings("ignore")
H={"User-Agent":"BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
def sparql(Q):
    r=requests.get("https://query.wikidata.org/sparql",params={"query":Q,"format":"json"},headers=H,timeout=180)
    r.raise_for_status(); return r.json()["results"]["bindings"]
base="""?p wdt:P31 wd:Q3305213; wdt:P18 ?img; wdt:P170 ?artist; wikibase:sitelinks ?sl.
  ?p wdt:P571 ?inc. FILTER(YEAR(?inc) >= 1726 && YEAR(?inc) <= 1929) FILTER(?sl >= 8)
  ?artist wdt:P570 ?death. FILTER(YEAR(?death) <= 1954)"""
def lab(var): return f'OPTIONAL{{?p {var[0]} ?{var[1]}. ?{var[1]} rdfs:label ?{var[1]}L FILTER(LANG(?{var[1]}L)="en")}}'
out={}
for name,prop in [("genre","P136"),("movement","P135"),("collection","P195")]:
    Q=f"""SELECT ?p ?v ?vL WHERE {{ {base} ?p wdt:{prop} ?v. ?v rdfs:label ?vL FILTER(LANG(?vL)="en") }}"""
    rows=sparql(Q); m={}
    for b in rows: m.setdefault(b["p"]["value"],[]).append(b["vL"]["value"])
    out[name]=m; print(name,len(m))
Q=f"""SELECT DISTINCT ?artist ?birth ?death ?bpL ?dpL ?ctL ?nameL WHERE {{ {base}
 ?artist rdfs:label ?nameL FILTER(LANG(?nameL)="en")
 OPTIONAL{{?artist wdt:P569 ?birth}} ?artist wdt:P570 ?death.
 OPTIONAL{{?artist wdt:P19 ?bp. ?bp rdfs:label ?bpL FILTER(LANG(?bpL)="en")}}
 OPTIONAL{{?artist wdt:P20 ?dp. ?dp rdfs:label ?dpL FILTER(LANG(?dpL)="en")}}
 OPTIONAL{{?artist wdt:P27 ?ct. ?ct rdfs:label ?ctL FILTER(LANG(?ctL)="en")}} }}"""
rows=sparql(Q); art={}
for b in rows:
    a=art.setdefault(b["artist"]["value"],{"name":b["nameL"]["value"]})
    for k,s in [("birth","birth"),("death","death"),("born_in","bpL"),("died_in","dpL")]:
        if s in b: a.setdefault(k,b[s]["value"][:10] if k in("birth","death") else b[s]["value"])
    if "ctL" in b: a.setdefault("cit",set()).add(b["ctL"]["value"])
for a in art.values():
    if "cit" in a: a["cit"]=sorted(a["cit"])
out["artists"]=art; print("artists",len(art))
json.dump(out,open("raw2.json","w"))
