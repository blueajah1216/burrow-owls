import json,glob
inp={}
for f in sorted(glob.glob("in3/p_*.json")):
    for r in json.load(open(f)): inp[r["id"]]=r
out={}
for f in sorted(glob.glob("out/new_*.json")):
    for r in json.load(open(f)): out[r[0]]=r
print("inputs",len(inp),"written",len(out),"extra",[i for i in out if i not in inp][:10])
done=[i for i in inp if i in out]
print("missing so far (first batches):",[i for i in list(inp)[:len(inp)] if i not in out][:0])
bad=[i for i,r in out.items() if len(r[3].split())<20 or r[3].strip().lower().startswith("skip")]
print("too short/skip:",bad)
