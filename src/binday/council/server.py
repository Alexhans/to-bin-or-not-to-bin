"""The Dilly Dally Borough Council website, served locally.

One page and two endpoints, all form-encoded:

    POST api/addresses     postcode=FX1 2ZZ   -> the properties at that postcode
    POST api/collections   uprn=OW-0002       -> next date for each container

The page fills in the address list and the collection table with JavaScript, the way
most council sites do, so there is nothing to scrape in the HTML itself.

**The date belongs to the world, not the request.** `/` uses today's date (or
`--today`), and `/w/2026-08-22/` is the site as it was on 22 August 2026. The client
only ever sees a base URL, so a test picks a world by picking a URL.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import json
import logging
import re
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from urllib.parse import parse_qs

from binday.council import schedule

logger = logging.getLogger(__name__)

STATIC = files("binday.council") / "static"
CONTENT_TYPES = {".html": "text/html", ".js": "text/javascript", ".css": "text/css"}
WORLD = re.compile(r"^/w/(\d{4}-\d{2}-\d{2})(/.*)$")


def _handler(default_today: dt.date | None) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            logger.info("%s %s", self.address_string(), format % args)

        def _route(self) -> tuple[dt.date, str] | None:
            path = self.path.split("?", 1)[0]
            if m := WORLD.match(path):
                try:
                    return dt.date.fromisoformat(m[1]), m[2]
                except ValueError:
                    return None
            return default_today or dt.date.today(), path

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: int, payload: object) -> None:
            self._send(status, json.dumps(payload, indent=2).encode(), "application/json")

        def do_GET(self) -> None:
            route = self._route()
            if route is None:
                return self._send(404, b"Not found", "text/plain")
            today, path = route
            if path == "/":
                html = (STATIC / "index.html").read_text()
                html = html.replace("{{TODAY_ISO}}", today.isoformat())
                html = html.replace("{{TODAY}}", today.strftime("%A %-d %B %Y"))
                return self._send(200, html.encode(), "text/html")
            name = path.removeprefix("/static/")
            suffix = name[name.rfind(".") :]
            if path.startswith("/static/") and "/" not in name and suffix in CONTENT_TYPES:
                asset = STATIC / name
                if asset.is_file():
                    return self._send(200, asset.read_bytes(), CONTENT_TYPES[suffix])
            self._send(404, b"Not found", "text/plain")

        def do_POST(self) -> None:
            route = self._route()
            if route is None:
                return self._send(404, b"Not found", "text/plain")
            today, path = route
            length = int(self.headers.get("Content-Length") or 0)
            form = {k: v[0] for k, v in parse_qs(self.rfile.read(length).decode()).items()}

            if path == "/api/addresses":
                found = schedule.addresses_for(form.get("postcode", ""))
                return self._json(
                    200, {"addresses": [{"uprn": a.uprn, "address": a.line} for a in found]}
                )
            if path == "/api/collections":
                address = schedule.find(form.get("uprn", ""))
                if address is None:
                    return self._json(404, {"error": "Unknown property"})
                rows = sorted(schedule.next_collections(address, today).items(), key=lambda r: r[1])
                return self._json(
                    200,
                    {
                        "address": address.line,
                        "collections": [
                            {"container": c, "next_collection": d.isoformat()} for c, d in rows
                        ],
                    },
                )
            self._send(404, b"Not found", "text/plain")

    return Handler


@contextlib.contextmanager
def serve(today: dt.date | None = None, port: int = 0) -> Iterator[str]:
    """Run the site on a background thread and yield its base URL."""
    server = ThreadingHTTPServer(("127.0.0.1", port), _handler(today))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()


def main() -> None:
    """Serve the council site until Ctrl-C."""
    parser = argparse.ArgumentParser(description="Run the Dilly Dally Borough Council website.")
    parser.add_argument("--port", type=int, default=8111)
    parser.add_argument("--today", type=dt.date.fromisoformat, help="pretend it is this date")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), _handler(args.today))
    logger.info(f"Dilly Dally Borough Council running at http://localhost:{args.port}")
    with contextlib.suppress(KeyboardInterrupt):
        server.serve_forever()
