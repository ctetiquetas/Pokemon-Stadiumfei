"""Minuto 29 selector with Stadium controlled by the existing TikTok LIVE."""
import os
import socket
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox
from stadium_backend import receiver, command, GAME_PORT

_window = None
ROOT = Path(os.environ.get('STADIUMFEI_ROOT', Path.home() / 'Documents/GitHub/Pokemon-Stadiumfei'))
PORT = ROOT.parent / 'PokemonStadiumRecomp'


def open_minuto29(parent, start_live=None, stop_live=None, account=None):
    global _window
    if _window is not None and _window.winfo_exists():
        _window.deiconify()
        _window.lift()
        return
    try:
        state = receiver()
    except OSError as error:
        messagebox.showerror('Minuto 29', f'No se pudo abrir el receptor de taps: {error}', parent=parent)
        return
    window = _window = tk.Toplevel(parent)
    window.title('Minuto 29')
    window.geometry('560x650')
    ttk.Label(window, text='¿Qué vamos a jugar?', font=('Segoe UI', 17, 'bold')).pack(pady=16)
    picks = ttk.Frame(window)
    picks.pack(fill='x', padx=16)
    controls = ttk.Frame(window)
    controls.pack(fill='both', expand=True, padx=22, pady=12)

    def select(mode):
        state.activate(False)
        for child in controls.winfo_children():
            child.destroy()
        if mode != 'stadium':
            from pokemon_bridge import forward, open_battle
            from minuto29 import open_swimming
            forward('control', 'owner', message=mode + ':select')
            title = 'Battle Royal' if mode == 'battle' else 'Relevos acuáticos'
            ttk.Label(controls, text=title, font=('Segoe UI', 13, 'bold')).pack(pady=8)

            def launch():
                try:
                    (open_battle if mode == 'battle' else open_swimming)()
                except Exception as error:
                    messagebox.showerror('Minuto 29', str(error), parent=window)

            ttk.Button(controls, text='Abrir ventana del juego', command=launch).pack(fill='x', pady=4)
            for label, action in [('Nueva sala de inscripción', 'room'),
                                  ('Comenzar batalla' if mode == 'battle' else 'Comenzar carrera', 'start')]:
                ttk.Button(controls, text=label, command=lambda a=action: forward('control', 'owner', message=mode + ':' + a)).pack(fill='x', pady=4)
            ttk.Label(controls, text='OBS: http://127.0.0.1:8765/overlay', wraplength=480).pack(pady=8)
            return
        ttk.Label(controls, text='Magikarp · Pokémon Stadium', font=('Segoe UI', 14, 'bold')).pack(pady=8)
        ttk.Label(controls, text='10 taps = una pulsación A · jugador 1').pack(pady=4)

        def guarded(action):
            try:
                action()
            except Exception as error:
                messagebox.showerror('Magikarp', str(error), parent=window)

        def launch_port():
            # Reuse an already running Stadium port instead of starting a second game.
            try:
                with socket.create_connection(('127.0.0.1', GAME_PORT), timeout=0.5) as sock:
                    with sock.makefile('rwb') as stream:
                        command(stream, {'cmd': 'ping'})
                return
            except OSError:
                pass
            exe = PORT / 'build/PokemonStadiumRecomp.exe'
            rom = PORT / 'baserom.z64'
            if not exe.is_file() or not rom.is_file():
                raise FileNotFoundError(f'Falta el port o la ROM en {PORT}')
            (exe.parent / 'rom.cfg').write_text(str(rom), encoding='utf-8')
            environment = dict(os.environ, PSR_AUTOBOOT='1')
            subprocess.Popen([str(exe), str(rom)], cwd=exe.parent, env=environment,
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))

        ttk.Button(controls, text='Abrir Pokémon Stadium', command=lambda: guarded(launch_port)).pack(fill='x', pady=4)
        live_label = 'Conectar al LIVE' + (f' de @{account.get().lstrip("@")}' if account is not None else '')
        ttk.Button(controls, text=live_label, command=lambda: guarded(start_live), state='normal' if start_live else 'disabled').pack(fill='x', pady=4)
        timings = ttk.Frame(controls)
        timings.pack(fill='x', pady=6)
        hold, interval = tk.IntVar(value=100), tk.IntVar(value=700)
        ttk.Label(timings, text='A sostenido (ms):').pack(side='left')
        ttk.Entry(timings, textvariable=hold, width=6).pack(side='left', padx=5)
        ttk.Label(timings, text='Intervalo (ms):').pack(side='left')
        ttk.Entry(timings, textvariable=interval, width=6).pack(side='left', padx=5)

        def activate():
            with socket.create_connection(('127.0.0.1', GAME_PORT), timeout=0.5) as sock:
                with sock.makefile('rwb') as stream:
                    command(stream, {'cmd': 'ping'})
            state.activate(True, hold.get(), interval.get())

        ttk.Button(controls, text='Activar taps (ronda en marcha)', command=lambda: guarded(activate)).pack(fill='x', pady=4)
        ttk.Button(controls, text='Pausar y borrar taps pendientes', command=lambda: state.activate(False)).pack(fill='x', pady=4)
        ttk.Button(controls, text='Probar +10 taps', command=lambda: state.likes(10)).pack(fill='x', pady=4)
        if stop_live:
            ttk.Button(controls, text='Detener LIVE', command=lambda: (state.activate(False), stop_live())).pack(fill='x', pady=4)
        status = tk.StringVar()
        label = ttk.Label(controls, textvariable=status, wraplength=500)
        label.pack(pady=8)

        def refresh():
            if not label.winfo_exists():
                return
            info = state.status()
            status.set(info['error'] or f"{'Taps activos' if info['armed'] else 'Taps pausados'} · resto {info['remainder']}/10 · cola {info['pending']} · A enviadas {info['sent']}")
            window.after(250, refresh)

        refresh()
        ttk.Label(controls, text='Entra a Kids’ Club → Magikarp e inicia la ronda. Pausa los taps al terminar. Captura la ventana del port en OBS/TikTok LIVE Studio.', wraplength=500).pack(pady=4)

    for title, mode in [('Battle Royal', 'battle'), ('Carrera de agua', 'swimming'), ('Magikarp', 'stadium')]:
        ttk.Button(picks, text=title, command=lambda m=mode: select(m)).pack(side='left', expand=True, fill='x', padx=3)

    def close():
        state.activate(False)
        window.destroy()

    window.protocol('WM_DELETE_WINDOW', close)
