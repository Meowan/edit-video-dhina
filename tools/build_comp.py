"""Generate the HyperFrames project (index.html + sub-compositions) from the edit
decision list below and the cut voice (assets/audio/voice_words.json).

Run from repo root:  python3 tools/build_comp.py video
"""
import json, sys, os, html

PROJ = sys.argv[1]
VOICE = json.load(open(f"{PROJ}/assets/audio/voice_words.json"))
VO = 0.40                       # voice starts 0.4 s in (frame 0 = hook title, no speech yet)
VOICE_END = VO + VOICE["duration"]
TOTAL = round(VOICE_END + 2.8, 2)   # end card tail
W, H = 1080, 1920

def ch(i, edge=0):              # chunk start/end on the film clock
    return round(VOICE["chunks"][i][edge] + VO, 2)

# ---------------------------------------------------------------- shot list
# (clip, film_start, media_start, tag)  - each shot runs until the next one starts.
# tag: hook | mesra | para | prize | end
P = "para"
SHOTS = [
  # HOOK: Dato' mesra dengan atlet + cek gergasi RM809,050
  ("IMG_1277", 0.00, 0.6, "hook"),
  ("IMG_1200", 2.10, 0.8, "hook"),
  # PARA SUKMA highlight (voice: "...insentif kepada atlet-atlet Pahang yang cemerlang di SUKMA dan Para SUKMA")
  ("IMG_1219", 3.90, 2.2, P),      # Loh Chi Hui (kerusi roda) - Asian Para Games
  ("IMG_1220", 6.20, 4.0, P),      # Para Badminton
  ("IMG_1221", 7.60, 6.0, P),      # Para Powerlifting
  ("IMG_1222", 9.00, 2.5, P),      # Para Pingpong
  ("IMG_1223", 10.40, 5.0, P),     # Para Renang
  ("IMG_1225", 11.80, 1.0, P),     # Para Olahraga
  ("IMG_1226", 13.20, 3.0, P),     # Para Tenpin Boling
  ("IMG_1228", 14.60, 17.0, P),    # Para Memanah  (+ YouTube overlay)
  ("IMG_1229", 17.60, 1.5, P),     # Para Boling Padang
  # Hoki & menembak juara keseluruhan
  ("IMG_1257", ch(2), 1.5, "prize"),
  ("IMG_1260", ch(2) + 2.45, 1.0, "prize"),
  ("IMG_1262", ch(2) + 4.90, 2.5, "prize"),
  # RM2,000 -> RM3,000 ; Cheah Zen Hong (+ YouTube overlay)
  ("IMG_1263", ch(3), 22.0, "prize"),
  # Cadangan media sosial - mesra rakyat
  ("IMG_1296", ch(4), 2.0, "mesra"),
  ("IMG_1197", ch(4) + 2.6, 1.0, "mesra"),
  ("IMG_1215a", ch(4) + 5.0, 3.0, "prize"),
  ("IMG_1216", ch(4) + 7.4, 2.5, "prize"),
  # Jurulatih: gaji minimum & pelarasan
  ("IMG_1217", ch(5), 1.5, "prize"),
  ("IMG_1231", ch(5) + 2.5, 0.2, "prize"),
  ("IMG_1232", ch(5) + 4.8, 2.5, "prize"),
  ("IMG_1233", ch(6), 1.0, "prize"),
  ("IMG_1234", ch(6) + 1.6, 5.0, "prize"),
  # Kenaikan RM200 - RM1,200
  ("IMG_1236", ch(7), 1.0, "prize"),
  ("IMG_1238", ch(7) + 2.3, 0.0, "prize"),
  ("IMG_1240", ch(7) + 4.4, 0.2, "prize"),
  ("IMG_1241", ch(7) + 6.6, 0.4, "prize"),
  # Januari 2027 kompetitif
  ("IMG_1242", ch(8), 2.0, "prize"),
  ("IMG_1243", ch(8) + 2.5, 1.0, "prize"),
  ("IMG_1244", ch(8) + 4.9, 0.4, "prize"),
  ("IMG_1245", ch(8) + 7.3, 0.8, "prize"),
  # Pelawa jurulatih
  ("IMG_1246", ch(9), 1.0, "prize"),
  ("IMG_1247", ch(9) + 2.7, 1.5, "prize"),
  ("IMG_1248", ch(9) + 5.3, 0.8, "prize"),
  # Transformasi sukan + end card
  ("IMG_1266", ch(10), 3.0, "end"),
]
DUR = {}
for f in os.listdir(f"{PROJ}/assets/clips"):
    pass
