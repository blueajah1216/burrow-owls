"""Four-part singing practice, separate from the Seattle concert calendar."""
import json
import hashlib
from pathlib import Path

from flask import Blueprint, render_template, send_from_directory

bp = Blueprint("choir", __name__, url_prefix="/fineart/music")
DATA = Path(__file__).resolve().parent / "data" / "choir"


def init_choir(app):
    app.register_blueprint(bp)


@bp.route("/practice/")
@bp.route("/practice")
def index():
    raw_catalog = (DATA / "library.json").read_bytes()
    catalog = json.loads(raw_catalog)
    preferred = ['Jewish songs', 'Folk songs around the world', 'Folk & familiar',
                 'Anthems', 'Christmas carols', 'Hymns & spirituals']
    categories = sorted({song['category'] for song in catalog},
                        key=lambda value: (preferred.index(value) if value in preferred else len(preferred), value))
    return render_template("choir/index.html", songs=catalog, categories=categories,
                           catalog_version=hashlib.sha256(raw_catalog).hexdigest()[:12])


@bp.route("/library.json")
def library():
    return send_from_directory(DATA, "library.json", max_age=3600)


@bp.route("/sources/<path:filename>")
def source(filename):
    return send_from_directory(DATA / "sources", filename, as_attachment=True)
