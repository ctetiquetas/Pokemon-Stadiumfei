"""Read MPEG Layer III duration, including Xing/LAME encoder trimming."""
from pathlib import Path

def mp3_duration(path):
    data=Path(path).read_bytes();offset=0
    if data[:3]==b'ID3':
        offset=10+sum((b&127)<<(7*(3-i)) for i,b in enumerate(data[6:10]))
    total=0.0
    while offset+4<=len(data):
        h=int.from_bytes(data[offset:offset+4],'big');version=(h>>19)&3;layer=(h>>17)&3
        bitrate=(h>>12)&15;sr=(h>>10)&3
        if h>>21!=2047 or version==1 or layer!=1 or bitrate in (0,15) or sr==3:
            offset+=1;continue
        rate=(44100,48000,32000)[sr]//(1 if version==3 else 2 if version==2 else 4)
        kbps=((0,32,40,48,56,64,80,96,112,128,160,192,224,256,320) if version==3 else (0,8,16,24,32,40,48,56,64,80,96,112,128,144,160))[bitrate]
        samples=1152 if version==3 else 576
        length=(144 if version==3 else 72)*kbps*1000//rate+((h>>9)&1)
        if offset+length>len(data):break
        mono=((h>>6)&3)==3
        side=(17 if mono else 32) if version==3 else (9 if mono else 17)
        xing=offset+4+(0 if h&(1<<16) else 2)+side
        if data[xing:xing+4] in (b'Xing',b'Info'):
            flags=int.from_bytes(data[xing+4:xing+8],'big');p=xing+8;frames=None
            for flag,size in [(1,4),(2,4),(4,100),(8,4)]:
                if flags&flag:
                    if flag==1:frames=int.from_bytes(data[p:p+4],'big')
                    p+=size
            if frames:
                trim=0
                if data[p:p+4] in (b'LAME',b'Lavc',b'Lavf'):
                    packed=int.from_bytes(data[p+21:p+24],'big');trim=(packed>>12)+(packed&4095)
                return (frames*samples-trim)/rate
        total+=samples/rate;offset+=length
    if total<=.9:raise ValueError('No se pudo leer la duración de Magikarps.mp3')
    return total
