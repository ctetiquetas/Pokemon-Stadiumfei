"""Extract Kids' Club's original countdown from the user's verified ROM."""
from pathlib import Path
import argparse,hashlib,struct
from export_models import yay0,png

def main():
 p=argparse.ArgumentParser();p.add_argument('--rom',type=Path,default=Path.home()/'Documents/GitHub/PokemonStadiumRecomp/baserom.z64');p.add_argument('--output',type=Path,default=Path(__file__).parent/'local-assets');a=p.parse_args()
 rom=a.rom.read_bytes()
 if hashlib.md5(rom).hexdigest()!='ed1378bc12115f71209a77844965ba50':raise ValueError('ROM US 1.0 requerida')
 data=rom[0x675FA0:]
 if data[:8]==b'PERS-SZP':data=yay0(data[struct.unpack_from('>I',data,8)[0]:])
 a.output.mkdir(parents=True,exist_ok=True)
 for digit,offset in [('3',0x8000),('2',0x4000),('1',0),('go',0xC000)]:
  (a.output/f'countdown-{digit}.png').write_bytes(png(64,64,data[offset:offset+16384]))
 print('Cuenta regresiva original extraída: 3, 2, 1 y salida.')

if __name__=='__main__':main()
