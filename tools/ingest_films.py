#!/usr/bin/env python3
"""Turn each film's script.json + timings.json into data/transcripts/<id>.json (scene starts and timed lines).

Scene starts are the running sum of scene durations (this matches the chapter lists we published with the films).
Two older films have no timing file; for those the starts are estimated from word counts and marked "approx".
Also links the rendered mp4 into media/<id>.mp4 (symlink; git-ignored) for local preview.
Usage: python3 tools/ingest_films.py
"""
import json, os, re, subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.dirname(HERE)                      # /Users/birger/RenaissanceLabs
os.chdir(HERE)
os.makedirs("data/transcripts", exist_ok=True)
os.makedirs("media", exist_ok=True)
FILES = json.load(open("data/film_files.json"))

SPECIAL = [("Z dot A I", "Z.ai"), ("dot com", ".com"), ("dot org", ".org")]
SPELLED = re.compile(r"\b(?:[A-Z] ){1,5}[A-Z]\b")


def despell(s):
    """Narration is spelled for the voice ("A I", "Z dot A I"); show it the way people write it."""
    for a, b in SPECIAL: s = s.replace(a, b)
    return SPELLED.sub(lambda m: m.group(0).replace(" ", ""), s)


def duration(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path])
    return round(float(out.decode().strip()), 2)


for fid, rel in FILES.items():
    mp4 = os.path.join(SRC, rel)
    folder = os.path.join(SRC, rel.split("/")[0])
    script = json.load(open(os.path.join(folder, "script.json")))
    tpath = os.path.join(folder, "src/generated/timings.json")
    timings = json.load(open(tpath)) if os.path.exists(tpath) else None
    total = duration(mp4)
    scenes, t0, approx = [], 0.0, timings is None
    if timings:
        for sc in script:
            tm = timings.get(sc["id"])
            if not tm: approx = True; break
            lines = [[round(t0 + a, 1), despell(txt)] for (a, _b), txt in zip(tm["lines"], tm["text"])]
            scenes.append({"id": sc["id"], "start": round(t0, 1), "lines": lines})
            t0 += tm["duration"]
    if timings is None or approx:
        scenes, t0 = [], 0.0
        words = [sum(len(x.split()) for x in (sc["say"] if isinstance(sc["say"], list) else [sc["say"]])) for sc in script]
        speech = total - 6.0                    # leave a little for the closing tail
        per = speech / max(1, sum(words))
        for sc, w in zip(script, words):
            say = sc["say"] if isinstance(sc["say"], list) else [sc["say"]]
            lines, tt = [], t0
            for x in say:
                lines.append([round(tt, 1), despell(x)]); tt += len(x.split()) * per
            scenes.append({"id": sc["id"], "start": round(t0, 1), "lines": lines})
            t0 += w * per
    rec = {"id": fid, "duration": total, "approx": bool(approx), "file": os.path.basename(mp4), "scenes": scenes}
    json.dump(rec, open(f"data/transcripts/{fid}.json", "w"), ensure_ascii=False)
    link = f"media/{fid}.mp4"
    if os.path.lexists(link): os.remove(link)
    os.symlink(mp4, link)
    print(f"{fid:20s} {total/60:5.1f} min  {len(scenes):2d} scenes  {'approx' if approx else 'exact'}")
