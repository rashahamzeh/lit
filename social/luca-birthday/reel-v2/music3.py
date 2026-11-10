# Upbeat 120 BPM birthday track, fully synthesised (royalty-free).
import numpy as np, wave
from scipy.signal import butter, sosfilt
sr = 44100; BPM = 120; B = 60 / BPM; T = 44.0; N = int(sr * T)
rng = np.random.RandomState(7)
mix = {k: np.zeros(N) for k in ['kick', 'clap', 'hat', 'bass', 'chord', 'lead', 'fx', 'pad']}
m = lambda x: 440 * 2 ** ((x - 69) / 12)
def lp(x, f, o=2): return sosfilt(butter(o, min(f, sr/2.2), 'low', fs=sr, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=sr, output='sos'), x)
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], 'band', fs=sr, output='sos'), x)
def add(ch, t0, sig):
    i = int(t0 * sr); j = min(N, i + len(sig))
    if i < N: mix[ch][i:j] += sig[:j - i]
def saw(f, L, detune=0.0):
    t = np.arange(L) / sr; ph = (f * (1 + detune) * t + rng.rand()) % 1
    return 2 * ph - 1

# ---- sections ----
DROPS = [(4, 26), (30, 38), (38, 44)]
GAP = (23.0, 24.0)  # drums drop out under 'but we remember...'
in_drop = lambda t: any(a <= t < b for a, b in DROPS)
prog = [[62, 66, 69], [61, 64, 69], [59, 62, 66], [55, 59, 62]]   # D  A  Bm  G
roots = [50, 45, 47, 43]
outro = [[62, 66, 69], [61, 64, 69], [61, 64, 69], [62, 66, 69]]  # D A A D
outro_roots = [50, 45, 45, 50]

def kick(t0, a=1.0):
    L = int(.35 * sr); t = np.arange(L) / sr
    f = 50 + 110 * np.exp(-t * 35); ph = 2 * np.pi * np.cumsum(f) / sr
    s = np.sin(ph) * np.exp(-t * 7) + .3 * np.exp(-t * 300) * rng.randn(L) * .3
    add('kick', t0, a * s)
def clap(t0, a=.55):
    L = int(.25 * sr); t = np.arange(L) / sr
    n = bp(rng.randn(L), 900, 4000)
    env = np.exp(-t * 18) + .6 * (np.exp(-((t - .012) * 400) ** 2) + np.exp(-((t - .024) * 400) ** 2))
    add('clap', t0, a * n * env)
def hat(t0, a=.18, d=40):
    L = int(.08 * sr); t = np.arange(L) / sr
    add('hat', t0, a * hp(rng.randn(L), 7000) * np.exp(-t * d))
def crash(t0, a=.35):
    L = int(2.5 * sr); t = np.arange(L) / sr
    add('fx', t0, a * hp(rng.randn(L), 4000) * np.exp(-t * 1.6))
def impact(t0, a=.9):
    L = int(1.5 * sr); t = np.arange(L) / sr
    f = 30 + 60 * np.exp(-t * 8); s = np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-t * 2.5)
    add('fx', t0, a * s); crash(t0)
def riser(t0, dur, a=.25):
    L = int(dur * sr); t = np.arange(L) / sr; p = t / dur
    noise = rng.randn(L); out = np.zeros(L); seg = L // 16
    for k in range(16):  # sweep the filter up in steps
        sl = slice(k * seg, (k + 1) * seg if k < 15 else L)
        out[sl] = bp(noise, 400 + 7000 * (k / 15) ** 2, 9000 + 6000 * (k / 15))[sl]
    sweep = np.sin(2 * np.pi * np.cumsum(200 + 1200 * p ** 2) / sr) * .25
    add('fx', t0, a * (out + sweep) * p ** 2)
def snare_roll(t0, dur):
    t = 0; n = 0
    while t < dur:
        step = B / 2 if t < dur * .5 else (B / 4 if t < dur * .8 else B / 8)
        clap(t0 + t, .18 + .35 * t / dur); t += step

def pluck(f, t0, dur, a, cut=3500):
    L = int(dur * sr); t = np.arange(L) / sr
    s = saw(f, L) + .5 * saw(f, L, .005) + .3 * np.sin(2 * np.pi * 2 * f * t)
    s = lp(s, cut) * np.exp(-t * 6) * np.minimum(1, t / .003)
    add('lead', t0, a * s)
def stab(notes, t0, dur, a, cut=5000):
    L = int(dur * sr); t = np.arange(L) / sr; s = np.zeros(L)
    for n in notes:
        for d in (-.012, -.005, 0, .006, .013): s += saw(m(n), L, d)
        s += .6 * saw(m(n + 12), L, .003)
    s = lp(s, cut) * np.exp(-t * 4) * np.minimum(1, t / .004)
    add('chord', t0, a * s / len(notes))
def bass(note, t0, dur, a=.5):
    L = int(dur * sr); t = np.arange(L) / sr
    s = saw(m(note), L) + .6 * np.sin(2 * np.pi * m(note) * t / 2 * 2)
    s = lp(s, 600) * np.minimum(1, t / .004) * np.exp(-t * 3)
    add('bass', t0, a * s)
def pad(notes, t0, dur, a=.06, cut=1800):
    L = int(dur * sr); t = np.arange(L) / sr; s = np.zeros(L)
    for n in notes:
        for d in (-.006, 0, .007): s += saw(m(n), L, d)
    env = np.minimum(1, t / .4) * np.minimum(1, (dur - t) / .4).clip(0)
    add('pad', t0, a * lp(s, cut) * env)

