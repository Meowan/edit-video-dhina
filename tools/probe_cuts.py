import wave,numpy as np,sys
from faster_whisper import WhisperModel
m=WhisperModel(sys.argv[2],device='cpu',compute_type='int8')
wf=wave.open(sys.argv[1]);a=np.frombuffer(wf.readframes(wf.getnframes()),dtype=np.int16).astype(np.float32)/32768
def first(s,e):
  r,_=m.transcribe(a[int(s*16000):int(e*16000)],language='ms',beam_size=3,condition_on_previous_text=False,vad_filter=False)
  return ' '.join(x.text.strip() for x in r)
for s0,s1,dur in [(285.2,285.9,1.6),(289.9,290.4,1.4),(323.9,324.4,1.6),(327.6,328.7,1.8),(442.9,443.6,1.8),(496.9,498.2,2.0),(154.2,154.6,1.4)]:
  for s in np.arange(s0,s1+1e-6,0.1):
    print(f'{s:.2f}: {first(s,s+dur)}')
  print()
