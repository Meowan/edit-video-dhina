"""Locate disfluencies (err / emm / hmm / eh / aa) inside kept voice spans.
Whisper normally drops them, so we prompt it with fillers to make it write them out.
Usage: python3 tools/find_fillers.py voice16k.wav model_dir spans.json > fillers.json
"""
import sys, json, re, wave, numpy as np
from faster_whisper import WhisperModel
wav, model, spans_f = sys.argv[1:4]
m = WhisperModel(model, device="cpu", compute_type="int8")
wf = wave.open(wav); a = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768
spans = json.load(open(spans_f))
FILL = re.compile(r"^(e+r+m*|e+m+|h+m+|m+|e+h*|a+h*|u+h*m*|uh|um|erm|er|hmm|emm|aa+|ee+)$", re.I)
PROMPT = "Err, saya, emm, nak, hmm, cakap, eh, bahawa, aa, kita, umm, akan."
out = []
for s, e in spans:
    seg = a[int((s - 0.1) * 16000):int((e + 0.1) * 16000)]
    r, _ = m.transcribe(seg, language="ms", word_timestamps=True, initial_prompt=PROMPT, beam_size=5,
                        condition_on_previous_text=False, vad_filter=False)
    words = [(w.word.strip(), w.start + s - 0.1, w.end + s - 0.1) for x in r for w in (x.words or [])]
    txt = " ".join(w for w, _, _ in words)
    fl = [(w, round(ws, 2), round(we, 2)) for w, ws, we in words if FILL.match(re.sub(r"[^\w]", "", w))]
    out.append({"span": [s, e], "text": txt, "fillers": fl})
    print(f"[{s:.2f}-{e:.2f}] {txt}  FILLERS={fl}", file=sys.stderr)
json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