import subprocess
def probe(c):
    return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f"{PROJ}/assets/clips/{c}.mp4"]).decode())

shots = []
for i, (c, s, ms, tag) in enumerate(SHOTS):
    e = SHOTS[i+1][1] if i+1 < len(SHOTS) else TOTAL
    d = round(e - s, 2)
    L = probe(c)
    ms = max(0.0, min(ms, L - d - 0.05))
    if L < d:   # clip shorter than slot: start at 0 and let speed ramp cover it (rare)
        ms = 0.0
    shots.append(dict(clip=c, start=round(s, 2), dur=d, ms=round(ms, 2), tag=tag, srclen=L))

# --------------------------------------------------------------- overlays
PARA_LABELS = {"IMG_1219": "LOH CHI HUI · ASIAN PARA GAMES", "IMG_1220": "PARA BADMINTON", "IMG_1221": "PARA POWERLIFTING",
               "IMG_1222": "PARA PINGPONG", "IMG_1223": "PARA RENANG", "IMG_1225": "PARA OLAHRAGA",
               "IMG_1226": "PARA TENPIN BOLING", "IMG_1228": "PARA MEMANAH", "IMG_1229": "PARA BOLING PADANG"}

YT = [  # YouTube overlays (clips supplied by the client via Drive)
  dict(id="yt-para", over="IMG_1228", src="assets/yt/memanah_para.mp4",
       credit="▶ Para SUKMA · Para Recurve · Pahang vs Sabah"),
  dict(id="yt-cheah", over="IMG_1262", src="assets/yt/cheah_shoot.mp4",
       credit=""),
]

def shot(c): return next(s for s in shots if s["clip"] == c)

# ------------------------------------------------------------------- index
vids = []
for i, s in enumerate(shots):
    vids.append(f'''      <video id="v{i:02d}" class="clip shot" src="assets/clips/{s['clip']}.mp4" data-start="{s['start']}" data-duration="{s['dur']}" data-media-start="{s['ms']}" data-track-index="{i % 2}" muted playsinline></video>''')

kb = []   # gentle push-in on every shot, punchier on hook/para
for i, s in enumerate(shots):
    z0, z1 = (1.42, 1.30) if s["tag"] in ("hook", "para") else (1.26, 1.34)
    if s["clip"] in ("IMG_1277", "IMG_1296", "IMG_1197", "IMG_1266"):
        z0, z1 = (1.08, 1.0) if s["tag"] != "end" else (1.0, 1.08)
    kb.append(f'      tl.fromTo("#v{i:02d}", {{ scale: {z0} }}, {{ scale: {z1}, duration: {s["dur"]}, ease: "{"power3.out" if s["tag"] in ("hook","para") else "none"}" }}, {s["start"]});')

