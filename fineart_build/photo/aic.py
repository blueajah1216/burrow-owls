import json, requests, time, warnings, collections
warnings.filterwarnings("ignore")
H = {"User-Agent": "BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
out = []; page = 1
F = "id,title,artist_display,artist_title,date_display,date_start,medium_display,image_id,is_public_domain,credit_line,description,short_description,place_of_origin,classification_title,department_title,thumbnail,dimensions,color,publication_history,exhibition_history,is_boosted,pageviews"
while page <= 40:
    body = {"query": {"bool": {"must": [{"term": {"is_public_domain": True}}, {"term": {"classification_titles.keyword": "photography"}}, {"exists": {"field": "image_id"}}]}},
            "fields": F.split(","), "limit": 100, "page": page, "sort": [{"pageviews": "desc"}]}
    r = requests.post("https://api.artic.edu/api/v1/artworks/search", json=body, headers=H, timeout=60)
    if r.status_code != 200: print(r.status_code, r.text[:200]); break
    j = r.json()
    for a in j["data"]:
        th = a.get("thumbnail") or {}
        out.append({k: a.get(k) for k in ("id", "title", "artist_title", "artist_display", "date_display", "date_start", "medium_display", "image_id", "credit_line", "description", "short_description", "place_of_origin", "pageviews")} | {"w": th.get("width"), "h": th.get("height")})
    print(page, len(out), j["pagination"]["total"], flush=True)
    if page >= j["pagination"]["total_pages"]: break
    page += 1; time.sleep(1.2)
json.dump(out, open("c_aic.json", "w"), ensure_ascii=False)
print(collections.Counter(a["artist_title"] for a in out).most_common(40))
