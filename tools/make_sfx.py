"""Synthesise whoosh + impact SFX (original, royalty-free)."""
import numpy as np, sys
from scipy.signal import butter, sosfilt
from scipy.io import wavfile
SR = 48000; rng = np.random.default_rng(3); out = sys.argv[1]
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], "band", fs=SR, output="sos"), x)
# whoosh: noise through a band sweeping up then down, swelling to the cut
L = int(0.75 * SR); t = np.arange(L) / SR
n = rng.standard_normal(L); y = np.zeros(L); hop = 480
for i in range(0, L, hop):
    p = i / L; fc = 300 + 3200 * np.sin(np.pi * min(p * 1.15, 1)) ** 2
    seg = bp(rng.standard_normal(hop + 2000), fc * 0.6, min(fc * 1.6, 20000))[2000:]
    y[i:i + hop] = seg[:len(y[i:i + hop])]
env = np.where(t < 0.5, (t / 0.5) ** 2.2, np.exp(-(t - 0.5) * 14))
y *= env; pan = np.linspace(-0.8, 0.8, L)
wh = np.stack([y * (1 - pan) / 2, y * (1 + pan) / 2], 1); wh /= np.abs(wh).max() * 1.05
wavfile.write(f"{out}/whoosh.wav", SR, (wh * 32767).astype(np.int16))
# impact: sub boom + noise crack
L = int(1.2 * SR); t = np.arange(L) / SR
f = 48 * (1 + 1.5 * np.exp(-t * 25)); boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4)
crack = bp(rng.standard_normal(L), 800, 6000) * np.exp(-t * 40) * 0.5
im = boom + crack; im /= np.abs(im).max() * 1.05
wavfile.write(f"{out}/impact.wav", SR, (np.stack([im, im], 1) * 32767).astype(np.int16))
print("ok")
