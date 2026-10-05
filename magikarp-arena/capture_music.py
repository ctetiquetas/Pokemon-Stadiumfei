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
    a=p.parse_args();a.assets.mkdir(exist_ok=True,parents=True)
    request=a.assets/'music-request.txt';log=a.assets/'music-capture.log'
    for name,song,seconds in [('lobby',0x13,65),('playing',10,65),('winner',0x1A,24)]:
        serial=int(time.time()*1000)&0xffffffff;request.write_text(f'{serial} {song}',encoding='ascii')
        deadline=time.monotonic()+25
        while f'serial={serial} song={song}' not in log.read_text(errors='replace'):
            if time.monotonic()>deadline:raise RuntimeError('El hook de música no respondió')
            time.sleep(.1)
        baseline=command(a.port,cmd='ai_submit_recent',n=1)['write_idx']
        print(f'Capturando {name}: pista {song}, {seconds}s',flush=True)
        time.sleep(seconds)
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
        with wave.open(str(a.assets/f'{name}.wav'),'wb') as output:
            output.setnchannels(2);output.setsampwidth(2);output.setframerate(rate);output.writeframes(samples.tobytes())
        raw.unlink()
        print(f'{name}.wav: {len(samples)/2/rate:.2f}s, {rate}Hz',flush=True)

if __name__=='__main__':main()
