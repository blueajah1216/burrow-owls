"""Library of Congress photo sweeps -> c_loc.json. Queries: (query, how many, group)."""
import json, re, sys, time, requests, warnings
warnings.filterwarnings("ignore")
H = {"User-Agent": "BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
Q = [
 # (query, n, extra filter)
 ("migrant mother lange", 2), ("dorothea lange", 14), ("walker evans", 14), ("arthur rothstein dust", 5), ("russell lee", 8), ("jack delano", 8),
 ("marion post wolcott", 8), ("gordon parks american gothic", 3), ("gordon parks", 8), ("ben shahn", 6), ("john vachon", 6), ("carl mydans", 5),
 ("russell lee pie town", 3), ("john collier", 4), ("esther bubley", 6), ("jack delano locomotive", 3), ("alfred palmer aircraft", 5),
 ("lewis hine child labor", 14), ("lewis hine empire state building", 5), ("lewis hine spinner cotton mill", 3), ("jacob riis tenement", 6), ("jacob riis how the other half lives", 4),
 ("mathew brady portrait", 8), ("alexander gardner antietam", 8), ("alexander gardner lincoln", 4), ("timothy o'sullivan harvest of death gettysburg", 3), ("timothy o'sullivan", 6),
 ("george barnard sherman atlanta", 4), ("civil war photographs", 14), ("edward curtis north american indian", 14), ("edward s. curtis", 8),
 ("prokudin-gorskii", 28), ("prokudin-gorskii tolstoy", 2), ("detroit publishing company photochrom", 24), ("carol m. highsmith", 24),
 ("frances benjamin johnston", 10), ("bain news service", 10), ("harris & ewing", 6), ("toni frissell", 8), ("arnold genthe", 10), ("arnold genthe san francisco earthquake", 4),
 ("george grantham bain", 4), ("wright brothers first flight kitty hawk", 3), ("wright brothers", 5), ("william henry jackson yellowstone", 8), ("william henry jackson", 6),
 ("carleton watkins yosemite", 6), ("eadweard muybridge", 8), ("underwood stereograph", 4), ("c. m. bell portrait", 3), ("louis daguerre daguerreotype", 5), ("daguerreotype portrait", 10),
 ("frederick douglass portrait", 3), ("abraham lincoln photograph", 6), ("harriet tubman", 2), ("sojourner truth", 2), ("mark twain", 2), ("buffalo bill", 2), ("geronimo", 3), ("sitting bull", 2),
 ("amelia earhart", 2), ("albert einstein", 2), ("ansel adams", 3), ("dust bowl", 6), ("child laborers", 6), ("breaker boys", 2), ("jackie robinson", 2), ("dorothea lange japanese american", 4),
 ("harlem", 4), ("lunch atop a skyscraper", 1), ("brooklyn bridge photograph", 4), ("coney island", 4), ("new york skyline", 5), ("titanic", 4), ("hindenburg", 2), ("v-j day", 2),
 ("martin luther king march on washington", 3), ("marion trikosko", 6), ("warren k. leffler", 6), ("us news world report photograph", 4), ("yosemite valley photograph", 4),
 ("niagara falls photograph", 4), ("grand canyon photograph", 4), ("panama canal construction", 4), ("elephants circus photograph", 2), ("baseball photograph", 4), ("women suffrage parade", 3),
 ("bonus army", 2), ("soup kitchen depression", 3), ("hoovervilles", 2), ("tenant farmer", 5), ("sharecropper", 5), ("coal miners", 5), ("steelworkers", 3), ("shipyard", 3), ("rosie riveter", 3),
 ("iwo jima flag", 2), ("d-day normandy", 3), ("hiroshima", 2), ("tuskegee airmen", 3), ("harlem renaissance", 2), ("duke ellington", 2), ("louis armstrong", 2), ("billie holiday", 2), ("jazz photograph gottlieb", 8),
]
seen = {}
for q, n in Q:
    try:
        r = requests.get("https://www.loc.gov/photos/", params={"q": q, "fo": "json", "c": n, "fa": "online-format:image", "at": "results"}, headers=H, timeout=60).json()
    except Exception as e:
        print("ERR", q, e); continue
    k = 0
    for it in r.get("results", []):
        iu = it.get("image_url") or []
        if not iu or str(it.get("unrestricted")) != "True": continue
        u = iu[-1].split("#")[0] if isinstance(iu, list) else iu
        m = re.match(r"(https://tile.loc.gov/storage-services/service/.+?/[0-9a-z]+?)(_150px\.jpg|t\.gif|r\.jpg|v\.jpg)$", u)
        if not m: continue
        item = it.get("item") or {}
        sid = it["id"].rstrip("/").rsplit("/", 1)[1]
        if sid in seen: seen[sid]["qs"].append(q); continue
        base = m.group(1)
        seen[sid] = {"src": "loc", "sid": sid, "title": it.get("title"), "date": it.get("date"), "contrib": item.get("contributor_names") or it.get("contributor"),
                     "loc": it.get("location"), "base": base, "url": it["url"], "q": q, "qs": [q], "notes": (item.get("notes") or [])[:3], "medium": item.get("medium"),
                     "subjects": (item.get("subject_headings") or [])[:6], "partof": it.get("partof")}
        k += 1
    print(q, k, len(seen), flush=True); time.sleep(1.2)
json.dump(list(seen.values()), open("c_loc.json", "w"), ensure_ascii=False)
