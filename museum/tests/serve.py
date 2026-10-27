"""Local QA server: serve this checkout at / and /CRITT/ (never deploys)."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
import argparse

class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        parts = urlsplit(path)
        if parts.path == '/CRITT':
            parts = parts._replace(path='/')
        elif parts.path.startswith('/CRITT/'):
            parts = parts._replace(path=parts.path[len('/CRITT'):])
        return super().translate_path(urlunsplit(parts))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    options = parser.parse_args()
    root = str(Path(__file__).resolve().parents[2])
    server = ThreadingHTTPServer(('127.0.0.1', options.port), lambda *args, **kwargs: Handler(*args, directory=root, **kwargs))
    print(f'QA preview: http://127.0.0.1:{options.port}/museum/ and /CRITT/museum/', flush=True)
    server.serve_forever()
