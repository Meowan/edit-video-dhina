"""v2 edit (after client feedback, modelled on ref1):
hook "TRANSFORMASI" -> cartoon card -> SUKMA/Para SUKMA -> 3 numbered points with
whoosh + point cards; stage clips compacted into triptychs and interleaved with
hall / photo-session shots; cartoon outro.

Run from repo root:  python3 tools/build_comp2.py video
"""
import json, sys, os, html, subprocess

PROJ = sys.argv[1]
V = json.load(open(f"{PROJ}/assets/audio/voice_words.json"))
VO = 0.30
W, H = 1080, 1920
def ch(i, e=0): return round(V["chunks"][i][e] + VO, 2)
VOICE_END = round(VO + V["duration"], 2)

CARTOON_IN = ch(0, 1)            # cartoon right after the hook line
P1, P2, P3 = ch(1, 1), ch(3, 1), ch(7, 1)   # point cards start in the gaps
OUTRO = round(VOICE_END + 0.09, 2)
CART_LEN = 2.75
TOTAL = round(OUTRO + CART_LEN, 2)

C = "assets/clips/"; T = "assets/trip/"
# (start, src, media_start, kind)  kind: single | trip | cartoon | wide
SHOTS = [
  (0.00, C+"IMG_1277", 0.6, "single"),        # watak utama: Dato' bersalam dgn atlet
  (2.40, C+"IMG_1164", 0.5, "wide"),          # backdrop majlis
  (CARTOON_IN, "assets/fx/cartoon", 0.0, "cartoon"),
  (CARTOON_IN + CART_LEN, C+"IMG_1266", 3.0, "wide"),   # dewan penuh
  (9.40, C+"IMG_1219", 2.2, "single"),        # PARA: Loh Chi Hui
  (11.40, T+"t_para1", 0.0, "trip"),          # para badminton / powerlifting / pingpong
  (13.60, T+"t_g", 0.0, "trip"),              # para renang / tenpin / boling padang
  (15.60, C+"IMG_1228", 17.0, "single"),      # para memanah (+ YT)
  # POINT 1
  (P1, C+"IMG_1257", 1.5, "single"),          # hoki lelaki
  (P1 + 2.30, C+"IMG_1296", 2.0, "wide"),     # sesi bergambar
  (P1 + 4.30, C+"IMG_1260", 1.0, "single"),   # hoki wanita
  (P1 + 6.10, C+"IMG_1262", 2.5, "single"),   # menembak (+ YT Cheah)
  (P1 + 9.60, C+"IMG_1263", 22.0, "single"),  # Cheah Zen Hong
  # POINT 2
  (P2, C+"IMG_1197", 0.5, "wide"),
  (P2 + 2.20, T+"t_a", 0.0, "trip"),
  (P2 + 4.60, C+"IMG_1266", 9.0, "wide"),
  (P2 + 7.46, T+"t_b", 0.0, "trip"),
  (P2 + 9.86, C+"IMG_1296", 6.5, "wide"),
  (P2 + 11.96, T+"t_c", 0.0, "trip"),
  (P2 + 14.46, C+"IMG_1197", 3.8, "wide"),
  (P2 + 17.00, T+"t_d", 0.0, "trip"),
  (P2 + 19.50, C+"IMG_1266", 13.0, "wide"),
  (P2 + 21.80, T+"t_e", 0.0, "trip"),
  (P2 + 24.30, C+"IMG_1200", 0.8, "single"),
  (P2 + 27.21, T+"t_f", 0.0, "trip"),
  (P2 + 29.81, C+"IMG_1296", 9.0, "wide"),
  (P2 + 31.81, C+"IMG_1164", 2.5, "wide"),
  # POINT 3
  (P3, C+"IMG_1225", 1.0, "single"),          # olahraga
  (ch(9), C+"IMG_1266", 6.0, "wide"),         # silat
  (ch(10), C+"IMG_1221", 6.0, "single"),      # angkat berat
  (ch(11), C+"IMG_1266", 14.5, "wide"),       # pahang pernah jaguh
  (ch(11) + 3.6, C+"IMG_1262", 4.9, "single"),
  (ch(12) - 0.22, C+"IMG_1263", 15.0, "single"),  # kegemilangan (sparks)
  (OUTRO, "assets/fx/cartoon", 0.0, "cartoon"),
]

def probe(p):
    return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f"{PROJ}/{p}.mp4"]).decode())
