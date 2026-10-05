"""Existing Minuto 29 games plus the original-graphics Magikarp arena."""
import tkinter as tk
import os
from tkinter import ttk, messagebox
import magikarp_live

_window=None

def open_minuto29(parent,start_live=None,stop_live=None,account=None):
    global _window
    if _window is not None and _window.winfo_exists():
        _window.deiconify();_window.lift();return
    window=_window=tk.Toplevel(parent);window.title('Minuto 29');window.geometry('560x590')
    ttk.Label(window,text='¿Qué vamos a jugar?',font=('Segoe UI',17,'bold')).pack(pady=16)
    picks=ttk.Frame(window);picks.pack(fill='x',padx=16)
    controls=ttk.Frame(window);controls.pack(fill='both',expand=True,padx=22,pady=12)

    def guarded(action):
        try: action()
        except Exception as error: messagebox.showerror('Minuto 29',str(error),parent=window)

    def select(mode):
        for child in controls.winfo_children():child.destroy()
        if mode!='stadium':
            magikarp_live.set_active(False)
            from pokemon_bridge import forward,open_battle
            from minuto29 import open_swimming
            forward('control','owner',message=mode+':select')
            ttk.Label(controls,text='Battle Royal' if mode=='battle' else 'Relevos acuáticos',font=('Segoe UI',13,'bold')).pack(pady=8)
            ttk.Button(controls,text='Abrir ventana del juego',command=lambda:guarded(open_battle if mode=='battle' else open_swimming)).pack(fill='x',pady=4)
            for label,action in [('Nueva sala de inscripción','room'),('Comenzar batalla' if mode=='battle' else 'Comenzar carrera','start')]:
                ttk.Button(controls,text=label,command=lambda a=action:forward('control','owner',message=mode+':'+a)).pack(fill='x',pady=4)
            ttk.Label(controls,text='OBS: http://127.0.0.1:8765/overlay').pack(pady=8)
            return
        guarded(magikarp_live.open_arena)
        if account is not None and not account.get().strip():
            account.set(os.environ.get('STADIUMFEI_TIKTOK_ACCOUNT','xkafei'))
        ttk.Label(controls,text='Magikarp · 12 jugadores',font=('Segoe UI',14,'bold')).pack(pady=8)
        ttk.Label(controls,text='!unir para entrar · 10 taps propios = 1 salto').pack(pady=4)
        ttk.Button(controls,text='Abrir pantalla vertical 9:16',command=lambda:guarded(magikarp_live.open_arena)).pack(fill='x',pady=4)
        live_label='Conectar al LIVE'+(f' de @{account.get().lstrip("@")}' if account is not None else '')
        ttk.Button(controls,text=live_label,command=lambda:guarded(start_live),state='normal' if start_live else 'disabled').pack(fill='x',pady=4)
        ttk.Label(controls,text='La ronda termina con Magikarps.mp3.\nDitto 3 → 2 → 1 → timbre → ganador.',wraplength=490).pack(pady=6)
        ttk.Button(controls,text='Nueva sala de inscripción',command=lambda:guarded(lambda:magikarp_live.control('room'))).pack(fill='x',pady=4)
        ttk.Button(controls,text='Comenzar ronda',command=lambda:guarded(lambda:magikarp_live.control('start'))).pack(fill='x',pady=4)
        ttk.Button(controls,text='Terminar ronda',command=lambda:guarded(lambda:magikarp_live.control('finish'))).pack(fill='x',pady=4)
        if stop_live:
            def stop():
                stop_live()
                guarded(lambda:magikarp_live.post('/api/event',dict(kind='connection',message='LIVE detenido por el anfitrión')))
            ttk.Button(controls,text='Detener LIVE',command=stop).pack(fill='x',pady=4)
        ttk.Label(controls,text='OBS: fuente navegador http://127.0.0.1:4390/\nAncho 1080 · alto 1920. También puedes capturar la ventana.',wraplength=490).pack(pady=8)
        ttk.Button(controls,text='Controles y prueba local',command=lambda:guarded(open_controls)).pack(fill='x',pady=4)

    def open_controls():
        import webbrowser
        magikarp_live.ensure_server();webbrowser.open(magikarp_live.URL+'/control')
    for title,mode in [('Battle Royal','battle'),('Carrera de agua','swimming'),('Magikarp','stadium')]:
        ttk.Button(picks,text=title,command=lambda m=mode:select(m)).pack(side='left',expand=True,fill='x',padx=3)
