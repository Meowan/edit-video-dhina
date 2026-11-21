"""v3 voice edit: smoother joins, no fillers, every word allowed to finish.

- Spans are probe-verified start points (first intended word) and end points.
- Each span END is extended until the voice has actually decayed (energy below the
  room floor for 70 ms) so the last syllable rings out, but never into the next word.
- Fillers (aa / hmm / err / false starts) are removed as (cut_end, resume) pairs.
- Long pauses inside a span are shortened from the middle, keeping natural decay.
- Joins: 25 ms fade-in, 70 ms fade-out, then a short silence; chunk gaps give breathing room.
Usage: python3 tools/build_voice3.py words.json voice16k.wav source.m4a out_dir
"""
import json, sys, wave, subprocess
import numpy as np

WORDS, SRC16, SRC_FULL, OUT_DIR = sys.argv[1:5]
W = json.load(open(WORDS))

# chunk = (list of spans, gap_after). A span may list internal cuts [(cut_at, resume_at), ...].
CHUNKS = [
  # HOOK
  ([(590.1, 594.2), (595.0, 596.5)], 2.75),                       # Bermula Januari ini kita nak buat transformasi sukan di negeri Pahang
  # SUKMA, Para SUKMA + SPM
  ([(100.15, 101.82), (102.18, 112.88), (114.6, 121.75)], 0.65),  # Hari ini kita sampaikan insentif ... SUKMA dan Para SUKMA, dan juga ... cemerlang dalam akademik, khususnya SPM
  # POINT 1
  ([(150.9, 153.95), (154.65, 161.6)], 0.30),                     # Untuk sukan hoki dan sukan menembak, pencapaian Pahang sebagai juara keseluruhan
  ([(248.3, 250.0), (253.5, 257.0)], 0.65),                       # Kita naikkan kadar itu, daripada 2,000 kita tambah 1,000, jadi 3,000
  # POINT 2
  ([(312.7, 317.75), (324.2, 327.05)], 0.30),                     # Pahang dah naikkan kadar gaji minimum jurulatih, untuk jurulatih sepenuh masa 2,200
  ([(498.25, 505.1), (505.8, 508.15), (509.95, 513.25, [(510.76, 511.44)])], 0.30),  # Kadar gaji ... Januari 2027 sangat kompetitif, tinggi [hmm] berbanding negeri lain
  ([(516.35, 520.0), (520.6, 521.55), (529.38, 532.4)], 0.65),    # Saya nak pelawa jurulatih di luar sana, cuba cari rezeki di Pahang
  # POINT 3
  ([(732.12, 733.1), (734.6, 736.2)], 0.25),                      # Saya nak cari jurulatih olahraga
  ([(736.5, 738.25)], 0.25),                                      # Yang kedua silat
  ([(739.6, 742.4)], 0.30),                                       # Yang ketiga angkat berat
  ([(753.85, 759.5)], 0.30),                                      # Pahang satu ketika adalah jaguh untuk sukan ini
  ([(760.2, 762.8, [(761.25, 761.72)])], 0.30),                   # Saya nak kembalikan [aa] kegemilangan itu
]
CAPTIONS = [   # exact caption text per chunk (spelling fixed, fillers never shown)
  "Bermula Januari ini kita nak buat transformasi sukan di negeri Pahang",
  "Hari ini kita sampaikan insentif kepada atlet-atlet Pahang yang cemerlang di SUKMA dan Para SUKMA dan juga kepada atlet-atlet Pahang yang cemerlang dalam akademik khususnya SPM",
  "Untuk sukan hoki dan sukan menembak pencapaian Pahang sebagai juara keseluruhan",
  "Kita naikkan kadar itu daripada 2,000 kita tambah 1,000 jadi 3,000",
  "Pahang dah naikkan kadar gaji minimum jurulatih untuk jurulatih sepenuh masa di Pahang 2,200",
  "Kadar gaji jurulatih penuh masa di Pahang bermula Januari 2027 sangat kompetitif tinggi berbanding negeri-negeri lain",
  "Saya nak pelawa jurulatih di luar sana cuba cari rezeki di Pahang",
  "Saya nak cari jurulatih olahraga",
  "Yang kedua silat",
  "Yang ketiga angkat berat",
  "Pahang satu ketika adalah jaguh untuk sukan ini",
  "Saya nak kembalikan kegemilangan itu",
]

wf = wave.open(SRC16); sr = wf.getframerate()
a = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768
hop = sr // 100
rms = np.sqrt(np.convolve(a**2, np.ones(hop * 2) / (hop * 2), mode="same")[::hop])
db = 20 * np.log10(rms + 1e-9)
FLOOR, SPEECH = -25.0, -20.0

