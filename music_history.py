"""A curated, file-backed listening history, alongside the concert calendar."""

import json
import unicodedata
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlencode

from flask import abort, render_template, request


def search_text(value):
    return "".join(c for c in unicodedata.normalize("NFKD", value.casefold())
                   if not unicodedata.combining(c))


@lru_cache(maxsize=1)
def load_history():
    path = Path(__file__).parent / "data" / "music_history" / "history.json"
    data = json.loads(path.read_text())
    composers = {c["id"]: c for c in data["composers"]}
    eras = {e["id"]: e for e in data["eras"]}
    for composer in composers.values():
        composer["works"] = [w for w in data["works"] if w["composer"] == composer["id"]]
        composer["search"] = search_text(" ".join([
            composer["name"], composer["place"], composer["signature"],
            composer["bio"], *(w["title"] for w in composer["works"]),
        ]))
    for work in data["works"]:
        composer = composers[work["composer"]]
        work["search"] = search_text(" ".join([
            work["title"], composer["name"], work["form"],
            work["description"], work["importance"],
        ]))
        work["recording_url"] = "https://www.youtube.com/results?" + urlencode({
            "search_query": f'{composer["name"]} {work["title"]} full performance',
        })
    for era in data["eras"]:
        era["works"] = [w for w in data["works"] if w["era"] == era["id"]]
        era["composers"] = sorted(
            (c for c in composers.values() if c["era"] == era["id"]),
            key=lambda c: (c["birth"], c["name"]),
        )
    return data, composers, eras


def register_history_routes(bp, ctx_fn):
    @bp.get("/history")
    def history():
        data, composers, eras = load_history()
        view = "composers" if request.args.get("view") == "composers" else "works"
        era_id = request.args.get("era", "all")
        if era_id not in eras:
            era_id = "all"
        query = request.args.get("q", "").strip()[:200]
        tokens = search_text(query).split()
        visible_ids = {
            item["id"] for era in data["eras"] for item in era[view]
            if (era_id == "all" or era_id == era["id"])
            and all(token in item["search"] for token in tokens)
        }
        return render_template(
            "music_history/timeline.html", **ctx_fn(), data=data,
            composers=composers, eras=eras, view=view, selected_era=era_id,
            query=query, visible_ids=visible_ids,
        )

    @bp.get("/history/pieces/<slug>")
    def history_piece(slug):
        data, composers, eras = load_history()
        work = next((w for w in data["works"] if w["id"] == slug), None)
        if work is None:
            abort(404)
        index = data["works"].index(work)
        composer = composers[work["composer"]]
        return render_template(
            "music_history/piece.html", **ctx_fn(), work=work,
            composer=composer, era=eras[work["era"]],
            composer_era=eras[composer["era"]],
            previous=data["works"][index - 1] if index else None,
            following=data["works"][index + 1] if index + 1 < len(data["works"]) else None,
            related=[w for w in composer["works"] if w is not work],
        )

    @bp.get("/history/composers/<slug>")
    def history_composer(slug):
        data, composers, eras = load_history()
        composer = composers.get(slug)
        if composer is None:
            abort(404)
        peers = sorted(composers.values(), key=lambda c: (c["birth"], c["name"]))
        index = peers.index(composer)
        return render_template(
            "music_history/composer.html", **ctx_fn(), composer=composer,
            era=eras[composer["era"]], eras=eras,
            previous=peers[index - 1] if index else None,
            following=peers[index + 1] if index + 1 < len(peers) else None,
        )
