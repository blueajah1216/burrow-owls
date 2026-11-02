import requests, sys, json
H={"User-Agent":"BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
for q in sys.argv[1:]:
    r=requests.get("https://commons.wikimedia.org/w/api.php",params={"action":"query","list":"search","srsearch":q,"srnamespace":14,"srlimit":8,"format":"json"},headers=H).json()
    print(q,"=>",[ (x["title"][9:]) for x in r["query"]["search"]])
