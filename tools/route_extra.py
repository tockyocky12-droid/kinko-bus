"""直行バス（direct）と空港バス（airport）の線を道路に沿わせる（v27）。
route_lines.py と同じやり方（国土数値情報 バスルート N07 の線を道のつながりにし、目印の点どうしを最短の道すじでつなぐ）。
・直行バス：鹿屋→垂水港（道）、垂水港→鴨池港（フェリー。海の上なので直線。FERRY_SEGS に入れて点線で描く）、鴨池港→鹿児島中央駅→金生町（道）
・空港バス：鹿屋→霧島市役所前→鹿児島空港（道）。市役所前〜鹿屋は海岸線・中央線の線と重なるので描かない
使い方：python3 -I tools/route_extra.py /tmp/n07.json data/stops.js
"""
import json,re,sys,math,heapq
src,stops_js=sys.argv[1],sys.argv[2]
BBOX=(130.45,31.0,131.1,31.9);LINK=12;TOL=6;SNAP=300
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
cell=lambda p:(int(p[0]/0.0002),int(p[1]/0.0002))
grid={}
for p in adj:grid.setdefault(cell(p),[]).append(p)
for p in list(adj):
    cx,cy=cell(p)
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            for q in grid.get((cx+dx,cy+dy),[]):
                if q!=p and q not in adj[p] and m(p,q)<=LINK:add(p,q)
def nearest(p):
    best=None;bd=1e18;cx,cy=cell(p)
    for r in range(0,12):
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
            if nd<dist.get(v,1e18):dist[v]=nd;prev[v]=u;heapq.heappush(h,(nd,v))
    if t not in dist:return None,None
    path=[t]
    while path[-1]!=s:path.append(prev[path[-1]])
    return path[::-1],dist[t]
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
def road(wps):
    out=[];fb=0
    for a,b in zip(wps,wps[1:]):
        A=(a[1],a[0]);B=(b[1],b[0]);na,da=nearest(A);nb,db=nearest(B);seg=None
        if na and nb and da<=SNAP and db<=SNAP:
            path,L=dijkstra(na,nb)
            if path and L<=2.5*m(A,B)+2000:seg=path
        if seg is None:seg=[A,B];fb+=1
        if out and out[-1]==seg[0]:seg=seg[1:]
        out+=seg
    return [[round(y,5),round(x,5)] for x,y in dp(out)],fb
s=open(stops_js,encoding='utf-8').read()
P=json.loads(re.search(r'const STOP_POS=(\{.*?\});',s,re.S).group(1))
KAMOIKE=[31.55273,130.55922]
d1,f1=road([P['鹿屋'],P['垂水港']])
d2,f2=road([KAMOIKE,P['鹿児島中央駅'],P['金生町（山形屋）']])
ferry=[d1[-1],d2[0]]
direct=d1+d2
air,f3=road([P['鹿屋'],P['霧島市役所前'],P['鹿児島空港']])
mm=re.search(r'const LINE_PATHS=(\{.*?\});',s,re.S);LP=json.loads(mm.group(1))
LP['direct']=direct;LP['airport']=air
s=s[:mm.start(1)]+json.dumps(LP,ensure_ascii=False,separators=(',',':'))+s[mm.end(1):]
s=re.sub(r'\nconst FERRY_SEGS=.*?;\n','\n',s)
s=s.rstrip('\n')+'\n// 直行バスのフェリー区間（垂水港〜鴨池港）。海の上なので直線で、点線で描く\nconst FERRY_SEGS='+json.dumps([ferry])+';\n'
open(stops_js,'w',encoding='utf-8').write(s)
def L(p):return sum(m((a[1],a[0]),(b[1],b[0])) for a,b in zip(p,p[1:]))/1000
print('直線のまま',f1,f2,f3,'| direct',len(direct),round(L(d1),1),'+',round(L(d2),1),'km | airport',len(air),round(L(air),1),'km')
