#!/usr/bin/env python3
"""Back up the hi-res originals of the gallery to Backblaze B2 (private bucket, fallback only).

Usage (from the repo root, with the venv):
  .venv/bin/python backup/backup_hires.py --site photo --dry-run     # list + total size, uploads nothing
  .venv/bin/python backup/backup_hires.py --site photo               # download + upload, resumable
  .venv/bin/python backup/backup_hires.py --site paintings           # same for the paintings
Options: --limit N (first N only), --delay SECONDS (default 1.5 between downloads from the same host)

Env vars (never commit these):
  B2_KEY_ID, B2_APP_KEY, B2_BUCKET, B2_ENDPOINT   e.g. https://s3.us-west-004.backblazeb2.com

Objects are stored as  <site>/<id>.<ext>  with the source page, license and credit in object metadata,
and a manifest.json per site. Files already in the bucket are skipped, so it is safe to re-run.
If a source answers 403/429 the script stops for that host instead of retrying hard.
"""
import argparse, json, mimetypes, os, re, sys, tempfile, time
from urllib.parse import urlparse, unquote

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
UA = {"User-Agent": "BurrowOwlsFineArtBackup/1.0 (blueajah@pm.me)"}


def items(site):
    if site == "photo":
        d = json.load(open(os.path.join(ROOT, "data/photo/gallery.json")))
        for p in d["photos"]:
            yield dict(id=p["id"], url=p["hi"], page=p["p"], lic=p.get("lic", ""), credit=p.get("by") or p.get("cr") or "", title=p["t"])
    else:
        import fineart
        d = fineart.load()
        for p in d["paintings"]:
            yield dict(id=p["id"], url=fineart.original_url(p), page=p["p"], lic="Public domain", credit="", title=p["t"])


def ext_of(url, ctype=""):
    m = re.search(r"\.([A-Za-z0-9]{2,5})(?:$|\?)", urlparse(url).path + ("?" if "?" not in url else "?"))
    e = (m.group(1).lower() if m else "") or (mimetypes.guess_extension(ctype.split(";")[0]) or ".bin").lstrip(".")
    return "jpg" if e == "jpeg" else e


def ascii_meta(s, n=200):
    return unquote(str(s)).encode("ascii", "ignore").decode()[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", choices=["photo", "paintings"], required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--delay", type=float, default=1.5)
    a = ap.parse_args()
    its = list(items(a.site))[: a.limit]
    s3 = None
    if not a.dry_run:
        import boto3
        from botocore.config import Config
        need = [k for k in ("B2_KEY_ID", "B2_APP_KEY", "B2_BUCKET", "B2_ENDPOINT") if not os.environ.get(k)]
        if need: sys.exit("Missing env vars: " + ", ".join(need))
        s3 = boto3.client("s3", endpoint_url=os.environ["B2_ENDPOINT"], aws_access_key_id=os.environ["B2_KEY_ID"], aws_secret_access_key=os.environ["B2_APP_KEY"], config=Config(retries={"max_attempts": 5}))
        bucket = os.environ["B2_BUCKET"]
        have = set()
        for pg in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=a.site + "/"):
            have |= {o["Key"] for o in pg.get("Contents", [])}
        print(len(have), "objects already in the bucket")
    blocked, total, done, manifest = set(), 0, 0, []
    last = {}
    for n, it in enumerate(its, 1):
        host = urlparse(it["url"]).netloc
        if host in blocked:
            print("skip (host blocked)", it["id"]); continue
        wait = a.delay - (time.time() - last.get(host, 0))
        if wait > 0: time.sleep(wait)
        last[host] = time.time()
        try:
            if a.dry_run:
                r = requests.head(it["url"], headers=UA, timeout=30, allow_redirects=True)
                if r.status_code in (403, 429): blocked.add(host); print("BLOCKED", host, r.status_code); continue
                size = int(r.headers.get("Content-Length") or 0); total += size
                print(f"{n}/{len(its)} {it['id']} {size/1e6:.1f} MB {ext_of(it['url'], r.headers.get('Content-Type',''))}")
                continue
            key_guess = f"{a.site}/{it['id']}."
            if any(k.startswith(key_guess) for k in have):
                done += 1; continue
            with requests.get(it["url"], headers=UA, timeout=120, stream=True) as r:
                if r.status_code in (403, 429): blocked.add(host); print("BLOCKED", host, r.status_code); continue
                r.raise_for_status()
                ext = ext_of(it["url"], r.headers.get("Content-Type", ""))
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    for chunk in r.iter_content(1 << 20): tmp.write(chunk)
                size = os.path.getsize(tmp.name)
            key = f"{a.site}/{it['id']}.{ext}"
            s3.upload_file(tmp.name, bucket, key, ExtraArgs={"ContentType": mimetypes.guess_type("x." + ext)[0] or "application/octet-stream",
                           "Metadata": {"source-url": ascii_meta(it["url"]), "source-page": ascii_meta(it["page"]), "license": ascii_meta(it["lic"]), "credit": ascii_meta(it["credit"]), "title": ascii_meta(it["title"], 100)}})
            os.unlink(tmp.name)
            total += size; done += 1
            manifest.append(dict(id=it["id"], key=key, bytes=size, source=it["url"], page=it["page"], license=it["lic"], credit=it["credit"], title=it["title"]))
            print(f"{n}/{len(its)} uploaded {key} {size/1e6:.1f} MB", flush=True)
        except Exception as e:
            print("ERROR", it["id"], str(e)[:120])
    print(f"done: {done} items, {total/1e9:.2f} GB {'(estimated)' if a.dry_run else 'uploaded this run'}; blocked hosts: {sorted(blocked) or 'none'}")
    if not a.dry_run and manifest:
        body = json.dumps(manifest, indent=1, ensure_ascii=False).encode()
        s3.put_object(Bucket=bucket, Key=f"{a.site}/manifest-{int(time.time())}.json", Body=body, ContentType="application/json")


if __name__ == "__main__":
    main()
