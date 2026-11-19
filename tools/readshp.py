import struct,sys,json
def read_dbf(p,enc):
    b=open(p,'rb').read();n=struct.unpack('<I',b[4:8])[0];hl,rl=struct.unpack('<HH',b[8:12])
    fs=[];o=32
    while b[o]!=0x0D:
        name=b[o:o+11].split(b'\0')[0].decode();t=chr(b[o+11]);ln=b[o+16];fs.append((name,t,ln));o+=32
    recs=[];o=hl
    for i in range(n):
        r=b[o+1:o+rl];o+=rl;d={};p2=0
        for name,t,ln in fs:
            d[name]=r[p2:p2+ln].decode(enc,'replace').strip();p2+=ln
        recs.append(d)
    return recs
def read_shp(p):
    b=open(p,'rb').read();o=100;out=[]
    while o<len(b):
        num,cl=struct.unpack('>II',b[o:o+8]);o+=8;st=struct.unpack('<i',b[o:o+4])[0]
        if st in (3,13,23):
            np_,npt=struct.unpack('<ii',b[o+36:o+44]);parts=struct.unpack('<%di'%np_,b[o+44:o+44+4*np_])
            q=o+44+4*np_;pts=[struct.unpack('<dd',b[q+16*i:q+16*i+16]) for i in range(npt)]
            segs=[pts[parts[i]:(parts[i+1] if i+1<np_ else npt)] for i in range(np_)]
            out.append(segs)
        else: out.append([])
        o+=cl*2
    return out
if __name__=='__main__':
    base=sys.argv[1];enc=sys.argv[2]
    R=read_dbf(base+'.dbf',enc);G=read_shp(base+'.shp')
    json.dump({'recs':R,'geom':G},open(sys.argv[3],'w'),ensure_ascii=False)
    print(len(R),len(G),R[0])
