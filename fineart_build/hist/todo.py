import json,sys
d=json.load(open('../base4.json')); ev=json.load(open('ev_of.json'))
a,n=int(sys.argv[1]),int(sys.argv[2])
for i,p in enumerate(d['paintings'][a:a+n]):
    nm=", ".join(d['artists'].get(x,{}).get('name',x) for x in p['artist_ids'])
    print(f"{a+i}|{p['id']}|{p['title']}|{nm}|{p['year']}|{p.get('med','')}|{','.join(ev.get(p['id'],[]))}|{p['w']}x{p['h']}")
