"""Serve the built Vue app and proxy API requests to the existing local Django server."""
import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'code' / 'frontend' / 'dist'
EXCLUDED = {'connection', 'transfer-encoding', 'content-length', 'keep-alive', 'host'}


class Handler(SimpleHTTPRequestHandler):
    backend = 'http://localhost:8001'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST), **kwargs)

    def proxy(self):
        length = int(self.headers.get('Content-Length', '0'))
        if length > 27 * 1024 * 1024:
            self.send_error(413)
            return
        headers = {k: v for k, v in self.headers.items() if k.lower() not in EXCLUDED}
        request = urllib.request.Request(self.backend + self.path, data=self.rfile.read(length) if length else None,
                                         headers=headers, method=self.command)
        try:
            # Never send local cookies/Bearer tokens through a machine's HTTP_PROXY.
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            response = opener.open(request, timeout=600)
        except urllib.error.HTTPError as error:
            response = error
        except (urllib.error.URLError, TimeoutError, OSError):
            data = b'{"error":{"code":"BACKEND_UNAVAILABLE","message":"Backend belum dapat dihubungi. Jalankan server Django pada port 8001.","fields":{}}}'
            self.send_response(503)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        with response:
            data = response.read()
            self.send_response(response.status)
            for key, value in response.headers.items():
                if key.lower() not in EXCLUDED:
                    self.send_header(key, value)
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            if self.command != 'HEAD':
                self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith('/api/'):
            return self.proxy()
        path = Path(self.translate_path(self.path)).resolve()
        if not path.is_relative_to(DIST.resolve()):
            return self.send_error(404)
        if not path.exists() and not Path(self.path.split('?', 1)[0]).suffix:
            self.path = '/index.html'
        return super().do_GET()

    def do_HEAD(self):
        if self.path.startswith('/api/'):
            return self.proxy()
        return super().do_HEAD()

    def mutate(self):
        return self.proxy() if self.path.startswith('/api/') else self.send_error(405)

    do_POST = mutate
    do_PATCH = mutate
    do_PUT = mutate
    do_DELETE = mutate
    do_OPTIONS = mutate

    def end_headers(self):
        if not self.path.startswith('/api/'):
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('X-Content-Type-Options', 'nosniff')
        super().end_headers()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5173)
    parser.add_argument('--backend', default='http://localhost:8001')
    args = parser.parse_args()
    if not (DIST / 'index.html').is_file():
        raise SystemExit('Build frontend belum tersedia. Jalankan npm ci dan npm run build di code/frontend.')
    if args.backend not in ('http://localhost:8001', 'http://127.0.0.1:8001'):
        raise SystemExit('Server bawaan hanya untuk backend localhost:8001.')
    Handler.backend = args.backend
    print(f'SILAR: http://localhost:{args.port} | Backend: {args.backend}', flush=True)
    print('Biarkan terminal ini terbuka. Ctrl+C untuk berhenti.', flush=True)
    try:
        ThreadingHTTPServer(('localhost', args.port), Handler).serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
