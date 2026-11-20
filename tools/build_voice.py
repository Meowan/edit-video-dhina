"""Cut the press-conference voice into the edit: keep only chosen words,
tighten pauses, drop fillers/repeats. Writes voice_edit.wav + voice_words.json."""
import json, sys, wave, subprocess
import numpy as np

WORDS, SRC16, SRC_FULL, OUT_DIR = sys.argv[1:5]
W = json.load(open(WORDS))

# Kept source spans (seconds); every word whose start lies in a span is kept.
# Each chunk = one thought; chunks are separated by a short breath.
CHUNKS = [
  [(78.3, 86.65)],                                    # Pahang negeri pertama salurkan insentif kepada atlet-atlet Pahang
  [(100.15, 113.8)],                                  # Hari ini kita sampaikan pula insentif ... SUKMA dan Para SUKMA baru-baru ini
  [(150.9, 153.95), (154.45, 161.6)],                  # Untuk sukan hoki dan sukan menembak, pencapaian Pahang sebagai juara keseluruhan
  [(248.3, 250.0), (253.5, 257.0)],                  # Kita naikkan kadar ... daripada 2,000 kita tambah 1,000, jadi 3,000
  [(277.7, 281.75), (285.40, 289.75), (290.30, 293.2)],  # Saya dapat cadangan ini di media sosial ... boleh dilaksanakan. Sebab tu kita naikkan
  [(312.7, 317.75), (324.20, 327.05)],                  # Pahang dah naikkan kadar gaji minimum jurulatih, untuk jurulatih sepenuh masa 2,200
  [(328.0, 330.6), (331.6, 333.5)],                  # Pada Januari ni akan buat pelarasan gaji
  [(443.12, 445.75), (446.5, 455.0)],                  # Dengan pelarasan gaji baru ni, mereka akan menerima kenaikan antara RM200 kepada RM1,200
  [(498.25, 505.1), (505.8, 508.15), (509.95, 513.25)],  # Kadar gaji jurulatih ... bermula Januari 2027 sangat kompetitif, tinggi berbanding negeri lain
  [(516.2, 520.0), (520.6, 523.7), (523.75, 524.6), (526.4, 527.3), (529.1, 532.4)],  # Saya nak pelawa jurulatih di luar sana yang berkelayakan, berkemahiran, cuba cari rezeki di Pahang
  [(590.1, 594.2), (595.0, 596.5)],                  # Bermula Januari ni kita nak buat transformasi sukan di negeri Pahang
]

FIX = {"selalukan":"salurkan","julatih":"jurulatih","dipahang":"di Pahang","sukma":"SUKMA",
       "kesuruhan":"keseluruhan","social":"sosial","ni":"ini","tu":"itu","1200":"1,200"}

wf = wave.open(SRC16); sr = wf.getframerate()
a = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768
hop = int(sr * 0.01)
rms = np.sqrt(np.convolve(a**2, np.ones(hop*3)/(hop*3), mode="same")[::hop])
db = 20*np.log10(rms + 1e-9)
thr = -22.0   # pause threshold (room noise ~-28 dB, speech -8..-20 dB)

def tighten(s, e):
  i0, i1 = int(s*100), int(e*100)
  v = np.where(db[i0:i1] > thr)[0]
  if len(v) == 0: return s, e
  return (i0 + v[0]) / 100, (i0 + v[-1] + 1) / 100

def in_spans(w, spans): return any(a <= w["s"] < b for a, b in spans)

BREATH, MAX_PAUSE, KEEP_PAUSE = 0.30, 0.40, 0.20

def snap(c, win=0.0):
  """Move a cut point to the quietest 60 ms nearby so words are not clipped."""
  if win <= 0: return c
  i0, i1 = max(0, int((c-win)*100)), int((c+win)*100)
  seg = np.convolve(db[i0:i1], np.ones(6)/6, mode="same")
  return (i0 + int(np.argmin(seg))) / 100

