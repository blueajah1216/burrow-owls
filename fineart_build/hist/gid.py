import json,sys,re
d=json.load(open('../../data/fineart/gallery.json')); A=d['artists']
pat=re.compile("|".join(sys.argv[1:]),re.I)
for p in d['paintings']:
    if pat.search(p['id']) or pat.search(p['t']) or pat.search(A[p['a'][0]]['n']):
        print(p['id'],"|",p['t'][:48],"|",A[p['a'][0]]['n'],p['y'],'N' if p.get('n') else '')