hook = [74, 76, 78, 76, 74, 73, 71, 73]   # 8 eighths per bar, shifted per chord
hook_off = [0, -1, -3, -5]

for bar in range(22):
    t0 = bar * 2 * B * 2  # bar = 4 beats = 2 s
    ci = bar % 4
    if t0 >= 38: break
    ch, rt = prog[ci], roots[ci]
    drop = in_drop(t0)
    if t0 < 4:  # intro: filtered pad + hats building
        pad(ch, t0, 2, .08, 900 + 900 * bar)
        for k in range(4): stab(ch, t0 + k * B + B / 2, .25, .25, 1200 + 800 * bar)
        for k in range(8 if bar else 4): hat(t0 + k * B / (2 if bar else 1), .1)
        continue
    if 26 <= t0 < 30:  # breakdown
        pad(ch, t0, 2.05, .12, 2500)
        for k in range(8):
            pluck(m(ch[k % 3] + 12), t0 + k * B / 2, .4, .16, 2800)
        bass(rt, t0, 2, .35)
        continue
    ingap = lambda x: GAP[0] <= x < GAP[1]
    if t0 + 1 >= GAP[0] and t0 < GAP[1]: pad(ch, GAP[0], 1.05, .12, 3000)
    for k in range(4):
        if not ingap(t0 + k * B): kick(t0 + k * B)
    for k in (1, 3):
        if not ingap(t0 + k * B): clap(t0 + k * B)
    for k in range(8):
        if ingap(t0 + k * B / 2): continue
        hat(t0 + k * B / 2 + B / 4 * 0, .07)  # 8ths
        hat(t0 + k * B / 2 + B / 4, .16 if t0 >= 30 else .13)  # offbeats louder
        stab(ch, t0 + k * B / 2 + B / 2 * 0, .22, .30 if k % 2 else .2)
        bass(rt if k % 2 == 0 else rt + 12, t0 + k * B / 2, .24, .45)
    for k, n in enumerate(hook):
        if ingap(t0 + k * B / 2): continue
        pluck(m(n + hook_off[ci]), t0 + k * B / 2, .35, .14 if t0 < 30 else .17)

# FX
riser(1.0, 3.0); impact(4.0)
riser(22.6, 1.4, .3); impact(24.0, 1.0); impact(24.5, .8)
riser(27.0, 3.0, .3); snare_roll(28.0, 2.0); impact(30.0)
riser(36.0, 2.0, .22); impact(38.0, 1.0)
for t in (8, 12, 16, 20, 34): crash(t, .2)
# drum fills
for k in range(4): clap(17.0 + k * B / 4, .3); clap(37.0 + k * B / 4, .35)

# ---- outro 38–44: Happy Birthday melody (public domain) over D A A D ----
for bar in range(3):
    t0 = 38 + bar * 2
    ch, rt = outro[bar], outro_roots[bar]
    for k in range(4): kick(t0 + k * B, .9)
    clap(t0 + B); clap(t0 + 3 * B)
    for k in range(8):
        hat(t0 + k * B / 2 + B / 4, .13)
        stab(ch, t0 + k * B / 2, .22, .28 if k % 2 else .2)
        bass(rt if k % 2 == 0 else rt + 12, t0 + k * B / 2, .24, .42)
# melody: A A B A D C# | A A B A E D  (in beats)
mel = [(69, .75), (69, .25), (71, 1), (69, 1), (74, 1), (73, 2),
       (69, .75), (69, .25), (71, 1), (69, 1), (76, 1), (74, 2.5)]
t = 38.0 - B * 1.0  # pickup into the downbeat
for n, d in mel:
    pluck(m(n + 12), t, d * B + .3, .26, 5000); pluck(m(n), t, d * B + .3, .12, 3000); t += d * B
stab([62, 66, 69, 74], 44 - 1.6, 1.6, .35, 3000); kick(44 - 1.6)

# ---- sidechain pumping on music channels ----
duck = np.ones(N); L = int(.28 * sr); shape = 1 - .75 * np.exp(-np.arange(L) / sr * 14)
for t0 in np.arange(4, 44, B):
    if 26 <= t0 < 30 or GAP[0] <= t0 < GAP[1]: continue
    i = int(t0 * sr); j = min(N, i + L); duck[i:j] = np.minimum(duck[i:j], shape[:j - i])
for k in ('bass', 'chord', 'pad', 'lead'): mix[k] *= duck

gains = dict(kick=.9, clap=.55, hat=.6, bass=.55, chord=.42, lead=.5, fx=.6, pad=.6)
out = sum(gains[k] * v for k, v in mix.items())
# simple room reverb on a send
ir = rng.randn(int(1.2 * sr)) * np.exp(-np.arange(int(1.2 * sr)) / sr * 4)
from scipy.signal import fftconvolve
wet = fftconvolve(mix['clap'] * .5 + mix['lead'] * .5 + mix['chord'] * .2, ir)[:N]
out = out + .015 * wet
out = np.tanh(out / np.percentile(np.abs(out), 99.5) * .9)  # soft clip / glue
fo = int(1.2 * sr); out[-fo:] *= np.linspace(1, 0, fo) ** 1.5
out = out / np.max(np.abs(out)) * .92
L_ch = out; R_ch = np.roll(out, int(.008 * sr)) * .97 + .03 * out
st = np.stack([L_ch, R_ch], 1)
w = wave.open('music3.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
w.writeframes((st * 32767).astype(np.int16).tobytes()); w.close(); print('ok')
