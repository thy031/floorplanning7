#!/usr/bin/env python3
"""Serve the lab site with WebVTT captions as text/vtt."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import mimetypes
import sys

ROOT = Path(__file__).resolve().parent / "site"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8777

mimetypes.add_type("text/vtt; charset=utf-8", ".vtt")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def guess_type(self, path):
        if str(path).endswith(".vtt"):
            return "text/vtt; charset=utf-8"
        return super().guess_type(path)


if __name__ == "__main__":
    httpd = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Serving {ROOT} on http://127.0.0.1:{PORT}")
    httpd.serve_forever()
