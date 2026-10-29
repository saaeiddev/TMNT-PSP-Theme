#!/usr/bin/env python3
"""Rebuild a PTF using PTF Studio's sample as the structural template. Requires Pillow."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import struct,zlib,io,json,hashlib
R=Path(__file__).resolve().parents[1]
S=4
font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
if not Path(font).exists(): font='DejaVuSans-Bold.ttf'
colors=['#44aaff','#ee4d4d','#bf75f4','#ff9d35','#86cf49']
items=['MS','UMD','CAM','SHARE','SAVE','UPDATE','UPDATE','USB','VIDEO','PHOTO','SYSTEM','THEME','TIME','POWER','DISPLAY','SOUND','LOCK','RSS','NETWORK','HELP','REMOTE','RADIO','RSS','WEB','SEARCH','ACCOUNT','DEFAULT','BT','MUSIC']
category=['SETTINGS','PHOTO','MUSIC','VIDEO','TV','GAME','NETWORK','EXTRAS']
cat_symbols=['preferences-system','camera-photo','audio-x-generic','video-x-generic','tv','input-gaming','web-browser','applications-utilities']
item_symbols=['media-flash','media-optical','camera-photo','emblem-shared','document-save','view-refresh','folder-download','drive-harddisk-usb','camera-video','folder-pictures','computer','preferences-desktop-appearance','preferences-system-time','battery-full','preferences-desktop-display','audio-volume-high','system-lock-screen','network-wireless','preferences-system-network','help-contents','preferences-desktop-remote-desktop','audio-headphones','network-wireless','web-browser','system-search','user-available','emblem-default','bluetooth','applications-multimedia']
def badge(name, size, idx, sub=False, cat=False):
 w,h=size; im=Image.new('RGBA',(w*S,h*S)); d=ImageDraw.Draw(im); c=colors[idx%len(colors)]
 x=w*S/2;y=h*S/2;rad=min(w,h)*S*.41
 d.ellipse((x-rad,y-rad,x+rad,y+rad),fill='#102c28',outline='#9ada62',width=1*S)
 d.arc((x-rad*.79,y-rad*.79,x+rad*.79,y+rad*.79),195,345,fill='#497e41',width=S)
 d.polygon([(x-rad*.86,y+rad*.51),(x+rad*.87,y+rad*.19),(x+rad*.87,y+rad*.38),(x-rad*.76,y+rad*.70)],fill=c)
 if name=='TMNT': sym='emblem-default'
 elif cat: sym=cat_symbols[idx-1]
 elif sub: sym=['document-properties','emblem-ok'][idx]
 else: sym=item_symbols[idx]
 mask=Image.open(R/'assets/symbols'/f'{sym}.png').convert('RGBA').getchannel('A')
 side=int(rad*1.05); mask=mask.resize((side,side),Image.Resampling.LANCZOS)
 glyph=Image.new('RGBA',(side,side),'#f4f9e7'); glyph.putalpha(mask); im.alpha_composite(glyph,(int(x-side/2),int(y-side/2-rad*.12)))
 return im.resize((w,h),Image.Resampling.LANCZOS)
def block(t,sz,nxt):return struct.pack('<HHIII',t,0,sz,nxt,16)
def imageblock(t,fmt,order,w,h,bpp,pixels,level):
 c=bytearray(64+len(pixels)); struct.pack_into('<H',c,0,0x30); struct.pack_into('<HHHHHHHH',c,4,fmt,order,w,h,bpp,16,8,2); struct.pack_into('<IIII',c,24,0x30,0x40,len(c),0); struct.pack_into('<HHHH',c,40,level,1,3,1); struct.pack_into('<I',c,48,0x40); c[64:]=pixels
 return block(t,16+len(c),16+len(c))+c
def gim(im,indexed=True):
 im=im.convert('RGBA'); w,h=im.size
 if indexed:
  q=im.quantize(colors=256,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE).convert('RGBA'); colors=[]; ids={}; pix=[]
  for rgba in q.getdata():
   if rgba not in ids: ids[rgba]=len(colors);colors.append(rgba)
   pix.append(ids[rgba])
  assert len(colors)<=256
  pal=b''.join(bytes(x) for x in colors)+bytes(4*(256-len(colors)))
  sw=bytearray()
  for oy in range(0,(h+7)//8*8,8):
   for ox in range(0,(w+15)//16*16,16):
    for y in range(8):
     for x in range(16):sw.append(pix[(oy+y)*w+ox+x] if ox+x<w and oy+y<h else 0)
  parts=imageblock(5,3,0,256,1,32,pal,2)+imageblock(4,5,1,w,h,8,sw,1)
 else: parts=imageblock(4,3,0,w,h,32,im.tobytes(),1)
 pic=block(3,16+len(parts),16)+parts
 info=b'\0\0TMNT PSP THEME\0'; info+=bytes((-len(info))%4); info=block(255,16+len(info),16+len(info))+info
 root=block(2,16+len(pic)+len(info),16)+pic+info
 return b'MIG.00.1PSP\0\0\0\0\0'+root
def bmp(im):
 o=io.BytesIO(); im.convert('RGB').save(o,format='BMP'); return o.getvalue()
def records(template):
 groups={}
 for off in struct.unpack_from('<8I',template,0x100):
  if not off:continue
  g,n,sz,pos=struct.unpack_from('<HHII',template,off); arr={}
  for _ in range(n):
   sub,_,fmt,comp,size,rawsize=struct.unpack_from('<HHHHII',template,pos); packed=template[pos+32:pos+32+size]; raw=zlib.decompress(packed) if comp==2 and size<rawsize else packed[:rawsize]; arr[sub]=(fmt,raw); pos+=32+size
  groups[g]=arr
 return groups
def entry(sub,fmt,raw):
 p=zlib.compress(raw,9); comp=2
 if len(p)>=len(raw):p=raw;comp=0
 if len(raw)==4: p=raw;comp=2
 p+=bytes((-len(p))%4); h=bytearray(32);struct.pack_into('<H',h,0,sub);struct.pack_into('<HHII',h,4,fmt,comp,len(p),len(raw));return h+p
def build(groups):
 headers=[]; offset=0x120
 for g,arr in sorted(groups.items()):
  body=b''.join(entry(s,f,r) for s,(f,r) in sorted(arr.items())); h=bytearray(32);struct.pack_into('<HHII',h,0,g,len(arr),len(body),offset+32);headers.append((offset,h,body));offset+=32+len(body)
 b=bytearray(offset); b[:8]=b'\0PTF\0\1\0\0'; b[8:8+len(b'TMNT PSP Theme')]=b'TMNT PSP Theme';b[136:136+4]=b'TMNT';b[184:188]=b'6.20';b[192:197]=b'1.0.0';struct.pack_into('<I',b,200,8)
 for i,(off,h,body) in enumerate(headers):struct.pack_into('<I',b,0x100+4*i,off);b[off:off+32]=h;b[off+32:off+32+len(body)]=body
 return b
wall=Image.open(R/'assets/TMNT_wallpaper_480x272.png').convert('RGB')
g=records((R/'vendor/ptf-studio-sample.ptf').read_bytes())
# The metadata preview uses a full-colour GIM; background uses a 24-bit BMP.
thumb=ImageOps.fit(wall,(300,170),method=Image.Resampling.LANCZOS)
g[0][0]=(5,gim(badge('TMNT',(16,16),4),True));g[0][1]=(5,gim(thumb,False));g[1][0]=(4,bmp(wall))
for i,name in enumerate(category,1):
 im=badge(name,(64,48),i,cat=True);im.save(R/f'assets/icons/category_{i:02}_{name.lower()}.png');g[2][i]=(5,gim(im))
for i,name in enumerate(items):
 sub=2+2*i; im=badge(name,(48,48),i);im.save(R/f'assets/icons/item_{sub:02}_{name.lower()}.png');g[3][sub]=(5,gim(im))
for i,name in enumerate(['OPTION','SELECT']):
 im=badge(name,(32,32),i,True);im.save(R/f'assets/icons/second_{i}.png');g[4][2*i]=(5,gim(im))
out=build(g); assert len(out)<768*1024; (R/'dist/TMNT_PSP_Theme.ptf').write_bytes(out)
# Labeled approximations, composited from exported assets; never emulator captures.
for i,name in enumerate(category,1):
 im=wall.convert('RGBA'); overlay=Image.new('RGBA',im.size); d=ImageDraw.Draw(overlay);d.rectangle((0,0,480,272),fill=(0,0,0,35));im=Image.alpha_composite(im,overlay)
 for j in range(1,9):
  x=110+(j-i)*64-32
  if -64<x<480:im.alpha_composite(Image.open(R/f'assets/icons/category_{j:02}_{category[j-1].lower()}.png'),(x,48))
 d=ImageDraw.Draw(im);f=ImageFont.truetype(font,11);d.text((78,102),name.title(),font=f,fill='white',stroke_width=1,stroke_fill='black')
 sub={1:22,2:2,3:2,4:2,5:54,6:10,7:48,8:56}[i]; icon=next((R/'assets/icons').glob(f'item_{sub:02}_*.png'));im.alpha_composite(Image.open(icon),(86,118));d=ImageDraw.Draw(im);d.text((145,137),items[(sub-2)//2].title(),font=ImageFont.truetype(font,14),fill='white',stroke_width=1,stroke_fill='black'); im.convert('RGB').save(R/f'previews/{name.lower()}_approximation.png')
print('PTF bytes',len(out),'sha256',hashlib.sha256(out).hexdigest(),'group counts', {k:len(v) for k,v in g.items()})
