import json, re, sys
d = json.load(open("work2.json"))
a, b = int(sys.argv[1]), int(sys.argv[2])
for i in range(a, min(b, len(d))):
    r = d[i]
    desc = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", r.get("desc") or ""))[:60]
    print(f"{10000+i}|{r['y']}|{(r['who'] or '')[:24]}|{r['title'][:62]}|{r['src'][:3]}|{(r.get('place') or '')[:18]}|{desc}")