index = f'''<!doctype html>
<html lang="ms">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: {W}px; height: {H}px; overflow: hidden; background: #07080c; }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; }}
      .shot {{ position: absolute; left: 0; top: 0; width: {W}px; height: {H}px; object-fit: cover; transform-origin: 50% 54%; }}
      .host {{ position: absolute; inset: 0; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="{W}" data-height="{H}" data-fps="30">
{chr(10).join(vids)}
      <audio id="voice" class="clip" src="assets/audio/voice_edit.wav" data-start="{VO}" data-duration="{VOICE['duration']}" data-volume="1" data-track-index="3"></audio>
      <audio id="music" class="clip" src="assets/audio/music.wav" data-start="0" data-duration="{TOTAL}" data-volume="1" data-fade-out="1.6" data-track-index="2"
        data-automation='{{"version":1,"lanes":[{{"target":"volume","points":[{{"t":0,"v":0.85}},{{"t":0.45,"v":0.26}},{{"t":{VOICE_END:.2f},"v":0.26}},{{"t":{VOICE_END+0.5:.2f},"v":0.8}}]}}]}}'></audio>
      <div id="gfx" class="clip host" data-composition-id="gfx" data-composition-src="compositions/overlays.html" data-start="0" data-duration="{TOTAL}" data-track-index="4" data-track-kind="graphics"></div>
      <div id="caps" class="clip host" data-composition-id="caps" data-composition-src="compositions/captions.html" data-start="0" data-duration="{TOTAL}" data-track-index="5" data-track-kind="captions"></div>
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
{chr(10).join(kb)}
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
'''
open(f"{PROJ}/index.html", "w").write(index)

# --------------------------------------------------------------- captions
FIX_CASE = {"sukma": "SUKMA", "pahang": "Pahang", "para": "Para"}
words = []
for w in VOICE["words"]:
    t = w["text"]
    low = t.lower()
    t = FIX_CASE.get(low, low)
    words.append(dict(text=t, start=round(w["start"] + VO, 3), end=round(w["end"] + VO, 3), chunk=w["chunk"]))
# money / numbers -> RM
for i, w in enumerate(words):
    if w["text"] in ("2,000", "1,000", "3,000", "2,200", "200", "1,200"):
        w["text"] = "RM" + w["text"]; w["hot"] = True
    if w["text"] in ("2027", "insentif", "para", "jurulatih", "kompetitif", "transformasi", "hoki", "menembak", "keseluruhan"):
        w["hot"] = True
    if w["text"] == "ringgit": w["drop"] = True        # RM already shown
    if w["text"] == "Para": w["hot"] = True
words = [w for w in words if not w.get("drop")]
# capitalise first word of every chunk
seen = set()
for w in words:
    if w["chunk"] not in seen:
        seen.add(w["chunk"]); w["text"] = w["text"][0].upper() + w["text"][1:]

groups, cur = [], []
for i, w in enumerate(words):
    if cur and (w["chunk"] != cur[-1]["chunk"] or len(cur) >= 3 or w["start"] - cur[-1]["end"] > 0.35):
        groups.append(cur); cur = []
    cur.append(w)
groups.append(cur)

cap_html, cap_js = [], []
for gi, g in enumerate(groups):
    gs = round(g[0]["start"] - 0.05, 3)
    nxt = groups[gi+1][0]["start"] - 0.05 if gi + 1 < len(groups) else g[-1]["end"] + 0.4
    ge = round(min(max(g[-1]["end"] + 0.15, gs + 0.5), nxt), 3)
    spans = " ".join(f'<span class="w{" hot" if w.get("hot") else ""}" id="g{gi}w{k}">{html.escape(w["text"])}</span>' for k, w in enumerate(g))
    cap_html.append(f'        <div class="grp" id="g{gi}">{spans}</div>')
    cap_js.append(f'        tl.set("#g{gi}", {{ opacity: 1, visibility: "visible" }}, {gs});')
    cap_js.append(f'        tl.fromTo("#g{gi}", {{ y: 18, scale: 0.94 }}, {{ y: 0, scale: 1, duration: 0.16, ease: "back.out(2)" }}, {gs});')
    for k, w in enumerate(g):
        cap_js.append(f'        tl.fromTo("#g{gi}w{k}", {{ opacity: 0, scale: 0.7 }}, {{ opacity: 1, scale: 1, duration: 0.1, ease: "back.out(2.5)" }}, {max(gs, w["start"]-0.03):.3f});')
    cap_js.append(f'        tl.set("#g{gi}", {{ opacity: 0, visibility: "hidden" }}, {ge});')

