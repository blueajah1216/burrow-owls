"""python3 sheet.py START COUNT -> writes scratchpad sheet_h.html with labeled thumbnails of base4 paintings."""
import json, sys, html
S="/private/tmp/claude-501/-Users-whitetower-dev-burrow-owls/717d435b-0809-4761-bc97-df7352efb381/scratchpad"
d=json.load(open("../base4.json")); P=d["paintings"]
a,n=int(sys.argv[1]),int(sys.argv[2])
def thumb(p,w=330):
    u=p["thumb"].split("?")[0]
    if "/1280px-" in u and p["w"]>w: return u.replace("/1280px-",f"/{w}px-")
    return u
cells=[]
for i,p in enumerate(P[a:a+n]):
    nm=", ".join(d["artists"].get(x,{}).get("name",x) for x in p["artist_ids"])[:26]
    cells.append(f'<figure><img src="{html.escape(thumb(p))}"><figcaption><b>{a+i}</b> {html.escape(p["id"][:34])}<br>{html.escape(p["title"][:44])}<br><i>{html.escape(nm)} {p["year"]}</i></figcaption></figure>')
open(f"{S}/sheet_h.html","w").write("<style>body{margin:0;background:#111;color:#eee;font:11px sans-serif;display:grid;grid-template-columns:repeat(6,1fr);gap:4px;padding:4px}figure{margin:0}img{width:100%;height:150px;object-fit:contain;background:#222}figcaption{padding:2px;height:50px;overflow:hidden}</style>"+"".join(cells))
print(len(cells))
