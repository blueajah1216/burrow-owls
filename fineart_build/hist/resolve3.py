import json, re, time, requests
from events import EV
H={"User-Agent":"BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
terms=sorted({t for e in EV for t in e[5]})
bad=re.compile(r"given name|family name|album|film|disambiguation|commune|municipality|village|song|television|novel|video game|asteroid|band|surname|company|magazine|encyclopedia article|station|musical|opera|episode|human settlement|comic|fictional|arcade|singer",re.I)
# manual title overrides (Wikipedia article titles)
ALT={"Cleopatra":"Cleopatra","Claudius":"Claudius","Pompey":"Pompey","Spartacus":"Spartacus","Attila":"Attila","Augustus":"Augustus","Brutus":"Marcus Junius Brutus","Moon landing":"Apollo 11","Bloody Sunday (1905)":"Bloody Sunday (1905)",
 "Eastern Front (World War I)":"Eastern Front (World War I)","Siege of Constantinople (1453)":"Fall of Constantinople","Siege of Jerusalem (1099)":"Siege of Jerusalem (1099)","Siege of Rome (1849)":"Siege of Rome (1849)",
 "Siege of Sevastopol (1854–1855)":"Siege of Sevastopol (1854–1855)","Salon (gathering)":"Salon (gathering)","Boyar":"Boyar","Cowboy":"Cowboy","Saladin":"Saladin","Pericles":"Pericles","Aristotle":"Aristotle","Raphael":"Raphael",
 "Muhammad":"Muhammad","Ambrose":"Ambrose","Miltiades":"Miltiades","Themistocles":"Themistocles","Belisarius":"Belisarius","Genseric":"Gaiseric","Livia":"Livia","Lucretia":"Lucretia","Theodora":"Theodora (wife of Justinian I)","Titus":"Titus","Tilly":"Johann Tserclaes, Count of Tilly","Danton":"Georges Danton","Roxana":"Roxana","Canute":"Cnut the Great","Menshikov":"Alexander Danilovich Menshikov","Okie":"Okie","Dido":"Dido","Marie Antoinette":"Marie Antoinette","Machiavelli":"Niccolò Machiavelli","Florence":"Florence","Magna Carta":"Magna Carta","Mayflower":"Mayflower","Pilgrims":"Pilgrims (Plymouth Colony)","Plague doctor":"Plague doctor","Printing press":"Printing press","Rape of the Sabine Women":"Rape of the Sabine women","Space Race":"Space Race","Trail of Tears":"Trail of Tears","Triumph of Death":"The Triumph of Death","Zeppelin":"Zeppelin","Wagon train":"Wagon train","Viking ship":"Viking ship","Trench warfare":"Trench warfare","Battle of the Somme":"Battle of the Somme","Battle of Britain":"Battle of Britain","D-Day":"Normandy landings","Attack on Pearl Harbor":"Attack on Pearl Harbor","Battle of the Bulge":"Battle of the Bulge","Gladiator":"Gladiator","Athenian democracy":"Athenian democracy","Anatomy lesson":"The Anatomy Lesson of Dr. Nicolaes Tulp","Amistad":"La Amistad","Acadia":"Acadia","New Amsterdam":"New Amsterdam","Fur trade":"Fur trade","Manifest destiny":"Manifest destiny","Franklin D. Roosevelt":"Franklin D. Roosevelt","Grigori Rasputin":"Grigori Rasputin","Apollo 13":"Apollo 13","Battleship Potemkin":"Battleship Potemkin","Slave market":"Slave market","Slave Auction":"Slave auction","Slave Ship":"Slave ship","Skylab":"Skylab","International Space Station":"International Space Station","Steamboat":"Steamboat","Uncle Tom's Cabin":"Uncle Tom's Cabin","Thin Red Line":"Thin Red Line (military)","Battle of Antietam":"Battle of Antietam","Christian martyrs":"Christian martyrs","Battle of Zama":"Battle of Zama","Bloody Week":"Bloody Week","Coalbrookdale":"Coalbrookdale"}
cache={}
def wd_titles(titles):
    out={}
    for i in range(0,len(titles),40):
        ch=titles[i:i+40]
        r=requests.get("https://www.wikidata.org/w/api.php",params={"action":"wbgetentities","sites":"enwiki","titles":"|".join(ch),"props":"labels|descriptions","languages":"en","normalize":1,"format":"json"},headers=H,timeout=60).json()
        norm={n["to"]:n["from"] for n in r.get("normalized",[])}
        for q,e in r.get("entities",{}).items():
            if q.startswith("-") or "missing" in e: continue
            t=e.get("sitelinks",{}).get("enwiki",{}).get("title")
            lab=(e.get("labels",{}).get("en") or {}).get("value","")
            out[q]=[q,lab,(e.get("descriptions",{}).get("en") or {}).get("value","")]
        # map by order not reliable; query one by one fallback below
        time.sleep(.5)
    return out
# One-by-one exact lookup (reliable mapping), batched via threads is overkill: ~790 calls at 0.1s
def exact(title):
    for a in range(4):
        r=requests.get("https://www.wikidata.org/w/api.php",params={"action":"wbgetentities","sites":"enwiki","titles":title,"props":"labels|descriptions","languages":"en","normalize":1,"format":"json"},headers=H,timeout=30)
        if r.status_code==200:
            for q,e in r.json().get("entities",{}).items():
                if q.startswith("Q"):
                    return [q,(e.get("labels",{}).get("en") or {}).get("value",""),(e.get("descriptions",{}).get("en") or {}).get("value","")]
            return None
        time.sleep(3*(a+1))
def search(t):
    r=requests.get("https://www.wikidata.org/w/api.php",params={"action":"wbsearchentities","search":t,"language":"en","type":"item","limit":8,"format":"json"},headers=H,timeout=30)
    for s in r.json().get("search",[]):
        d=s.get("description","")
        if not bad.search(d): return [s["id"],s.get("label",""),d]
for i,t in enumerate(terms):
    v=exact(ALT.get(t,t))
    if v and bad.search(v[2]) and not re.search(r"painting|ship",v[2]): v=None
    if not v: v=search(t)
    cache[t]=v
    if i%50==0: print(i,len(terms),end="\r",flush=True)
    time.sleep(.1)
json.dump(cache,open("qid_cache.json","w"),ensure_ascii=False)
print("\nunresolved:",[t for t in terms if not cache.get(t)])
for t in ["Cleopatra","Claudius","Moon landing","Pericles","Siege of Constantinople (1453)","Bloody Sunday (1905)","Salon (gathering)","Spartacus","Printing press"]: print(t,cache[t])