def compress(s, e):
  """Split [s,e] into voiced pieces, shortening internal pauses > MAX_PAUSE."""
  i0, i1 = int(s*100), int(e*100)
  voiced = db[i0:i1] > thr
  out, cur, run = [], i0, 0
  for k, v in enumerate(voiced):
    idx = i0 + k
    run = 0 if v else run + 1
    if run == int(MAX_PAUSE*100):          # long pause starts at idx-run+1
      cut = idx - run + 1 + int(KEEP_PAUSE*50)
      out.append((cur/100, cut/100)); cur = None
    if v and cur is None:
      cur = max(idx - int(KEEP_PAUSE*50), out[-1][1]*100 if out else 0)
  if cur is not None: out.append((cur/100, e))
  # trim leading/trailing silence
  if out:
    a, b = out[0]; va = np.where(db[int(a*100):int(b*100)] > thr)[0]
    if len(va): out[0] = (max(a, a + va[0]/100 - 0.05), b)
    a, b = out[-1]; vb = np.where(db[int(a*100):int(b*100)] > thr)[0]
    if len(vb): out[-1] = (a, min(b, a + (vb[-1]+1)/100 + 0.08))
  return [(a, b) for a, b in out if b - a > 0.04]

FIX_TOKENS = lambda ws: ws
pieces, words_out, chunk_bounds = [], [], []
t = 0.0
for ci, spans in enumerate(CHUNKS):
  c0 = t
  for (sa, sb) in spans:
    a, b = snap(sa), snap(sb)
    parts = compress(a, b)
    ws = [dict(w) for w in W if a - 0.05 <= (w["s"] + w["e"]) / 2 < b]
    merged = []
    for w in ws:
      txt = w["w"].strip()
      if merged and (txt.startswith(",") or txt.startswith("-") or (merged[-1]["w"].strip()=="20" and txt=="27")):
        merged[-1]["w"] = merged[-1]["w"].strip() + txt; merged[-1]["e"] = w["e"]; continue
      merged.append(w)
    def mapt(x):
      acc = t
      for pa, pb in parts:
        if x < pa: return acc
        if x <= pb: return acc + (x - pa)
        acc += pb - pa
      return acc
    for w in merged:
      txt = w["w"].strip(); txt = FIX.get(txt.lower(), txt)
      ws_, we_ = mapt(max(w["s"], a)), mapt(min(w["e"], b))
      words_out.append({"text": txt, "start": round(ws_, 3), "end": round(max(we_, ws_ + 0.08), 3), "chunk": ci})
    for pa, pb in parts:
      pieces.append((pa, pb)); t += pb - pa
  chunk_bounds.append([round(c0, 3), round(t, 3)])
  t += BREATH; pieces.append(("gap", BREATH))

# render with ffmpeg: trim each piece from full-quality source, short fades, concat
flt, labels = [], []
for i, p in enumerate(pieces):
  if p[0] == "gap":
    flt.append(f"anullsrc=r=48000:cl=mono,atrim=0:{p[1]}[p{i}]")
  else:
    s, e = p
    flt.append(f"[0:a]atrim={s:.3f}:{e:.3f},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=mono,afade=t=in:d=0.015,afade=t=out:st={e-s-0.02:.3f}:d=0.02[p{i}]")
  labels.append(f"[p{i}]")
flt.append("".join(labels) + f"concat=n={len(labels)}:v=0:a=1,highpass=f=80,acompressor=threshold=-20dB:ratio=3,loudnorm=I=-16:TP=-1.5[out]")
open(f"{OUT_DIR}/voice_filter.txt", "w").write(";\n".join(flt))
subprocess.run(["ffmpeg","-v","error","-y","-i",SRC_FULL,"-filter_complex_script",f"{OUT_DIR}/voice_filter.txt","-map","[out]","-ar","48000","-ac","2",f"{OUT_DIR}/voice_edit.wav"], check=True)
json.dump({"duration": round(t - BREATH, 3), "chunks": chunk_bounds, "words": words_out}, open(f"{OUT_DIR}/voice_words.json","w"), ensure_ascii=False, indent=1)
print("duration", round(t - BREATH, 2))
for ci,(a,b) in enumerate(chunk_bounds):
  print(ci, a, b, " ".join(w["text"] for w in words_out if w["chunk"]==ci))
