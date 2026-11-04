"""One-request HTTP server on 127.0.0.1 that receives the sign-in code from the browser."""

import hmac
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional
from urllib.parse import parse_qs, urlparse

DONE_PAGE = (
    b'<!doctype html><meta charset="utf-8"><title>Godfather</title>'
    b'<p>Signed in. You can close this tab and go back to the terminal.</p>'
)


class _Handler(BaseHTTPRequestHandler):
    server: '_Server'

    def do_GET(self) -> None:
        url = urlparse(self.path)
        if url.path != '/callback':
            self._answer(404, b'Not found')
            return
        query = parse_qs(url.query)
        state = (query.get('state') or [''])[0]
        code = (query.get('code') or [''])[0]
        if not code or not hmac.compare_digest(state.encode(), self.server.expected_state.encode()):
            self._answer(400, b'This sign-in link is not for this terminal.')
            return
        self.server.code = code
        self._answer(200, DONE_PAGE, 'text/html; charset=utf-8')

    def _answer(self, status: int, body: bytes, content_type: str = 'text/plain; charset=utf-8') -> None:
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        """Request lines carry the code, so nothing is logged."""


class _Server(HTTPServer):
    expected_state = ''
    code: Optional[str] = None


class LoopbackReceiver:
    """Listens on 127.0.0.1 on a port the OS picks and keeps the code from GET /callback."""

    def __init__(self, state: str):
        self._server = _Server(('127.0.0.1', 0), _Handler)
        self._server.expected_state = state

    @property
    def port(self) -> int:
        return self._server.server_address[1]

    def wait(self, timeout: float) -> Optional[str]:
        """The code from the browser, or None when timeout seconds pass first."""
        deadline = time.monotonic() + timeout
        while self._server.code is None:
            left = deadline - time.monotonic()
            if left <= 0:
                return None
            self._server.timeout = min(left, 1.0)
            self._server.handle_request()
        return self._server.code

    def close(self) -> None:
        self._server.server_close()