def ring_out(b, limit=0.18):
    """Extend end b until the voice decays below FLOOR for 70 ms; stop before a new onset."""
    i0 = int(b * 100); quiet = 0
    for k in range(int(limit * 100)):
        v = db[i0 + k]
        if v < FLOOR:
            quiet += 1
            if quiet >= 4: return (i0 + k - 4 + 3) / 100      # keep ~30 ms of the decay
        else:
            if quiet >= 3 and v > SPEECH:                      # next word started: cut in the dip
                return (i0 + k - quiet // 2) / 100
            quiet = 0
    seg = db[i0:i0 + int(limit * 100)]
    return (i0 + int(np.argmin(seg))) / 100

def onset(s, back=0.06):
    """Start a hair before the first voiced frame (keeps consonant attack)."""
    i0 = int(s * 100)
    v = np.where(db[i0:i0 + 30] > FLOOR)[0]
    return max(s, (i0 + (v[0] if len(v) else 0)) / 100 - back)

def squeeze(s, e, max_pause=0.36, keep=0.24):
    """Shorten long silent runs inside [s,e] from the middle; returns sub-pieces."""
    i0, i1 = int(s * 100), int(e * 100)
    quiet = db[i0:i1] < FLOOR
    pieces, cur, k = [], s, 0
    while k < len(quiet):
        if quiet[k]:
            j = k
            while j < len(quiet) and quiet[j]: j += 1
            if (j - k) / 100 > max_pause:
                mid = (i0 + (k + j) / 2) / 100
                pieces.append((cur, mid - keep / 2)); cur = mid + keep / 2
            k = j
        else:
            k += 1
    pieces.append((cur, e))
    return [(x, y) for x, y in pieces if y - x > 0.03]

pieces, chunk_bounds, t = [], [], 0.0
for ci, (spans, gap) in enumerate(CHUNKS):
    c0 = t
    for si, sp in enumerate(spans):
        s, e = sp[0], sp[1]; cuts = sp[2] if len(sp) > 2 else []
        s = onset(s)
        e = ring_out(e)
        # split around fillers
        segs, cur = [], s
        for cut_at, resume in cuts:
            segs.append((cur, ring_out(cut_at, 0.15))); cur = onset(resume, 0.03)
        segs.append((cur, e))
        for x, y in segs:
            for px, py in squeeze(x, y):
                pieces.append((px, py)); t += py - px
            pieces.append(("gap", 0.05)); t += 0.05
    pieces.pop(); t -= 0.05
    chunk_bounds.append([round(c0, 3), round(t, 3)])
    pieces.append(("gap", gap)); t += gap
pieces.pop(); t -= CHUNKS[-1][1]

flt, labels = [], []
for i, p in enumerate(pieces):
    if p[0] == "gap":
        flt.append(f"anullsrc=r=48000:cl=mono,atrim=0:{p[1]}[p{i}]")
    else:
        s, e = p; d = e - s
        fo = min(0.07, d / 3)
        flt.append(f"[0:a]atrim={s:.3f}:{e:.3f},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=mono,afade=t=in:d=0.025:curve=qsin,afade=t=out:st={d-fo:.3f}:d={fo:.3f}:curve=qsin[p{i}]")
    labels.append(f"[p{i}]")
flt.append("".join(labels) + f"concat=n={len(labels)}:v=0:a=1,highpass=f=80,afftdn=nf=-30,acompressor=threshold=-20dB:ratio=3:attack=8:release=120,loudnorm=I=-16:TP=-1.5[out]")
open(f"{OUT_DIR}/voice_filter.txt", "w").write(";\n".join(flt))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC_FULL, "-filter_complex_script", f"{OUT_DIR}/voice_filter.txt",
                "-map", "[out]", "-ar", "48000", "-ac", "2", f"{OUT_DIR}/voice_edit.wav"], check=True)

# caption words: spread each chunk's text over its voiced time, weighted by syllable-ish length
words_out = []
for ci, (c0, c1) in enumerate(chunk_bounds):
    toks = CAPTIONS[ci].split()
    wts = [max(2, len(x)) for x in toks]; tot = sum(wts); acc = c0
    for x, w_ in zip(toks, wts):
        d_ = (c1 - c0) * w_ / tot
        words_out.append({"text": x, "start": round(acc, 3), "end": round(acc + d_ * 0.92, 3), "chunk": ci}); acc += d_
json.dump({"duration": round(t, 3), "chunks": chunk_bounds, "words": words_out},
          open(f"{OUT_DIR}/voice_words.json", "w"), ensure_ascii=False, indent=1)
print("duration", round(t, 2))
for ci, (c0, c1) in enumerate(chunk_bounds): print(ci, c0, c1, CAPTIONS[ci][:60])
