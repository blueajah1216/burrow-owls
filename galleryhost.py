"""Serve the gallery at the root of its own domain (thegreatgallery.art).

On that host, /p/x is handled as /fineart/p/x, links drop the /fineart prefix, and any old /fineart/... URL
redirects to the clean one. Every other host (theburrowowls.com) is untouched.
"""
import os

from flask import request, url_for as flask_url_for

HOSTS = {h.strip().lower() for h in os.environ.get("GALLERY_HOSTS", "thegreatgallery.art,www.thegreatgallery.art").split(",") if h.strip()}
CANONICAL = os.environ.get("GALLERY_CANONICAL_HOST", "thegreatgallery.art")


class GalleryHostMiddleware:
    def __init__(self, wsgi):
        self.wsgi = wsgi

    def __call__(self, environ, start_response):
        host = (environ.get("HTTP_X_FORWARDED_HOST") or environ.get("HTTP_HOST") or "").split(",")[0].strip().lower().split(":")[0]
        if host not in HOSTS:
            return self.wsgi(environ, start_response)
        environ["fa.gallery_host"] = True
        path = environ.get("PATH_INFO") or "/"
        qs = environ.get("QUERY_STRING", "")
        scheme = (environ.get("HTTP_X_FORWARDED_PROTO") or environ.get("wsgi.url_scheme") or "https").split(",")[0]

        def redirect(url):
            start_response("301 Moved Permanently", [("Location", url), ("Content-Length", "0")])
            return [b""]

        if host != CANONICAL:
            return redirect(f"{scheme}://{CANONICAL}{path}" + (f"?{qs}" if qs else ""))
        if path == "/fineart" or path.startswith("/fineart/"):
            if environ.get("REQUEST_METHOD") in ("GET", "HEAD"):
                clean = path[len("/fineart"):] or "/"
                return redirect(clean + (f"?{qs}" if qs else ""))
            return self.wsgi(environ, start_response)
        if path == "/robots.txt" or path.startswith("/static/") or path == "/photography" or path.startswith("/photography/"):
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
    def fa_url_for(endpoint, **values):
        u = flask_url_for(endpoint, **values)
        return _strip(u) if is_gallery_host() and not values.get("_external") else u

    app.jinja_env.globals["url_for"] = fa_url_for

    @app.context_processor
    def _base():
        return {"fa_base": "" if is_gallery_host() else "/fineart"}

    app.wsgi_app = GalleryHostMiddleware(app.wsgi_app)
