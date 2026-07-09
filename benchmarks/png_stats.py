"""Hard pixel discriminator for Octane previews.

Bars/geometry render -> high local edge energy (Laplacian std).
A pure HDRI gradient -> near-zero edge energy.

Usage: python png_stats.py <path> [<path2> ...]
"""
from __future__ import annotations
import sys, struct, zlib
from pathlib import Path

def load_png(path: str):
    data = Path(path).read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not png"
    pos = 8; W=H=bd=ct=None; idat=b""
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos+4])[0]; typ = data[pos+4:pos+8]
        chunk = data[pos+8:pos+8+ln]
        if typ == b"IHDR":
            W,H,bd,ct = struct.unpack(">IIBB", chunk[:10])
        elif typ == b"IDAT":
            idat += chunk
        elif typ == b"IEND":
            break
        pos += 12+ln
    raw = zlib.decompress(idat)
    ch = 3 if ct==2 else (4 if ct==6 else 1)
    stride = W*ch
    # unfilter
    out = bytearray(H*stride); prev = bytearray(stride)
    p=0
    for y in range(H):
        f = raw[p]; p+=1
        line = bytearray(raw[p:p+stride]); p+=stride
        for x in range(stride):
            a = line[x-ch] if x>=ch else 0
            b = prev[x]
            c = prev[x-ch] if x>=ch else 0
            if f==1: line[x]=(line[x]+a)&255
            elif f==2: line[x]=(line[x]+b)&255
            elif f==3: line[x]=(line[x]+((a+b)>>1))&255
            elif f==4:
                pp=a+b-c; pa=abs(pp-a); pb=abs(pp-b); pc=abs(pp-c)
                pr=a if (pa<=pb and pa<=pc) else (b if pb<=pc else c)
                line[x]=(line[x]+pr)&255
        out[y*stride:(y+1)*stride]=line; prev=line
    return W,H,ch,out

def stats(path: str):
    W,H,ch,px = load_png(path)
    # mean/std per channel over RGB
    n=W*H
    sums=[0,0,0]; sq=[0,0,0]
    for i in range(n):
        for c in range(3):
            v=px[i*ch+c]; sums[c]+=v; sq[c]+=v*v
    mean=[s/n for s in sums]; std=[(sq[c]/n - mean[c]**2)**0.5 for c in range(3)]
    # background fraction: pixels near-white (all ch>250)
    bg=0
    for i in range(n):
        if px[i*ch]>=250 and px[i*ch+1]>=250 and px[i*ch+2]>=250: bg+=1
    nonbg=(1-bg/n)*100
    # edge energy: Laplacian magnitude on luminance
    def lum(x,y):
        i=y*W+x; return 0.299*px[i*ch]+0.587*px[i*ch+1]+0.114*px[i*ch+2]
    edge=[]
    for y in range(1,H-1):
        for x in range(1,W-1):
            v=abs(4*lum(x,y)-lum(x-1,y)-lum(x+1,y)-lum(x,y-1)-lum(x,y+1))
            edge.append(v)
    elen=len(edge); esum=sum(edge); e2=sum(e*e for e in edge)
    emean=esum/elen; estd=(e2/elen-emean**2)**0.5
    print(f"{Path(path).name}: {W}x{H} ch{ch}")
    print(f"  mean RGB      = {[round(m,1) for m in mean]}")
    print(f"  std RGB       = {[round(s,1) for s in std]}")
    print(f"  nonbg_pct     = {nonbg:.2f}%")
    print(f"  EDGE energy   = mean {emean:.2f}  std {estd:.2f}  (bars => high; gradient => ~0)")
    return dict(mean=mean,std=std,nonbg=nonbg,edge_mean=emean,edge_std=estd)

if __name__=="__main__":
    for p in sys.argv[1:]:
        try: stats(p)
        except Exception as e: print(p, "ERR", e)
