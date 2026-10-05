"""Local receiver for Stadium likes from the existing TikTok connection."""
import json
import queue
import socket
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HTTP_PORT = 4380
GAME_PORT = 4371


def command(stream, value):
    stream.write(json.dumps(value).encode() + b'\n')
    stream.flush()
    line = stream.readline()
    if not line:
        raise ConnectionError('El port cerró la conexión')
    result = json.loads(line)
    if not result.get('ok'):
        raise RuntimeError(result.get('error', 'Comando rechazado'))
    return result


class StadiumState:
    def __init__(self, pulse=None):
        self.lock = threading.Condition()
        self.armed = False
        self.remainder = self.pending = self.sent = 0
        self.hold_ms, self.interval_ms = 100, 700
        self.error = ''
        self.pulse = pulse or self._pulse
        threading.Thread(target=self._work, daemon=True).start()

    def status(self):
        with self.lock:
            return dict(armed=self.armed, remainder=self.remainder,
                        pending=self.pending, sent=self.sent, error=self.error)

    def activate(self, enabled, hold_ms=100, interval_ms=700):
        if not 30 <= hold_ms <= 3000 or not hold_ms + 30 <= interval_ms <= 10000:
            raise ValueError('El intervalo debe superar la pulsación en al menos 30 ms')
        with self.lock:
            self.armed = enabled
            self.hold_ms, self.interval_ms = hold_ms, interval_ms
            self.remainder = self.pending = 0
            self.error = ''
            self.lock.notify_all()

    def likes(self, count):
        if type(count) is not int or not 0 <= count <= 1000000:
            raise ValueError('Cantidad de taps inválida')
        with self.lock:
            if self.armed:
                presses, self.remainder = divmod(self.remainder + count, 10)
                self.pending += presses
                self.lock.notify_all()

    def _pulse(self, hold_ms):
        with socket.create_connection(('127.0.0.1', GAME_PORT), timeout=2) as sock:
            with sock.makefile('rwb') as stream:
                try:
                    command(stream, dict(cmd='set_button', name='A', down=True))
                    time.sleep(hold_ms / 1000)
                finally:
                    command(stream, dict(cmd='set_button', name='A', down=False))

    def _work(self):
        while True:
            with self.lock:
                self.lock.wait_for(lambda: self.armed and self.pending > 0)
                self.pending -= 1
                hold, interval = self.hold_ms, self.interval_ms
            try:
                self.pulse(hold)
                with self.lock:
                    self.sent += 1
            except Exception as error:
                with self.lock:
                    self.armed = False
                    self.pending = self.remainder = 0
                    self.error = f'Se pausaron los taps: {error}'
            with self.lock:
                # Pause/reset wakes the wait; A already in progress is released first.
                self.lock.wait_for(lambda: not self.armed, timeout=(interval - hold) / 1000)


_state = None
_server = None


def receiver():
    global _state, _server
    if _state is not None:
        return _state
    state = StadiumState()

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            try:
                length = int(self.headers.get('Content-Length', 0))
                if self.path != '/likes' or not 0 < length <= 4096:
                    raise ValueError('Solicitud inválida')
                data = json.loads(self.rfile.read(length))
                state.likes(data['count'])
                self.send_response(200)
            except (ValueError, KeyError, TypeError):
                self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{}')

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', HTTP_PORT), Handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    _state, _server = state, server
    return state


_outgoing = queue.Queue(maxsize=512)
_sender_started = False


def forward_likes(count):
    """Do not block the TikTok event loop while the panel receives events."""
    global _sender_started
    if not _sender_started:
        _sender_started = True
        threading.Thread(target=_send, daemon=True).start()
    try:
        _outgoing.put_nowait(int(count))
    except queue.Full:
        pass


def _send():
    while True:
        count = _outgoing.get()
        try:
            request = urllib.request.Request(
                f'http://127.0.0.1:{HTTP_PORT}/likes',
                data=json.dumps(dict(count=count)).encode(),
                headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(request, timeout=0.5):
                pass
        except (OSError, ValueError):
            # A closed/inactive minigame must not stop the main LIVE connection.
            pass
