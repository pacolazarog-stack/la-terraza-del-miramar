#!/usr/bin/env python3
from pathlib import Path
import csv, json, math, os, re, subprocess, tempfile, unicodedata
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, resample_poly

SR=44100
ROOT=Path(__file__).resolve().parent
MP3=ROOT/"build"/"mp3"
FLAC=ROOT/"build"/"flac"
MP3.mkdir(parents=True,exist_ok=True)
FLAC.mkdir(parents=True,exist_ok=True)
rng=np.random.default_rng(270918)

TITLES=[
"MIRAMAR COMUNIDAD","OK","EL CUERPO","CLAC","NADIE","NACE EL CONFLICTO",
"PRIMERA INCURSIÓN TERRESTRE","TERRITORIO","MAYORÍA SIMPLE","VOTEN","MAYORÍA SIMPLE",
"NOSOTROS","DERECHO","TOGA · BANDERA · REINA","MÍRENME","ESTADO","VIENTO","EL SOL",
"CONFORME A DERECHO","QUE CONSTE","EL REINO CABE EN UNA CARPETA","MIRAMAR","INNOVAR",
"¿QUIÉN GOBIERNA?","RUMOR","CENTRO DE DATOS","MIRA QUIÉN MIRA QUIÉN","CÓMO SEGUIMOS",
"DESARMAR A LA REINA","DIEZ MINUTOS"]
DUR=[80,45,80,60,60,90,75,90,75,75,60,75,75,90,75,90,90,75,90,75,75,90,90,75,75,90,90,90,150,210]
assert sum(DUR)==2560

def stereo(x,pan=0):
    pan=max(-1,min(1,pan)); th=(pan+1)*math.pi/4
    return np.column_stack((x*math.cos(th),x*math.sin(th))).astype(np.float32)

def add(buf,snd,t,pan=0,gain=1):
    i=int(round(t*SR))
    if i>=len(buf): return
    if snd.ndim==1: snd=stereo(snd,pan)
    n=min(len(snd),len(buf)-i)
    if n>0: buf[i:i+n]+=snd[:n]*gain

def thump(length=.48,amp=.7,freq=58):
    n=max(1,int(round(length*SR))); t=np.arange(n)/SR
    f=freq+42*np.exp(-t*20); ph=2*np.pi*np.cumsum(f)/SR
    body=np.sin(ph)*np.exp(-t*8)
    noise=rng.normal(0,1,n)*np.exp(-t*35)
    noise=sosfilt(butter(2,900,btype="low",fs=SR,output="sos"),noise)
    return (amp*(.88*body+.12*noise)).astype(np.float32)

def slap(length=.18,amp=.45):
    n=max(1,int(round(length*SR))); t=np.arange(n)/SR
    y=rng.normal(0,1,n)
    y=sosfilt(butter(2,[550,5000],btype="bandpass",fs=SR,output="sos"),y)*np.exp(-t*26)
    return (amp*y/(np.max(np.abs(y))+1e-9)).astype(np.float32)

def click(length=.08,amp=.5,pitch=1800):
    n=max(1,int(round(length*SR))); t=np.arange(n)/SR
    y=(np.sin(2*np.pi*pitch*t)+.5*np.sin(2*np.pi*pitch*2.17*t))*np.exp(-t*60)
    y+=.25*rng.normal(0,1,n)*np.exp(-t*80)
    return (amp*y/(np.max(np.abs(y))+1e-9)).astype(np.float32)

def clac():
    return np.concatenate([click(.07,.55,1600),np.zeros(int(.045*SR),np.float32),click(.06,.4,2300)])

def tac(length=.26,amp=.62):
    n=max(1,int(round(length*SR))); t=np.arange(n)/SR
    y=.55*np.sin(2*np.pi*105*t)*np.exp(-t*15)+.22*np.sin(2*np.pi*2700*t)*np.exp(-t*38)
    y+=.08*rng.normal(0,1,n)*np.exp(-t*55)
    return (amp*y).astype(np.float32)

