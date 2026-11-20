import json,glob,re,textwrap,sys
from PIL import Image,ImageDraw,ImageFont
SB=sys.argv[1]
d=json.load(open('video/edl.json')); v=json.load(open('video/assets/audio/voice_words.json'))
words=[(w['start']+0.4,w['end']+0.4,w['text']) for w in v['words']]
frames=sorted(glob.glob(SB+'/frame-*.png'),key=lambda f:int(re.search(r'frame-(\d+)',f)[1]))
shots=d['shots']+[dict(clip='END CARD',start=d['total']-0.25,dur=0,tag='end')]
fb=lambda s:ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',s)
fr=lambda s:ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',s)
TW,TH=300,533; CW=TW+20; CH=TH+175
tagname={'hook':'HOOK','para':'PARALIMPIK','prize':'PENYAMPAIAN','mesra':'MESRA RAKYAT','end':'PENUTUP'}
tagcol={'hook':'#ff4d4d','para':'#ffcc1f','prize':'#7fb2ff','mesra':'#5fe08a','end':'#c08cff'}
def sheet(idx,items,title):
  cols=6; rows=(len(items)+cols-1)//cols
  im=Image.new('RGB',(cols*CW+20,rows*CH+90),'#111318'); dr=ImageDraw.Draw(im)
  dr.text((20,22),title,font=fb(30),fill='white')
  for k,(i,f,s) in enumerate(items):
    x=20+(k%cols)*CW; y=80+(k//cols)*CH
    im.paste(Image.open(f).convert('RGB').resize((TW,TH)),(x,y))
    tg=s.get('tag','end'); dr.rectangle([x,y,x+TW,y+30],fill=tagcol[tg]); dr.text((x+8,y+5),f"#{i+1}  {tagname[tg]}",font=fb(17),fill='#111')
    st=s['start']; en=st+s['dur'] if s['dur'] else d['total']
    dr.text((x,y+TH+6),f"{st:05.2f}–{en:05.2f}s  {s['clip']}",font=fb(16),fill='white')
    vt=' '.join(t for a,b,t in words if a<en and b>st)
    for j,l in enumerate(textwrap.wrap('Suara: '+vt if vt else '(tiada suara)',34)[:6]):
      dr.text((x,y+TH+30+j*22),l,font=fr(16),fill='#c9ccd6')
  im.save(f'draft/storyboard-{idx}.png',optimize=True)
items=[(i,f,shots[i]) for i,f in enumerate(frames)]
sheet(1,items[:18],f'DRAF STORYBOARD (1/2) · Insentif Atlet Pahang · 9:16 · {d["total"]:.0f}s')
sheet(2,items[18:],f'DRAF STORYBOARD (2/2) · Insentif Atlet Pahang · 9:16 · {d["total"]:.0f}s')
