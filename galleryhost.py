"""Serve the gallery at the root of its own domain (thegreatgallery.art).

On that host, /p/x is handled as /fineart/p/x, links drop the /fineart prefix, and any old /fineart/... URL
redirects to the clean one. Music history, concert listings, and photography keep
their public paths. /music is the landing page for concerts, history, and practice.
"""
import os

from flask import request, url_for as flask_url_for

HOSTS = {h.strip().lower() for h in os.environ.get("GALLERY_HOSTS", "thegreatgallery.art,www.thegreatgallery.art").split(",") if h.strip()}
CANONICAL = os.environ.get("GALLERY_CANONICAL_HOST", "thegreatgallery.art")
LEGACY_HOSTS = {"theburrowowls.com", "www.theburrowowls.com"}


class GalleryHostMiddleware:
    def __init__(self, wsgi):
        self.wsgi = wsgi

    def __call__(self, environ, start_response):
        host = (environ.get("HTTP_X_FORWARDED_HOST") or environ.get("HTTP_HOST") or "").split(",")[0].strip().lower().split(":")[0]
        path = environ.get("PATH_INFO") or "/"
        qs = environ.get("QUERY_STRING", "")
        scheme = (environ.get("HTTP_X_FORWARDED_PROTO") or environ.get("wsgi.url_scheme") or "https").split(",")[0]

        def redirect(url):
            start_response("301 Moved Permanently", [("Location", url), ("Content-Length", "0")])
            return [b""]

        # Old calendar bookmarks and cached links should land on the Gallery.
        if host in LEGACY_HOSTS and (path == "/music" or path.startswith("/music/")):
            destination = "/music/concerts" if path.rstrip("/") == "/music" else path
            return redirect(f"https://{CANONICAL}{destination}" + (f"?{qs}" if qs else ""))
        if host not in HOSTS:
            return self.wsgi(environ, start_response)
        environ["fa.gallery_host"] = True

        if host != CANONICAL:
            return redirect(f"{scheme}://{CANONICAL}{path}" + (f"?{qs}" if qs else ""))
        if path == "/fineart" or path.startswith("/fineart/"):
            if environ.get("REQUEST_METHOD") in ("GET", "HEAD"):
                clean = path[len("/fineart"):] or "/"
                return redirect(clean + (f"?{qs}" if qs else ""))
            return self.wsgi(environ, start_response)
        if path == "/robots.txt" or path.startswith("/static/") or path == "/photography" or path.startswith("/photography/"):
            return self.wsgi(environ, start_response)
        if path == "/music" or path.startswith("/music/"):
            choir_path = (path.rstrip("/") == "/music/practice" or
                          path == "/music/library.json" or path.startswith("/music/sources/"))
            if not choir_path:
                return self.wsgi(environ, start_response)
        environ["PATH_INFO"] = "/fineart" + path
        return self.wsgi(environ, start_response)


def is_gallery_host():
    return bool(request and request.environ.get("fa.gallery_host"))


def _strip(u):
    if u == "/fineart":
        return "/"
    if u.startswith("/fineart/"):
        return u[len("/fineart"):]
    if u.startswith("/fineart?"):
        return "/" + u[len("/fineart"):]
    return u


def init_gallery_host(app):
    # Public tracking ID, not an account ID or API credential. An empty override
    # disables analytics without changing templates.
    app.config.setdefault("UMAMI_WEBSITE_ID", os.environ.get(
        "UMAMI_WEBSITE_ID", "396a7fd0-b7ee-462b-992d-41f2b601cd8a"))

    def fa_url_for(endpoint, **values):
        u = flask_url_for(endpoint, **values)
        return _strip(u) if is_gallery_host() and not values.get("_external") else u

    app.jinja_env.globals["url_for"] = fa_url_for

    @app.context_processor
    def _base():
        return {
            "fa_base": "" if is_gallery_host() else "/fineart",
            "gallery_analytics_id": app.config["UMAMI_WEBSITE_ID"] if (
                is_gallery_host() and request.endpoint and
                request.blueprint in ("fineart", "photo", "choir", "music")
            ) else None,
        }

    app.wsgi_app = GalleryHostMiddleware(app.wsgi_app)