captions = f'''<!doctype html>
<html lang="ms">
  <body>
    <template>
      <style>
        #root {{ position: absolute; inset: 0; width: {W}px; height: {H}px; pointer-events: none; }}
        .grp {{ position: absolute; left: 0; width: {W}px; top: 1300px; text-align: center; opacity: 0; visibility: hidden;
               font-family: "Montserrat"; font-weight: 900; font-size: 74px; line-height: 1.08; letter-spacing: -0.01em;
               color: #ffffff; padding: 0 110px; overflow: visible;
               text-shadow: 0 4px 0 rgba(0,0,0,.85), 0 0 24px rgba(0,0,0,.75); -webkit-text-stroke: 3px #000; paint-order: stroke fill; }}
        .w {{ display: inline-block; margin: 0 6px; }}
        .hot {{ color: #ffcc1f; }}
      </style>
      <div id="root" data-composition-id="caps" data-width="{W}" data-height="{H}" data-layout-allow-overflow>
{chr(10).join(cap_html)}
      </div>
      <script>
        const tl = gsap.timeline({{ paused: true }});
{chr(10).join(cap_js)}
        window.__timelines = window.__timelines || {{}};
        window.__timelines["caps"] = tl;
      </script>
    </template>
  </body>
</html>
'''
os.makedirs(f"{PROJ}/compositions", exist_ok=True)
open(f"{PROJ}/compositions/captions.html", "w").write(captions)

# --------------------------------------------------------------- overlays
o_html, o_js = [], []
def chip(id_, text, s, e, cls="chip"):
    o_html.append(f'        <div class="{cls}" id="{id_}"><span>{html.escape(text)}</span></div>')
    o_js.append(f'        tl.set("#{id_}", {{ visibility: "visible" }}, {s:.2f});')
    o_js.append(f'        tl.fromTo("#{id_}", {{ opacity: 0, x: -40 }}, {{ opacity: 1, x: 0, duration: 0.3, ease: "power3.out" }}, {s:.2f});')
    o_js.append(f'        tl.to("#{id_}", {{ opacity: 0, duration: 0.15, ease: "power2.in" }}, {e-0.15:.2f});')
    o_js.append(f'        tl.set("#{id_}", {{ visibility: "hidden" }}, {e:.2f});')

# HOOK title (frame 0 already on screen)
h1 = shot("IMG_1200")
o_html.append('''        <div id="scrim"></div>
        <div id="hook">
          <div id="hook-kicker">INSENTIF KECEMERLANGAN ATLET PAHANG</div>
          <div id="hook-big">RM<span id="hook-num">809,050</span></div>
          <div id="hook-sub">untuk jaguh sukan &amp; para atlet Pahang</div>
        </div>''')
o_js.append('        tl.set(["#hook", "#scrim"], { visibility: "visible" }, 0);')
o_js.append(f'        tl.to("#scrim", {{ opacity: 0, duration: 0.25 }}, {shot("IMG_1219")["start"]-0.25:.2f});')
o_js.append(f'        tl.set("#scrim", {{ visibility: "hidden" }}, {shot("IMG_1219")["start"]:.2f});')
o_js.append('        tl.fromTo("#hook-big", { scale: 1.6, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.35, ease: "expo.out" }, 0);')
o_js.append('        tl.fromTo("#hook-kicker", { y: -30, opacity: 0 }, { y: 0, opacity: 1, duration: 0.3, ease: "power3.out" }, 0.1);')
o_js.append('        tl.fromTo("#hook-sub", { y: 30, opacity: 0 }, { y: 0, opacity: 1, duration: 0.3, ease: "power3.out" }, 0.25);')
o_js.append('        tl.to("#hook-big", { scale: 1.06, duration: 1.6, ease: "sine.inOut" }, 2.1);')
o_js.append(f'        tl.to("#hook", {{ opacity: 0, y: -40, duration: 0.25, ease: "power2.in" }}, {shot("IMG_1219")["start"]-0.25:.2f});')
o_js.append(f'        tl.set("#hook", {{ visibility: "hidden" }}, {shot("IMG_1219")["start"]:.2f});')

