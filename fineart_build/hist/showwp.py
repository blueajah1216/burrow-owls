import json,sys,re
slug=sys.argv[1]; n=int(sys.argv[2]) if len(sys.argv)>2 else 40
rows=json.load(open(f"wp/{slug}.json"))
print("===",slug,len(rows))
for r in rows[:n]: print(f"{r['n']:2d} {r['file'][:70]:70s} {r['w']}x{r['h']} | {r['artist'][:26]} | {r['date'][:12]}")
