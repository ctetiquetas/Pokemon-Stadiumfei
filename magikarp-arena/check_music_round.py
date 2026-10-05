"""Local timing check; never replaces a room containing real participants."""
import json,time,urllib.request,math,os
URL=os.environ.get('MAGIKARP_TEST_URL','http://127.0.0.1:4390')
def state():
    return json.load(urllib.request.urlopen(URL+'/api/state',timeout=2))
def post(path,**data):
    request=urllib.request.Request(URL+path,data=json.dumps(data).encode(),headers={'Content-Type':'application/json'})
    return json.load(urllib.request.urlopen(request,timeout=2))
if any(not p['id'].startswith(('demo','test-')) for p in state()['players']):
    raise RuntimeError('La sala contiene participantes reales')
post('/api/control',action='room');post('/api/control',action='demo',count=2)
post('/api/control',action='start',duration=999)
s=state();assert abs(s['duration']+.9-s['music_duration'])<1e-8
print(f"MP3: {s['music_duration']:.6f}s; juego: {s['duration']:.6f}s",flush=True)
deadline=time.monotonic()+s['music_duration']+8;closing=[];ending_at=None;points=None;sent=False
while time.monotonic()<deadline:
    s=state()
    if s['phase']=='playing':
        if not sent:post('/api/control',action='demo_taps');sent=True
        if 0<s['remaining']<=2.7:
            beat=min(3,max(1,math.ceil(s['remaining']/.9)))
            if not closing or closing[-1]!=beat:closing.append(beat)
    elif s['phase']=='ending' and ending_at is None:
        ending_at=time.monotonic();points=[p['score'] for p in s['players']]
        post('/api/event',kind='like',user='demo1',count=1000)
        print('Timbre; puntuación congelada',points,flush=True)
    elif s['phase']=='finished':
        assert ending_at is not None and time.monotonic()-ending_at>=1.5
        assert [p['score'] for p in s['players']]==points==[1,2]
        assert s['winners']==['demo2'] and closing==[3,2,1]
        assert s.get('reward') is None
        print('Ditto 3 -> 2 -> 1, fin del MP3, timbre y ganador posterior: OK',flush=True)
        break
    time.sleep(.08)
else:raise AssertionError('La ronda no terminó con la canción')
