"""Plain helmet with one thin side pinstripe (data/helmets_src/plain_line.png, drawn by image AI on flat blue). Earlier 8-pattern sheet kept as sheet.png (data/helmets_src/sheet.png, 4x2 grid on flat blue) into 8 pattern sprites -> data/helmets.json.
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
sh=Image.open(R/'data/helmets_src/plain_line.png').convert('RGBA');SW,SH=sh.size;p=sh.load()
for y in range(SH):
  for x in range(SW):
    r,g,b,a=p[x,y]
    if b>r+50 and b>g+50:p[x,y]=(0,0,0,0)
out=[]
for i in range(1):
  cell=sh.crop(sh.getbbox())
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
  # pinstripe: fill gaps along its path up to the front edge (fit y per column from the magenta pixels)
  col={}
  for y in range(h):
    for x in range(W):
      if cls(px[x,y])=='M':col.setdefault(x,[]).append(y)
  if col:
    xs=sorted(col);mid={x:sum(col[x])/len(col[x]) for x in xs};th=max(1,round(sum(len(col[x]) for x in xs)/len(xs)))
    last=xs[-6:];slope=(mid[last[-1]]-mid[last[0]])/max(1,last[-1]-last[0]);mc=Counter(px[x,y] for x in xs for y in col[x]).most_common(1)[0][0]
    for x in range(xs[0],W):
      if x in col:continue
      prev=max(k for k in xs if k<x);nxt=min((k for k in xs if k>x),default=None)
      yc=mid[prev]+((mid[nxt]-mid[prev])*(x-prev)/(nxt-prev) if nxt else slope*(x-prev))
      for y in range(round(yc-th/2+.01),round(yc-th/2+.01)+th):
        if 0<=y<h and cls(px[x,y]) in 'Gg':px[x,y]=mc
  # very dark shell-green blend pixels (edge shading) -> outline black, so they don't turn into odd dark dots after recolouring
  for y in range(h):
    for x in range(W):
      r_,g_,b_,a_=px[x,y]
      if a_ and max(r_,g_,b_)<70 and g_>r_+12 and g_>b_+8:px[x,y]=(14,15,18,255)
  # stray visor-cyan pixels away from the visor -> neighbour colour; single-pixel holes in the pinstripe -> stripe colour
  for y in range(h):
    for x in range(W):
      q=px[x,y];hq,lq,sq=colorsys.rgb_to_hls(q[0]/255,q[1]/255,q[2]/255)
      if q[3] and max(q[:3])>=70 and sq>.2 and .42<=hq<.6 and sum(cls(px[x+a,y+b2])=='C' for a in range(-3,4) for b2 in range(-3,4) if 0<=x+a<W and 0<=y+b2<h)<6:
        nb=[px[x+a,y+b2] for a in (-1,0,1) for b2 in (-1,0,1) if (a or b2) and 0<=x+a<W and 0<=y+b2<h and cls(px[x+a,y+b2]) in 'GgM']
        if nb:px[x,y]=Counter(nb).most_common(1)[0][0]
  for y in range(1,h-1):
    for x in range(1,W-1):
      if cls(px[x,y]) in 'Gg' and (cls(px[x-1,y])=='M' and cls(px[x+1,y])=='M' or cls(px[x,y-1])=='M' and cls(px[x,y+1])=='M'):
        px[x,y]=px[x-1,y] if cls(px[x-1,y])=='M' else px[x,y-1]
  # crisp black outline: every opaque pixel touching transparency (8-neighbourhood) becomes outline black
  K=(14,15,18,255);edge=[]
  for y in range(h):
    for x in range(W):
      if px[x,y][3] and any(not(0<=x+a<W and 0<=y+b2<h) or not px[x+a,y+b2][3] for a in (-1,0,1) for b2 in (-1,0,1)):edge.append((x,y))
  for x,y in edge:px[x,y]=K
  # palette reduction can merge a few blend pixels into an off-key colour: snap those to a neighbour afterwards
  s=s.quantize(96,method=Image.FASTOCTREE).convert('RGBA');px=s.load()
  for y in range(h):
    for x in range(W):
      q=px[x,y]
      if q[3] and cls(q) in 'oC' and max(q[:3])>=70 and sum(cls(px[x+a,y+b2])=='C' for a in range(-3,4) for b2 in range(-3,4) if 0<=x+a<W and 0<=y+b2<h)<6:
        nb=[px[x+a,y+b2] for a in (-1,0,1) for b2 in (-1,0,1) if (a or b2) and 0<=x+a<W and 0<=y+b2<h and cls(px[x+a,y+b2]) in 'GM']
        if nb:px[x,y]=Counter(nb).most_common(1)[0][0]
  b=io.BytesIO();s.save(b,'PNG',optimize=True);out.append('data:image/png;base64,'+base64.b64encode(b.getvalue()).decode())
(R/'data/helmets.json').write_text(json.dumps(out),encoding='utf-8')
print(len(out),'helmet',sum(len(x) for x in out)//1024,'KB')