# PARA badge for the whole para block
pb_s, pb_e = shot("IMG_1219")["start"], shot("IMG_1257")["start"]
o_html.append('        <div id="para-badge"><span class="pill"><span class="dot"></span>HIGHLIGHT · ATLET PARALIMPIK</span></div>')
o_html.append('        <div id="para-frame"></div>')
o_js.append(f'        tl.set(["#para-badge", "#para-frame"], {{ visibility: "visible" }}, {pb_s:.2f});')
o_js.append(f'        tl.fromTo("#para-badge", {{ opacity: 0, y: -30 }}, {{ opacity: 1, y: 0, duration: 0.3, ease: "back.out(2)" }}, {pb_s:.2f});')
o_js.append(f'        tl.fromTo("#para-frame", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, {pb_s:.2f});')
o_js.append(f'        tl.to(["#para-badge", "#para-frame"], {{ opacity: 0, duration: 0.2 }}, {pb_e-0.2:.2f});')
o_js.append(f'        tl.set(["#para-badge", "#para-frame"], {{ visibility: "hidden" }}, {pb_e:.2f});')
for c, lab in PARA_LABELS.items():
    s = shot(c); chip(f"pl-{c[4:]}", lab, s["start"] + 0.05, s["start"] + s["dur"] - 0.02, "chip para")

# Stat callouts
def stat(id_, top, big, sub, s, e):
    o_html.append(f'        <div class="stat" id="{id_}"><div class="stat-top">{top}</div><div class="stat-big">{big}</div><div class="stat-sub">{sub}</div></div>')
    o_js.append(f'        tl.set("#{id_}", {{ visibility: "visible" }}, {s:.2f});')
    o_js.append(f'        tl.fromTo("#{id_}", {{ opacity: 0, scale: 0.8 }}, {{ opacity: 1, scale: 1, duration: 0.35, ease: "back.out(1.8)" }}, {s:.2f});')
    o_js.append(f'        tl.to("#{id_}", {{ opacity: 0, duration: 0.2, ease: "power2.in" }}, {e-0.2:.2f});')
    o_js.append(f'        tl.set("#{id_}", {{ visibility: "hidden" }}, {e:.2f});')

stat("st-hoki", "HOKI &amp; MENEMBAK", "JUARA", "keseluruhan SUKMA 2026", ch(2) + 2.5, shot("IMG_1262")["start"] + 0.25)
stat("st-3k", "INSENTIF SETIAP ATLET", "RM2,000 → <b>RM3,000</b>", "hoki &amp; menembak", ch(3) + 2.45, ch(4) - 0.05)
chip("ch-sosial", "CADANGAN ATLET DI MEDIA SOSIAL — DILAKSANAKAN", ch(4) + 0.2, ch(5) - 0.1, "chip gold")
stat("st-gaji", "GAJI MINIMUM JURULATIH SEPENUH MASA", "RM2,200", "pelarasan gaji mulai Januari 2027", ch(5) + 3.0, ch(7) - 0.05)
stat("st-naik", "KENAIKAN GAJI JURULATIH", "+RM200 – RM1,200", "untuk 43 jurulatih sepenuh masa", ch(7) + 4.0, ch(8) - 0.05)
stat("st-komp", "MULAI JANUARI 2027", "KOMPETITIF", "lebih tinggi berbanding negeri lain", ch(8) + 5.0, ch(9) - 0.05)
chip("ch-pelawa", "JURULATIH BERKELAYAKAN? CARI REZEKI DI PAHANG", ch(9) + 0.3, ch(10) - 0.1, "chip gold")

# YouTube overlays (picture-in-picture over the ceremony shot)
def yt_window(y):
    if y["id"] == "yt-cheah":
        st = shot("IMG_1262")["start"] + 0.3
        return st, st + 4.8
    s_ = shot(y["over"]); return s_["start"] + 0.2, s_["start"] + s_["dur"] - 0.05
