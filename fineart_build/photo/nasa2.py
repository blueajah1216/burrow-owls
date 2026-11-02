"""More NASA: space, Earth, aeronautics -> c_nasa2.json + nasa_urls2.json (verified size variants). Public domain."""
import json, re, time, requests, warnings
warnings.filterwarnings("ignore")
H = {"User-Agent": "BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
Q = """apollo 8 earthrise|apollo 12 surveyor|apollo 15 rover lunar|apollo 16 young moon|apollo 17 cernan|apollo command module splashdown|apollo saturn v launch|saturn v rollout|mercury seven astronauts|john glenn friendship 7|gemini 4 spacewalk|gemini 7 rendezvous|skylab space station|apollo soyuz handshake|space shuttle atlantis|space shuttle discovery landing|space shuttle endeavour|shuttle mission control|astronaut portrait|sally ride|mae jemison|neil armstrong portrait|buzz aldrin|katherine johnson|mission control apollo 11|viking mars lander|voyager 2 neptune|voyager saturn|galileo jupiter|cassini enceladus|cassini titan|mars reconnaissance orbiter|mars gale crater|mars olympus mons|mars valles marineris|mars dust devil|mars sunset|mars rover tracks|curiosity mars rock|phoenix mars lander|insight mars|moon craters lro|moon earthrise lro|moon south pole|mercury messenger|venus magellan|venus transit|jupiter juno clouds|jupiter io|saturn rings|uranus rings|neptune triton|pluto heart|arrokoth|ceres dawn|vesta dawn|asteroid bennu|asteroid eros|comet hale-bopp|halley comet|comet neowise|meteor shower|hubble carina nebula|hubble orion nebula|hubble butterfly nebula|hubble cat's eye nebula|hubble ring nebula|hubble helix nebula|hubble lagoon nebula|hubble antennae galaxies|hubble whirlpool|hubble andromeda|hubble sombrero|hubble cartwheel galaxy|hubble galaxy cluster lensing|hubble supernova|hubble globular cluster|hubble spiral galaxy|hubble elliptical galaxy|hubble black hole jet|hubble pluto|hubble jupiter|hubble saturn storm|hubble deep field|hubble extreme deep field|chandra x-ray supernova remnant|spitzer infrared nebula|webb carina|webb pillars of creation|webb southern ring|webb cartwheel|webb phantom galaxy|webb orion bar|webb tarantula|webb rho ophiuchi|webb neptune|webb uranus|webb saturn|webb sagittarius|webb cosmic cliffs|webb first images|solar flare|solar eclipse 2017|total eclipse|sun sdo|aurora borealis|aurora australis iss|iss earth horizon|iss astronaut spacewalk|iss solar panels|iss cupola|earth at night|earth blue marble|earth from space hurricane|earth from space volcano|earth from space ice|earth from space river delta|earth from space desert|earth from space clouds|landsat image|landsat farmland|glacier from space|great barrier reef from space|manhattan from iss|dust storm from space|wildfire from space|tornado|lightning from space|x-15|x-1 yeager|sr-71|space shuttle enterprise|wright flyer replica|apollo 1 crew|saturn v test|rocket engine test|lunar rover|moon sample|astronaut helmet reflection|astronaut floating|astronaut tools|launch pad night|space telescope servicing|hubble launch|webb assembly|webb mirror|artemis orion|artemis sls launch|orion earth moon|crew dragon|space x launch|parker solar probe|osiris-rex|dart asteroid impact|ingenuity mars|perseverance selfie|perseverance rock|mars sample|jezero crater""".split("|")
out = {}
for q in Q:
    for attempt in range(3):
        try:
            r = requests.get("https://images-api.nasa.gov/search", params={"q": q, "media_type": "image", "page_size": 12}, headers=H, timeout=60).json(); break
        except Exception: r = {}; time.sleep(3)
    k = 0
    for it in r.get("collection", {}).get("items", []):
        d = it["data"][0]
        if d["nasa_id"] in out or not it.get("links") or "images-assets" not in it["links"][0]["href"]: continue
        out[d["nasa_id"]] = {"src": "nasa", "sid": d["nasa_id"], "title": d["title"], "date": d.get("date_created", "")[:10], "desc": d.get("description", ""), "center": d.get("center"),
                             "photographer": d.get("photographer") or d.get("secondary_creator"), "keywords": d.get("keywords", []), "q": q, "thumb": it["links"][0]["href"], "page": f"https://images.nasa.gov/details/{d['nasa_id']}"}
        k += 1
        if k >= 3: break
    print(q, k, len(out), flush=True); time.sleep(.5)
json.dump(list(out.values()), open("c_nasa2.json", "w"), ensure_ascii=False)
# verify variants
urls = {}
for sid in out:
    base = f"https://images-assets.nasa.gov/image/{sid}/{sid}"
    v = {}
    for suf in ("~medium.jpg", "~large.jpg", "~orig.jpg", "~orig.tif", "~orig.png"):
        try:
            h = requests.head(base + suf, headers=H, timeout=30, allow_redirects=True)
            if h.status_code == 200:
                v["~" + suf[1:].split(".")[0]] = "." + suf.split(".")[-1]
        except Exception: pass
        time.sleep(.1)
    urls[sid] = v
json.dump(urls, open("nasa_urls2.json", "w"))
print("done", len(out))