shots = []
for i, (s, src, ms, kind) in enumerate(SHOTS):
    e = SHOTS[i+1][0] if i+1 < len(SHOTS) else TOTAL
    d = round(e - s, 2); L = probe(src)
    ms = max(0.0, min(ms, L - d - 0.03))
    shots.append(dict(src=src, start=round(s, 2), dur=d, ms=round(ms, 2), kind=kind, L=L))
def shot_at(t): return next(s for s in shots if s["start"] <= t < s["start"] + s["dur"])

# ------------------------------------------------------------------ audio
SFX = []   # (id, file, start, volume)
def whoosh(cut, vol=0.55): SFX.append((f"wh{len(SFX)}", "assets/sfx/whoosh.wav", round(cut - 0.5, 2), vol))
def impact(t, vol=0.5): SFX.append((f"im{len(SFX)}", "assets/sfx/impact.wav", round(t, 2), vol))
whoosh(CARTOON_IN); impact(CARTOON_IN, 0.35); whoosh(CARTOON_IN + CART_LEN, 0.45)
for p in (P1, P2, P3): whoosh(p); impact(p + 0.05, 0.45)
whoosh(9.40, 0.3); whoosh(OUTRO); impact(OUTRO, 0.4)
duck = [(0, .8), (VO, .26), (CARTOON_IN - .1, .26), (CARTOON_IN + .05, .9), (CARTOON_IN + CART_LEN - .2, .9), (ch(1) - .05, .26)]
for p in (P1, P2, P3): duck += [(p, .26), (p + .15, .45), (p + .55, .26)]
duck += [(VOICE_END, .26), (OUTRO + .1, .9)]
duck.sort()
lane = json.dumps({"version": 1, "lanes": [{"target": "volume", "points": [{"t": round(a, 2), "v": b} for a, b in duck]}]})

# ------------------------------------------------------------------ index
vids, kb = [], []
for i, s in enumerate(shots):
    vids.append(f'      <video id="v{i:02d}" class="clip shot" src="{s["src"]}.mp4" data-start="{s["start"]}" data-duration="{s["dur"]}" data-media-start="{s["ms"]}" data-track-index="{i % 2}" muted playsinline></video>')
    z = {"single": (1.36, 1.26), "trip": (1.0, 1.05), "cartoon": (1.0, 1.0), "wide": (1.0, 1.1)}[s["kind"]]
    if i == 0: z = (1.12, 1.0)
    if s["kind"] != "cartoon":
        kb.append(f'      tl.fromTo("#v{i:02d}", {{ scale: {z[0]} }}, {{ scale: {z[1]}, duration: {s["dur"]}, ease: "{"power3.out" if s["kind"]=="single" else "none"}" }}, {s["start"]});')
auds = [f'      <audio id="voice" class="clip" src="assets/audio/voice_edit.wav" data-start="{VO}" data-duration="{V["duration"]}" data-volume="1" data-track-index="3"></audio>',
        f'      <audio id="music" class="clip" src="assets/audio/music.wav" data-start="0" data-duration="{TOTAL}" data-volume="1" data-fade-out="1.2" data-track-index="2"\n        data-automation=\'{lane}\'></audio>']
for k, (id_, f, st, vol) in enumerate(SFX):
    auds.append(f'      <audio id="{id_}" class="clip" src="{f}" data-start="{st}" data-duration="0.75" data-volume="{vol}" data-track-index="{6 + k % 2}"></audio>')

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
{chr(10).join(auds)}
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
words = []
for w in V["words"]:
    t = w["text"]; low = t.lower()
    t = {"sukma": "SUKMA", "para": "Para"}.get(low, low).replace("pahang", "Pahang")
    words.append(dict(text=t, start=round(w["start"] + VO, 3), end=round(w["end"] + VO, 3), chunk=w["chunk"]))
HOT = {"insentif", "para", "jurulatih", "kompetitif", "transformasi", "hoki", "menembak", "keseluruhan", "2027",
       "olahraga", "silat", "angkat", "berat", "jaguh", "kegemilangan", "SUKMA"}
for w in words:
    if w["text"] in ("2,000", "1,000", "3,000", "2,200", "200", "1,200"): w["text"] = "RM" + w["text"]; w["hot"] = True
    if w["text"] in HOT or w["text"].lower() in HOT: w["hot"] = True
    if w["text"] == "ringgit": w["drop"] = True
words = [w for w in words if not w.get("drop")]
seen = set()
for w in words:
    if w["chunk"] not in seen: seen.add(w["chunk"]); w["text"] = w["text"][0].upper() + w["text"][1:]
