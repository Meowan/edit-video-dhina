import sys,subprocess,wave,numpy as np
from faster_whisper import WhisperModel
subprocess.run(["ffmpeg","-v","error","-y","-i",sys.argv[1],"-ac","1","-ar","16000","/tmp/_chk.wav"],check=True)
m=WhisperModel(sys.argv[2],device='cpu',compute_type='int8')
wf=wave.open('/tmp/_chk.wav');a=np.frombuffer(wf.readframes(wf.getnframes()),dtype=np.int16).astype(np.float32)/32768
s,_=m.transcribe(a,language='ms')
for x in s: print(f'{x.start:5.1f}-{x.end:5.1f} {x.text}')