for y in YT:
    ys, ye = yt_window(y)
    o_html.append(f'''        <div class="yt" id="{y['id']}">
          <video id="{y['id']}-v" class="clip yt-img" src="{y['src']}" data-start="{ys:.2f}" data-duration="{ye-ys:.2f}" data-media-start="0" muted playsinline></video>
          {'<div class="yt-cred">' + html.escape(y['credit']) + '</div>' if y['credit'] else ''}
        </div>''')
    o_js.append(f'        tl.set("#{y["id"]}", {{ visibility: "visible" }}, {ys:.2f});')
    o_js.append(f'        tl.fromTo("#{y["id"]}", {{ opacity: 0, y: -60, rotation: -2 }}, {{ opacity: 1, y: 0, rotation: 0, duration: 0.4, ease: "back.out(1.6)" }}, {ys:.2f});')
    o_js.append(f'        tl.to("#{y["id"]}", {{ opacity: 0, y: -40, duration: 0.2, ease: "power2.in" }}, {ye-0.2:.2f});')
    o_js.append(f'        tl.set("#{y["id"]}", {{ visibility: "hidden" }}, {ye:.2f});')
cs, ce = yt_window(YT[1])
chip("ch-cheah", "CHEAH ZEN HONG · PECAH REKOD SUKMA", cs, ce, "chip para")

# End card
es = round(VOICE_END + 0.1, 2)
o_html.append('''        <div id="end">
          <div id="end-kicker">INSENTIF KECEMERLANGAN ATLET PAHANG</div>
          <div id="end-big">RM809,050</div>
          <div id="end-sub">Atlet dihargai · Jurulatih diperkasa</div>
        </div>''')
o_js.append(f'        tl.set("#end", {{ visibility: "visible" }}, {es:.2f});')
o_js.append(f'        tl.fromTo("#end", {{ opacity: 0, y: 40 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: "power3.out" }}, {es:.2f});')

