"""Local-only OBS arena and host controls; no account credentials stored here."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import mimetypes
import threading
import time
from urllib.parse import urlsplit
from game import Arena

ROOT = Path(__file__).resolve().parent
PORT = 4390
arena = Arena()

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def respond(self, code, body, content='application/json'):
        if not isinstance(body, bytes): body = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', content)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        path=urlsplit(self.path).path
        if path=='/api/state': return self.respond(200, arena.snapshot())
        if path=='/api/health': return self.respond(200, dict(ok=True, app='stadiumfei-magikarp', assets=(ROOT/'local-assets/models.json').is_file()))
        files={'/':'arena.html','/arena.js':'arena.js','/style.css':'style.css','/control':'control.html',
            '/models.json':'local-assets/models.json','/vendor/three.module.js':'node_modules/three/build/three.module.js',
            '/vendor/three.core.js':'node_modules/three/build/three.core.js'}
        target=ROOT/files[path] if path in files else None
        if target is None or not target.is_file(): return self.respond(404,dict(error='Archivo no disponible'))
        return self.respond(200,target.read_bytes(),mimetypes.guess_type(target.name)[0] or 'application/octet-stream')
    def do_POST(self):
        # Protect host controls from requests originating on unrelated websites.
        origin=self.headers.get('Origin')
        if origin and origin not in [f'http://127.0.0.1:{PORT}',f'http://localhost:{PORT}']:
            return self.respond(403,dict(error='Origen no permitido'))
        try:
            length=int(self.headers.get('Content-Length',0))
            if not 0<length<=16384: raise ValueError('Solicitud inválida')
            data=json.loads(self.rfile.read(length))
            if not isinstance(data,dict): raise ValueError('Solicitud inválida')
            path=urlsplit(self.path).path
            if path=='/api/event': arena.event(data)
            elif path=='/api/control':
                action=data.get('action')
                if action=='room': arena.new_room()
                elif action=='start': arena.start(data.get('duration',60))
                elif action=='finish': arena.finish()
                elif action=='demo':
                    if arena.phase!='lobby': raise ValueError('La demo se carga en una sala nueva')
                    for i in range(12): arena.event(dict(kind='comment',user=f'demo{i+1}',name=f'Jugador {i+1}',message='!unir'))
                elif action=='demo_taps':
                    for p in list(arena.players.values()):
                        if p['id'].startswith('demo'): arena.event(dict(kind='like',user=p['id'],count=(p['slot']+1)*10))
                else: raise ValueError('Acción no válida')
            else: return self.respond(404,dict(error='Ruta no válida'))
            return self.respond(200,dict(ok=True))
        except (ValueError,TypeError,KeyError) as e:
            return self.respond(400,dict(error=str(e)))

def ticker():
    while True: arena.tick(); time.sleep(0.02)

if __name__=='__main__':
    threading.Thread(target=ticker,daemon=True).start()
    server=ThreadingHTTPServer(('127.0.0.1',PORT),Handler)
    server.daemon_threads=True
    print(f'Magikarp: http://127.0.0.1:{PORT}/',flush=True)
    server.serve_forever()
