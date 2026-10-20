"""python3 find.py "query 1" "query 2" ...  -> top painting-ish Wikidata hits (id, label, description)"""
import sys, requests, time, warnings
warnings.filterwarnings("ignore")
H={"User-Agent":"BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
for q in sys.argv[1:]:
    for a in range(3):
        r=requests.get("https://www.wikidata.org/w/api.php",params={"action":"wbsearchentities","search":q,"language":"en","type":"item","limit":8,"format":"json"},headers=H,timeout=30)
        if r.status_code==200: break
        time.sleep(3)
    hits=[s for s in r.json().get("search",[]) if any(w in s.get("description","").lower() for w in ("painting","print","drawing","mural","fresco","woodcut","engraving","lithograph","poster"))]
    print(f"## {q}")
    for s in hits[:5]: print("  ",s["id"],"|",s.get("label","")[:50],"|",s.get("description","")[:70])
    time.sleep(.25)