groups, cur = [], []
for w in words:
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
oh, oj = [], []
def show(id_, s, e, frm="{ opacity: 0, y: -30 }", to="{ opacity: 1, y: 0, duration: 0.3, ease: \"power3.out\" }"):
    oj.append(f'        tl.set("#{id_}", {{ visibility: "visible" }}, {s:.2f});')
    oj.append(f'        tl.fromTo("#{id_}", {frm}, {to}, {s:.2f});')
    oj.append(f'        tl.to("#{id_}", {{ opacity: 0, duration: 0.15, ease: "power2.in" }}, {e-0.15:.2f});')
    oj.append(f'        tl.set("#{id_}", {{ visibility: "hidden" }}, {e:.2f});')
def chip(id_, text, s, e, cls="chip"):
    oh.append(f'        <div class="{cls}" id="{id_}"><span>{html.escape(text)}</span></div>')
    show(id_, s, e, "{ opacity: 0, x: -40 }", '{ opacity: 1, x: 0, duration: 0.3, ease: "power3.out" }')
def stat(id_, top, big, sub, s, e):
    oh.append(f'        <div class="stat" id="{id_}"><div class="stat-top">{top}</div><div class="stat-big">{big}</div><div class="stat-sub">{sub}</div></div>')
    show(id_, s, e, "{ opacity: 0, scale: 0.8 }", '{ opacity: 1, scale: 1, duration: 0.35, ease: "back.out(1.8)" }')
def bigword(id_, text, s, e, cls="big"):
    oh.append(f'        <div class="{cls}" id="{id_}"><span>{html.escape(text)}</span></div>')
    show(id_, s, e, "{ opacity: 0, scale: 1.8 }", '{ opacity: 1, scale: 1, duration: 0.28, ease: "expo.out" }')

# HOOK - TRANSFORMASI (on screen from frame 0)
letters = "".join(f'<span class="L" id="hl{i}">{c}</span>' for i, c in enumerate("TRANSFORMASI"))
oh.append(f'''        <div id="scrim"></div>
        <div id="hook">
          <div id="hook-kicker">MULAI JANUARI 2027</div>
          <div id="hook-big">{letters}</div>
          <div id="hook-sub">SUKAN PAHANG</div>
        </div>''')
oj.append('        tl.set(["#hook", "#scrim"], { visibility: "visible" }, 0);')
oj.append('        tl.fromTo(".L", { opacity: 0, y: 60, scale: 1.4 }, { opacity: 1, y: 0, scale: 1, duration: 0.2, stagger: 0.02, ease: "back.out(2)" }, 0);')
oj.append('        tl.fromTo("#hook-kicker", { opacity: 0, y: -24 }, { opacity: 1, y: 0, duration: 0.3, ease: "power3.out" }, 0.25);')
oj.append('        tl.fromTo("#hook-sub", { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.35, ease: "back.out(2.2)" }, 0.5);')
oj.append('        tl.to("#hook-big", { scale: 1.07, duration: 3.8, ease: "sine.inOut" }, 0.6);')
oj.append(f'        tl.to(["#hook", "#scrim"], {{ opacity: 0, duration: 0.2, ease: "power2.in" }}, {CARTOON_IN-0.2:.2f});')
oj.append(f'        tl.set(["#hook", "#scrim"], {{ visibility: "hidden" }}, {CARTOON_IN:.2f});')

# SUKMA intro label + Para highlight
chip("ch-majlis", "MAJLIS INSENTIF ATLET PAHANG 2026", CARTOON_IN + CART_LEN + 0.1, 9.38)
oh.append('        <div id="para-badge"><span class="pill"><span class="dot"></span>HIGHLIGHT · ATLET PARALIMPIK</span></div>')
oh.append('        <div id="para-frame"></div>')
show("para-badge", 9.40, P1, "{ opacity: 0, y: -30 }", '{ opacity: 1, y: 0, duration: 0.3, ease: "back.out(2)" }')
show("para-frame", 9.40, P1, "{ opacity: 0 }", "{ opacity: 1, duration: 0.3 }")
chip("pl-1219", "LOH CHI HUI · ASIAN PARA GAMES", 9.45, 11.38, "chip para")
chip("pl-1228", "PARA MEMANAH", 15.65, P1 - 0.02, "chip para")

