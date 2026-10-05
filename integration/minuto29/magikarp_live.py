"""Forward attributed TikTok events to the local 12-player Magikarp arena."""
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import threading
import urllib.request

URL='http://127.0.0.1:4390'
ROOT=Path(os.environ.get('STADIUMFEI_ROOT',Path.home()/'Documents/GitHub/Pokemon-Stadiumfei'))/'magikarp-arena'
_queue=queue.Queue(maxsize=2048)
_thread=None
_window=None

def post(path,data):
    request=urllib.request.Request(URL+path,data=json.dumps(data).encode(),headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(request,timeout=1) as response: return json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(json.load(error).get('error','Solicitud rechazada')) from error

def forward(kind,user='',**data):
    global _thread
    if _thread is None:
        _thread=threading.Thread(target=_sender,daemon=True);_thread.start()
    try: _queue.put_nowait(dict(kind=kind,user=user,**data))
    except queue.Full: pass

def active():
    try:return json.loads((ROOT/'local-assets/active.json').read_text(encoding='utf-8')).get('active',False)
    except (OSError,ValueError):return False

def set_active(enabled):
    path=ROOT/'local-assets/active.json'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(dict(active=bool(enabled))),encoding='utf-8')

def _sender():
    while True:
        data=_queue.get()
        try: post('/api/event',data)
        except (OSError,ValueError,RuntimeError): pass

def ensure_server():
    try:
        with urllib.request.urlopen(URL+'/api/health',timeout=.5) as response:
            health=json.load(response)
        if health.get('app')!='stadiumfei-magikarp': raise RuntimeError('El puerto 4390 está ocupado por otra aplicación')
        return
    except OSError: pass
    if not (ROOT/'server.py').is_file(): raise FileNotFoundError(f'Falta la sala de Magikarp en {ROOT}')
    if not (ROOT/'local-assets/models.json').is_file() or not (ROOT/'node_modules/three/build/three.module.js').is_file():
        raise RuntimeError(f'Ejecuta Preparar.ps1 en {ROOT} para preparar los gráficos locales')
    python=Path(sys.executable)
    if getattr(sys,'frozen',False):
        python=Path.home()/'AppData/Local/Python/pythoncore-3.14-64/python.exe'
    log=open(ROOT/'server.log','a',encoding='utf-8')
    try: subprocess.Popen([str(python),str(ROOT/'server.py')],cwd=ROOT,stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    finally: log.close()
    import time
    for _ in range(30):
        try:
            with urllib.request.urlopen(URL+'/api/health',timeout=.2) as response:
                if json.load(response).get('app')=='stadiumfei-magikarp': return
        except OSError: time.sleep(.1)
    raise RuntimeError(f'No arrancó la sala; revisa {ROOT / "server.log"}')

def open_arena():
    global _window
    ensure_server()
    set_active(True)
    if _window is not None and _window.poll() is None: return
    candidates=[Path(os.environ.get('PROGRAMFILES','C:/Program Files'))/'Google/Chrome/Application/chrome.exe',
                Path(os.environ.get('LOCALAPPDATA',''))/'Google/Chrome/Application/chrome.exe',
                Path('C:/Program Files (x86)/Google/Chrome/Application/chrome.exe'),
                Path(os.environ.get('PROGRAMFILES(X86)','C:/Program Files (x86)'))/'Microsoft/Edge/Application/msedge.exe']
    browser=next((p for p in candidates if p.is_file()),None)
    if browser is None: raise RuntimeError('Se necesita Chrome o Edge para la ventana 3D')
    _window=subprocess.Popen([str(browser),'--app='+URL+'/', '--window-size=558,999',
        '--user-data-dir='+str(ROOT/'local-assets/browser-profile'),'--no-first-run','--autoplay-policy=no-user-gesture-required'],creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))

def control(action,duration=60):
    ensure_server()
    return post('/api/control',dict(action=action,duration=duration))
