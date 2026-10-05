"""Convert Stadium US 1.0's original 32px IA8 alphabet to local TrueType.

Glyph shapes, widths and Latin-1 mapping come from the user's ROM. Interpolate
the bitmap's half-alpha contours so the original shapes scale in HTML/OBS.
Generated game resources stay in ignored local-assets.
Requires fonttools: python -m pip install fonttools
"""
import argparse
import hashlib
import struct
from pathlib import Path
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from export_models import yay0

def contours(pixels):
    values=[[0]*34 for _ in range(34)]
    for y in range(32):
        for x in range(32):
            value=pixels[y*32+x]
            # IA8 stores a dark outline in opaque pixels too: trace the ink,
            # not alpha alone, so counters in A/B/O remain open.
            values[y+1][x+1]=(value>>4)/15*(value&15)/15
    graph={}
    for y in range(33):
        for x in range(33):
            points=[(x,y),(x+1,y),(x+1,y+1),(x,y+1)]
            v=[values[b][a] for a,b in points]; crossings={}
            for edge in range(4):
                a,b=edge,(edge+1)%4
                if (v[a]>=.5)==(v[b]>=.5):continue
                t=(.5-v[a])/(v[b]-v[a]);p,q=points[a],points[b]
                crossings[edge]=(round(p[0]+t*(q[0]-p[0]),6),round(p[1]+t*(q[1]-p[1]),6))
            if len(crossings)==2:pairs=[list(crossings)]
            elif len(crossings)==4:
                pairs=[(0,1),(2,3)] if (v[0]>=.5)==(sum(v)/4>=.5) else [(0,3),(1,2)]
            else:continue
            for a,b in pairs:
                p,q=crossings[a],crossings[b]
                graph.setdefault(p,[]).append(q);graph.setdefault(q,[]).append(p)
    loops=[];seen=set()
    for start in graph:
        if start in seen:continue
        path=[];p=start;previous=None
        while p not in seen:
            seen.add(p);path.append(p)
            nxt=next(q for q in graph[p] if q!=previous)
            previous,p=p,nxt
        loops.append(path)
    return loops

def inside(point,polygon):
    x,y=point;result=False
    for (a,b),(c,d) in zip(polygon,polygon[1:]+polygon[:1]):
        if (b>y)!=(d>y) and x<(c-a)*(y-b)/(d-b)+a:result=not result
    return result

def glyph(pixels):
    loops=contours(pixels);pen=TTGlyphPen(None)
    for loop in loops:
        depth=sum(inside(loop[0],other) for other in loops if other is not loop)
        pts=[(round((x-1)*32),round((29-y)*32)) for x,y in loop]
        area=sum(a*d-c*b for (a,b),(c,d) in zip(pts,pts[1:]+pts[:1]))
        if (area<0)!=(depth%2==0):pts.reverse()
        pen.moveTo(pts[0])
        for p in pts[1:]:pen.lineTo(p)
        pen.closePath()
    return pen.glyph()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--rom',type=Path,default=Path.home()/'Documents/GitHub/PokemonStadiumRecomp/baserom.z64')
    parser.add_argument('--output',type=Path,default=Path(__file__).parent/'local-assets/stadium.ttf')
    args=parser.parse_args();rom=args.rom.read_bytes()
    if hashlib.md5(rom).hexdigest()!='ed1378bc12115f71209a77844965ba50':raise ValueError('ROM US 1.0 requerida')
    archive=rom[0x3BA190:];offset=struct.unpack_from('>I',archive,16+5*16)[0]
    assert archive[offset:offset+8]==b'PERS-SZP'
    data=yay0(archive[offset+struct.unpack_from('>I',archive,offset+8)[0]:])
    cmap={};glyphs={'.notdef':TTGlyphPen(None).glyph()};metrics={'.notdef':(512,0)}
    for cp in list(range(32,127))+list(range(160,256)):
        index=rom[0x70230+cp] if cp<128 else rom[0x70208+8+cp]
        if index==0 and cp not in (32,160):continue
        name=f'g{index}';cmap[cp]=name
        if name in glyphs:continue
        glyphs[name]=glyph(data[144+index*1024:144+(index+1)*1024])
        metrics[name]=(max(1,data[index]-2)*32,0)
    # The game doesn't map '$'. Extend its original S with a currency stem.
    dollar=TTGlyphPen(None);glyphs[cmap[ord('S')]].draw(dollar,None)
    width=metrics[cmap[ord('S')]][0];x=width//2
    dollar.moveTo((x-25,-32));dollar.lineTo((x-25,832));dollar.lineTo((x+25,832));dollar.lineTo((x+25,-32));dollar.closePath()
    glyphs['dollar']=dollar.glyph();metrics['dollar']=(width,0);cmap[36]='dollar'
    cmap[0x202F]=cmap[32];cmap[0x2019]=cmap[39];cmap[0x2018]=cmap[39]
    cmap[0x201C]=cmap[34];cmap[0x201D]=cmap[34];cmap[0x2013]=cmap[45];cmap[0x2014]=cmap[45]
    font=FontBuilder(1024,isTTF=True);font.setupGlyphOrder(list(glyphs));font.setupCharacterMap(cmap)
    font.setupGlyf(glyphs);font.setupHorizontalMetrics(metrics);font.setupHorizontalHeader(ascent=896,descent=-128)
    font.setupNameTable(dict(familyName='Stadium Local',styleName='Regular',uniqueFontIdentifier='StadiumLocal-32-US10',fullName='Stadium Local',psName='StadiumLocal'))
    font.setupOS2(sTypoAscender=896,sTypoDescender=-128,sTypoLineGap=0,usWinAscent=1024,usWinDescent=160)
    font.setupPost();font.setupMaxp();args.output.parent.mkdir(parents=True,exist_ok=True);font.save(args.output)
    from fontTools.ttLib import TTFont
    loaded=TTFont(args.output);mapped=loaded.getBestCmap()
    missing=[c for c in 'Jugador ¡GANADOR! golpes al botón inscripción Ññ áéíóú ü 0123456789 K$' if ord(c) not in mapped]
    if missing:raise ValueError(f'Caracteres faltantes: {missing}')
    print(f'Fuente original lista: {len(cmap)} caracteres, {len(glyphs)} formas · {args.output}')

if __name__=='__main__':main()