# Point cards: big slam then a persistent top chip
POINTS = [(P1, "01", "INSENTIF ATLET NAIK RM1,000", "Hoki &amp; menembak", P2),
          (P2, "02", "GAJI BAHARU JURULATIH", "Mulai Januari 2027 · kompetitif", P3),
          (P3, "03", "TAMBAH JURULATIH", "Olahraga · Silat · Angkat berat", OUTRO)]
for k, (s, num, title, sub, nxt) in enumerate(POINTS):
    oh.append(f'''        <div class="pcard" id="pc{k}"><div class="pc-num">{num}</div><div class="pc-title">{title}</div><div class="pc-sub">{sub}</div></div>
        <div class="pchip" id="pp{k}"><span class="pn">{num}</span><span class="pt">{title}</span></div>''')
    oj.append(f'        tl.set("#pc{k}", {{ visibility: "visible" }}, {s:.2f});')
    oj.append(f'        tl.fromTo("#pc{k}", {{ opacity: 0, scaleX: 0.2 }}, {{ opacity: 1, scaleX: 1, duration: 0.22, ease: "expo.out" }}, {s:.2f});')
    oj.append(f'        tl.fromTo("#pc{k} .pc-num", {{ scale: 2.4, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "back.out(2.2)" }}, {s+0.05:.2f});')
    oj.append(f'        tl.fromTo("#pc{k} .pc-title", {{ x: 80, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.28, ease: "power3.out" }}, {s+0.12:.2f});')
    oj.append(f'        tl.fromTo("#pc{k} .pc-sub", {{ x: 80, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.28, ease: "power3.out" }}, {s+0.2:.2f});')
    oj.append(f'        tl.to("#pc{k}", {{ opacity: 0, y: -520, scale: 0.5, duration: 0.3, ease: "power2.in" }}, {s+1.5:.2f});')
    oj.append(f'        tl.set("#pc{k}", {{ visibility: "hidden" }}, {s+1.8:.2f});')
    show(f"pp{k}", s + 1.7, nxt - 0.05, "{ opacity: 0, y: -20 }", '{ opacity: 1, y: 0, duration: 0.25, ease: "power3.out" }')

# POINT 1 content
stat("st-hoki", "HOKI &amp; MENEMBAK", "JUARA", "keseluruhan SUKMA 2026", ch(2) + 1.2, P1 + 6.05)
cs, ce = P1 + 6.2, P1 + 9.55
oh.append(f'''        <div class="yt" id="yt-cheah">
          <video id="yt-cheah-v" class="clip yt-img" src="assets/yt/cheah_shoot.mp4" data-start="{cs:.2f}" data-duration="{ce-cs:.2f}" data-media-start="0" muted playsinline></video>
        </div>''')
show("yt-cheah", cs, ce, "{ opacity: 0, y: -60, rotation: -2 }", '{ opacity: 1, y: 0, rotation: 0, duration: 0.4, ease: "back.out(1.6)" }')
chip("ch-cheah", "CHEAH ZEN HONG · PECAH REKOD SUKMA", cs, ce, "chip para")
stat("st-3k", "INSENTIF SETIAP ATLET", "RM2,000 → <b>RM3,000</b>", "hoki &amp; menembak", ch(3) + 1.5, P2 - 0.05)
# para memanah YT
ms_, me_ = 15.75, P1 - 0.05
oh.append(f'''        <div class="yt" id="yt-para">
          <video id="yt-para-v" class="clip yt-img" src="assets/yt/memanah_para.mp4" data-start="{ms_:.2f}" data-duration="{me_-ms_:.2f}" data-media-start="0" muted playsinline></video>
          <div class="yt-cred">▶ Para SUKMA · Para Recurve · Pahang vs Sabah</div>
        </div>''')
show("yt-para", ms_, me_, "{ opacity: 0, y: -60, rotation: -2 }", '{ opacity: 1, y: 0, rotation: 0, duration: 0.4, ease: "back.out(1.6)" }')

# POINT 2 content
stat("st-gaji", "GAJI MINIMUM JURULATIH SEPENUH MASA", "RM2,200", "Pahang · melebihi kadar persekutuan", ch(4) + 3.4, ch(4, 1) + 0.2)
stat("st-naik", "PELARASAN GAJI BAHARU", "+RM200 – RM1,200", "untuk jurulatih sepenuh masa", ch(5) + 4.0, ch(5, 1) + 0.2)
stat("st-komp", "MULAI JANUARI 2027", "KOMPETITIF", "lebih tinggi berbanding negeri lain", ch(6) + 4.8, ch(6, 1) + 0.2)
chip("ch-pelawa", "JURULATIH BERKELAYAKAN? CARI REZEKI DI PAHANG", ch(7) + 0.3, P3 - 0.05, "chip gold")

