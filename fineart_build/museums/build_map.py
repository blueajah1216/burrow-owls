"""Decode world-atlas countries-110m TopoJSON into one SVG path string (equirectangular, K px/degree)."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
K, TOP = 5, 84
t = json.load(open(os.path.join(HERE, "countries-110m.json")))
sx, sy = t["transform"]["scale"]; tx, ty = t["transform"]["translate"]
arcs = []
for a in t["arcs"]:
    x = y = 0; pts = []
    for dx, dy in a:
        x += dx; y += dy
        pts.append((x * sx + tx, y * sy + ty))
    arcs.append(pts)
def ring(idx):
    out = []
    for i in idx:
        pts = arcs[i] if i >= 0 else arcs[~i][::-1]
        out += pts if not out else pts[1:]
    return out
def path(pts):
    pts = [p for p in pts if p[1] > -60]
    out, seg = [], []
    for i, p in enumerate(pts):
        if seg and abs(p[0] - seg[-1][0]) > 180:  # crosses the antimeridian: break the line
            out.append(seg); seg = []
        seg.append(p)
    out.append(seg)
    return "".join("M" + "L".join(f"{round((lon+180)*K,1)} {round((TOP-lat)*K,1)}" for lon, lat in s) + "Z" for s in out if len(s) > 2)
d = []
for g in t["objects"]["countries"]["geometries"]:
    polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]] if g["type"] == "Polygon" else []
    for poly in polys:
        for r in poly:
            d.append(path(ring(r)))
json.dump(dict(d="".join(d), k=K, top=TOP, w=360 * K, h=(TOP + 60) * K), open(os.path.join(HERE, "..", "..", "static/fineart/world.json"), "w"), separators=(",", ":"))
print(len("".join(d)))
