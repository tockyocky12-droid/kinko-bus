"""QRコード（型番4・誤り訂正M・バイトモード）を自前で作る。外部ライブラリ不要。
使い方：python3 make_qr.py <文字列> <出力.svg>"""
import sys
V=4;N=17+4*V;EC_PER_BLOCK=18;BLOCKS=[32,32]
# GF(256)
EXP=[0]*512;LOG=[0]*256;x=1
for i in range(255):
    EXP[i]=x;LOG[x]=i;x<<=1
    if x&0x100:x^=0x11d
for i in range(255,512):EXP[i]=EXP[i-255]
def mul(a,b):return 0 if a==0 or b==0 else EXP[LOG[a]+LOG[b]]
def gen(n):
    g=[1]
    for i in range(n):
        ng=[0]*(len(g)+1)
        for j,c in enumerate(g):ng[j]^=c;ng[j+1]^=mul(c,EXP[i])
        g=ng
    return g
def rs(data,n):
    g=gen(n);r=list(data)+[0]*n
    for i in range(len(data)):
        c=r[i]
        if c:
            for j in range(1,len(g)):r[i+j]^=mul(g[j],c)
    return r[len(data):]
def encode(text):
    b=text.encode('utf-8');cap=sum(BLOCKS)*8
    bits='0100'+format(len(b),'08b')+''.join(format(c,'08b') for c in b)
    assert len(bits)<=cap
    bits+='0'*min(4,cap-len(bits));bits+='0'*((8-len(bits)%8)%8)
    data=[int(bits[i:i+8],2) for i in range(0,len(bits),8)];pad=[0xEC,0x11];k=0
    while len(data)<sum(BLOCKS):data.append(pad[k%2]);k+=1
    blocks=[];o=0
    for n in BLOCKS:blocks.append(data[o:o+n]);o+=n
    ecs=[rs(bl,EC_PER_BLOCK) for bl in blocks]
    out=[]
    for i in range(max(BLOCKS)):
        for bl in blocks:
            if i<len(bl):out.append(bl[i])
    for i in range(EC_PER_BLOCK):
        for e in ecs:out.append(e[i])
    return out
def build(cw,mask):
    M=[[None]*N for _ in range(N)]
    def finder(r,c):
        for dr in range(-1,8):
            for dc in range(-1,8):
                rr,cc=r+dr,c+dc
                if 0<=rr<N and 0<=cc<N:
                    on=(0<=dr<=6 and 0<=dc<=6) and (dr in(0,6) or dc in(0,6) or (2<=dr<=4 and 2<=dc<=4))
                    M[rr][cc]=on
    finder(0,0);finder(0,N-7);finder(N-7,0)
    for i in range(8,N-8):M[6][i]=M[i][6]=(i%2==0)
    for dr in range(-2,3):
        for dc in range(-2,3):M[26+dr][26+dc]=max(abs(dr),abs(dc))!=1
    M[4*V+9][8]=True
    res=set()
    for i in range(9):res.add((8,i));res.add((i,8))
    for i in range(8):res.add((8,N-1-i));res.add((N-1-i,8))
    for (r,c) in res:
        if M[r][c] is None:M[r][c]=False
    bits=''.join(format(c,'08b') for c in cw);bi=0;up=True;col=N-1
    while col>0:
        if col==6:col-=1
        rows=range(N-1,-1,-1) if up else range(N)
        for r in rows:
            for c in (col,col-1):
                if M[r][c] is None and (r,c) not in res:
                    v=bits[bi]=='1' if bi<len(bits) else False;bi+=1
                    if [lambda r,c:(r+c)%2==0,lambda r,c:r%2==0,lambda r,c:c%3==0,lambda r,c:(r+c)%3==0,
                        lambda r,c:(r//2+c//3)%2==0,lambda r,c:(r*c)%2+(r*c)%3==0,lambda r,c:((r*c)%2+(r*c)%3)%2==0,
                        lambda r,c:((r+c)%2+(r*c)%3)%2==0][mask](r,c):v=not v
                    M[r][c]=v
        up=not up;col-=2
    fmt=(0b00<<3)|mask;d=fmt<<10;g=0b10100110111
    for i in range(14,9,-1):
        if d>>i&1:d^=g<<(i-10)
    f=((fmt<<10)|d)^0b101010000010010
    fb=[(f>>i)&1 for i in range(15)]  # bit0 = LSB
    for i in range(15):
        v=bool(fb[i])
        if i<6:M[i][8]=v
        elif i<8:M[i+1][8]=v
        else:M[N-15+i][8]=v
        if i<8:M[8][N-1-i]=v
        elif i<9:M[8][15-i-1+1]=v
        else:M[8][15-i-1]=v
    M[4*V+9][8]=True
    return M
def penalty(M):
    p=0
    for rows in (M,[list(x) for x in zip(*M)]):
        for row in rows:
            run=1
            for i in range(1,N):
                if row[i]==row[i-1]:run+=1
                else:
                    if run>=5:p+=run-2
                    run=1
            if run>=5:p+=run-2
    for r in range(N-1):
        for c in range(N-1):
            if M[r][c]==M[r][c+1]==M[r+1][c]==M[r+1][c+1]:p+=3
    dark=sum(map(sum,M));p+=abs(dark*100//(N*N)-50)//5*10
    return p
text,out=sys.argv[1],sys.argv[2]
cw=encode(text)
best=min(range(8),key=lambda m:penalty(build(cw,m)));M=build(cw,best)
q=4;S=N+2*q
rects=''.join(f'<rect x="{c+q}" y="{r+q}" width="1" height="1"/>' for r in range(N) for c in range(N) if M[r][c])
open(out,'w').write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}" shape-rendering="crispEdges"><rect width="{S}" height="{S}" fill="#fff"/><g fill="#000">{rects}</g></svg>')
# PNG for checking
try:
    from PIL import Image
    sc=10;im=Image.new('L',(S*sc,S*sc),255);px=im.load()
    for r in range(N):
        for c in range(N):
            if M[r][c]:
                for y in range(sc):
                    for x in range(sc):px[(c+q)*sc+x,(r+q)*sc+y]=0
    im.save(out.replace('.svg','.png'))
except Exception as e:print(e)
print('mask',best)