def brr(length=.9,amp=.15,freq=94):
    n=max(1,int(round(length*SR))); t=np.arange(n)/SR
    mod=.55+.45*np.sin(2*np.pi*7.3*t)
    y=(np.sin(2*np.pi*freq*t)+.34*np.sin(4*np.pi*freq*t)+.18*np.sin(6*np.pi*freq*t))*mod
    e=np.minimum(1,t/.03)*np.minimum(1,np.maximum(0,(length-t)/.08))
    return (amp*y*e).astype(np.float32)

def breath(length=1,amp=.12,voiced=False,exact_n=None):
    n=exact_n or max(1,int(round(length*SR))); t=np.arange(n)/SR
    y=rng.normal(0,1,n)
    y=sosfilt(butter(2,[250,6500],btype="bandpass",fs=SR,output="sos"),y)
    y/=np.max(np.abs(y))+1e-9
    e=np.sin(np.pi*np.clip(t/max(length,n/SR,1e-6),0,1))**1.6
    if voiced: y=.7*y+.3*np.sin(2*np.pi*185*t)
    return (amp*y*e).astype(np.float32)

def sweep(length=1.2,amp=.15,lo=500,hi=8000):
    n=max(1,int(round(length*SR))); t=np.arange(n)/SR
    y=rng.normal(0,1,n)
    y=sosfilt(butter(2,[lo,min(hi,SR/2-100)],btype="bandpass",fs=SR,output="sos"),y)
    e=np.sin(np.pi*np.clip(t/length,0,1))**1.4
    return (amp*y/(np.max(np.abs(y))+1e-9)*e).astype(np.float32)

def plip(length=.8,amp=.22):
    n=max(1,int(round(length*SR))); t=np.arange(n)/SR
    f=1400*np.exp(-t*5)+420; ph=2*np.pi*np.cumsum(f)/SR
    return (amp*np.sin(ph)*np.exp(-t*7)).astype(np.float32)

def room(length,amp=.004):
    n=int(round(length*SR)); t=np.arange(n)/SR
    y=rng.normal(0,1,n)
    y=sosfilt(butter(2,1800,btype="low",fs=SR,output="sos"),y)
    y/=np.max(np.abs(y))+1e-9
    mod=.55+.45*np.sin(2*np.pi*(.037+.003*np.sin(2*np.pi*.004*t))*t+.7)
    return (amp*y*mod).astype(np.float32)