# POINT 3 content: big sport words, then "pernah jaguh", then kegemilangan
bigword("bw-ola", "OLAHRAGA", ch(8) + 0.6, ch(9) - 0.02)
bigword("bw-sil", "SILAT", ch(9), ch(10) - 0.02)
bigword("bw-ang", "ANGKAT BERAT", ch(10), ch(11) - 0.02)
oh.append('''        <div id="jaguh"><div class="jg-list"><span>OLAHRAGA</span><span>SILAT</span><span>ANGKAT BERAT</span></div><div class="jg-big">PAHANG PERNAH JAGUH</div></div>''')
show("jaguh", ch(11) + 0.1, ch(11) + 3.55, "{ opacity: 0, scale: 0.85 }", '{ opacity: 1, scale: 1, duration: 0.4, ease: "back.out(1.7)" }')
oj.append(f'        tl.fromTo("#jaguh .jg-list span", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.25, stagger: 0.12, ease: "power3.out" }}, {ch(11)+0.2:.2f});')
bigword("bw-gem", "KEMBALIKAN KEGEMILANGAN", ch(12), OUTRO - 0.02, "big gold")

overlays = f'''<!doctype html>
<html lang="ms">
  <body>
    <template>
      <style>
        #root {{ position: absolute; inset: 0; width: {W}px; height: {H}px; pointer-events: none; font-family: "Montserrat"; }}
        #scrim, #hook, #para-badge, #para-frame, .chip, .stat, .yt, .pcard, .pchip, .big, #jaguh {{ visibility: hidden; }}
        #scrim {{ position: absolute; left: 0; top: 0; width: {W}px; height: 1150px; background: linear-gradient(rgba(0,0,0,.75) 0%, rgba(0,0,0,.55) 60%, rgba(0,0,0,0) 100%); }}
        #hook {{ position: absolute; left: 0; width: {W}px; top: 360px; text-align: center; color: #fff; }}
        #hook-kicker {{ display: inline-block; font-weight: 800; font-size: 36px; letter-spacing: .1em; background: #ffcc1f; color: #111; padding: 10px 24px; border-radius: 8px; }}
        #hook-big {{ font-weight: 900; font-size: 110px; line-height: 1; margin-top: 22px; letter-spacing: -0.02em; color: #fff;
                     -webkit-text-stroke: 4px #111; paint-order: stroke fill; text-shadow: 0 10px 0 rgba(0,0,0,.55), 0 0 60px rgba(255,204,31,.45); }}
        .L {{ display: inline-block; }}
        #hook-sub {{ display: inline-block; font-weight: 900; font-size: 76px; margin-top: 14px; color: #ffcc1f; letter-spacing: .06em; -webkit-text-stroke: 3px #111; paint-order: stroke fill; text-shadow: 0 6px 20px rgba(0,0,0,.8); }}
        #para-frame {{ position: absolute; inset: 0; border: 14px solid #ffcc1f; box-shadow: inset 0 0 90px rgba(255,204,31,.45); }}
        #para-badge {{ position: absolute; left: 0; width: {W}px; top: 300px; text-align: center; }}
        #para-badge .pill {{ display: inline-block; font-weight: 900; font-size: 38px; letter-spacing: .05em; color: #fff; background: #e21d2c; padding: 10px 24px; border-radius: 40px; }}
        #para-badge .dot {{ display: inline-block; width: 16px; height: 16px; border-radius: 50%; background: #fff; margin-right: 12px; vertical-align: middle; }}
        .chip {{ position: absolute; left: 0; width: {W}px; top: 392px; text-align: center; }}
        .chip span {{ display: inline-block; font-weight: 800; font-size: 38px; letter-spacing: .02em; color: #fff; background: rgba(10,12,20,.84); padding: 12px 26px; border-radius: 10px; border-left: 8px solid #ffcc1f; max-width: 940px; }}
        .chip.para span {{ background: #ffcc1f; color: #111; border-left-color: #e21d2c; }}
        .chip.gold span {{ font-size: 36px; }}
        .pcard {{ position: absolute; left: 60px; width: 960px; top: 720px; padding: 34px 40px 40px; background: rgba(8,10,18,.92); border: 4px solid #ffcc1f; border-radius: 28px; color: #fff; text-align: center; box-shadow: 0 30px 80px rgba(0,0,0,.6); }}
        .pc-num {{ font-weight: 900; font-size: 150px; line-height: .95; color: #ffcc1f; letter-spacing: -0.03em; }}
        .pc-title {{ font-weight: 900; font-size: 64px; line-height: 1.05; margin-top: 10px; letter-spacing: -0.01em; }}
        .pc-sub {{ font-weight: 700; font-size: 38px; margin-top: 12px; color: #d9dbe4; }}
        .pchip {{ position: absolute; left: 0; width: {W}px; top: 296px; text-align: center; font-weight: 900; }}
        .pchip .pn {{ display: inline-block; font-size: 34px; background: #ffcc1f; color: #111; padding: 10px 16px; border-radius: 10px 0 0 10px; }}
        .pchip .pt {{ display: inline-block; font-size: 34px; background: rgba(8,10,18,.88); color: #fff; padding: 10px 20px; border-radius: 0 10px 10px 0; letter-spacing: .02em; }}
        .stat {{ position: absolute; left: 90px; width: 900px; top: 400px; text-align: center; background: rgba(8,10,18,.86); border: 3px solid #ffcc1f; border-radius: 22px; padding: 24px 24px 28px; color: #fff; }}
        .stat-top {{ font-weight: 800; font-size: 32px; letter-spacing: .06em; color: #ffcc1f; }}
        .stat-big {{ font-weight: 900; font-size: 100px; line-height: 1.05; margin-top: 8px; letter-spacing: -0.02em; }}
        .stat-big b {{ color: #ffcc1f; }}
        .stat-sub {{ font-weight: 600; font-size: 34px; margin-top: 8px; color: #e8e8ee; }}
        .yt {{ position: absolute; left: 70px; width: 940px; top: 470px; height: 529px; border-radius: 22px; overflow: hidden; border: 5px solid #fff; box-shadow: 0 24px 60px rgba(0,0,0,.6); background: #000; }}
        .yt-img {{ position: absolute; left: 0; top: 0; width: 100%; height: 100%; object-fit: cover; }}
        .yt-cred {{ position: absolute; left: 0; bottom: 0; width: 100%; padding: 12px 18px; font-weight: 800; font-size: 30px; color: #fff; background: linear-gradient(transparent, rgba(0,0,0,.85)); }}
        .big {{ position: absolute; left: 0; width: {W}px; top: 520px; text-align: center; padding: 0 60px; }}
        .big span {{ display: inline-block; font-weight: 900; font-size: 120px; line-height: 1.02; color: #fff; letter-spacing: -0.02em; -webkit-text-stroke: 4px #111; paint-order: stroke fill; text-shadow: 0 10px 0 rgba(0,0,0,.55), 0 0 50px rgba(0,0,0,.6); }}
        .big.gold span {{ color: #ffcc1f; font-size: 104px; }}
        #jaguh {{ position: absolute; left: 70px; width: 940px; top: 470px; text-align: center; background: rgba(8,10,18,.86); border: 4px solid #ffcc1f; border-radius: 26px; padding: 30px 30px 36px; }}
        .jg-list span {{ display: inline-block; font-weight: 800; font-size: 40px; color: #111; background: #ffcc1f; padding: 8px 18px; border-radius: 10px; margin: 6px; }}
        .jg-big {{ font-weight: 900; font-size: 86px; line-height: 1.02; color: #fff; margin-top: 18px; letter-spacing: -0.02em; }}
      </style>
      <div id="root" data-composition-id="gfx" data-width="{W}" data-height="{H}" data-layout-allow-overflow data-layout-allow-overlap>
{chr(10).join(oh)}
      </div>
      <script>
        const tl = gsap.timeline({{ paused: true }});
{chr(10).join(oj)}
        window.__timelines = window.__timelines || {{}};
        window.__timelines["gfx"] = tl;
      </script>
    </template>
  </body>
</html>
'''
open(f"{PROJ}/compositions/overlays.html", "w").write(overlays)
json.dump(dict(total=TOTAL, shots=shots, sfx=SFX), open(f"{PROJ}/edl.json", "w"), ensure_ascii=False, indent=1)
print("TOTAL", TOTAL, "shots", len(shots), "P1/P2/P3", P1, P2, P3, "outro", OUTRO)
for s in shots: print(f'{s["start"]:6.2f} +{s["dur"]:5.2f} {s["src"].split("/")[-1]:10s} ms={s["ms"]:5.2f}/{s["L"]:.1f} {s["kind"]}')
