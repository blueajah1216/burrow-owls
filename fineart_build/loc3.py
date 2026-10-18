import json, re
g=json.load(open("../data/fineart/gallery.json")); d=json.load(open("base2.json"))
l=json.load(open("loc.json")); l2=json.load(open("loc2.json"))
ids={p["id"]:p["qid"] for p in d["paintings"]}
DONOR={"Andrew W. Mellon collection","Samuel H. Kress Collection","Paul Mellon","Chester Dale Collection","Ailsa Mellon Bruce Collection"}
NA={"Führermuseum","\"degenerate art\" collection","Brett Gorvy","Oval Office Private Dining Room","Musée d'Orsay website","Kingdom of the Netherlands","Switzerland","Norway","Russia","United Kingdom","United States","New York","Chicago","Room 87","rue de Miromesnil"}
FIX={ # venue label -> (venue, city, country)
 "Louvre Museum":("Louvre Museum","Paris","France"),"Louvre Museum storage":("Louvre Museum","Paris","France"),
 "Tate":("Tate Britain","London","United Kingdom"),"Tretyakov Gallery":("State Tretyakov Gallery","Moscow","Russia"),
 "Metropolitan Museum of Art":("Metropolitan Museum of Art","New York City","United States"),
 "Gallery 619, Goya and Eighteenth-Century Italy, Metropolitan Museum of Art":("Metropolitan Museum of Art","New York City","United States"),
 "Post-Impressionism: French Painting 1850–1900 - room 44":("Courtauld Gallery","London","United Kingdom"),
 "Alte Pinakothek, upper floor, gallery XII":("Alte Pinakothek","Munich","Germany"),
 "Delaware Art Museum":("Delaware Art Museum","Wilmington, Delaware","United States"),
 "Audrey Jones Beck Building":("Museum of Fine Arts, Houston","Houston","United States"),
 "Museo Sorolla building":("Sorolla Museum","Madrid","Spain"),"Sacre Hall":("Palace of Versailles","Versailles","France"),
 "Antichambre de la reine du Château de Versailles":("Palace of Versailles","Versailles","France"),
 "Musée de l'Histoire de France":("Palace of Versailles","Versailles","France"),
 "United States Capitol rotunda":("United States Capitol","Washington, D.C.","United States"),
 "General Staff Building, Saint Petersburg":("Hermitage Museum (General Staff Building)","Saint Petersburg","Russia"),
 "Beaux-Arts de Paris":("Beaux-Arts de Paris","Paris","France"),"Musée des Beaux-Arts de Bordeaux":("Musée des Beaux-Arts de Bordeaux","Bordeaux","France"),
 "Pérez Simón Collection":("Museo Soumaya (Pérez Simón Collection)","Mexico City","Mexico"),
 "National Museum of Fine Arts":("National Museum of Fine Arts","Manila","Philippines"),"Rasmus Meyer":("Rasmus Meyer Collection (KODE)","Bergen","Norway"),
 "Sukiennice Museum":("Sukiennice Museum (National Museum in Kraków)","Kraków","Poland"),"Breda":("Breda","Breda","Netherlands"),
 "Porto-Vecchio":("Porto-Vecchio","Porto-Vecchio","France"),"Kunst Museum Winterthur | Reinhart am Stadtgarten":("Kunst Museum Winterthur","Winterthur","Switzerland"),
 "De Morgan Centre":("De Morgan Foundation","London","United Kingdom"),"Victoria Memorial":("Victoria Memorial","Kolkata","India"),
 "Museo del Novecento":("Museo del Novecento","Milan","Italy"),"Hearst Castle":("Hearst Castle","San Simeon, California","United States"),
 "Clark Art Institute":("Clark Art Institute","Williamstown, Massachusetts","United States"),"Joslyn Art Museum":("Joslyn Art Museum","Omaha, Nebraska","United States"),
 "Allen Memorial Art Museum":("Allen Memorial Art Museum","Oberlin, Ohio","United States"),"Raclin Murphy Museum of Art":("Raclin Murphy Museum of Art","Notre Dame, Indiana","United States"),
 "Lady Lever Art Gallery":("Lady Lever Art Gallery","Port Sunlight","United Kingdom"),"Chatsworth House":("Chatsworth House","Derbyshire","United Kingdom"),
 "National Museum Cardiff":("National Museum Cardiff","Cardiff","United Kingdom"),
}
LOUVRE_ROOM=re.compile(r"^Room \d{3}$")
CITYCLEAN=[(r"^City of ",""),(r" Municipality$",""),(r" Governorate$",""),(r"^Royal Borough of ",""),(r"^London Borough of ","")]
def clean(c):
    for a,b in CITYCLEAN: c=re.sub(a,b,c)
    return c
