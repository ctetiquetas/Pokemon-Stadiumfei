"""Local-only OBS arena and host controls; no account credentials stored here."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import mimetypes
import threading
import time
import wave
from urllib.parse import urlsplit
from game import Arena
from audio_duration import mp3_duration

ROOT = Path(__file__).resolve().parent
PORT = 4390
with wave.open(str(ROOT/'local-assets/buzzer.wav')) as buzzer:
    ending_seconds=buzzer.getnframes()/buzzer.getframerate()+.1
arena = Arena(round_duration=mp3_duration(ROOT/'local-assets/Magikarps.mp3')-.9, ending_seconds=ending_seconds)

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
        files={'/':'arena.html','/arena.js':'arena.js','/music.js':'music.js','/style.css':'style.css','/control':'control.html',
            '/assets/kafeacuario.png':'assets/kafeacuario.png',
            '/countdown/3.png':'local-assets/countdown-3.png','/countdown/2.png':'local-assets/countdown-2.png',
            '/countdown/1.png':'local-assets/countdown-1.png','/countdown/go.png':'local-assets/countdown-go.png',
            '/music/countdown.wav':'local-assets/countdown.wav','/music/jump.wav':'local-assets/jump.wav','/music/hit.wav':'local-assets/hit.wav',
            '/music/buzzer.wav':'local-assets/buzzer.wav',
            '/music/lobby.mp3':'local-assets/Menumusic.mp3','/music/playing.mp3':'local-assets/Magikarps.mp3','/music/winner.wav':'local-assets/winner.wav',
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
                elif action=='start':
                    arena.round_duration=mp3_duration(ROOT/'local-assets/Magikarps.mp3')-.9
                    arena.start()
                elif action=='finish': arena.finish()
                elif action=='demo':
                    if arena.phase!='lobby': raise ValueError('La demo se carga en una sala nueva')
                    count=data.get('count',12)
                    if type(count) is not int or not 1<=count<=12:raise ValueError('Prueba: de 1 a 12 jugadores')
                    for i in range(count): arena.event(dict(kind='comment',user=f'demo{i+1}',name=f'Jugador {i+1}',message='!unir'))
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
