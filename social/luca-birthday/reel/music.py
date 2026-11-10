import numpy as np, wave
sr=44100; T=31.0; n=int(sr*T); out=np.zeros(n)
def note(f,t0,dur,amp):
    i0=int(t0*sr); L=int(min(dur,T-t0)*sr)
    if L<=0: return
    t=np.arange(L)/sr; s=np.zeros(L)
    for k in range(1,7):
        s+= (1/k**1.6)*np.sin(2*np.pi*f*k*t + k)*np.exp(-t*(1.2+0.7*k))
    s*=np.minimum(1,t/0.006)
    out[i0:i0+L]+=amp*s
def pad(fs,t0,dur,amp):
    i0=int(t0*sr); L=int(min(dur,T-t0)*sr); t=np.arange(L)/sr
    env=np.minimum(1,t/1.2)*np.minimum(1,(dur-t)/1.2)
    s=sum(np.sin(2*np.pi*f*t)+0.3*np.sin(2*np.pi*f*2.003*t) for f in fs)
    out[i0:i0+L]+=amp*env*s
m=lambda x:440*2**((x-69)/12)
beat=60/66; bar=4*beat
chords=[(57,[57,60,64]),(53,[53,57,60]),(48,[48,52,55]),(55,[55,59,62]),
        (57,[57,60,64]),(53,[53,57,60]),(48,[48,52,55]),(55,[55,59,62])]
t=0.3
for bi,(root,tri) in enumerate(chords):
    if t>T-4: break
    note(m(root-12),t,4,0.35); pad([m(x) for x in tri],t,bar+0.3,0.025)
    arp=[tri[0]+12,tri[1]+12,tri[2]+12,tri[1]+24,tri[2]+12,tri[1]+12,tri[0]+12,tri[2]]
    for j,x in enumerate(arp): note(m(x),t+j*beat/2,2.5,0.16 if j%2 else 0.2)
    # melody on later bars
    if bi>=2: note(m([76,72,72,74,76,77,79,79][bi]),t+beat*0.0,3,0.13)
    t+=bar/1.0*0.5 if False else bar
# final chord
for x in [48,60,64,67,72]: note(m(x),t,5,0.2)
pad([m(x) for x in [60,64,67]],t,T-t,0.03)
# reverb
ir_len=int(2.2*sr); ir=np.random.RandomState(1).randn(ir_len)*np.exp(-np.arange(ir_len)/sr*3.0)
N=1<<int(np.ceil(np.log2(n+ir_len)))
wet=np.fft.irfft(np.fft.rfft(out,N)*np.fft.rfft(ir,N),N)[:n]
mix=out+0.06*wet/np.max(np.abs(wet))*np.max(np.abs(out))*3
fo=int(3*sr); mix[-fo:]*=np.linspace(1,0,fo)**2
mix=mix/np.max(np.abs(mix))*0.8
st=np.stack([mix,np.roll(mix,int(0.012*sr))],1)
w=wave.open('music.wav','wb');w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes((st*32767).astype(np.int16).tobytes());w.close()
print('ok')
