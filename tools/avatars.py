"""Cut the avatar sheets (data/avatars_src/sheet*.png, 3x2 grids on white) into 12 sprites -> data/avatars.json (base64 PNG list).
Trophy pose sheets (win*.png, same order, arms up with empty hands) -> data/avatars_win.json.
Suit must be pure green (recolored to helmet base in-game), stripes magenta (-> helmet sec).
Usage: python3 tools/avatars.py
"""
import pathlib,json,base64,io
from collections import deque
from PIL import Image
R=pathlib.Path(__file__).resolve().parent.parent
H=420  # sprite height; high enough for the card photo (bust crop) to stay sharp
def cut(pat,dst):
 out=[]
 for sh in sorted((R/'data/avatars_src').glob(pat)):
   im=Image.open(sh).convert('RGBA');W,Ht=im.size;px=im.load()
   bg=lambda p:min(p[:3])>=200 and max(p[:3])-min(p[:3])<30
   seen=bytearray(W*Ht);q=deque((x,y) for x in range(W) for y in (0,Ht-1))
   q.extend((x,y) for y in range(Ht) for x in (0,W-1))
   while q:
     x,y=q.popleft()
     if x<0 or y<0 or x>=W or y>=Ht or seen[y*W+x] or not bg(px[x,y]):continue
     seen[y*W+x]=1;px[x,y]=(0,0,0,0);q.extend(((x+1,y),(x-1,y),(x,y+1),(x,y-1)))
   # white pockets enclosed by the body (between arm and torso): big near-white blobs
   vis=bytearray(W*Ht)
   for y0 in range(Ht):
     for x0 in range(W):
       if vis[y0*W+x0] or px[x0,y0][3]==0 or not bg(px[x0,y0]):continue
       blob=[];q=deque([(x0,y0)]);vis[y0*W+x0]=1
       while q:
         x,y=q.popleft();blob.append((x,y))
         for a,b in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
           if 0<=a<W and 0<=b<Ht and not vis[b*W+a] and px[a,b][3] and bg(px[a,b]):vis[b*W+a]=1;q.append((a,b))
       if len(blob)>400:
         for x,y in blob:px[x,y]=(0,0,0,0)
   # eat the light anti-alias fringe touching transparency (3 passes)
   for _ in range(5):
     kill=[]
     for y in range(1,Ht-1):
       for x in range(1,W-1):
         p=px[x,y]
         if p[3]==0:continue
         if (sum(p[:3])/3>=150 and max(p[:3])-min(p[:3])<60 or sum(p[:3])/3>=105 and max(p[:3])-min(p[:3])<40) and any(px[a,b][3]==0 for a,b in ((x+1,y),(x-1,y),(x,y+1),(x,y-1))):kill.append((x,y))
     for x,y in kill:px[x,y]=(0,0,0,0)
   for r in range(2):
     for c in range(3):
       cell=im.crop((c*W//3,r*Ht//2,(c+1)*W//3,(r+1)*Ht//2));bb=cell.getbbox();cell=cell.crop(bb)
       w=round(cell.size[0]*H/cell.size[1]);cell=cell.convert('RGBa').resize((w,H),Image.LANCZOS).convert('RGBA');a=cell.getchannel('A').point(lambda v:255 if v>=140 else 0);cell.putalpha(a)
       # edge pixels much lighter than their opaque neighbours -> repaint with the neighbours' colour
       cp=cell.load();cw,ch=cell.size
       for _ in range(4):
         fix=[]
         for y in range(ch):
           for x in range(cw):
             q0=cp[x,y]
             if not q0[3]:continue
             nb=[(x+a,y+b) for a in (-1,0,1) for b in (-1,0,1) if (a or b) and 0<=x+a<cw and 0<=y+b<ch]
             if all(cp[u,v][3] for u,v in nb if abs(u-x)+abs(v-y)==1) and len(nb)==8:continue
             op=[cp[u,v] for u,v in nb if cp[u,v][3]]
             if len(op)<2:fix.append((x,y,None));continue
             m=sorted(op,key=lambda c:sum(c[:3]))[len(op)//2];dk=min(op,key=lambda c:sum(c[:3]))
             if sum(q0[:3])/3-sum(m[:3])/3>45:fix.append((x,y,m))
             elif max(q0[:3])-min(q0[:3])<40 and sum(q0[:3])/3-sum(dk[:3])/3>50:fix.append((x,y,dk))
         for x,y,m in fix:cp[x,y]=m if m else (0,0,0,0)
       # near-white leftovers within 4px of the outline -> darkest-ish neighbour colour
       dist={}
       fr=[(x,y) for y in range(ch) for x in range(cw) if not cp[x,y][3]]
       for d in range(1,5):
         nf=[]
         for x,y in fr:
           for a,b2 in ((1,0),(-1,0),(0,1),(0,-1)):
             n=(x+a,y+b2)
             if 0<=n[0]<cw and 0<=n[1]<ch and cp[n][3] and n not in dist:dist[n]=d;nf.append(n)
         fr=nf
       for _ in range(3):
         for (x,y) in dist:
           q0=cp[x,y]
           if sum(q0[:3])/3>=130 and max(q0[:3])-min(q0[:3])<45:
             op=sorted([cp[x+a,y+b2] for a in (-1,0,1) for b2 in (-1,0,1) if (a or b2) and 0<=x+a<cw and 0<=y+b2<ch and cp[x+a,y+b2][3]],key=lambda c:sum(c[:3]))
             if op and sum(op[0][:3])/3<80:cp[x,y]=op[len(op)//3]
       # drop tiny floating specks (islands under 12 px)
       vs=set()
       for y in range(ch):
         for x in range(cw):
           if (x,y) in vs or not cp[x,y][3]:continue
           isl=[];st=[(x,y)];vs.add((x,y))
           while st:
             u,v=st.pop();isl.append((u,v))
             for a in (-1,0,1):
               for b2 in (-1,0,1):
                 n=(u+a,v+b2)
                 if n not in vs and 0<=n[0]<cw and 0<=n[1]<ch and cp[n][3]:vs.add(n);st.append(n)
           if len(isl)<12*(H//200)**2:
             for n in isl:cp[n]=(0,0,0,0)
       b=io.BytesIO();cell.quantize(128,method=Image.FASTOCTREE).save(b,'PNG',optimize=True);out.append('data:image/png;base64,'+base64.b64encode(b.getvalue()).decode())
 (R/dst).write_text(json.dumps(out),encoding='utf-8')
 print(len(out),dst,sum(len(s) for s in out)//1024,'KB')
cut('sheet*.png','data/avatars.json')
cut('win*.png','data/avatars_win.json')
