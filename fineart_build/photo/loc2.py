"""Library of Congress, second sweep -> c_loc2.json. One request every 3 s, honest UA; stops on any 429/403."""
import json, re, sys, time, requests, warnings, signal, os
warnings.filterwarnings("ignore")
H = {"User-Agent": "BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
C = "https://www.loc.gov/collections/"
JOBS = []  # (url, params, pages, tag)
JOBS.append((C + "fsa-owi-color-photographs/", {}, 9, "fsac"))
for q in ["dust storm", "migrant", "tenant farmer", "sharecropper", "child", "children playing", "mill workers", "cotton", "church", "main street", "family", "mother", "farmer", "miner", "factory", "train", "railroad", "bus", "diner", "barber", "street scene", "harvest", "school", "soldier", "war bond", "aircraft", "shipyard", "women workers", "migrant camp", "Christmas", "parade", "fair", "rodeo", "farm", "cabin", "interior", "portrait"]:
    JOBS.append((C + "fsa-owi-black-and-white-negatives/", {"q": q}, 1, "fsa:" + q))
for q in ["lange", "evans walker", "rothstein", "russell lee", "delano", "wolcott", "vachon", "parks gordon", "bubley", "collier", "palmer", "mydans", "shahn", "post wolcott"]:
    JOBS.append((C + "fsa-owi-black-and-white-negatives/", {"q": q}, 2, "fsa:" + q))
for q in ["yosemite", "grand canyon", "new york", "san francisco", "chicago", "new orleans", "washington monument", "statue of liberty", "golden gate", "lighthouse", "covered bridge", "barn", "waterfall", "canyon", "mountain", "desert", "glacier", "river", "lake", "bridge", "sunset", "skyline", "mural", "neon sign", "diner", "church", "cathedral", "capitol", "monument", "fall foliage", "snow", "beach", "carousel", "locomotive", "farm", "harbor", "boats", "fishing", "cowboy", "festival", "bison", "wildlife", "arch", "waterfront", "railroad", "memorial", "tower", "hot air balloons", "cactus", "swamp"]:
    JOBS.append((C + "carol-m-highsmith/", {"q": q}, 1, "hs:" + q))
JOBS.append((C + "photochrom-prints/", {}, 8, "photochrom"))
JOBS.append((C + "detroit-publishing-company/", {"q": "photograph"}, 5, "detroit"))
for q in ["portrait officer", "battlefield dead", "ruins", "camp", "bridge", "railroad", "ship", "cannon", "fort", "hospital", "contrabands", "lincoln"]:
    JOBS.append((C + "civil-war-glass-negatives/", {"q": q}, 1, "cw:" + q))
for q in ["trikosko", "leffler", "civil rights march", "kennedy", "beatles", "muhammad ali", "apollo", "vietnam protest", "king", "nixon", "johnson", "bobby kennedy", "truman", "eisenhower", "marilyn", "elvis", "jazz", "baseball", "football", "olympic"]:
    JOBS.append(("https://www.loc.gov/photos/", {"q": q + " u.s. news world report", "fa": "partof:u.s. news & world report magazine photograph collection"}, 1, "usnwr:" + q))
out = {x["sid"]: x for x in json.load(open("c_loc2.json"))} if os.path.exists("c_loc2.json") else {}
DONE = set(json.load(open("loc2_done.json"))) if os.path.exists("loc2_done.json") else set()
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
            print("STOP", resp.status_code, tag); json.dump(list(out.values()), open("c_loc2.json", "w"), ensure_ascii=False); sys.exit()
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
    DONE.add(tag); json.dump(sorted(DONE), open("loc2_done.json", "w")); json.dump(list(out.values()), open("c_loc2.json", "w"), ensure_ascii=False)
    time.sleep(3)
json.dump(list(out.values()), open("c_loc2.json", "w"), ensure_ascii=False)
print("done", len(out))
