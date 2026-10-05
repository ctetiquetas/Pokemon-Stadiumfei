"""Export the original Stadium minigame meshes from a user's local US 1.0 ROM.

Format decoded against PokemonStadiumRecomp/disasm geo_layout.c, F420.c,
3FB0.h and ultralib gbi.h. No game resources are committed to the repository.
"""
import argparse
import base64
import hashlib
import json
import math
from pathlib import Path
import struct
import zlib

SIZES = [8,4,8,8,4,4,4,8,12,4,8,24,4,4,4,4,4,4,4,8,12,12,4,20,8,8,4,16,16,28,8,24,20,16,8,16,4,4,20]
IDENTITY = [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]

def mul(a, b):
    return [sum(a[k*4+r]*b[c*4+k] for k in range(4)) for c in range(4) for r in range(4)]

def transform(m, v, w=1):
    return [sum(m[c*4+r]*v[c] for c in range(3))+m[12+r]*w for r in range(3)]

def matrix(t, angles, scale):
    sx,sy,sz = [math.sin(a*math.pi/32768) for a in angles]
    cx,cy,cz = [math.cos(a*math.pi/32768) for a in angles]
    # Skeletal nodes use func_8000F5A8, column-major for WebGL.
    m = [cy*cz,cy*sz,-sy,0,
         sx*sy*cz-cx*sz,sx*sy*sz+cx*cz,sx*cy,0,
         cx*sy*cz+sx*sz,cx*sy*sz-sx*cz,cx*cy,0,*t,1]
    for c in range(3):
        for r in range(3): m[c*4+r] *= scale[c]
    return m

def yay0(data):
    if data[:4] != b'Yay0': raise ValueError('Missing Yay0 header')
    size, link, chunk = struct.unpack_from('>III', data, 4)
    out=bytearray(); maskpos=16; bits=0; mask=0
    while len(out)<size:
        if bits==0: mask=struct.unpack_from('>I',data,maskpos)[0]; maskpos+=4; bits=32
        if mask & 0x80000000:
            out.append(data[chunk]); chunk+=1
        else:
            value=struct.unpack_from('>H',data,link)[0]; link+=2
            length=value>>12
            if length==0: length=data[chunk]+18; chunk+=1
            else: length+=2
            distance=(value&4095)+1
            for _ in range(length): out.append(out[-distance])
        mask=(mask<<1)&0xffffffff; bits-=1
    return bytes(out)

def resource(rom, index):
    archive=0x920000
    offset,size=struct.unpack_from('>II',rom,archive+16+index*16)
    data=rom[archive+offset:archive+offset+size]
    if data[:8]==b'PERS-SZP': data=yay0(data[struct.unpack_from('>I',data,8)[0]:])
    if data[8:16]!=b'FRAGMENT': raise ValueError(f'Unknown resource {index}')
    return data

def png(width,height,rgba):
    def chunk(kind,payload):
        return struct.pack('>I',len(payload))+kind+payload+struct.pack('>I',zlib.crc32(kind+payload)&0xffffffff)
    pixels=b''.join(b'\0'+bytes(rgba[y*width*4:(y+1)*width*4]) for y in range(height))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(pixels))+chunk(b'IEND',b'')

