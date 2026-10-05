"""Capture the original ROM's music through the port's own audio engine."""
from pathlib import Path
import argparse, array, json, re, socket, struct, sys, time, wave

def command(port, **data):
    with socket.create_connection(('127.0.0.1',port),timeout=10) as sock:
        sock.sendall((json.dumps(data)+'\n').encode())
        return json.loads(sock.makefile('rb').readline())

def main():
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=4372)
    p.add_argument('--assets',type=Path,default=Path(__file__).parent/'local-assets')
    p.add_argument('--only',choices=['lobby','playing','winner','countdown','jump','hit','buzzer'])
    a=p.parse_args();a.assets.mkdir(exist_ok=True,parents=True)
    request=a.assets/'music-request.txt';log=a.assets/'music-capture.log'
    # Let the boot/title scene finish assigning its own background music.
    # Otherwise it can replace our requested track just after the hook responds.
    print('Esperando a que termine el arranque del port…',flush=True)
    time.sleep(40)
    # Kids' Club selection: fragment39 func_82504370 explicitly starts 0x16.
    def request_sound(song):
        serial=int(time.time()*1000)&0xffffffff;request.write_text(f'{serial} {song}',encoding='ascii')
        deadline=time.monotonic()+25
        while f'serial={serial} song={song}' not in log.read_text(errors='replace'):
            if time.monotonic()>deadline:raise RuntimeError('El hook de música no respondió')
            time.sleep(.05)
    for name,song,seconds in [('lobby',0x16,65),('playing',10,65),('winner',0x1A,8),('countdown',0x20001,2),('jump',0x20006,2),('hit',0x20008,2),('buzzer',0x20009,3)]:
        if a.only and a.only!=name:continue
        for attempt in range(4):
            request_sound(-1);time.sleep(1)
            if song>79:
                # The audio thread must finish initializing a newly loaded SFX
                # bank before queuing the take. Discard the first warm-up cue.
                request_sound(song);time.sleep(2)
            baseline=command(a.port,cmd='ai_submit_recent',n=1)['write_idx']
            request_sound(song)
            print(f'Capturando {name}: pista {song}, {seconds}s',flush=True)
            until=time.monotonic()+seconds;changed=False
            while time.monotonic()<until:
                time.sleep(min(1,max(0,until-time.monotonic())))
                active=command(a.port,cmd='rdram_peek',addr=0x800FF9B4,n=4)
                if song<=79 and int(active['hex'],16)!=song:
                    changed=True;break
            if not changed:break
            print('La escena de arranque cambió la música; descartando y reiniciando captura.',flush=True)
        else:raise RuntimeError('El juego sigue cambiando la pista; no se guardó el archivo')
        raw=a.assets/f'{name}.pcm-ring';result=command(a.port,cmd='ai_submit_dump',path=str(raw.resolve()))
        if not result.get('ok'):raise RuntimeError(result)
        size=result['record_size'];data=raw.read_bytes();pcm=bytearray()
        for offset in range(0,len(data),size):
            seq,ms,addr,count,length,pad=struct.unpack_from('<QQIIII',data,offset)
            if seq>=baseline:pcm.extend(data[offset+32:offset+32+length])
        samples=array.array('h');samples.frombytes(pcm)
        if sys.byteorder=='little':samples.byteswap()
        events=command(a.port,cmd='audio_queue_recent',n=1)['events']
        rates=re.findall(r'bridge ON\s+src=(\d+)',log.read_text(errors='replace'))
        rate=events[-1]['sample_rate'] if events else int(rates[-1]) if rates else 32000
        if not samples or max(abs(v) for v in samples)<100:raise RuntimeError('Captura silenciosa')
        audible=[i//2 for i,v in enumerate(samples) if abs(v)>64]
        begin=max(0,audible[0]-int(rate*.015));end=min(len(samples)//2,audible[-1]+int(rate*.06))
        samples=samples[begin*2:end*2]
        with wave.open(str(a.assets/f'{name}.wav'),'wb') as output:
            output.setnchannels(2);output.setsampwidth(2);output.setframerate(rate);output.writeframes(samples.tobytes())
        raw.unlink()
        print(f'{name}.wav: {len(samples)/2/rate:.2f}s, {rate}Hz',flush=True)

if __name__=='__main__':main()
