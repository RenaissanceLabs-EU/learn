#!/usr/bin/env python3
"""Build data/transcripts/<id>.json for films that only exist on YouTube, from their English captions (json3).

Download first (public captions):
  yt-dlp --skip-download --write-subs --write-auto-subs --sub-langs en --sub-format json3 -o "%(id)s" 'https://www.youtube.com/watch?v=<videoid>'
Then: python3 tools/ingest_youtube.py <captions-dir>
Lines are caption text grouped at pauses; "scenes" are roughly 45 second windows (ids c01, c02, ...), which the film's
chapters then group. Captions are auto-generated, so a note is added on the film page (transcript.auto = true).
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(HERE)
CAPS = sys.argv[1]
# film id -> (youtube id, duration seconds)
FILMS = {
    "rl-scaling": ("texGa4HwuPk", 953), "post-training": ("w8Almrj1c0E", 685), "hallucinations": ("yeGs0KUWai0", 385),
    "interpretability": ("xyGMDTtTXk8", 440), "alignment-problem": ("OIi-AP8znXg", 474), "agent-safety": ("fSj1Y0jgAeY", 353),
    "how-agents-work": ("qz4cSKa3Feo", 405), "mind-making-up-stories": ("_uMOyd8-7qU", 267),
    "how-the-mind-processes-information": ("vEZS3d4oW38", 403), "self-compassion": ("Nytvnlcek-8", 107),
}


def load(path):
    ev = json.load(open(path)).get("events", [])
    out = []
    for e in ev:
        if "segs" not in e: continue
        txt = "".join(s.get("utf8", "") for s in e["segs"]).replace("\n", " ")
        txt = re.sub(r"\s+", " ", txt).strip()
        if txt: out.append((e["tStartMs"] / 1000.0, txt))
    return out


def group(events):
    """One continuous text with a time per caption event, split into sentences; each line starts at the time of its first word."""
    import bisect
    text, offs = "", []
    for t, txt in events:
        offs.append((len(text), t)); text += txt + " "
    starts = [o for o, _ in offs]
    lines = []
    for m in re.finditer(r"[^.!?]+(?:[.!?]+[\"')]*|$)\s*", text):
        sent = m.group(0).strip()
        if len(sent) < 2: continue
        i = max(0, bisect.bisect_right(starts, m.start() + (len(m.group(0)) - len(m.group(0).lstrip()))) - 1)
        if len(sent) <= 260:
            lines.append([round(offs[i][1], 1), sent]); continue
        # no punctuation (older auto captions): cut at event boundaries into pieces of about 110 characters
        j0, buf, t0 = i, "", None
        for (o, t), nxt in zip(offs[i:], offs[i + 1:] + [(len(text), 0)]):
            if o >= m.end(): break
            seg = text[max(o, m.start()):min(nxt[0], m.end())].strip()
            if t0 is None: t0 = t
            buf += " " + seg
            if len(buf) >= 110:
                lines.append([round(t0, 1), buf.strip()]); buf, t0 = "", None
        if buf.strip(): lines.append([round(t0 if t0 is not None else offs[i][1], 1), buf.strip()])
    return lines


for fid, (vid, dur) in FILMS.items():
    p = next((os.path.join(CAPS, f"{vid}.{s}.json3") for s in ("en", "en-orig") if os.path.exists(os.path.join(CAPS, f"{vid}.{s}.json3"))), None)
    if not p: print(fid, "no captions yet"); continue
    lines = group(load(p))
    scenes, win = [], 45
    for t, txt in lines:
        k = int(t // win)
        if not scenes or scenes[-1]["k"] != k:
            scenes.append({"k": k, "id": f"c{len(scenes) + 1:02d}", "start": round(t if not scenes else k * win, 1), "lines": []})
        scenes[-1]["lines"].append([t, txt])
    if scenes: scenes[0]["start"] = 0.0
    for s in scenes: s.pop("k")
    json.dump({"id": fid, "duration": dur, "approx": False, "auto": True, "file": f"{fid}.mp4", "scenes": scenes}, open(f"data/transcripts/{fid}.json", "w"), ensure_ascii=False)
    print(f"{fid:36s} {len(lines):3d} lines  {len(scenes):2d} windows  {dur / 60:.1f} min")