voice_cache={}
def voice(text,speed=95,pitch=38):
    key=(text,speed,pitch)
    if key in voice_cache: return voice_cache[key].copy()
    fd,name=tempfile.mkstemp(suffix=".wav"); os.close(fd)
    try:
        cmd=["espeak-ng","-v","es+f3","-s",str(speed),"-p",str(pitch),"-a","120","-w",name,text]
        subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        x,sr0=sf.read(name,dtype="float32")
    finally:
        try: os.unlink(name)
        except OSError: pass
    if x.ndim>1: x=x.mean(axis=1)
    if sr0!=SR:
        from math import gcd
        g=gcd(sr0,SR); x=resample_poly(x,SR//g,sr0//g).astype(np.float32)
    nz=np.where(np.abs(x)>.002)[0]
    if len(nz): x=x[max(0,nz[0]-int(.05*SR)):min(len(x),nz[-1]+int(.12*SR))]
    x=sosfilt(butter(2,[120,7000],btype="bandpass",fs=SR,output="sos"),x)
    x=x/(np.max(np.abs(x))+1e-9)*.32
    x=(x+breath(len(x)/SR,.025,exact_n=len(x))).astype(np.float32)
    voice_cache[key]=x
    return x.copy()

def echo(x,pan=0,delay=.22,feedback=.18):
    b=stereo(x,pan); n=len(b)+int((delay*3+.2)*SR); out=np.zeros((n,2),np.float32); out[:len(b)]+=b
    for k,g in [(1,feedback),(2,feedback*.55),(3,feedback*.28)]:
        d=int(delay*k*SR); bb=b[:,::-1] if k%2 else b; out[d:d+len(b)]+=bb*g
    return out

TUM,TA,AH,CLAC,TAC,PLIP=thump(),slap(),breath(.55,.13,True),clac(),tac(),plip()

def vadd(buf,text,t,pan=0,gain=1,ech=False,speed=90,pitch=35):
    x=voice(text,speed,pitch)
    add(buf,echo(x,pan) if ech else stereo(x,pan),t,0,gain)

def collective(buf,text,t,gain=.8):
    for dt,pan,sp,pit,g in [(0,-.55,92,34,.60),(.07,.05,87,42,.48),(.13,.55,97,30,.42)]:
        add(buf,voice(text,sp,pit),t+dt,pan,gain*g)

def cell(buf,start,end,bpm,density=.8,heavy=.8,spread=.45):
    beat=60/bpm; t=start; k=0
    while t<end:
        for off,snd,g in [(0,TUM,.75*heavy),(1,TA,.52*density),(2,AH,.70*density),(3,TUM,.66*heavy)]:
            if t+off*beat<end: add(buf,snd,t+off*beat,((k+off)%3-1)*spread,g)
        t+=4*beat; k+=1

def vote(buf,start,end,bpm,intensity=.8):
    beat=60/bpm; t=start; k=0
    while t<end:
        for j,(snd,g) in enumerate([(TUM,.8),(TA,.55),(CLAC,.45),(TA,.48)]):
            if t+j*beat<end: add(buf,snd,t+j*beat,-.5 if j%2==0 else .5,g*intensity)
        if k%3==2 and t+1.5*beat<end: add(buf,TAC,t+1.5*beat,0,.55*intensity)
        t+=4*beat; k+=1

def machine(buf,start,end,bpm,intensity=.75):
    beat=60/bpm; t=start; k=0; clk=click(.05,.38,2500)
    while t<end:
        add(buf,clk,t,-.6 if k%2==0 else .6,intensity)
        if k%2==0 and t+beat/2<end: add(buf,TA,t+beat/2,.3,.35*intensity)
        if k%4==0 and t+beat<end: add(buf,brr(.6,.13),t+beat,-.2,intensity)
        t+=beat; k+=1


def sea_layer(length,amp=.055):
    n=max(1,int(round(length*SR))); t=np.arange(n)/SR
    a=rng.normal(0,1,n)
    a=sosfilt(butter(2,[45,7200],btype="bandpass",fs=SR,output="sos"),a)
    b=rng.normal(0,1,n)
    b=sosfilt(butter(2,650,btype="low",fs=SR,output="sos"),b)
    wave=.34+.66*(.5+.5*np.sin(2*np.pi*.066*t+.45*np.sin(2*np.pi*.009*t)))**1.8
    m=(.68*a/(np.std(a)+1e-9)+.32*b/(np.std(b)+1e-9))*wave*amp
    r=np.roll(m,int(.019*SR))*.985
    return np.column_stack((m,r)).astype(np.float32)

def cloth(length=1.2,amp=.055,lo=650,hi=9000):
    x=sweep(length,amp,lo,hi)
    n=len(x); t=np.arange(n)/SR
    mod=.22+.78*np.abs(np.sin(2*np.pi*(1.05+.18*np.sin(2*np.pi*.07*t))*t))
    return (x*mod).astype(np.float32)

def sparse_body(buf,times,kind="foot",gain=.45,spread=.45):
    for k,t in enumerate(times):
        snd=thump(.55,.48,72 if kind=="chest" else 104)
        add(buf,snd,float(t),(-1 if k%2==0 else 1)*spread,gain)

def scene(idx,length):
    # The corporal score privileges real-scale breath, cloth, pinza, body and silence.
    # Electronics transform those sources but do not introduce an external musical language.
    buf=stereo(room(length,.0018 if idx<14 else .0024))

    if idx==1:  # MIRAMAR COMUNIDAD
        for t in [2,18,39,61]:
            add(buf,breath(7,.040),t,-.08 if int(t)%2 else .08,.65)
        add(buf,plip(.55,.08),12,.32,.55)
        add(buf,brr(.42,.035,58),58,.02,.65)

    elif idx==2:  # OK
        add(buf,breath(9,.030),2,0,.55)
        vadd(buf,"ok",18,0,.54,False,80,34)

    elif idx==3:  # EL CUERPO
        for t,p in [(7,-.18),(22,.12),(39,-.05),(58,.15)]:
            add(buf,breath(5,.040,True),t,p,.62)
        sparse_body(buf,[15,33,51,69],"foot",.28,.16)
        for t in [11,46]:
            add(buf,cloth(4,.028,900,6500),t,.05,.55)

    elif idx==4:  # CLAC
        add(buf,breath(8,.022),3,0,.45)
        add(buf,CLAC,29,0,.82)
        # One origin event; the rest of the scene is deliberate silence.

    elif idx==5:  # NADIE
        add(buf,cloth(16,.022,1400,9200),6,-.12,.62)
        add(buf,breath(7,.020),31,.08,.45)

    elif idx==6:  # NACE EL CONFLICTO
        # Tension grows from cloth, not from an external riser.
        for t,g,p in [(6,.42,-.45),(19,.48,-.20),(34,.55,.05),(51,.62,.28),(68,.70,.48)]:
            add(buf,cloth(10,.040+g*.018,650,7800),t,p,g)
        add(buf,breath(12,.050),73,0,.72)

    elif idx==7:  # PRIMERA INCURSION TERRESTRE
        for t,p in [(8,-.45),(24,-.15),(43,.18)]:
            add(buf,sweep(4,.040,180,3100),t,p,.60)
        add(buf,cloth(8,.030,850,7000),49,.25,.55)
        add(buf,CLAC,62,.42,.67)

    elif idx==8:  # TERRITORIO
        # Long lateral drag: the ear follows the same physical crossing as the sheet.
        pieces=12
        for k in range(pieces):
            t=5+k*6.6
            pan=-.82+1.64*(k/(pieces-1))
            add(buf,cloth(5.4,.026,500,5200),t,pan,.70)
        add(buf,breath(8,.018),80,.1,.45)

    elif idx==9:  # MAYORIA SIMPLE
        events=[
            (8,thump(.6,.45,104),-.70,.40),
            (16,thump(.6,.42,118),-.48,.36),
            (24,slap(.22,.30),-.25,.46),
            (32,thump(.75,.42,78),0,.40),
            (40,thump(.6,.42,104),.22,.36),
            (48,slap(.20,.30),.44,.44),
            (56,CLAC,.63,.48),
            (64,cloth(1.2,.035,700,6000),.78,.58)]
        for t,s,p,g in events: add(buf,s,t,p,g)

    elif idx==10:  # VOTEN
        sparse_body(buf,np.arange(6,length-4,8.2),"foot",.26,.58)
        for t,p in [(12,-.62),(25,.54),(39,-.12),(54,.28)]:
            add(buf,breath(12,.022),t,p,.58)

    elif idx==11:  # MAYORIA SIMPLE
        t=5; k=0
        while t<length-3:
            if k%3==0: add(buf,thump(.5,.42,104),t,-.35,.34)
            elif k%3==1: add(buf,CLAC,t,.22,.38)
            else: add(buf,cloth(.9,.031,700,6500),t,.38,.45)
            t+=3.25; k+=1

    elif idx==12:  # NOSOTROS
        for off,p,sp,g in [(2,-.70,.054,.55),(8,.62,.067,.52),(17,-.10,.047,.48),(29,.28,.079,.42)]:
            t=off
            while t<length-7:
                add(buf,breath(6,.022),t,p,g)
                t+=1/sp

    elif idx==13:  # DERECHO
        # Mouth becomes regulation: phonetic matter, not declaimed prose.
        tokens=["mmm","rrr","ka","sss","te","pe"]
        t=5
        while t<length-4:
            tok=tokens[int((t*10)%len(tokens))]
            vadd(buf,tok,t,float(.65*np.sin(t*.63)),.20,False,88,30)
            t+=3.7
        add(buf,breath(8,.018),63,0,.40)

    elif idx==14:  # TOGA · BANDERA · REINA
        add(buf,sweep(7,.090,120,7200),22,0,.90)
        add(buf,cloth(12,.035,500,6500),45,.2,.62)

    elif idx==15:  # MIRENME
        # Structural silence: only human room/body remains.
        add(buf,breath(12,.018),18,0,.48)
        sparse_body(buf,[36,55],"foot",.18,.10)

    elif idx==16:  # ESTADO
        times=np.arange(6,length-4,7.2)
        for k,t in enumerate(times):
            add(buf,thump(.65+.05*k,.34,76),float(t),0,.30+min(.30,k*.035))

    elif idx==17:  # VIENTO
        # The same pinza becomes spatial surveillance.
        for t,p,g in [(7,-.82,.34),(22,.58,.31),(39,-.18,.29),(58,.84,.33),(76,.04,.52)]:
            add(buf,CLAC,t,p,g)
        add(buf,breath(16,.022),31,0,.46)

    elif idx==18:  # EL SOL
        # Breath slowly loses its owner and becomes open air.
        for t,p,g in [(3,-.15,.58),(20,.12,.54),(38,-.05,.48)]:
            add(buf,breath(20,.040),t,p,g)
        for t,p,g in [(28,-.55,.35),(43,.10,.40),(56,.58,.44)]:
            add(buf,sweep(14,.035,180,5600),t,p,g)

    elif idx==19:  # CONFORME A DERECHO
        t=6; k=0
        while t<length-4:
            add(buf,thump(.75,.38,78),t,-.10,.34+min(.20,k*.018))
            add(buf,thump(.55,.34,104),t+1.8,.18,.30+min(.16,k*.014))
            t+=5.0; k+=1

    elif idx==20:  # QUE CONSTE
        # The sheet behaves as a membrane, never as a drum kit.
        for t,p in [(7,-.25),(17,.10),(29,-.08),(42,.22),(56,0),(68,.15)]:
            add(buf,slap(.24,.26),t,p,.34)
            add(buf,cloth(.65,.027,420,3200),t+.03,p,.42)

    elif idx==21:  # EL REINO CABE EN UNA CARPETA
        sources=[thump(.5,.30,104),CLAC,cloth(.7,.025,650,6000),breath(1.4,.035)]
        for n,t in enumerate(np.arange(5,length-4,8.2)):
            base=sources[n%len(sources)]
            p=float(.58*np.sin(n*1.2))
            add(buf,base,t,p,.38)
            add(buf,base,t+.16,-p,.22)
            add(buf,base,t+.34,p*.4,.14)
            add(buf,base,t+.57,-p*.4,.08)

    elif idx==22:  # MIRAMAR
        # Apparent tear generated only from tension/cloth.
        for t,g,p in [(4,.35,-.60),(19,.42,-.30),(37,.50,0),(55,.60,.28),(73,.70,.58)]:
            add(buf,cloth(12,.045,420,5400),t,p,g)
        add(buf,sweep(20,.026,55,1200),57,0,.62)
        vadd(buf,"mar",79,0,.18,True,68,25)

    elif idx==23:  # INNOVAR
        # The eight human materials of scene 9 become a single exact machine.
        beat=60/84/2
        pattern=[
            ("foot",-.65),("palm",-.30),("chest",.05),("foot",.42),
            ("clac",.66),("palm",.24),("foot",-.18),("cloth",.48)]
        t=3; k=0
        while t<length-2:
            typ,p=pattern[k%8]
            if typ=="clac": snd=CLAC; g=.31
            elif typ=="cloth": snd=cloth(.42,.026,650,5200); g=.36
            elif typ=="palm": snd=slap(.18,.25); g=.30
            elif typ=="chest": snd=thump(.60,.32,78); g=.30
            else: snd=thump(.50,.34,104); g=.28
            add(buf,snd,t,p,g)
            t+=beat; k+=1

    elif idx==24:  # ¿QUIEN GOBIERNA?
        # Scene 23 becomes ill: absence, delay, duplication, anticipation.
        beat=60/84/2
        pattern=["foot","palm","chest","foot","clac","palm","foot","cloth"]
        t=3; k=0
        while t<length-2:
            frac=t/length
            if rng.random()<.06+.33*frac:
                t+=beat; k+=1; continue
            typ=pattern[k%8]
            p=(-.62+.18*(k%8))
            if typ=="clac": snd=CLAC; g=.28
            elif typ=="cloth": snd=cloth(.42,.024,650,5200); g=.32
            elif typ=="palm": snd=slap(.18,.23); g=.28
            elif typ=="chest": snd=thump(.58,.30,78); g=.28
            else: snd=thump(.48,.31,104); g=.26
            delay=float(rng.choice([0,0,0,.06,.12,-.05]))*(.4+frac)
            add(buf,snd,max(.2,t+delay),p,g)
            if rng.random()<.08*frac: add(buf,snd,t+delay+.10,-p,g*.48)
            t+=beat; k+=1

    elif idx==25:  # RUMOR
        words=["comunidad","mirar","nadie","mar","ok"]
        t=5; k=0
        while t<length-4:
            vadd(buf,words[k%len(words)],t,float(.78*np.sin(k*1.37)),.12+(k%3)*.025,False,96,30)
            t+=2.8; k+=1
        add(buf,breath(18,.018),49,0,.42)

    elif idx==26:  # CENTRO DE DATOS / RAM
        # Memory flashes: recognizable but incomplete; the gaps matter.
        memories=[
            (CLAC,.25),
            (thump(.40,.25,78),.22),
            (thump(.35,.23,104),.20),
            (cloth(.45,.020,700,5000),.28),
            (breath(.7,.022),.26),
            (plip(.35,.08),.20)]
        t=2.5; k=0
        while t<length-3:
            snd,g=memories[k%len(memories)]
            add(buf,snd,t,float(rng.uniform(-.82,.82)),g)
            t+=float(rng.uniform(.65,2.8)); k+=1
        for t,w,p in [(23,"ram",-.55),(52,"mar",.20),(78,"ok",.58)]:
            vadd(buf,w,t,p,.12,True,78,27)

    elif idx==27:  # MIRA QUIEN MIRA QUIEN
        # Electronics fall away: raw organism again.
        for t,p in [(5,-.12),(28,.09),(54,-.04),(75,.14)]:
            add(buf,breath(11,.025),t,p,.52)
        sparse_body(buf,[18,46,69],"foot",.20,.12)
        add(buf,cloth(12,.017,800,4800),60,.10,.40)

    elif idx==28:  # COMO SEGUIMOS
        add(buf,thump(2.8,.46,76),5,0,.54)
        add(buf,sweep(30,.022,45,1500),8,0,.52)
        add(buf,sea_layer(37,.022),48,0,.62)

    elif idx==29:  # DESARMAR A LA REINA
        # Dance grows exclusively from already-heard body/object materials.
        beat=60/98
        t=2; k=0
        while t<length-3:
            add(buf,thump(.45,.30,104),t,-.18,.28)
            if k%2==1: add(buf,slap(.17,.21),t+.02,.14,.27)
            if k%2==0: add(buf,CLAC,t+beat*.5,.44,.18)
            if k%4==0: add(buf,cloth(.8,.018,650,5000),t+.08,-.30,.34)
            t+=beat; k+=1
        add(buf,breath(length-24,.012),12,0,.35)
        vadd(buf,"Comunidad, venid para acá. Vamos a bailar.",42,0,.54,False,108,38)
        # Human error enters after the invitation.
        for t in np.arange(55,length-3,beat):
            if rng.random()<.72:
                jitter=float(rng.normal(0,.035+.0007*(t-55)))
                add(buf,slap(.16,.16),t+jitter,float(rng.uniform(-.80,.80)),.18)

    else:  # 30 · DIEZ MINUTOS
        # Dismantle the dance stem by stem, then breath -> sea -> second OK.
        beat=.62
        t=2; k=0
        while t<56:
            fade=max(0,1-t/56)
            if k%2==0: add(buf,thump(.42,.24,104),t,-.18,.18*fade)
            if k%3==1: add(buf,CLAC,t+.16,.32,.14*fade)
            if k%5==0: add(buf,cloth(.50,.015,650,4800),t+.06,-.10,.18*fade)
            t+=beat; k+=1
        add(buf,breath(122,.025),42,0,.58)
        add(buf,sea_layer(118,.040),78,0,.74)
        vadd(buf,"ok",174,0,.42,False,78,34)
        add(buf,sea_layer(27,.028),181,0,.58)

    # No loudness spectacle: preserve headroom and microscopic detail.
    buf=np.tanh(buf*.84).astype(np.float32)
    f=int(.06*SR)
    buf[:f]*=np.linspace(0,1,f)[:,None]
    buf[-f:]*=np.linspace(1,0,f)[:,None]
    return buf

def safe_name(i,title):
    s=unicodedata.normalize("NFKD",title).encode("ascii","ignore").decode("ascii")
    s=re.sub(r"[^A-Za-z0-9]+","_",s).strip("_").upper()
    return f"{i:02d}_{s}"

starts=[]; x=0
for d in DUR: starts.append(x); x+=d
manifest=[]
master_flac=FLAC/"MASTER_MIRAMAR_CORPORAL_42m40.flac"
with sf.SoundFile(master_flac,"w",samplerate=SR,channels=2,subtype="PCM_16",format="FLAC") as mf:
    for i,(title,d,st) in enumerate(zip(TITLES,DUR,starts),1):
        buf=scene(i,d); stem=safe_name(i,title)
        flac=FLAC/f"{stem}.flac"; mp3=MP3/f"{stem}.mp3"
        sf.write(flac,buf,SR,subtype="PCM_16",format="FLAC")
        subprocess.run(["ffmpeg","-loglevel","error","-y","-i",str(flac),"-codec:a","libmp3lame","-b:a","128k",str(mp3)],check=True)
        mf.write(buf)
        manifest.append({"scene":i,"title":title,"in_seconds":st,"out_seconds":st+d,"duration_seconds":d,"mp3":mp3.name})
subprocess.run(["ffmpeg","-loglevel","error","-y","-i",str(master_flac),"-codec:a","libmp3lame","-b:a","128k",str(ROOT/"MASTER_MIRAMAR_CORPORAL_42m40.mp3")],check=True)

info=sf.info(master_flac)
assert info.frames==2560*SR
for i,d in enumerate(DUR,1):
    p=FLAC/f"{safe_name(i,TITLES[i-1])}.flac"; inf=sf.info(p); assert inf.frames==d*SR

WEB=ROOT.parents[2]/"audio"
WEB.mkdir(parents=True,exist_ok=True)
web1=WEB/"LA_TERRAZA_DEL_MIRAMAR_CORPORAL_64K_PARTE_1_ESC_01-15.mp3"
web2=WEB/"LA_TERRAZA_DEL_MIRAMAR_CORPORAL_64K_PARTE_2_ESC_16-30.mp3"
subprocess.run(["ffmpeg","-loglevel","error","-y","-i",str(master_flac),"-t","1105","-codec:a","libmp3lame","-b:a","64k",str(web1)],check=True)
subprocess.run(["ffmpeg","-loglevel","error","-y","-ss","1105","-i",str(master_flac),"-t","1455","-codec:a","libmp3lame","-b:a","64k",str(web2)],check=True)

(ROOT/"MANIFIESTO_AUDIO.json").write_text(json.dumps({
"title":"La terraza del Miramar · versión corporal · partitura sonora",
"version":"CORPORAL V1 · 2026-09-18",
"sample_rate":SR,"channels":2,"total_duration_seconds":2560,"total_duration":"42:40",
"principle":"El sonido nace del cuerpo, respiración, pinza, sábana, móvil, suelo, aire y mar; el procesamiento transforma esas fuentes sin introducir una música externa.",
"sound_arcs":{
"respiracion":"individuo → invasión → masa → recuperación → mar",
"pinza":"CLAC doméstico → límite → vigilancia → máquina → ritmo → desaparición",
"sabana":"roce → tensión → territorio → arquitectura → membrana → resto → juego → sábana",
"cuerpo":"presencia → número → mecanismo → reina → caída → baile → respiración"
},
"critical_scenes":{"04":"CLAC originario","23":"máquina exacta","24":"fallo","26":"RAM","29":"baile corporal","30":"respiración → mar → OK"},
"web_parts":[str(web1.relative_to(ROOT.parents[2])),str(web2.relative_to(ROOT.parents[2]))],
"scenes":manifest},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("OK: versión corporal; 30 escenas; MASTER exacto 42:40; web 64k en dos partes.")
