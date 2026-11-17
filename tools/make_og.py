#!/usr/bin/env python3
"""Render 1200x630 social preview images (assets/og/*.jpg) with headless Chrome from the generated cover art.

Cards: home, models, minds, film-<id>. Resumable (skips existing unless --force). Usage: python3 tools/make_og.py [--force] [card ...]
"""
import html, importlib.util, os, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FORCE = "--force" in sys.argv
ONLY = [a for a in sys.argv[1:] if not a.startswith("--")]
spec = importlib.util.spec_from_file_location("build", "tools/build.py"); B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
os.makedirs("assets/og", exist_ok=True)
FONT = "file://" + os.path.join(ROOT, "assets/fonts/fraunces-latin-opsz-normal.woff2")
FONTI = "file://" + os.path.join(ROOT, "assets/fonts/fraunces-latin-opsz-italic.woff2")
e = html.escape


def card_html(kicker, title, sub, art, chip=""):
    return f"""<!doctype html><meta charset="utf-8"><style>
@font-face{{font-family:F;src:url({FONT});font-weight:100 900}}
@font-face{{font-family:F;font-style:italic;src:url({FONTI});font-weight:100 900}}
*{{margin:0;box-sizing:border-box}} body{{width:1200px;height:630px;overflow:hidden;background:#0a0a1d;color:#f4efe3;font-family:-apple-system,'Helvetica Neue',Arial,sans-serif;position:relative}}
.art{{position:absolute;inset:0}} .art .cover{{width:1200px;height:675px;aspect-ratio:auto}} .art svg{{width:1200px;height:675px;position:absolute;inset:0}}
.shade{{position:absolute;inset:0;background:linear-gradient(90deg,rgba(7,7,26,.92) 0%,rgba(7,7,26,.78) 46%,rgba(7,7,26,.1) 100%)}}
.in{{position:absolute;left:72px;top:64px;bottom:60px;width:640px;display:flex;flex-direction:column}}
.brand{{font-size:22px;letter-spacing:.16em;text-transform:uppercase;color:#e0b765;font-weight:600}} .brand i{{font-family:F;font-style:italic;text-transform:none;letter-spacing:0;font-weight:400;font-size:28px;color:#e0b765;margin-left:6px}}
h1{{font-family:F;font-weight:400;font-size:{ 78 if len(title) < 28 else 62 if len(title) < 46 else 52 }px;line-height:1.06;letter-spacing:-.02em;margin-top:auto;color:#fffaf0}}
p{{font-size:27px;line-height:1.4;color:#cfc8b6;margin-top:22px;max-width:560px}} .chip{{margin-top:26px;font-size:20px;color:#e0b765;letter-spacing:.08em;text-transform:uppercase;font-weight:600}}
</style><div class="art">{art}</div><div class="shade"></div>
<div class="in"><div class="brand">Renaissance Labs<i>Learn</i></div><h1>{e(title)}</h1><p>{e(sub)}</p>{f'<div class="chip">{e(chip)}</div>' if chip else ''}</div>"""


def render(name, doc):
    out = f"assets/og/{name}.jpg"
    if os.path.exists(out) and not FORCE: return "skip"
    fd, src = tempfile.mkstemp(suffix=".html"); os.write(fd, doc.encode()); os.close(fd)
    png = tempfile.mktemp(suffix=".png")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", f"--user-data-dir={tempfile.mkdtemp()}",
                    "--window-size=1200,630", "--force-device-scale-factor=1", "--virtual-time-budget=4000", f"--screenshot={png}", "file://" + src],
                   capture_output=True, timeout=90)
    ok = os.path.exists(png) and os.path.getsize(png) > 5000 and subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "86", png, "--out", out], capture_output=True).returncode == 0
    for f in (src, png):
        try: os.unlink(f)
        except OSError: pass
    return "ok" if ok else "FAIL"


films = B.load_films()
art_home = B.cover({"id": "home", "track": "bridge", "theme": "mind-machine"})
cards = {
    "home": card_html("", "How intelligence is built.", "Films and lessons on how language models are trained and how human minds work.", art_home),
    "models": card_html("", "How models learn", "Sixteen lessons and five films on training large language models.", B.cover({"id": "models", "track": "machines", "theme": "training"})),
    "minds": card_html("", "How minds work", "Films on memory, attachment, shame, burnout and the craft of being a person.", B.cover({"id": "minds", "track": "minds", "theme": "memory-time"})),
}
for fid, f in films.items():
    cards[f"film-{fid}"] = card_html("", f["title"], f["kicker"], B.cover(f), f"{round(f['duration'] / 60)} min film")
for name, doc in cards.items():
    if ONLY and name not in ONLY: continue
    print(name, render(name, doc), flush=True)
