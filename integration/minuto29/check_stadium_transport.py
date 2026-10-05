"""Local transport check. Refuses to replace a room with real participants."""
import json
import time
import urllib.request
import magikarp_live

def state():
    with urllib.request.urlopen(magikarp_live.URL+'/api/state',timeout=1) as response:return json.load(response)
def wait_for(predicate,seconds=12):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        result=state()
        if predicate(result):return result
        time.sleep(.05)
    raise AssertionError('La sala no recibió los eventos esperados')

magikarp_live.ensure_server()
if any(not p['id'].startswith(('test-','demo')) for p in state()['players']):
    raise RuntimeError('Hay participantes reales en la sala; no se ejecuta la prueba')
magikarp_live.control('room')
for i in range(1,13):magikarp_live.forward('comment',f'test-{i}',name=f'Jugador {i}',message='!unir')
wait_for(lambda s:len(s['players'])==12)
magikarp_live.control('start',30)
wait_for(lambda s:s['phase']=='playing',5)
for i in range(1,13):magikarp_live.forward('like',f'test-{i}',count=i*10)
wait_for(lambda s:[p['score'] for p in s['players']]==list(range(1,13)),20)
magikarp_live.control('finish')
result=state()
assert result['winners']==['test-12'],result
print('Transporte TikTok -> sala: 12 participantes, puntos 1..12, ganador test-12. OK')
