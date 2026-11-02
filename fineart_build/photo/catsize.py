import sys, time, requests
H = {"User-Agent": "BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
for c in [l.strip() for l in open(sys.argv[1]) if l.strip() and not l.startswith("#")]:
    r = requests.get("https://commons.wikimedia.org/w/api.php", params=dict(action="query", format="json", titles="Category:" + c, prop="categoryinfo"), headers=H, timeout=60).json()
    p = list(r["query"]["pages"].values())[0]
    ci = p.get("categoryinfo")
    print(f"{(ci or {}).get('files', 'MISSING'):>7} files {(ci or {}).get('subcats', '-'):>5} subcats  {c}", flush=True)
    time.sleep(1.5)