class Model:
    def __init__(self,data):
        self.d=data; self.cache={}; self.groups={}; self.textures=[]; self.material=0
        self.shift_s=self.shift_t=0; self.parents=[IDENTITY]; self.current=IDENTITY
        self.bones=[]; self.bone=-1; self.bone_parents=[-1]; self.current_bone=-1
    def u(self,p): return struct.unpack_from('>I',self.d,p)[0]
    def ptr(self,p): return self.u(p)&0xfffff
    def texture_table(self,p,count):
        for i in range(count):
            entry=p+i*12; kind=self.d[entry+1]; w,h=struct.unpack_from('>HH',self.d,entry+2); off=self.ptr(entry+8)
            rgba=[]
            if kind==2:
                for x in range(w*h):
                    v=struct.unpack_from('>H',self.d,off+x*2)[0]
                    if self.d[entry]==3: rgba += [v>>8,v>>8,v>>8,v&255]
                    else: rgba += [((v>>11)&31)*255//31,((v>>6)&31)*255//31,((v>>1)&31)*255//31,255*(v&1)]
            elif kind==3: rgba=list(self.d[off:off+w*h*4])
            elif kind==1 and self.d[entry]==4:
                for value in self.d[off:off+w*h]: rgba += [value,value,value,255]
            else: raise ValueError(f'Unsupported texture encoding {kind}')
            self.textures.append(dict(width=w,height=h,png='data:image/png;base64,'+base64.b64encode(png(w,h,rgba)).decode()))
    def display(self,p,emit=True,depth=0):
        if depth>20: raise ValueError('Display list recursion')
        for _ in range(10000):
            a,b=struct.unpack_from('>II',self.d,p); op=a>>24; p+=8
            if op==0xdf: return
            if op==0xde:
                self.display(b&0xfffff,emit,depth+1)
                if (a>>16)&1: return
            elif op==1:
                n=(a>>12)&255; start=((a>>1)&127)-n; offset=b&0xfffff
                for i in range(n):
                    x,y,z,flag,s,t,nx,ny,nz,alpha=struct.unpack_from('>hhhHhhbbbB',self.d,offset+i*16)
                    self.cache[start+i]=(transform(self.current,[x,y,z]),[s,t],transform(self.current,[nx/127,ny/127,nz/127],0),[x,y,z],self.current_bone,[nx/127,ny/127,nz/127])
            elif op in [5,6] and emit:
                self.triangle([(a>>16)&255,(a>>8)&255,a&255])
                if op==6: self.triangle([(b>>16)&255,(b>>8)&255,b&255])
            elif op==0xf5 and ((b>>24)&7)==0:
                self.shift_s=b&15; self.shift_t=(b>>10)&15
        raise ValueError('Unterminated display list')
    def triangle(self,indices):
        group=self.groups.setdefault(self.material,dict(position=[],uv=[],normal=[],local=[],bone=[],rawNormal=[]))
        tex=self.textures[self.material]
        for idx in indices:
            pos,st,normal,local,bone,raw=self.cache[idx//2]
            group['position'] += [round(v,5) for v in pos]
            group['normal'] += [round(v,5) for v in normal]
            group['local'] += local; group['bone'].append(bone)
            group['rawNormal'] += raw
            ss=2**(-self.shift_s if self.shift_s<=10 else 16-self.shift_s)
            ts=2**(-self.shift_t if self.shift_t<=10 else 16-self.shift_t)
            group['uv'] += [st[0]/32*ss/tex['width'],1-st[1]/32*ts/tex['height']]
    def geo(self,p,depth=0):
        if depth>20: raise ValueError('Geo recursion')
        for _ in range(10000):
            op=self.d[p]
            if op>=len(SIZES): raise ValueError(f'Unknown geo command {op:02x} at {p:x}')
            if op in [1,4]: return
            if op in [0,3]: self.geo(self.ptr(p+4),depth+1)
            elif op==2: p=self.ptr(p+4); continue
            elif op==5:
                self.parents.append(self.current); self.bone_parents.append(self.current_bone)
            elif op==6:
                self.parents.pop(); self.bone_parents.pop()
                self.current=self.parents[-1]; self.current_bone=self.bone_parents[-1]
            elif op==0x17:
                count=struct.unpack_from('>H',self.d,p+2)[0]
                self.texture_table(self.ptr(p+8),count)
            elif op==0x1c:
                scale=[v/65536 for v in struct.unpack_from('>iii',self.d,p+4)]
                self.current=mul(self.parents[-1],matrix([0,0,0],[0,0,0],scale))
            elif op==0x1d:
                t=struct.unpack_from('>hhh',self.d,p+4); angles=struct.unpack_from('>hhh',self.d,p+10)
                scale=[v/65536 for v in struct.unpack_from('>iii',self.d,p+16)]
                self.current=mul(self.parents[-1],matrix(t,angles,scale))
                self.current_bone=len(self.bones)
                self.bones.append(dict(parent=self.bone_parents[-1],translation=t,rotation=angles,scale=scale,bind=self.current,index=self.d[p+3],id=self.d[p+1],base=self.parents[-1] if self.bone_parents[-1]==-1 else IDENTITY))
            elif op==0x23:
                texture=struct.unpack_from('>h',self.d,p+8)[0]
                if texture>=0: self.material=texture
                self.display(self.ptr(p+4),False)
            elif op in [0x1e,0x20,0x21,0x22]:
                offset={0x1e:4,0x20:16,0x21:12,0x22:4}[op]
                savedmatrix,savedbone=self.current,self.current_bone
                if op==0x1e:
                    boneid=struct.unpack_from('>h',self.d,p+2)[0]
                    matches=[(i,b) for i,b in enumerate(self.bones) if b['id']==boneid]
                    if not matches:raise ValueError(f'Unknown preload bone {boneid}')
                    self.current_bone,bone=matches[-1];self.current=bone['bind']
                self.display(self.ptr(p+offset),op!=0x1e)
                self.current,self.current_bone=savedmatrix,savedbone
            p+=SIZES[op]
        raise ValueError('Unterminated geo layout')
    def export(self):
        # Resource entry point returns a static model header via lui/addiu.
        hi=self.u(0x2c)&65535; lo=struct.unpack_from('>h',self.d,0x32)[0]
        header=((hi<<16)+lo)&0xfffff
        table=self.ptr(header+8); layout=self.ptr(table)
        self.geo(layout)
        animations={}
        table=self.ptr(header+12)
        for index in [0,5,6,7,8,10,14]:
            if index<self.d[header+4]: animations[str(index)]=self.animation(self.ptr(table+index*4))
        return dict(textures=self.textures,groups=[dict(texture=k,**v) for k,v in self.groups.items()],bones=self.bones,animations=animations)

    def animation(self,p):
        flags=struct.unpack_from('>H',self.d,p)[0]
        if flags&8: raise ValueError('Curve animation format is not supported')
        channels,frames=struct.unpack_from('>HH',self.d,p+8)
        channelptr,scaleptr,rotptr,transptr=[self.ptr(p+x) for x in [12,16,20,24]]
        def packed(off,index,bits):
            bit=index*bits; pos=off+bit//8; shift=bit%8
            value=int.from_bytes(self.d[pos:pos+4],'big')
            value=(value>>(32-shift-bits))&((1<<bits)-1)
            return value-(1<<bits) if value&(1<<(bits-1)) else value
        def component(channel,frame):
            ns,nr,nt,_=struct.unpack_from('>BBBB',self.d,channelptr+channel*10)
            vs,vr,vt=struct.unpack_from('>HHH',self.d,channelptr+channel*10+4)
            scale=vs/1000 if ns==1 else struct.unpack_from('>h',self.d,scaleptr+2*(vs+min(frame,ns-1)))[0]/1000
            rot=vr*16 if nr==1 else packed(rotptr,vr+min(frame,nr-1),12)*16
            trans=vt if nt==1 else packed(transptr,vt+min(frame,nt-1),16 if flags&4 else 12)
            if nt==1:
                bits=16 if flags&4 else 12
                trans&=(1<<bits)-1
                if trans&(1<<(bits-1)):trans-=1<<bits
            return scale,rot,trans
        result=[]
        for frame in range(frames):
            world=[]
            for bone in self.bones:
                index=bone['index']*3
                if index+2<channels:
                    values=[component(index+c,frame) for c in range(3)]
                    local=matrix([v[2] for v in values],[v[1] for v in values],[v[0] for v in values])
                else:local=matrix(bone['translation'],bone['rotation'],bone['scale'])
                parent=bone['parent']
                world.append(mul(world[parent] if parent>=0 else bone['base'],local))
            result.append([[round(v,6) for v in m] for m in world])
        return result

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--rom',type=Path,default=Path.home()/'Documents/GitHub/PokemonStadiumRecomp/baserom.z64'); parser.add_argument('--output',type=Path,default=Path(__file__).parent/'local-assets/models.json')
    args=parser.parse_args(); rom=args.rom.read_bytes()
    if hashlib.md5(rom).hexdigest()!='ed1378bc12115f71209a77844965ba50': raise ValueError('Se necesita la ROM US 1.0 en formato z64')
    models={}
    for name,index in [('magikarp',172),('button',173)]:
        models[name]=Model(resource(rom,index)).export()
        print(name, 'triangles',sum(len(g['position'])//9 for g in models[name]['groups']), 'textures',len(models[name]['textures']))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(models,separators=(',',':')),encoding='utf-8')

if __name__=='__main__': main()
