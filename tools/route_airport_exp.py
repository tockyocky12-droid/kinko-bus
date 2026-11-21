"""空港バスの線を、高速道路経由の道すじに描き直す（v33）。
鹿屋→旭原：国土数値情報 バスルート（N07）の道
旭原→鹿屋串良JCT：大隅縦貫道（串良鹿屋道路）。高速道路時系列（N06）にもN07にも入っていないため、直線の目安
鹿屋串良JCT→野方IC（道の駅あらさの）→曽於弥五郎→末吉財部→国分→隼人東→加治木JCT→溝辺鹿児島空港IC：国土数値情報 高速道路時系列（N06-25）の線
溝辺鹿児島空港IC→鹿児島空港：N07の道
使い方：python3 -I tools/route_airport_exp.py /tmp/n07.json <N06-25_HighwaySection.geojson> <N06-25_Joint.geojson> data/stops.js
"""
import json,re,sys,math,heapq
n07,n06,n06j,stops_js=sys.argv[1:5]
TOL=6
def m(a,b):
    la=math.radians((a[1]+b[1])/2);return math.hypot((a[0]-b[0])*111320*math.cos(la),(a[1]-b[1])*110540)
key=lambda p:(round(p[0],6),round(p[1],6))
class G:
    def __init__(s,lines,bbox,link):
        s.adj={}
        for pts in lines:
            pts=[key(p) for p in pts]
            if not any(bbox[0]<x<bbox[2] and bbox[1]<y<bbox[3] for x,y in pts):continue
            for a,b in zip(pts,pts[1:]):s.add(a,b)
        s.cell=lambda p:(int(p[0]/0.0002),int(p[1]/0.0002));s.grid={}
        for p in s.adj:s.grid.setdefault(s.cell(p),[]).append(p)
        for p in list(s.adj):
            cx,cy=s.cell(p)
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    for q in s.grid.get((cx+dx,cy+dy),[]):
                        if q!=p and q not in s.adj[p] and m(p,q)<=link:s.add(p,q)
    def add(s,a,b):
        if a==b:return
        w=m(a,b);s.adj.setdefault(a,{})[b]=w;s.adj.setdefault(b,{})[a]=w
    def nearest(s,p):
        return min(s.adj,key=lambda q:m(p,q))
    def path(s,A,B):
        a,b=s.nearest(A),s.nearest(B);da,db=m(A,a),m(B,b)
        dist={a:0};prev={};h=[(0,a)]
        while h:
            d,u=heapq.heappop(h)
            if u==b:break
            if d>dist[u]:continue
            for v,w in s.adj[u].items():
                nd=d+w
                if nd<dist.get(v,1e18):dist[v]=nd;prev[v]=u;heapq.heappush(h,(nd,v))
        assert b in dist,('つながらない',A,B)
        p=[b]
        while p[-1]!=a:p.append(prev[p[-1]])
        return p[::-1],dist[b],da,db
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
d=json.load(open(n07,encoding='utf-8'))
road=G([seg for g in d['geom'] for seg in g],(130.6,31.3,131.0,31.9),12)
hw=json.load(open(n06,encoding='utf-8'))
lines=[]
for f in hw['features']:
    if f['properties']['N06_003']!=9999:continue  # 今も使われている区間だけ
    g=f['geometry'];lines+= [g['coordinates']] if g['type']=='LineString' else g['coordinates']
exp=G(lines,(130.6,31.4,131.15,31.9),15)
J={f['properties']['N06_018']:tuple(f['geometry']['coordinates'][:2]) for f in json.load(open(n06j,encoding='utf-8'))['features'] if f['properties']['N06_014']==9999}
s=open(stops_js,encoding='utf-8').read()
P=json.loads(re.search(r'const STOP_POS=(\{.*?\});',s,re.S).group(1))
ll=lambda k:(P[k][1],P[k][0])
ASAHIBARU=(130.88078,31.40842) # 旭原（国土数値情報 バス停留所）
rep=[]
def seg_road(A,B):
    p,L,da,db=road.path(A,B);rep.append(('道',round(L/1000,1),round(da),round(db)));return p
def seg_exp(*wps):
    out=[]
    for A,B in zip(wps,wps[1:]):
        p,L,da,db=exp.path(A,B);rep.append(('高速',round(L/1000,1),round(da),round(db)))
        out+=p[1:] if out else p
    return out
a1=seg_road(ll('鹿屋'),ASAHIBARU)
a3=seg_exp(J['鹿屋串良JCT'],J['野方'],J['末吉財部'],J['国分'],J['加治木JCT'],J['溝辺鹿児島空港'])
a4=seg_road(J['溝辺鹿児島空港'],ll('鹿児島空港'))
gap=[a1[-1],a3[0]]  # 大隅縦貫道（データなし。直線の目安）
pts=dp(a1)+dp(a3)+dp(a4)
out=[[round(y,5),round(x,5)] for x,y in pts]
mm=re.search(r'const LINE_PATHS=(\{.*?\});',s,re.S);LP=json.loads(mm.group(1))
LP['airport']=out
s=s[:mm.start(1)]+json.dumps(LP,ensure_ascii=False,separators=(',',':'))+s[mm.end(1):]
s=re.sub(r'\n// 空港バスの大隅縦貫道.*?\nconst GUESS_SEGS=.*?;\n','\n',s,flags=re.S)
s=s.rstrip('\n')+'\n// 空港バスの大隅縦貫道（旭原〜鹿屋串良JCT）。道のデータがないため直線の目安で、点線で描く\nconst GUESS_SEGS='+json.dumps([[[round(y,5),round(x,5)] for x,y in gap]])+';\n'
open(stops_js,'w',encoding='utf-8').write(s)
L=sum(m((a[1],a[0]),(b[1],b[0])) for a,b in zip(out,out[1:]))/1000
print(rep,'点',len(out),'全長',round(L,1),'km','直線の目安',round(m(*gap)/1000,1),'km')
