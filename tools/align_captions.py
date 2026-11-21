"""Give each caption word the time whisper hears it in the edited voice (difflib alignment,
unmatched words interpolated). Rewrites voice_words.json in place."""
import json, sys, wave, re, subprocess, difflib, numpy as np
from faster_whisper import WhisperModel
VW, WAV, MODEL = sys.argv[1:4]
d = json.load(open(VW))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", WAV, "-ac", "1", "-ar", "16000", "/tmp/_al.wav"], check=True)
wf = wave.open("/tmp/_al.wav"); a = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768
m = WhisperModel(MODEL, device="cpu", compute_type="int8")
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower().replace("julatih", "jurulatih").replace("julatis", "jurulatih"))
out = []
for ci, (c0, c1) in enumerate(d["chunks"]):
    caps = [w for w in d["words"] if w["chunk"] == ci]
    seg = a[int(max(0, c0 - 0.05) * 16000):int((c1 + 0.1) * 16000)]
    r, _ = m.transcribe(seg, language="ms", word_timestamps=True, condition_on_previous_text=False, beam_size=5)
    hw = [(w.word.strip(), w.start + c0 - 0.05, w.end + c0 - 0.05) for x in r for w in (x.words or [])]
    A = [norm(w["text"]) for w in caps]; B = [norm(w) for w, _, _ in hw]
    times = [None] * len(caps)
    for blk in difflib.SequenceMatcher(None, A, B, autojunk=False).get_matching_blocks():
        for k in range(blk.size): times[blk.a + k] = (hw[blk.b + k][1], hw[blk.b + k][2])
    # interpolate gaps
    known = [i for i, t in enumerate(times) if t]
    for i in range(len(caps)):
        if times[i]: continue
        prv = max([k for k in known if k < i], default=None); nxt = min([k for k in known if k > i], default=None)
        t0 = times[prv][1] if prv is not None else c0; t1 = times[nxt][0] if nxt is not None else c1
        lo = prv if prv is not None else -1; hi = nxt if nxt is not None else len(caps)
        frac0 = (i - lo) / (hi - lo); frac1 = (i - lo + 1) / (hi - lo)
        times[i] = (t0 + (t1 - t0) * (frac0 - 1 / (hi - lo)) if prv is None else t0 + (t1 - t0) * (frac0 - 1/(hi-lo)) , t0 + (t1 - t0) * frac1)
        times[i] = (max(c0, min(times[i])), max(times[i]))
    for w, (s, e) in zip(caps, times):
        out.append({**w, "start": round(max(c0, s), 3), "end": round(min(c1, max(e, s + 0.08)), 3)})
    print(ci, f"{sum(1 for t in known)}/{len(caps)} matched")
d["words"] = out
json.dump(d, open(VW, "w"), ensure_ascii=False, indent=1)
