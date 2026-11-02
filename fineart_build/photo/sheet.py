"""usage: sheet.py list.json start n  -> screenshot at scratchpad/ph_<start>.png (8 per row, 5 rows)"""
import json, sys, html, subprocess, os, hashlib, requests
from concurrent.futures import ThreadPoolExecutor
H = {"User-Agent": "BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
C = "/private/tmp/claude-501/-Users-whitetower-dev-burrow-owls/717d435b-0809-4761-bc97-df7352efb381/scratchpad/thumbs"; os.makedirs(C, exist_ok=True)
def local(u):
    f = f"{C}/{hashlib.md5(u.encode()).hexdigest()}.jpg"
    if not os.path.exists(f):
        try: open(f, "wb").write(requests.get(u, headers=H, timeout=40).content)
        except Exception: return u
    return "file://" + f
S = "/private/tmp/claude-501/-Users-whitetower-dev-burrow-owls/717d435b-0809-4761-bc97-df7352efb381/scratchpad"
rows = json.load(open(sys.argv[1])); a, n = int(sys.argv[2]), int(sys.argv[3])
with ThreadPoolExecutor(8) as ex: locs = list(ex.map(local, [r["th"] for r in rows[a:a + n]]))
cells = []
for i, r in enumerate(rows[a:a + n]):
    cells.append(f'<figure><img src="{html.escape(locs[i])}"><figcaption><b>{a+i}</b> {html.escape((r["title"] or "")[:34])} <i>{html.escape((r.get("who") or "")[:18])} {r.get("y") or ""}</i></figcaption></figure>')
open(f"{S}/sheet_p.html", "w").write("<style>body{margin:0;background:#111;color:#eee;font:11px sans-serif;display:grid;grid-template-columns:repeat(8,1fr);gap:3px;padding:3px}figure{margin:0}img{width:100%;height:150px;object-fit:contain;background:#222}figcaption{padding:1px;height:38px;overflow:hidden}i{color:#9c9}</style>" + "".join(cells))
subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--headless", "--disable-gpu", "--hide-scrollbars", "--window-size=1500,1260", "--virtual-time-budget=25000", f"--screenshot={S}/ph_{a}.png", f"file://{S}/sheet_p.html"], capture_output=True)
print(f"{S}/ph_{a}.png")
