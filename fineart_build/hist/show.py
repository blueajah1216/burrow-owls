import sys, re, json
from analyze import load, have, EV
slug=sys.argv[1]; n=int(sys.argv[2]) if len(sys.argv)>2 else 30; minsl=int(sys.argv[3]) if len(sys.argv)>3 else 2
ex=re.compile(sys.argv[4],re.I) if len(sys.argv)>4 and sys.argv[4] else None
rows=[r for r in load(slug) if r["sl"]>=minsl and not (ex and ex.search(r["title"]))]
print(f"=== {slug} ({len(rows)} rows sl>={minsl})")
for r in rows[:n]:
    a=", ".join(v[0] for v in r["artists"].values())[:17]
    t=r["title"] if not re.match(r"^Q\d+$",r["title"]) else "(untitled)"
    print(f"{'*' if r['qid'] in have else ' '}{r['sl']:3d} {r['year'] or '----':>5} {t[:48]:48s} {a:17s} {r['qid']}")
