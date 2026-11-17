"""Four-part singing practice, separate from the Seattle concert calendar."""
import json
from pathlib import Path

from flask import Blueprint, render_template, send_from_directory

bp = Blueprint("choir", __name__, url_prefix="/fineart/music")
DATA = Path(__file__).resolve().parent / "data" / "choir"


def init_choir(app):
    app.register_blueprint(bp)


@bp.route("")
@bp.route("/")
def index():
    catalog = json.loads((DATA / "library.json").read_text())
    return render_template("choir/index.html", songs=catalog)


@bp.route("/library.json")
def library():
    return send_from_directory(DATA, "library.json", max_age=3600)


@bp.route("/sources/<path:filename>")
def source(filename):
    return send_from_directory(DATA / "sources", filename, as_attachment=True)
