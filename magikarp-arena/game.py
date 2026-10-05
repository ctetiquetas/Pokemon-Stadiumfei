"""Authoritative per-viewer Magikarp rounds; monotonic clocks, no client scoring."""
import re
import threading
import time

COLORS = ['#f65a49','#ffd34d','#43d7eb','#a780ff','#72de72','#ff83bd',
          '#ff9c42','#568cff','#e4f067','#36c8a0','#b7a6f5','#e6bc93']
JUMP_SECONDS = 33 / 30  # Original clips 8 → 10 → 14 → 5 → 6, at 30 fps.
HIT_SECONDS = 10 / 30  # Frame 2 of clip 14, after both four-frame takeoffs.


class Arena:
    def __init__(self, clock=time.monotonic, round_duration=60, ending_seconds=0):
        self.clock = clock
        self.round_duration=round_duration
        self.ending_seconds=ending_seconds
        self.lock = threading.RLock()
        self.revision = 0
        self.connection = 'Sin conexión al LIVE'
        self.connection_seen = None
        self.unattributed = 0
        self.new_room()

    def new_room(self):
        with self.lock:
            self.players = {}
            self.phase = 'lobby'
            self.round_id = getattr(self, 'round_id', 0) + 1
            self.starts = self.ends = None
            self.duration = self.round_duration
            self.result_at = None
            self.gift_events = set()
            self.revision += 1

    @staticmethod
    def identity(value):
        return str(value or '').strip().lstrip('@').casefold()[:128]

    def event(self, data):
        with self.lock:
            self.tick()
            kind = data.get('kind')
            if kind == 'connection':
                self.connection = str(data.get('message', ''))[:180]
                self.connection_seen = self.clock()
                return
            uid = self.identity(data.get('user'))
            if not uid:
                if kind == 'like': self.unattributed += max(0, int(data.get('count', 0)))
                return
            if kind == 'comment' and re.match(r'^!unir(?:\s|$)', str(data.get('message', '')).strip(), re.I):
                if self.phase != 'lobby' or uid in self.players or len(self.players) >= 12: return
                avatar = str(data.get('avatar') or '')[:2000]
                if not avatar.startswith('https://'): avatar = ''
                self.players[uid] = dict(id=uid, name=str(data.get('name') or uid)[:64], avatar=avatar,
                    color=COLORS[len(self.players)], slot=len(self.players), score=0, remainder=0,
                    pending=0, jump_start=None, hit=False, jumps=0, gift_hits=[], gift_start=None, double_until=0, gift_until=0, gift_effect='', testParticipant=bool(data.get('testParticipant',False)))
                self.revision += 1
            elif kind == 'like' and self.phase == 'playing' and uid in self.players:
                count = data.get('count', 0)
                if type(count) is not int or not 0 <= count <= 1000000: raise ValueError('Cantidad de taps inválida')
                player = self.players[uid]
                presses, player['remainder'] = divmod(player['remainder'] + count, 10)
                player['pending'] += presses
                self.tick()
            elif kind == 'gift':
                name=str(data.get('gift','')).strip().casefold().replace('’',"'")
                effect={'rose':'rose','rosa':'rose','its corn':'corn',"it's corn":'corn','elote':'corn'}.get(name)
                result=dict(assigned=bool(effect),applied=False,effect=effect,gift_id=data.get('gift_id'))
                if not effect:return dict(result,status='Sin asignación a Magikarp')
                if self.phase!='playing':return dict(result,status='Asignado · no aplicado: fuera de partida')
                if uid not in self.players:return dict(result,status='Asignado · no aplicado: usuario no inscrito')
                event_id=str(data.get('event_id') or '')
                if event_id and event_id in self.gift_events:return dict(result,status='Asignado · duplicado omitido')
                if event_id:self.gift_events.add(event_id)
                p=self.players[uid];now=self.clock()
                count=data.get('count',1)
                if type(count) is not int or not 1<=count<=1000000:raise ValueError('Cantidad de regalos inválida')
                if effect=='rose':
                    # Gift jumps run immediately, alongside the current tap jump.
                    # One collision per received rose; no pending gift backlog.
                    p['gift_start']=now
                    p['jumps']+=1
                    p['gift_hits'].append((now+HIT_SECONDS,count))
                    label='Rosa → salto extra aplicado'
                else:
                    p['double_until']=min(self.ends,now+8)
                    label='Elote → puntos ×2 activados (8 s)'
                p['gift_effect']=effect;p['gift_until']=min(self.ends,now+2.5)
                self.revision+=1
                return dict(result,applied=True,status=label)

    def start(self, duration=None):
        with self.lock:
            if self.phase != 'lobby': raise ValueError('Abre una nueva sala antes de comenzar')
            if not self.players: raise ValueError('Necesitas al menos un participante')
            if duration is None:duration=self.round_duration
            if type(duration) not in (int,float) or not 1 <= duration <= 3600: raise ValueError('Duración de audio inválida')
            self.duration = duration
            self.starts = self.clock() + 2.7  # Three original 27-frame Ditto beats at 30 FPS.
            self.ends = self.starts + duration
            self.phase = 'countdown'
            self.revision += 1

    def finish(self):
        with self.lock:
            self.tick()
            if self.phase not in ('playing', 'countdown'): return
            self.close_round(self.clock())

    def close_round(self, now):
        self.phase = 'ending' if self.ending_seconds else 'finished'
        self.result_at=now+self.ending_seconds
        self.ends=now
        for p in self.players.values(): p['pending'] = 0; p['jump_start'] = None; p['gift_hits']=[]; p['gift_start']=None
        self.revision += 1

    def tick(self):
        with self.lock:
            now = self.clock()
            if self.phase=='ending' and now>=self.result_at:self.phase='finished';self.revision+=1
            if self.connection_seen is not None and now-self.connection_seen>8:
                self.connection='Sin conexión al LIVE (esperando reconexión)'
            if self.phase == 'countdown' and now >= self.starts: self.phase = 'playing'
            if self.phase != 'playing': return
            # Resolve only collisions that occurred before the round's deadline.
            cutoff = min(now, self.ends)
            for p in self.players.values():
                future=[]
                for hit_at,count in p['gift_hits']:
                    if hit_at<=cutoff:
                        p['score']+=count*(2 if hit_at<p['double_until'] else 1)
                        self.revision+=1
                    else:future.append((hit_at,count))
                p['gift_hits']=future
                if p['jump_start'] is None and p['pending'] and now < self.ends:
                    p['pending'] -= 1; p['jump_start'] = now; p['hit'] = False; p['jumps'] += 1
                while p['jump_start'] is not None:
                    start = p['jump_start']
                    if not p['hit'] and start + HIT_SECONDS <= cutoff:
                        p['score'] += 2 if start + HIT_SECONDS < p['double_until'] else 1; p['hit'] = True; self.revision += 1
                    if start + JUMP_SECONDS > cutoff: break
                    p['jump_start'] = None
                    if p['pending'] and start + JUMP_SECONDS < self.ends:
                        p['pending'] -= 1; p['jump_start'] = start + JUMP_SECONDS; p['hit'] = False; p['jumps'] += 1
                    else: break
            if now >= self.ends:
                self.close_round(now)

    def snapshot(self):
        with self.lock:
            self.tick()
            now = self.clock()
            players = [dict(p, gift_jump_age=None if p['gift_start'] is None or self.phase!='playing' else now-p['gift_start'], double_remaining=max(0,p['double_until']-now), gift_visible=p['gift_until']>now and self.phase=='playing', jump_age=None if p['jump_start'] is None else now-p['jump_start']) for p in self.players.values()]
            ranking = sorted(players, key=lambda p: (-p['score'], p['slot']))
            best = ranking[0]['score'] if ranking else 0
            winners = [p['id'] for p in ranking if p['score'] == best] if self.phase == 'finished' else []
            return dict(phase=self.phase, round=self.round_id, players=players, winners=winners,
                remaining=max(0, (self.starts if self.phase == 'countdown' else self.ends or now)-now),
                duration=self.duration, music_duration=self.duration+.9,
                music_elapsed=max(0,min(self.duration+.9,now-(self.starts or now)+.9)),
                connection=self.connection, unattributed=self.unattributed,
                revision=self.revision, jump_seconds=JUMP_SECONDS, hit_seconds=HIT_SECONDS)
