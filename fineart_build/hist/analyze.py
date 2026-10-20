import json, sys, os, re
from events import EV
b2=json.load(open("../base2.json")); b3=json.load(open("../base3.json"))
have={r["qid"]:r["id"] for r in b2["paintings"]+b3["paintings"] if r.get("qid")}
gal=json.load(open("../../data/fineart/gallery.json")); gids={p["id"] for p in gal["paintings"]}
have={q:i for q,i in have.items() if i in gids}
def pd_ok(r):
    ys=[int(d) for a,(n,d) in r["artists"].items() if d and re.match(r"^-?\d{4}$",d)]
    if r["artists"] and not ys: return r["year"] is not None and r["year"]<=1850
    if ys: return max(ys)<=1954 or (r["year"] is not None and r["year"]<=1929 and False)
    return r["year"] is not None and r["year"]<=1900
def load(slug):
    return [r for r in json.load(open(f"cand/{slug}.json")) if pd_ok(r)]
if __name__=="__main__":
    n=int(sys.argv[2]) if len(sys.argv)>2 else 45
    ex=re.compile(sys.argv[3],re.I) if len(sys.argv)>3 and sys.argv[3] else None
    off=int(sys.argv[4]) if len(sys.argv)>4 else 0
    for slug,*_ in EV:
        if sys.argv[1:2] and sys.argv[1]!="all" and slug!=sys.argv[1]: continue
        if not os.path.exists(f"cand/{slug}.json"): continue
        rows=load(slug); h=sum(1 for r in rows if r["qid"] in have)
        print(f"\n=== {slug}: {len(rows)} PD candidates, {h} already in gallery")
        if sys.argv[1:2]==["all"]: continue
        rows=[r for r in rows if not (ex and ex.search(r["title"]))][off:]
        for r in rows[:n]:
            a=", ".join(v[0] for v in r["artists"].values())[:22]
            print(f"{'*' if r['qid'] in have else ' '} {r['sl']:3d} {r['year'] or '----':>5} {r['title'][:52]:52s} {a:22s} {r['qid']} {','.join(r['evs'])[:28]}")
