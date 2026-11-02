"""Library of Congress, second sweep -> c_loc3.json. One request every 3 s, honest UA; stops on any 429/403."""
import json, re, sys, time, requests, warnings, signal, os
warnings.filterwarnings("ignore")
H = {"User-Agent": "BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
C = "https://www.loc.gov/collections/"
JOBS = []
P = "https://www.loc.gov/photos/"
for q, n in [("trikosko", 3), ("leffler", 3), ("civil rights march washington", 2), ("martin luther king", 2), ("kennedy 1960", 2), ("beatles", 1), ("muhammad ali", 1), ("vietnam war protest", 2), ("nixon", 1), ("lyndon johnson", 1), ("eisenhower", 1), ("truman", 1), ("korean war", 1), ("astronauts", 1), ("moon landing", 1), ("selma", 1), ("freedom riders", 1), ("woodstock", 1), ("elvis presley", 1), ("jazz musician", 2), ("baseball player", 1), ("olympic athletes", 1), ("1950s street scene", 1), ("1960s demonstration", 2), ("1970s", 1), ("segregation", 1), ("school integration", 1), ("lunch counter sit-in", 1), ("peace march", 1), ("womens liberation", 1), ("earth day", 1), ("gas lines", 1), ("jackie kennedy", 1), ("first lady", 1), ("press conference", 1), ("fashion model", 1), ("new york city 1960s", 1), ("washington monument crowd", 1), ("space shuttle", 1)]:
    JOBS.append((P, {"q": q}, n, "p:" + q))
out = {x["sid"]: x for x in json.load(open("c_loc3.json"))} if os.path.exists("c_loc3.json") else {}
DONE = set(json.load(open("loc3_done.json"))) if os.path.exists("loc3_done.json") else set()
class TO(Exception): pass
def _alarm(*a): raise TO()
signal.signal(signal.SIGALRM, _alarm)
for url, params, pages, tag in JOBS:
    if tag in DONE: continue
    for pg in range(1, pages + 1):
        p = dict(params, fo="json", c=100, sp=pg, fa=params.get("fa", "") or "online-format:image") if "fa" not in params else dict(params, fo="json", c=100, sp=pg)
        signal.alarm(100)
        try: resp = requests.get(url, params=p, headers=H, timeout=60); body = resp.content
        except BaseException as e: signal.alarm(0); print("ERR", tag, type(e).__name__); time.sleep(5); continue
        signal.alarm(0)
        if resp.status_code in (403, 429):
            print("STOP", resp.status_code, tag); json.dump(list(out.values()), open("c_loc3.json", "w"), ensure_ascii=False); sys.exit()
        try: r = resp.json()
        except Exception: print("badjson", tag, resp.status_code); break
        n = 0
        for it in r.get("results", []):
            iu = it.get("image_url") or []
            if not iu or str(it.get("unrestricted", "True")) not in ("True", "None"): continue
            u = iu[-1].split("#")[0] if isinstance(iu, list) else iu
            m = re.match(r"(https://tile.loc.gov/storage-services/service/.+?/[0-9a-z]+?)(_150px\.jpg|t\.gif|r\.jpg|v\.jpg)$", u)
            if not m: continue
            item = it.get("item") or {}
            sid = it["id"].rstrip("/").rsplit("/", 1)[1]
            if sid in out: continue
            out[sid] = {"src": "loc", "sid": sid, "title": it.get("title"), "date": it.get("date"), "contrib": item.get("contributor_names") or it.get("contributor"),
                        "loc": it.get("location"), "base": m.group(1), "url": it["url"], "q": tag, "qs": [tag], "notes": (item.get("notes") or [])[:3], "medium": item.get("medium"),
                        "subjects": (item.get("subject_headings") or [])[:6], "partof": it.get("partof")}
            n += 1
        print(tag, pg, n, len(out), flush=True)
        if len(r.get("results", [])) < 100: break
        time.sleep(3)
    DONE.add(tag); json.dump(sorted(DONE), open("loc3_done.json", "w")); json.dump(list(out.values()), open("c_loc3.json", "w"), ensure_ascii=False)
    time.sleep(3)
json.dump(list(out.values()), open("c_loc3.json", "w"), ensure_ascii=False)
print("done", len(out))
