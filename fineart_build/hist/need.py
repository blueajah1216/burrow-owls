import json,sys
H='/Users/whitetower/dev/burrow-owls/fineart_build/'
b=json.load(open(H+'base4.json')); dr=set(json.load(open(H+'hist/review.json'))['drop'])
g=json.load(open(H+'../data/fineart/gallery.json'))
used={}
for p in b['paintings']:
    if p['id'] in dr: continue
    for a in p['artist_ids']: used.setdefault(a,[]).append(p['title'][:26])
need=[a for a in used if a not in g['artists']]
a0,n=int(sys.argv[1]),int(sys.argv[2])
for a in need[a0:a0+n]:
    x=b['artists'].get(a,{})
    print(f"{a}|{x.get('name')}|{(x.get('birth') or '')[:4]}-{(x.get('death') or '')[:4]}|{x.get('born_in','')}|{x.get('died_in','')}|{';'.join(used[a][:2])}")
