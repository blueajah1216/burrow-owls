import json, time, requests, warnings
warnings.filterwarnings("ignore")
H = {"User-Agent": "BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
Q = [("earthrise apollo 8", 2), ("blue marble apollo 17", 2), ("pale blue dot voyager", 1), ("pillars of creation hubble", 2), ("hubble ultra deep field", 2), ("buzz aldrin moon visor", 2),
 ("apollo 11 bootprint", 1), ("apollo 11 neil armstrong", 2), ("apollo 17 moonwalk", 2), ("apollo 14 shepard", 1), ("saturn cassini rings", 3), ("curiosity selfie mars", 2), ("space shuttle launch", 3),
 ("international space station over earth", 3), ("great red spot juno", 2), ("horsehead nebula", 1), ("crab nebula", 1), ("sombrero galaxy", 1), ("webb cosmic cliffs carina", 2), ("webb stephan's quintet", 1),
 ("webb deep field smacs", 1), ("eagle nebula", 1), ("voyager jupiter", 1), ("pluto new horizons", 2), ("total solar eclipse corona", 2), ("opportunity mars panorama", 2), ("ingenuity helicopter shadow", 1),
 ("perseverance mars", 2), ("aurora from space station", 2), ("andromeda galaxy", 1), ("whirlpool galaxy", 1), ("tarantula nebula", 1), ("mars sunset spirit", 1), ("hubble eye of god helix nebula", 1),
 ("apollo 13 earth moon", 1), ("gemini spacewalk ed white", 1), ("first american in space alan shepard", 1), ("sun solar dynamics observatory flare", 2), ("earth from space night lights", 2), ("hurricane from space", 2),
 ("saturn hexagon", 1), ("europa jupiter moon galileo", 1), ("mercury messenger", 1), ("comet 67p rosetta", 1), ("titan surface huygens", 1), ("lunar module eagle", 1), ("astronaut spacewalk earth", 3),
 ("space shuttle challenger", 1), ("columbia shuttle", 1), ("hubble repair mission", 1), ("moon far side", 1), ("earth from moon orion artemis", 2), ("webb ring nebula", 1), ("webb southern ring nebula", 1), ("webb jupiter", 1)]
out = {}
for q, n in Q:
    r = requests.get("https://images-api.nasa.gov/search", params={"q": q, "media_type": "image"}, headers=H, timeout=60).json()
    k = 0
    for it in r.get("collection", {}).get("items", []):
        d = it["data"][0]
        if d["nasa_id"] in out or not it.get("links"): continue
        out[d["nasa_id"]] = {"src": "nasa", "sid": d["nasa_id"], "title": d["title"], "date": d.get("date_created", "")[:10], "desc": d.get("description", ""), "center": d.get("center"),
                             "photographer": d.get("photographer") or d.get("secondary_creator"), "keywords": d.get("keywords", []), "q": q, "thumb": it["links"][0]["href"], "page": f"https://images.nasa.gov/details/{d['nasa_id']}"}
        k += 1
        if k >= n: break
    print(q, k, flush=True); time.sleep(.4)
json.dump(list(out.values()), open("c_nasa.json", "w"), ensure_ascii=False)
