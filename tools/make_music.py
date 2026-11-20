"""Original heroic orchestral-style bed (synthesised, royalty-free) for the edit.
D minor, 100 bpm: string pad + driving low ostinato + timpani/taiko + horn line.
Usage: python3 tools/make_music.py <seconds> <out.wav>
"""
import sys, numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

DUR = float(sys.argv[1]); OUT = sys.argv[2]
SR = 48000; N = int(DUR * SR); t = np.arange(N) / SR
BPM = 100; BEAT = 60 / BPM; BAR = 4 * BEAT
rng = np.random.default_rng(7)

def hz(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, f, o=2): return sosfilt(butter(o, f, "low", fs=SR, output="sos"), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, "high", fs=SR, output="sos"), x)
def saw(f, tt, ph=0.0): return 2 * ((f * tt + ph) % 1) - 1

# progression (2 bars each): Dm  Bb  F  C  | Dm Bb Gm A
PROG = [(50, [62, 65, 69]), (46, [62, 65, 70]), (41, [60, 65, 69]), (48, [60, 64, 67]),
        (50, [62, 65, 69]), (46, [62, 65, 70]), (43, [62, 67, 70]), (45, [61, 64, 69])]
SEG = 2 * BAR

# intensity curve (0..1): soft hook, build into para block, steady body, final swell
def intensity(x):
    pts = [(0, .7), (4.8, .8), (4.9, 1.0), (7.6, .9), (18.3, .9), (31.4, .9), (66.7, 1.0), (80.5, 1.0), (83.4, 1.0), (DUR, .9)]
    xs, ys = zip(*pts); return np.interp(x, xs, ys)
I = intensity(t)

pad = np.zeros(N); low = np.zeros(N); horn = np.zeros(N); perc = np.zeros(N)

nseg = int(np.ceil(DUR / SEG))
for k in range(nseg):
    root, tones = PROG[k % len(PROG)]
    s0, s1 = int(k * SEG * SR), min(N, int((k + 1) * SEG * SR + 0.6 * SR))
    tt = t[s0:s1] - k * SEG
    env = np.clip(tt / 0.8, 0, 1) * np.clip((SEG + 0.6 - tt) / 0.6, 0, 1)
    # string pad: detuned saws, chord tones + octave below
    sig = np.zeros(len(tt))
    for m in tones + [tones[0] - 12]:
        for d in (-0.08, -0.03, 0.03, 0.08):
            sig += saw(hz(m) * (1 + d / 100 * 12 / 12 * 0.6), tt, rng.random())
    pad[s0:s1] += sig * env * 0.05
    # low ostinato: 8ths on root (bars) with accent pattern, cellos+basses
    for b in range(16):
        st = k * SEG + b * BEAT / 2
        a, e = int(st * SR), int((st + BEAT / 2 * 0.85) * SR)
        if a >= N: break
        e = min(e, N); ts = t[a:e] - st
        acc = 1.0 if b % 4 == 0 else (0.75 if b % 2 == 0 else 0.55)
        f = hz(root - 12 + (12 if b % 8 in (3, 7) else 0))
        note = (saw(f, ts) + 0.6 * saw(f * 1.004, ts)) * np.exp(-ts * 5) * np.clip(ts / 0.008, 0, 1)
        low[a:e] += note * acc * 0.35
    # horn line on the 2nd half (bars) - sustained heroic fifths
    if k >= 1:
        mel = tones[-1] - 12
        for j, (m, ln) in enumerate([(mel, 1.5), (mel + 2 if k % 2 else mel - 2, 0.5), (tones[1] - 12, 2.0)]):
            st = k * SEG + BAR + sum(l for _, l in [(mel, 1.5), (0, .5), (0, 2.0)][:j]) * BAR / 2
            a, e = int(st * SR), int((st + ln * BAR / 2) * SR)
            if a >= N: continue
            e = min(e, N); ts = t[a:e] - st
            vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * ts) * np.clip(ts - 0.3, 0, 1)
            ph = np.cumsum(hz(m) * vib) / SR
            x = 2 * (ph % 1) - 1 + 0.5 * (2 * ((ph * 1.5) % 1) - 1)
            en = np.clip(ts / 0.12, 0, 1) * np.clip((ln * BAR / 2 - ts) / 0.25, 0, 1)
            horn[a:e] += x * en * 0.16

def timp(st, amp, f0=55):
    a = int(st * SR)
    if a >= N: return
    L = min(int(1.6 * SR), N - a); ts = np.arange(L) / SR
    f = f0 * (1 + 0.5 * np.exp(-ts * 30))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-ts * 3.2)
    hit = lp(rng.standard_normal(L), 900) * np.exp(-ts * 35) * 0.6
    perc[a:a + L] += (body + hit) * amp

nb = int(DUR / BEAT) + 1
for b in range(nb):
    st = b * BEAT
    if b % 4 == 0: timp(st, 0.9)
    if b % 4 == 2: timp(st, 0.55, 49)
    if b % 8 == 7: timp(st + BEAT / 2, 0.4, 62)
# big hits: hook, para entry, chapter changes, end card
for st in (0.0, 4.9, 18.31, 31.43, 66.7, 83.4):
    timp(st, 1.5, 41); timp(st + 0.01, 0.8, 82)
# riser into para block and final
for a0, a1 in ((3.4, 4.9), (81.9, 83.4)):
    a, e = int(a0 * SR), int(a1 * SR); ts = np.arange(e - a) / SR
    nz = hp(rng.standard_normal(e - a), 1500) * (ts / (a1 - a0)) ** 3 * 0.05
    perc[a:e] += nz

pad = lp(pad, 2600, 2); low = lp(low, 900, 2); horn = lp(horn, 1800, 2)
mix = pad * 0.9 + low * 0.9 + horn * 0.8 + perc * 0.9
mix *= I
# end: let it ring out after the final hit
fade_end = np.clip((DUR - t) / 2.0, 0, 1); mix *= fade_end
mix = hp(mix, 35)
# stereo + hall reverb (exp-decay noise IR)
irL = int(2.2 * SR); ti = np.arange(irL) / SR
ir_l = rng.standard_normal(irL) * np.exp(-ti * 2.6); ir_r = rng.standard_normal(irL) * np.exp(-ti * 2.6)
ir_l = lp(ir_l, 5000); ir_r = lp(ir_r, 5000)
wet_l = fftconvolve(mix, ir_l)[:N]; wet_r = fftconvolve(mix, ir_r)[:N]
wet_l /= np.max(np.abs(wet_l)); wet_r /= np.max(np.abs(wet_r)); dry = mix / np.max(np.abs(mix))
L_ = dry * 0.75 + wet_l * 0.45; R_ = dry * 0.75 + wet_r * 0.45
st = np.stack([L_, R_], 1); st /= np.max(np.abs(st)) * 1.12
wavfile.write(OUT, SR, (st * 32767).astype(np.int16))
print("wrote", OUT, DUR)
