"""
Lightweight HTTP server: serves the web dashboard + /api/* endpoints.
Run with: python web/server.py
"""
import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

from db import repository as db

PORT = int(os.getenv("PORT", 8080))
WEB_DIR = os.path.dirname(os.path.abspath(__file__))


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def log_message(self, fmt, *args):
        pass  # suppress per-request logging

    def send_json(self, data, status=200):
        body = json.dumps(data, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/api/today":
            rows = db.get_recent_articles(days=1)
            # attach tags per article
            result = []
            for r in rows:
                row = dict(r)
                row["tags"] = []  # could extend with a join query
                result.append(row)
            self.send_json(result)

        elif path == "/api/trends":
            self.send_json(list(db.get_topic_trends(days=7)))

        elif path == "/api/velocity":
            self.send_json(list(db.get_player_velocity()))

        elif path == "/api/emerging":
            self.send_json(list(db.get_emerging_terms()))

        elif path == "/api/weekly":
            digest = db.get_latest_digest("weekly")
            self.send_json(dict(digest) if digest else {})

        elif path == "/api/cost":
            self.send_json(list(db.get_cost_summary()))

        else:
            super().do_GET()


if __name__ == "__main__":
    print(f"UNFOMO dashboard → http://localhost:{PORT}")
    HTTPServer(("", PORT), Handler).serve_forever()
