"""Cut the helmet sheet (data/helmets_src/sheet.png, 4x2 grid on flat blue) into 8 pattern sprites -> data/helmets.json.
Key colours: shell green (-> helmet base), pattern magenta (-> helmet sec), visor cyan (-> visor tint). Recoloured in-game.
Also removes the dark rim shading right in front of the rear spoiler (so the spoiler reads as part of the shell).
Usage: python3 tools/helmets.py
"""
import pathlib,json,base64,io,colorsys
from collections import Counter
from PIL import Image
R=pathlib.Path(__file__).resolve().parent.parent
W=110
def cls(p):
  r,g,b,a=p
  if not a:return '.'
  if max(r,g,b)<70:return 'K'
  h,l,s=colorsys.rgb_to_hls(r/255,g/255,b/255)
  if s<.25:return 'k'
  if .2<h<.45:return 'G'
  if .75<h<.95:return 'M'
  if .45<=h<.6:return 'C'
  return 'o'
lum=lambda c:.3*c[0]+.59*c[1]+.11*c[2]
sh=Image.open(R/'data/helmets_src/sheet.png').convert('RGBA');SW,SH=sh.size;p=sh.load()
for y in range(SH):
  for x in range(SW):
    r,g,b,a=p[x,y]
    if b>r+50 and b>g+50:p[x,y]=(0,0,0,0)
out=[]
for i in range(8):
  r,c=divmod(i,4)
  cell=sh.crop((c*SW//4,r*SH//2,(c+1)*SW//4,(r+1)*SH//2));cell=cell.crop(cell.getbbox())
  h=round(cell.size[1]*W/cell.size[0])
  s=cell.convert('RGBa').resize((W,h),Image.BOX).convert('RGBA')
  s.putalpha(s.getchannel('A').point(lambda v:255 if v>=128 else 0))
  px=s.load()
  # leftover blue fringe on the outline -> outline black
  for y in range(h):
    for x in range(W):
      q=px[x,y]
      if q[3] and q[2]>q[0]+40 and q[2]>q[1]+40 and cls(q)!='C':px[x,y]=(14,15,18,255)
  # in-between blend pixels (neither key colour nor dark detail) -> most common key-colour neighbour
  for _ in range(2):
    fix=[]
    for y in range(h):
      for x in range(W):
        q=px[x,y]
        if q[3] and cls(q) in 'ko' and lum(q)>70:
          nb=[px[x+a,y+b2] for a in (-1,0,1) for b2 in (-1,0,1) if (a or b2) and 0<=x+a<W and 0<=y+b2<h and cls(px[x+a,y+b2]) in 'GMC']
          if nb:fix.append((x,y,Counter(nb).most_common(1)[0][0]))
    for x,y,c in fix:px[x,y]=c
  L=[next((x for x in range(W) if px[x,y][3]),None) for y in range(h)]
  ys=next(y for y in range(5,40) if L[y] is not None and L[y]<=8)
  cnt={k:Counter() for k in 'GM'}
  for y in range(h):
    for x in range(W):
      k=cls(px[x,y])
      if k in cnt:cnt[k][px[x,y][:3]]+=1
  main={k:(cnt[k].most_common(1)[0][0] if cnt[k] else None) for k in cnt}
  for y in range(max(0,ys-4),min(h,ys+16)):
    for x in range(0,min(W,(L[y] or 0)+16)):
      k=cls(px[x,y])
      if k in 'GM' and main[k] and lum(px[x,y])<lum(main[k])*.9:px[x,y]=main[k]+(255,)
  b=io.BytesIO();s.quantize(96,method=Image.FASTOCTREE).save(b,'PNG',optimize=True);out.append('data:image/png;base64,'+base64.b64encode(b.getvalue()).decode())
(R/'data/helmets.json').write_text(json.dumps(out),encoding='utf-8')
print(len(out),'helmets',sum(len(x) for x in out)//1024,'KB')