overlays = f'''<!doctype html>
<html lang="ms">
  <body>
    <template>
      <style>
        #root {{ position: absolute; inset: 0; width: {W}px; height: {H}px; pointer-events: none; font-family: "Montserrat"; }}
        #scrim {{ position: absolute; left: 0; top: 0; width: {W}px; height: 1100px; background: linear-gradient(rgba(0,0,0,.72) 0%, rgba(0,0,0,.55) 55%, rgba(0,0,0,0) 100%); }}
        #scrim, #hook, #para-badge, #para-frame, .chip, .stat, .yt, #end {{ visibility: hidden; }}
        #hook {{ position: absolute; left: 0; width: {W}px; top: 330px; text-align: center; color: #fff; }}
        #hook-kicker {{ display: inline-block; font-weight: 800; font-size: 34px; letter-spacing: .08em; background: #ffcc1f; color: #111; padding: 10px 22px; border-radius: 8px; }}
        #hook-big {{ font-weight: 900; font-size: 168px; line-height: 1; margin-top: 18px; color: #ffcc1f; letter-spacing: -0.03em;
                     -webkit-text-stroke: 4px #111; paint-order: stroke fill; text-shadow: 0 10px 0 rgba(0,0,0,.6), 0 0 50px rgba(0,0,0,.6); }}
        #hook-sub {{ font-weight: 800; font-size: 54px; margin-top: 16px; padding: 0 90px; line-height: 1.12; text-shadow: 0 4px 16px rgba(0,0,0,.9); -webkit-text-stroke: 2px #000; paint-order: stroke fill; }}
        #para-frame {{ position: absolute; inset: 0; border: 14px solid #ffcc1f; box-shadow: inset 0 0 90px rgba(255,204,31,.45); }}
        #para-badge {{ position: absolute; left: 0; width: {W}px; top: 300px; text-align: center; }}
        #para-badge .pill {{ display: inline-block; font-weight: 900; font-size: 38px; letter-spacing: .05em; color: #fff; background: #e21d2c; padding: 10px 24px; border-radius: 40px; }}
        #para-badge .dot {{ display: inline-block; width: 16px; height: 16px; border-radius: 50%; background: #fff; margin-right: 12px; vertical-align: middle; }}
        .chip {{ position: absolute; left: 0; width: {W}px; top: 392px; text-align: center; }}
        .chip span {{ display: inline-block; font-weight: 800; font-size: 40px; letter-spacing: .02em; color: #fff; background: rgba(10,12,20,.82); padding: 12px 26px; border-radius: 10px; border-left: 8px solid #ffcc1f; }}
        .chip.para span {{ background: #ffcc1f; color: #111; border-left-color: #e21d2c; }}
        .chip.gold {{ top: 330px; }}
        .chip.gold span {{ background: rgba(10,12,20,.86); font-size: 36px; max-width: 900px; }}
        .stat {{ position: absolute; left: 90px; width: 900px; top: 300px; text-align: center; background: rgba(8,10,18,.84); border: 3px solid #ffcc1f; border-radius: 22px; padding: 26px 24px 30px; color: #fff; }}
        .stat-top {{ font-weight: 800; font-size: 32px; letter-spacing: .06em; color: #ffcc1f; }}
        .stat-big {{ font-weight: 900; font-size: 104px; line-height: 1.05; margin-top: 8px; letter-spacing: -0.02em; }}
        .stat-big b {{ color: #ffcc1f; }}
        .stat-sub {{ font-weight: 600; font-size: 34px; margin-top: 8px; color: #e8e8ee; }}
        .yt {{ position: absolute; left: 70px; width: 940px; top: 470px; height: 529px; border-radius: 22px; overflow: hidden; border: 5px solid #fff; box-shadow: 0 24px 60px rgba(0,0,0,.6); background: #000; }}
        .yt-img {{ position: absolute; left: 0; top: 0; width: 100%; height: 100%; object-fit: cover; }}
        .yt-ph {{ position: absolute; left: 0; top: 0; width: 100%; padding: 10px; text-align: center; font-weight: 800; font-size: 30px; color: #111; background: rgba(255,204,31,.92); }}
        .yt-cred {{ position: absolute; left: 0; bottom: 0; width: 100%; padding: 12px 18px; font-weight: 800; font-size: 32px; color: #fff; background: linear-gradient(transparent, rgba(0,0,0,.85)); }}
        #end {{ position: absolute; left: 0; width: {W}px; top: 560px; text-align: center; color: #fff; padding: 0 80px; }}
        #end-kicker {{ font-weight: 800; font-size: 30px; letter-spacing: .06em; color: #ffcc1f; }}
        #end-big {{ font-weight: 900; font-size: 150px; line-height: 1.05; margin-top: 10px; -webkit-text-stroke: 4px #111; paint-order: stroke fill; text-shadow: 0 10px 30px rgba(0,0,0,.8); }}
        #end-sub {{ font-weight: 700; font-size: 40px; margin-top: 20px; line-height: 1.25; text-shadow: 0 4px 16px rgba(0,0,0,.9); }}
      </style>
      <div id="root" data-composition-id="gfx" data-width="{W}" data-height="{H}" data-layout-allow-overflow data-layout-allow-overlap>
{chr(10).join(o_html)}
      </div>
      <script>
        const tl = gsap.timeline({{ paused: true }});
{chr(10).join(o_js)}
        window.__timelines = window.__timelines || {{}};
        window.__timelines["gfx"] = tl;
      </script>
    </template>
  </body>
</html>
'''
open(f"{PROJ}/compositions/overlays.html", "w").write(overlays)
json.dump(dict(total=TOTAL, shots=shots, groups=[[w["text"] for w in g] for g in groups]), open(f"{PROJ}/edl.json", "w"), ensure_ascii=False, indent=1)
print("TOTAL", TOTAL, "shots", len(shots))
for s in shots: print(f'{s["start"]:6.2f} +{s["dur"]:5.2f}  {s["clip"]:10s} ms={s["ms"]:5.2f}/{s["srclen"]:.1f}  {s["tag"]}')
