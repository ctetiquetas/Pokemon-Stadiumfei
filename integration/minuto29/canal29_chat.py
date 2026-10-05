"""Independent Canal 29 chat, gift aliases and persistent clear markers."""
import json,os,time
from pathlib import Path
import tkinter as tk
from tkinter import ttk,messagebox
import urllib.request

ROOT=Path(__file__).resolve().parent
EVENTS=ROOT/'canal29-chat.jsonl'
SETTINGS=ROOT/'canal29-settings.json'
STATE=ROOT/'canal29-mode.json'
window=None

def read(path):
    try:return json.loads(path.read_text(encoding='utf-8'))
    except (OSError,ValueError):return {}
def save(path,data):
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8');os.replace(temporary,path)
def mode():return read(STATE).get('mode','')
def select(value):save(STATE,dict(mode=value))
def effect(name,gift_id=None):
    aliases=read(SETTINGS).get('aliases',{})
    return aliases.get('id:'+str(gift_id)) or aliases.get('name:'+str(name).casefold()) or {'rose':'rose','rosa':'rose','its corn':'corn',"it's corn":'corn','go popular':'popular','hazte popular':'popular'}.get(str(name).casefold().replace('’',"'"))
def assign(name,gift_id,chosen):
    settings=read(SETTINGS);aliases=settings.setdefault('aliases',{})
    aliases['name:'+str(name).casefold()]=chosen
    if gift_id is not None:aliases['id:'+str(gift_id)]=chosen
    save(SETTINGS,settings)
def emit(**data):
    with EVENTS.open('a',encoding='utf-8') as stream:stream.write(json.dumps(dict(time=time.time(),**data),ensure_ascii=False)+'\n')
def clear():
    settings=read(SETTINGS);settings['cleared_at']=time.time();save(SETTINGS,settings)
    return settings['cleared_at']

def simulate(user,gift,count=1,post=None):
    from magikarp_live import post as send
    chosen=effect(gift,'demo:'+gift)
    canonical={'rose':'Rose','corn':'Its corn','popular':'Go Popular'}.get(chosen,gift)
    result=(post or send)('/api/control',dict(action='demo_gift',user=user,gift=canonical,count=count))
    emit(kind='gift',sender='PRUEBA · '+user,gift=gift,gift_id='demo:'+gift,count=count,message='SIMULACIÓN · '+result.get('status','Sin asignación'))
    return result

def open_simulation(parent):
    from magikarp_live import ensure_server,URL
    try:
        ensure_server()
        with urllib.request.urlopen(URL+'/api/state',timeout=1) as response:state=json.load(response)
    except Exception as error:messagebox.showerror('Prueba de regalos',str(error),parent=parent);return
    players=[p for p in state['players'] if p.get('testParticipant')]
    if not players:messagebox.showinfo('Prueba de regalos','Añade jugadores demo en Controles y prueba local y comienza una ronda de Magikarp.',parent=parent);return
    dialog=tk.Toplevel(parent);dialog.title('Simular regalos · Magikarp');dialog.geometry('440x340')
    ttk.Label(dialog,text='Solo jugadores demo · no entrega monedas').pack(pady=12)
    user=tk.StringVar(value=players[0]['id']);gift=tk.StringVar(value='Rose');count=tk.IntVar(value=1)
    ttk.Label(dialog,text='Jugador de prueba').pack();ttk.Combobox(dialog,textvariable=user,values=[p['id'] for p in players],state='readonly').pack(pady=5)
    ttk.Label(dialog,text='Regalo').pack();ttk.Combobox(dialog,textvariable=gift,values=['Rose','Its corn','Go Popular','Regalo de prueba sin asignar'],state='readonly').pack(pady=5)
    ttk.Label(dialog,text='Cantidad').pack();ttk.Spinbox(dialog,from_=1,to=20,textvariable=count,width=8).pack(pady=5)
    status=ttk.Label(dialog,text='',wraplength=410)
    def run():
        try:
            quantity=count.get()
            if not 1<=quantity<=20:raise ValueError('Cantidad: de 1 a 20')
            result=simulate(user.get(),gift.get(),quantity);status.config(text=result.get('status',''))
        except Exception as error:status.config(text=str(error))
    ttk.Button(dialog,text='Enviar regalo de prueba',command=run).pack(pady=8);status.pack(pady=5)

def open_chat(parent):
    global window
    if window is not None and window.winfo_exists():window.lift();return
    window=tk.Toplevel(parent);window.title('Canal 29 · Chat y regalos');window.geometry('850x620')
    ttk.Label(window,text='Doble clic en un regalo para asignarlo. Se aplica a regalos nuevos; los anteriores no se repiten.').pack(pady=10)
    ttk.Button(window,text='Simular regalo (pruebas)',command=lambda:open_simulation(window)).pack(pady=5)
    tree=ttk.Treeview(window,columns=('user','gift','state'),show='headings',height=11)
    for key,title,width in [('user','Usuario',140),('gift','Regalo / ID',230),('state','Estado / efecto',440)]:tree.heading(key,text=title);tree.column(key,width=width)
    tree.pack(fill='both',expand=True,padx=12)
    chat=tk.Text(window,height=12,state='disabled',wrap='word');chat.pack(fill='both',expand=True,padx=12,pady=8)
    entries={};offset=0
    def wipe():
        clear();tree.delete(*tree.get_children());entries.clear();chat.config(state='normal');chat.delete('1.0','end');chat.config(state='disabled')
    ttk.Button(window,text='Eliminar toda la cola y el chat',command=wipe).pack(pady=8)
    def choose(event):
        item=tree.identify_row(event.y)
        if item not in entries:return
        data=entries[item];dialog=tk.Toplevel(window);dialog.title('Asignar regalo de Canal 29')
        ttk.Label(dialog,text=f"{data.get('gift')} · ID {data.get('gift_id','?')}").pack(padx=20,pady=12)
        def pick(key):
            assign(data['gift'],data.get('gift_id'),key)
            if tree.exists(item):
                values=list(tree.item(item,'values'));values[2]=f'Asignado a {key} · próximos regalos';tree.item(item,values=values)
            dialog.destroy()
        for label,key in [('Rosa · salto extra','rose'),('Elote · puntos dobles','corn'),('Go Popular','popular')]:ttk.Button(dialog,text=label,command=lambda k=key:pick(k)).pack(fill='x',padx=20,pady=5)
        ttk.Label(dialog,text='Go Popular no tiene efecto en Magikarp; conserva su efecto en los otros juegos.').pack(padx=20,pady=12)
    tree.bind('<Double-1>',choose)
    def poll():
        nonlocal offset
        if not tree.winfo_exists():return
        cutoff=read(SETTINGS).get('cleared_at',0)
        try:
            with EVENTS.open(encoding='utf-8') as stream:
                if EVENTS.stat().st_size<offset:offset=0
                stream.seek(offset);lines=stream.readlines();offset=stream.tell()
            for line in lines:
                try:data=json.loads(line)
                except ValueError:continue
                if data.get('time',0)<=cutoff:continue
                if data.get('kind')=='gift':
                    item=tree.insert('','end',values=(data.get('sender'),f"{data.get('gift')} ×{data.get('count',1)} · ID {data.get('gift_id','?')}",data.get('message')));entries[item]=data
                else:
                    chat.config(state='normal');chat.insert('end',f"{data.get('sender','')}: {data.get('message','')}\n");chat.see('end');chat.config(state='disabled')
        except OSError:pass
        window.after(200,poll)
    poll()