out={}; unk=[]
for p in g["paintings"]:
    q=ids[p["id"]]; v=l.get(q)
    if not v or v["venue"] in NA: unk.append(p["id"]); continue
    ven,city,ctry=v["venue"],None,v.get("country")
    if v["venue"] in DONOR: out[p["id"]]=["National Gallery of Art","Washington, D.C.","United States"]; continue
    if LOUVRE_ROOM.match(ven): out[p["id"]]=["Louvre Museum","Paris","France"]; continue
    if ven in FIX: out[p["id"]]=list(FIX[ven]); continue
    city=(l2.get(q) or {}).get("city2") or (clean(v["city"]) if v.get("city") else None)
    if city and ven.lower()==city.lower(): city=city
    city=clean(city) if city else city
    city={"Manhattan":"New York City","Westminster":"London","Philadelphia County":"Philadelphia","District 6":"Tehran","Dublin City":"Dublin","Avenidas Novas":"Lisbon","Brussels-Capital Region":"Brussels","Beyoğlu":"Istanbul","Feodosiya City Council":"Feodosia","Greenwich":"London","Kensington and Chelsea":"London","Southwark":"London","Maxvorstadt":"Munich","Pyrénées-Atlantiques":"Pau","Roma Capitale":"Rome","Runnymede":"Egham","Sefton":"Southport","Tirana municipality":"Tirana","Gentofte":"Charlottenlund","Frederikshavn":"Skagen","Derbyshire":"Bakewell, Derbyshire","Kitakyūshū":"Kitakyushu"}.get(city,city)
    if city=="Wales" or city=="Castle": city="Cardiff"
    out[p["id"]]=[ven,city,ctry]
for k,v in out.items():
    if v[2] in ("Wales","England","Scotland"): v[2]="United Kingdom"
    if v[2] in ("German Reich","Nazi Germany"): out.pop(k); unk.append(k)
NGA=["National Gallery of Art","Washington, D.C.","United States"]
MET=["Metropolitan Museum of Art","New York City","United States"]
MANUAL={}
for i in ("sunset-at-montmajour",): MANUAL[i]=["Van Gogh Museum","Amsterdam","Netherlands"]
for i in ("a-young-girl-reading","woman-with-a-parasol-madame-monet-and-her-son","the-railway","the-old-musician","symphony-in-white-no-1-the-white-girl","the-plum","la-mousme","the-open-window","farmhouse-in-provence","girl-in-white","fatata-te-miti","little-girl-in-a-blue-armchair","a-girl-with-a-watering-can","masked-ball-at-the-opera","the-dead-toreador","le-pont-neuf","the-boating-party","still-life-vase-with-pink-roses","boy-on-the-rocks","wivenhoe-park","girl-arranging-her-hair"): MANUAL[i]=NGA
for i in ("majas-on-the-balcony","springtime-pierre-augus"): MANUAL[i]=MET
MANUAL.update({"the-nightmare":["Detroit Institute of Arts","Detroit","United States"],"mr-and-mrs-andrews":["National Gallery","London","United Kingdom"],
 "salisbury-cathedral-from-the-bishop-s-grounds":["Victoria and Albert Museum","London","United Kingdom"],"the-skating-minister":["National Gallery of Scotland","Edinburgh","United Kingdom"],
 "the-slave-ship":["Museum of Fine Arts, Boston","Boston","United States"],"the-channel-of-gravelines-petit-fort-philippe":["Newfields (Indianapolis Museum of Art)","Indianapolis","United States"],
 "the-cyclops":["Kröller-Müller Museum","Ede","Netherlands"],"woman-with-a-cat":["Clark Art Institute","Williamstown, Massachusetts","United States"],
 "the-peacemakers":["The White House","Washington, D.C.","United States"],
 "the-tower-of-blue-horses":["Missing since World War II",None,None],
 "poppy-flowers":["Stolen from the Mohamed Mahmoud Khalil Museum in Cairo in 2010 and still missing",None,None],
 "the-stone-breakers":["Destroyed in World War II (1945)",None,None],
 "woman-with-a-fan":["Private collection",None,None],"adele-bloch-bauer-ii":["Private collection",None,None],"self-portrait-without-beard":["Private collection",None,None],
 "young-man-at-his-window":["Private collection",None,None],"pyramid-of-skulls":["Private collection",None,None],"le-desespere":["Private collection",None,None],
 "the-siren":["Private collection",None,None],"ophelia-john-william":["Private collection",None,None],"the-sorceress":["Private collection",None,None]})
for k,v in MANUAL.items(): out[k]=v; unk=[u for u in unk if u!=k]
for k in list(out):
    if out[k][0].lower()=="private collection": out[k]=["Private collection",None,None]
json.dump(out,open("out/locations.json","w"),ensure_ascii=False,indent=0)
print(len(out),"located;",len(unk),"unknown")
import collections
c=collections.Counter((v[0],v[1],v[2]) for v in out.values())
for k,n in c.most_common(30): print(n,k)
print("no city:",[ (k,v) for k,v in out.items() if not v[1]][:25])
print("no country:",[ (k,v) for k,v in out.items() if not v[2]][:25])
print("weird cities:",sorted({v[1] for v in out.values() if v[1] and re.search(r"District|Bezirk|ward|Ward|Quartier|district|-ku|Stadtbezirk|Municipal|County|Zone|Governorate",v[1])}))
print("unknown:",unk[:80])
