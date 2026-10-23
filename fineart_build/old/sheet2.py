import json, sys, html
S="/private/tmp/claude-501/-Users-whitetower-dev-burrow-owls/717d435b-0809-4761-bc97-df7352efb381/scratchpad"
d=json.load(open("../base4.json")); P={p["id"]:p for p in d["paintings"]}
ids=sorted(json.load(open("new_ids.json")), key=lambda i:(P[i]["year"],i))
a,n=int(sys.argv[1]),int(sys.argv[2])
def thumb(p,w=330):
    u=p["thumb"].split("?")[0]
    return u.replace("/1280px-",f"/{w}px-") if "/1280px-" in u and p["w"]>w else u
cells=[]
for i,k in enumerate(ids[a:a+n]):
    p=P[k]
    cells.append(f'<figure><img src="{html.escape(thumb(p))}"><figcaption><b>{a+i}</b> {html.escape(p["title"][:40])}</figcaption></figure>')
open(f"{S}/sheet_o.html","w").write("<style>body{margin:0;background:#111;color:#eee;font:11px sans-serif;display:grid;grid-template-columns:repeat(8,1fr);gap:3px;padding:3px}figure{margin:0}img{width:100%;height:150px;object-fit:contain;background:#222}figcaption{padding:1px;height:26px;overflow:hidden}</style>"+"".join(cells))
