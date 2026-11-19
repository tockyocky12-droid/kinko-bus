"""路線の線を道路に沿わせる。
国土数値情報 バスルート（N07）の線を道のつながり（グラフ）にし、今の LINE_PATHS の点（バス停の位置）どうしを
道に沿った最短の道すじでつなぐ。重なる区間は路線どうしで同じ点になるよう、区間ごとに一度だけ間引く。
使い方：python3 -I tools/readshp.py <N07のshpの拡張子なしパス> cp932 /tmp/n07.json
        python3 -I tools/route_lines.py /tmp/n07.json data/stops.js
"""
import json,re,sys,math,heapq
src,stops_js=sys.argv[1],sys.argv[2]
BBOX=(130.55,31.0,131.0,31.5)        # 錦江町・南大隅町・鹿屋のあたり
SNAP=250                              # バス停から道までこれ以上離れていたら直線のまま（m）
LINK=12                               # 別の線どうしの端がこれ以内ならつなぐ（m）
TOL=6                                 # 間引きの許容（m）
def m(a,b):
    la=math.radians((a[1]+b[1])/2);return math.hypot((a[0]-b[0])*111320*math.cos(la),(a[1]-b[1])*110540)
d=json.load(open(src,encoding='utf-8'))
key=lambda p:(round(p[0],6),round(p[1],6))
adj={}
def add(a,b):
    if a==b:return
    w=m(a,b);adj.setdefault(a,{})[b]=w;adj.setdefault(b,{})[a]=w
for g in d['geom']:
    for seg in g:
        pts=[key(p) for p in seg]
        if not any(BBOX[0]<x<BBOX[2] and BBOX[1]<y<BBOX[3] for x,y in pts):continue
        for a,b in zip(pts,pts[1:]):add(a,b)
# 近い点どうしをつなぐ（別々の線の継ぎ目）
cell=lambda p:(int(p[0]/0.0002),int(p[1]/0.0002))
grid={}
for p in adj:grid.setdefault(cell(p),[]).append(p)
for p in list(adj):
    cx,cy=cell(p)
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            for q in grid.get((cx+dx,cy+dy),[]):
                if q!=p and q not in adj[p] and m(p,q)<=LINK:add(p,q)
nodes=list(adj)
def nearest(p):
    best=None;bd=1e18
    cx,cy=cell(p)
    for r in range(0,8):
        for dx in range(-r,r+1):
            for dy in range(-r,r+1):
                if max(abs(dx),abs(dy))!=r:continue
                for q in grid.get((cx+dx,cy+dy),[]):
                    dd=m(p,q)
                    if dd<bd:bd,best=dd,q
        if best and bd<r*0.0002*90000:break
    return best,bd
def dijkstra(s,t):
    dist={s:0};prev={};h=[(0,s)]
    while h:
        dd,u=heapq.heappop(h)
        if u==t:break
        if dd>dist[u]:continue
        for v,w in adj[u].items():
            nd=dd+w
            if nd<dist.get(v,1e18):dist[v]=nd;prev[v]=u;heapq.heappush(h,(nd+0,v))
    if t not in dist:return None,None
    path=[t]
    while path[-1]!=s:path.append(prev[path[-1]])
    return path[::-1],dist[t]
s=open(stops_js,encoding='utf-8').read()
mm=re.search(r'const LINE_PATHS=(\{.*?\});',s,re.S);LP=json.loads(mm.group(1))
routed={};report={}
for rid,wps in LP.items():
    if rid=='direct':routed[rid]=None;continue
    out=[];fb=0
    for a,b in zip(wps,wps[1:]):
        A=(a[1],a[0]);B=(b[1],b[0])
        na,da=nearest(A);nb,db=nearest(B)
        seg=None
        if na and nb and da<=SNAP and db<=SNAP:
            path,L=dijkstra(na,nb)
            if path and L<=3*m(A,B)+400:seg=path
        if seg is None:seg=[A,B];fb+=1
        if out and out[-1]==seg[0]:seg=seg[1:]
        out+=seg
    routed[rid]=out;report[rid]=fb
# 区間ごとに一度だけ間引く（重なる区間は同じ点になる）
use={}
for rid,pts in routed.items():
    if not pts:continue
    for a,b in zip(pts,pts[1:]):use.setdefault(frozenset((a,b)),set()).add(rid)
deg={}
for e in use:
    for p in e:deg[p]=deg.get(p,0)+1
keyn=set()
for rid,pts in routed.items():
    if not pts:continue
    keyn.add(pts[0]);keyn.add(pts[-1])
    for i in range(1,len(pts)-1):
        p=pts[i]
        if deg.get(p,0)!=2 or use[frozenset((pts[i-1],p))]!=use[frozenset((p,pts[i+1]))]:keyn.add(p)
for rid,wps in LP.items():
    if rid=='direct':continue
def dp(pts):
    if len(pts)<3:return pts
    a,b=pts[0],pts[-1];la=math.cos(math.radians(a[1]))
    ax,ay,bx,by=a[0]*111320*la,a[1]*110540,b[0]*111320*la,b[1]*110540
    def dist(p):
        px,py=p[0]*111320*la,p[1]*110540;dx,dy=bx-ax,by-ay;L=dx*dx+dy*dy
        if L==0:return math.hypot(px-ax,py-ay)
        t=max(0,min(1,((px-ax)*dx+(py-ay)*dy)/L));return math.hypot(px-ax-t*dx,py-ay-t*dy)
    i,md=max(((i,dist(p)) for i,p in enumerate(pts[1:-1],1)),key=lambda x:x[1])
    if md<=TOL:return [a,b]
    return dp(pts[:i+1])[:-1]+dp(pts[i:])
cache={}
def simp(chain):
    k=tuple(chain);r=tuple(chain[::-1])
    if k in cache:return cache[k]
    if r in cache:return cache[r][::-1]
    cache[k]=dp(chain);return cache[k]
final={}
for rid,pts in routed.items():
    if not pts:final[rid]=LP[rid];continue
    res=[pts[0]];chain=[pts[0]]
    for p in pts[1:]:
        chain.append(p)
        if p in keyn:res+=simp(chain)[1:];chain=[p]
    if len(chain)>1:res+=simp(chain)[1:]
    final[rid]=[[round(y,5),round(x,5)] for x,y in res]
new=s[:mm.start(1)]+json.dumps(final,ensure_ascii=False,separators=(',',':'))+s[mm.end(1):]
open(stops_js,'w',encoding='utf-8').write(new)
print('直線のまま残った区間',report);print({k:len(v) for k,v in final.items()});print('bytes',len(new))
