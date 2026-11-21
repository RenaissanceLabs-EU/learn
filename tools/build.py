#!/usr/bin/env python3
"""Build the Learn site (static files in the repo root) from content/ and data/.

  content/lessons/*.md      written lessons (front matter + light Markdown, see content/BRIEF.md)
  content/films/*.json      film catalogue entries
  data/transcripts/*.json   scene starts and timed narration lines (tools/ingest_films.py)
  data/site.json            media base URL and film upload dates

Usage: python3 tools/build.py
"""
import datetime, glob, html, json, os, random, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
SITE = "https://learn.renaissancelabs.eu"
ATLAS = "https://labs.renaissancelabs.eu"
CFG = json.load(open("data/site.json"))
MEDIA = CFG.get("media_base", "/media/").rstrip("/") + "/"
BUILD = CFG.get("built", datetime.date.today().isoformat())
import hashlib
ASSETV = hashlib.md5(b"".join(open(f, "rb").read() for f in ("styles.css", "app.js", "widgets.js", "widgets2.js", "widgets3.js") if os.path.exists(f))).hexdigest()[:10]  # changes whenever a stylesheet or script does, so browsers never show new pages with old styles

PARTS = ["The basics", "Feeding the model", "The machine room", "After pre-training", "End to end"]
PART_BLURB = {
    "The basics": "What a model is, how it reads text, and how it learns.",
    "Feeding the model": "Data, scale and the memory a model needs.",
    "The machine room": "Chips, parallelism and what goes wrong at scale.",
    "After pre-training": "Turning a text predictor into something useful, and running it.",
    "End to end": "Two long guides that follow one real model, Agora 9B, from raw text to a working assistant.",
}
THEMES = {
    "training": ("How a model is trained", "Data, scale, cost and the engineering behind a frontier run."),
    "hardware": ("The hardware", "What the chips can and cannot do, and why."),
    "open-ecosystem": ("The open ecosystem", "The strongest open models and what makes them tick."),
    "safety": ("Safety and alignment", "Keeping capable models honest, understandable and under control."),
    "agents": ("How agents work", "Models that use tools and act in the world."),
    "memory-time": ("Memory, time and attention", "How the mind rebuilds the past, lives in the present and imagines the future."),
    "fear-shame": ("Fear, shame and being seen", "The emotions that hold us back, and what they are trying to tell us."),
    "connection": ("Attachment and belonging", "How early bonds shape adult life, and how people change."),
    "recovery": ("Depletion, regulation and follow-through", "Coming back from exhaustion, steadying strong feelings, doing what you meant to do."),
    "mind-machine": ("Where the two meet", "Information, entropy and what we mean by intelligence."),
}
TRACK_ORDER = {
    "machines": ["frontier-training", "open-models", "rl-scaling", "post-training", "gpu-hardware", "inkling", "how-agents-work", "cluster-agents", "agent-safety", "alignment-problem", "interpretability", "hallucinations"],
    "minds": ["memory", "present", "future", "mind-making-up-stories", "how-the-mind-processes-information", "fear", "old-friend", "shame", "fool", "envy", "attachment",
              "attachment-heal", "not-alone", "burnout", "emotion-regulation", "act-first", "self-compassion"],
    "bridge": ["intelligence", "entropy"],
}
THEME_ORDER = {"machines": ["training", "open-ecosystem", "hardware", "agents", "safety"],
               "minds": ["memory-time", "fear-shame", "connection", "recovery"], "bridge": ["mind-machine"]}
THEME_LABEL = {k: v[0] for k, v in THEMES.items()}


GLOSS_SKIP = {"active", "adam", "stacked", "times the tokens", "tokens seen", "gradients", "masked", "mixtures of experts", "classifiers",
              "swiglu clamping", "anticipatory routing", "tokens seen", "heads", "greedy", "reward", "student", "teacher", "arena"}
GLOSS_DEF = {
    "attention": "A mechanism that lets each token look back at the other tokens in the text and weigh which ones matter for the prediction.",
    "heads": "Several attention calculations run side by side, each free to learn a different pattern.",
    "loss spikes": "Sudden jumps in the training loss, often a sign of instability that can ruin a run if not handled.",
    "policy": "The model's behaviour seen as a rule for choosing what to write next.",
    "reward hacking": "When a model finds a way to score well on the reward without doing what the designer actually wanted.",
    "load balancing": "Keeping tokens spread evenly across the experts so none sit idle and none are overloaded.",
    "chat template": "The fixed format that marks who is speaking in a conversation, so the model can tell system, user and assistant text apart.",
    "mixture of experts": "An architecture where each layer holds many specialist sub-networks, called experts, and a router sends each token to only a few of them.",
    "instruction dataset": "A collection of pairs, each an instruction and a good response, used for supervised fine-tuning.",
    "silent data corruption": "A hardware fault that quietly changes numbers in a calculation without raising an error, so training carries on with bad values.",
    "hbm": "High-bandwidth memory: the memory stacked next to the GPU chip that holds weights and activations.",
    "adam": "The most widely used optimizer: it keeps running averages of each parameter's gradient to set its step size.",
    "model collapse": "The gradual loss of diversity and quality when models are trained on text that earlier models generated.",
    "optimizer": "The rule that turns gradients into parameter updates.",
}

# ------------------------------------------------------------------ helpers
def esc(s): return html.escape(str(s if s is not None else ""), quote=True)
def slugify(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "section"
TAGS = {  # slug: (label, one-line description). Unknown slugs get a label made from the slug.
    "hallucination": ("Hallucination", "Models that make things up, and how to measure and train against it."),
    "preference-tuning": ("Preference tuning", "Training on pairs of better and worse answers, with DPO and its relatives."),
    "supervised-fine-tuning": ("Supervised fine-tuning", "Teaching a model by showing it the answers you want."),
    "reinforcement-learning": ("Reinforcement learning", "Training on rewards for what the model does."),
    "evaluation": ("Evaluation", "How to measure a model, and what the measurements miss."),
    "datasets": ("Datasets", "Building, checking and documenting training data."),
    "identity": ("Model identity", "What a model says about itself, and how it learns it."),
    "alignment": ("Alignment", "Getting a model to behave as intended."),
    "multilingual": ("Multilingual", "Work across many languages, beyond English."),
    "swedish": ("Swedish", "Models and data for Swedish."),
    "decision-models": ("Decision models", "Small models that answer typed questions in one pass."),
    "training-practice": ("Training practice", "The craft of running training jobs, and what goes wrong."),
}
def tag_label(t): return TAGS.get(t, (t.replace("-", " ").capitalize(), ""))[0]
def tag_list(v): return [slugify(x) for x in (v if isinstance(v, list) else str(v or "").split(",")) if str(x).strip()]
def tag_row(tags, cls="tags"):
    return f'<p class="{cls}">' + "".join(f'<a class="tag" href="/tags/{t}/">{esc(tag_label(t))}</a>' for t in tags) + "</p>" if tags else ""


def clock(sec):
    sec = int(sec); h, m, s = sec // 3600, sec % 3600 // 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
def mins(sec): return f"{max(1, round(sec / 60))} min"
def write(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    open(path, "w", encoding="utf-8").write(text)


# ------------------------------------------------------------------ inline + block markdown
def inline(s):
    s = esc(s)
    codes = []
    def keep(m): codes.append(m.group(1)); return f"\x00{len(codes) - 1}\x00"
    s = re.sub(r"`([^`]+)`", keep, s)
    def link(m):
        u = m.group(2).replace("&amp;", "&")
        extern = u.startswith("http")
        attrs = ' target="_blank" rel="noopener"' if extern else ""
        return f'<a href="{esc(u)}"{attrs}>{m.group(1)}</a>'
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", s)
    return re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{codes[int(m.group(1))]}</code>", s)


def plain(s):
    return re.sub(r"\s+", " ", re.sub(r"[*`]|\[([^\]]+)\]\([^)]*\)", lambda m: m.group(1) or "", s)).strip()


def split_front(text):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m: raise ValueError("missing front matter")
    meta, key, lines = {}, None, m.group(1).split("\n")
    for ln in lines:
        if ln.startswith("- ") and key == "sources":
            meta.setdefault("sources", []).append(ln[2:].strip()); continue
        if ":" in ln and not ln.startswith(" "):
            k, v = ln.split(":", 1); key = k.strip(); v = v.strip()
            v = re.sub(r"\s+#.*$", "", v)
            if len(v) >= 2 and v[0] == v[-1] == '"': v = v[1:-1]
            meta[key] = [] if key == "sources" else v
    return meta, m.group(2)


def render_body(body, glossary_sink=None, lesson=None):
    """Light Markdown with :::blocks. Returns (html, toc)."""
    lines, out, toc, i = body.split("\n"), [], [], 0
    def para_flush(buf):
        if buf:
            text = " ".join(buf)
            out.append(f"<p>{inline(text)}</p>")
            if glossary_sink is not None: sink(text)
    def sink(text):
        for m in re.finditer(r"\*\*([^*]{2,42})\*\*", text):
            term = m.group(1).strip()
            if re.search(r"[0-9:;]", term): continue
            sentences = re.split(r"(?<=[.!?])\s+", text)
            sent = next((x for x in sentences if m.group(0) in x), text)
            glossary_sink.append((term, plain(sent), lesson))
    buf = []
    while i < len(lines):
        ln = lines[i]; st = ln.strip()
        if st == "":
            para_flush(buf); buf = []; i += 1; continue
        if st == ":::": i += 1; continue
        m = re.match(r"^:::(\w+)\s*(.*)$", st)
        if m:
            para_flush(buf); buf = []
            name, arg = m.group(1), m.group(2).strip()
            if name == "widget":
                out.append(f'<div class="widget" data-widget="{esc(arg)}" aria-live="polite"></div>'); i += 1; continue
            j, inner = i + 1, []
            while j < len(lines) and lines[j].strip() != ":::":
                inner.append(lines[j]); j += 1
            i = j + 1
            out.append(block(name, arg, inner, glossary_sink, lesson)); continue
        if st.startswith("## ") or st.startswith("### "):
            para_flush(buf); buf = []
            lvl = 2 if st.startswith("## ") else 3
            text = st[lvl + 1:].strip()
            hid = slugify(text)
            if lvl == 2: toc.append((hid, text))
            out.append(f'<h{lvl} id="{hid}">{inline(text)}</h{lvl}>'); i += 1; continue
        if st.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|?$", lines[i + 1].strip()):
            para_flush(buf); buf = []
            def cells(r): return [c.strip() for c in r.strip().strip("|").split("|")]
            head_ = cells(st)
            right = [c.endswith(":") for c in cells(lines[i + 1])]
            cls = lambda k: ' class="r"' if k < len(right) and right[k] else ""
            i += 2; rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(cells(lines[i])); i += 1
            th = "".join(f"<th{cls(k)}>{inline(c)}</th>" for k, c in enumerate(head_))
            tb = "".join("<tr>" + "".join(f"<td{cls(k)}>{inline(c)}</td>" for k, c in enumerate(r)) + "</tr>" for r in rows)
            out.append(f'<div class="tbl"><table><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table></div>'); continue
        if re.match(r"^(- |\* )", st):
            para_flush(buf); buf = []
            items = []
            while i < len(lines) and re.match(r"^\s*(- |\* )", lines[i]):
                items.append(re.sub(r"^\s*(- |\* )", "", lines[i]).strip()); i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>")
            if glossary_sink is not None:
                for x in items: sink(x)
            continue
        if re.match(r"^\d+\. ", st):
            para_flush(buf); buf = []
            items = []
            while i < len(lines) and re.match(r"^\s*\d+\. ", lines[i]):
                items.append(re.sub(r"^\s*\d+\. ", "", lines[i]).strip()); i += 1
            out.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ol>"); continue
        if st.startswith("> "):
            para_flush(buf); buf = []
            q = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                q.append(lines[i].strip().lstrip("> ")); i += 1
            out.append(f"<blockquote><p>{inline(' '.join(q))}</p></blockquote>"); continue
        buf.append(st); i += 1
    para_flush(buf)
    return "\n".join(out), toc


def block(name, arg, inner, gsink, lesson):
    rows = [x.strip() for x in inner if x.strip()]
    if name == "callout":
        return f'<aside class="callout"><span class="callout-t">{esc(arg or "Key idea")}</span><p>{inline(" ".join(rows))}</p></aside>'
    if name == "flow":
        li = []
        for r in rows:
            a, _, b = r.partition("|")
            li.append(f"<li><b>{inline(a.strip())}</b><span>{inline(b.strip())}</span></li>")
        return f'<ol class="flow">{"".join(li)}</ol>'
    if name == "stats":
        cells = []
        for r in rows:
            a, _, b = r.partition("|")
            cells.append(f"<div><b>{inline(a.strip())}</b><span>{inline(b.strip())}</span></div>")
        return f'<div class="stats">{"".join(cells)}</div>'
    if name == "bars":
        data = []
        for r in rows:
            p = [x.strip() for x in r.split("|")]
            try: data.append((p[0], float(p[1].replace(",", "")), p[1], p[2] if len(p) > 2 else ""))
            except Exception: continue
        mx = max([d[1] for d in data] or [1]) or 1
        rr = "".join(f'<div class="brow"><span class="bar-l">{inline(l)}</span><span class="bar-track"><i style="width:{max(2, v / mx * 100):.1f}%"></i></span>'
                     f'<span class="bar-v">{esc(raw)}</span>{f"<span class=bar-n>{inline(n)}</span>" if n else ""}</div>' for l, v, raw, n in data)
        title = f'<div class="bars-t">{esc(arg)}</div>' if arg else ""
        return f'<figure class="bars">{title}{rr}</figure>'
    if name == "compare":
        cols, cur = [], None
        for r in rows:
            if r.startswith("## "): cur = [r[3:].strip(), []]; cols.append(cur)
            elif cur is not None: cur[1].append(r)
        cells = []
        for t, items in cols:
            lis = "".join(f"<li>{inline(x[2:] if x.startswith('- ') else x)}</li>" for x in items)
            cells.append(f"<div class=\"col\"><h4>{inline(t)}</h4><ul>{lis}</ul></div>")
        return f'<div class="compare c{len(cols)}">{"".join(cells)}</div>'
    if name == "example":
        t = f'<span class="ex-t">{esc(arg or "Example")}</span>'
        return f'<div class="example">{t}' + "".join(f"<p>{inline(r)}</p>" for r in rows) + "</div>"
    return "<!-- unknown block " + esc(name) + " -->"


# ------------------------------------------------------------------ data
def load_films():
    tr = {os.path.basename(p)[:-5]: json.load(open(p)) for p in glob.glob("data/transcripts/*.json")}
    films = {}
    for p in glob.glob("content/films/*.json"):
        f = json.load(open(p)); t = tr.get(f["id"])
        if f["id"] in CFG.get("hidden", []): continue
        if not t: print("no transcript for", f["id"]); continue
        sc = {s["id"]: s for s in t["scenes"]}
        alllines = [ln for s_ in t["scenes"] for ln in s_["lines"]]
        chs = []
        for k, c in enumerate(f["chapters"]):
            s = sc.get(c["scene"])
            if not s: continue
            nxt = next((sc[x["scene"]]["start"] for x in f["chapters"][k + 1:] if x["scene"] in sc), t["duration"])
            chs.append({"scene": c["scene"], "title": c["title"], "start": s["start"], "end": nxt,
                        "lines": [ln for ln in alllines if s["start"] - 0.01 <= ln[0] < nxt]})
        f["chapters"], f["duration"], f["approx"], f["file"], f["auto"] = chs, t["duration"], t["approx"], t["file"], t.get("auto", False)
        f["date"] = CFG.get("dates", {}).get(f["id"], BUILD)
        films[f["id"]] = f
    return films


def load_lessons():
    lessons, gsink = {}, []
    for p in sorted(glob.glob("content/lessons/*.md")):
        meta, body = split_front(open(p, encoding="utf-8").read())
        lid = meta["slug"]
        html_, toc = render_body(body, gsink, lid)
        meta["id"], meta["html"], meta["toc"], meta["order"] = lid, html_, toc, int(meta.get("order", 99))
        meta["minutes"] = int(meta.get("minutes", 7))
        meta["words"] = len(re.findall(r"\w+", body))
        meta["films"] = [x.strip() for x in meta.get("films", "").split(",") if x.strip()]
        meta["related"] = [x.strip() for x in meta.get("related", "").split(",") if x.strip()]
        meta["sources"] = [tuple(x.strip() for x in s.split("|", 1)) + ("",) for s in meta.get("sources", [])]
        meta["sources"] = [(s[0], s[1]) for s in meta["sources"]]
        meta["text"] = plain(re.sub(r":::\w+[^\n]*|^:::$", " ", body, flags=re.M))
        meta["tags"] = tag_list(meta.get("tags"))
        lessons[lid] = meta
    return dict(sorted(lessons.items(), key=lambda kv: kv[1]["order"])), gsink


def load_notes():
    notes = {}
    for p in sorted(glob.glob("content/notes/*.md")):
        meta, body = split_front(open(p, encoding="utf-8").read())
        nid = meta["slug"]
        html_, toc = render_body(body, None, nid)
        meta.update(id=nid, html=html_, toc=toc, minutes=int(meta.get("minutes", 6)),
                    films=[x.strip() for x in meta.get("films", "").split(",") if x.strip()],
                    related=[x.strip() for x in meta.get("related", "").split(",") if x.strip()],
                    text=plain(re.sub(r":::\w+[^\n]*|^:::$", " ", body, flags=re.M)), tags=tag_list(meta.get("tags")))
        notes[nid] = meta
    return dict(sorted(notes.items(), key=lambda kv: kv[1]["date"], reverse=True))


def nice_date(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%B %Y')}"


# ------------------------------------------------------------------ art
HUE = {"machines": (196, 262), "minds": (36, 290), "bridge": (196, 36)}


def motif(theme, c):
    """Large faint line-art per theme, drawn in a 320x180 box, centred at 232,92."""
    s = f'stroke="{c}" fill="none" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"'
    if theme == "training":
        return "".join(f'<rect x="{176 + k * 6}" y="{52 + k * 17}" width="{110 - k * 12}" height="11" rx="3" {s} opacity="{0.9 - k * 0.13:.2f}"/>' for k in range(5))
    if theme == "hardware":
        pins = "".join(f'<path d="M{200 + k * 16} 52v-10M{200 + k * 16} 132v10M178 {74 + k * 16}h-10M258 {74 + k * 16}h10" {s}/>' for k in range(4))
        return f'<rect x="178" y="52" width="80" height="80" rx="6" {s}/><rect x="196" y="70" width="44" height="44" rx="3" {s}/>{pins}'
    if theme == "open-ecosystem":
        pts = [(232 + 56 * __import__("math").cos(k * 6.2832 / 7), 92 + 56 * __import__("math").sin(k * 6.2832 / 7)) for k in range(7)]
        ln = "".join(f'<path d="M232 92L{x:.0f} {y:.0f}" {s} opacity=".5"/>' for x, y in pts)
        nd = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="5" {s}/>' for x, y in pts)
        return ln + nd + f'<circle cx="232" cy="92" r="9" {s}/>'
    if theme == "safety":
        return f'<circle cx="232" cy="92" r="56" {s} stroke-dasharray="3 7"/><circle cx="232" cy="92" r="34" {s}/><path d="M218 93l10 10 18-22" {s}/>'
    if theme == "memory-time":
        return f'<path d="M150 128Q232 30 314 128" {s} stroke-dasharray="2 6"/><circle cx="232" cy="78" r="7" fill="{c}" opacity=".9"/>' + "".join(
            f'<circle cx="{x}" cy="{y}" r="2.6" fill="{c}" opacity=".6"/>' for x, y in ((170, 114), (192, 94), (272, 94), (294, 114)))
    if theme == "fear-shame":
        return f'<rect x="200" y="46" width="64" height="92" rx="30" {s}/><circle cx="232" cy="104" r="14" fill="{c}" opacity=".16"/><circle cx="232" cy="104" r="4" fill="{c}"/>'
    if theme == "connection":
        return f'<circle cx="212" cy="92" r="40" {s}/><circle cx="252" cy="92" r="40" {s}/>'
    if theme == "recovery":
        rays = "".join(f'<path d="M232 112L{232 + 62 * __import__("math").cos(a):.0f} {112 - 62 * __import__("math").sin(a):.0f}" {s} opacity=".4"/>' for a in (0.35, 0.8, 1.25, 1.9, 2.35, 2.8))
        return f'<path d="M180 112a52 52 0 0 1 104 0" {s}/><path d="M160 112h144" {s}/>{rays}'
    return f'<circle cx="190" cy="92" r="34" {s}/>' + "".join(f'<rect x="{236 + a * 20}" y="{62 + b * 20}" width="14" height="14" rx="2" {s}/>' for a in range(3) for b in range(3))


def cover(f):
    rnd = random.Random(f["id"])
    h1, h2 = HUE[f["track"]]
    stars = "".join(f'<circle cx="{rnd.uniform(4, 316):.0f}" cy="{rnd.uniform(4, 176):.0f}" r="{rnd.uniform(.4, 1.3):.1f}" fill="#fff" opacity="{rnd.uniform(.15, .8):.2f}"/>' for _ in range(34))
    gx, gy = rnd.uniform(40, 110), rnd.uniform(110, 170)
    gid = "g" + re.sub(r"\W", "", f["id"])
    col = f"hsl({h1} 70% 78%)"
    return (f'<div class="cover cover-{f["track"]}" style="--h1:{h1};--h2:{h2}"><svg viewBox="0 0 320 180" preserveAspectRatio="xMidYMid slice" aria-hidden="true">'
            f'<defs><radialGradient id="{gid}a"><stop offset="0" stop-color="hsl({h1} 80% 60%)" stop-opacity=".55"/><stop offset="1" stop-color="hsl({h1} 80% 60%)" stop-opacity="0"/></radialGradient>'
            f'<radialGradient id="{gid}b"><stop offset="0" stop-color="hsl({h2} 70% 62%)" stop-opacity=".4"/><stop offset="1" stop-color="hsl({h2} 70% 62%)" stop-opacity="0"/></radialGradient></defs>'
            f'<circle cx="{gx:.0f}" cy="{gy:.0f}" r="120" fill="url(#{gid}a)"/><circle cx="260" cy="40" r="110" fill="url(#{gid}b)"/>'
            f'{stars}<g opacity=".85">{motif(f["theme"], col)}</g></svg></div>')


def hero_stars(n=120):
    rnd = random.Random("hero")
    return "".join(f'<circle cx="{rnd.uniform(0, 1600):.0f}" cy="{rnd.uniform(0, 800):.0f}" r="{rnd.uniform(.5, 1.8):.1f}" fill="#fff" opacity="{rnd.uniform(.12, .75):.2f}"{" class=tw" if rnd.random() < .2 else ""}/>' for _ in range(n))


# ------------------------------------------------------------------ chrome
def head(title, desc, path, body_class="", image="home", extra="", jsonld=None):
    url = SITE + path
    img = f"{SITE}/assets/og/{image}.jpg"
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>\n' if jsonld else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(url)}">
<meta property="og:site_name" content="Renaissance Labs · Learn">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{esc(url)}">
<meta property="og:locale" content="en_GB">
<meta property="og:image" content="{esc(img)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{esc(img)}">
<meta name="theme-color" content="#fdfaf3">
<link rel="icon" href="/assets/favicon.png">
<link rel="preload" href="/assets/fonts/fraunces-latin-opsz-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/styles.css?v={ASSETV}">
{extra}{ld}</head>
<body class="{body_class}">
<a class="skip" href="#main">Skip to content</a>
<header class="bar">
  <a class="brand" href="/"><img src="/assets/mark.png" alt="" width="28" height="28"><span>Renaissance Labs</span><em>Learn</em></a>
  <div class="bar-r">
    <nav id="mainnav" aria-label="Main">
      <a href="/models/">Models</a>
      <a href="/lessons/">Lessons</a>
      <a href="/minds/">Minds</a>
      <a href="/films/">Films</a>
      <a class="sec" href="/recipes/">Recipes</a>
      <a class="sec" href="/notes/">Notes</a>
      <a class="sec" href="/glossary/">Glossary</a>
      <a class="sec ext" href="{ATLAS}/">Atlas</a>
    </nav>
    <button class="search-open" type="button" aria-label="Search" data-search><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg><kbd>/</kbd></button>
    <button class="menu-toggle" type="button" aria-label="Menu" aria-expanded="false" aria-controls="mainnav"><i></i><i></i><i></i></button>
  </div>
</header>
<div class="menu-scrim" hidden></div>
"""


def foot():
    return f"""<footer class="foot wrap">
  <p class="brand"><img src="/assets/mark.png" alt="" width="22" height="22"> Renaissance Labs · Learn · Made in Europe</p>
  <p class="foot-links"><a href="/tags/">Topics</a><a href="/about/">About and sources</a><a href="{ATLAS}/">Open Labs Atlas</a><a href="https://renaissancelabs.eu/">Renaissance Labs</a><a href="https://huggingface.co/RenaissanceLabsEU">Hugging Face</a><a href="/llms.txt">llms.txt</a></p>
</footer>
<div class="search" id="search" hidden role="dialog" aria-modal="true" aria-label="Search">
  <div class="search-box"><input id="q" type="search" placeholder="Search lessons, films and terms" autocomplete="off" spellcheck="false"><button type="button" data-search-close aria-label="Close">Esc</button>
  <ul id="results"></ul></div>
</div>
<script src="/app.js?v={ASSETV}" defer></script>
</body>
</html>
"""


def page(path, title, desc, content, **kw):
    out = head(title, desc, path, **kw) + f'<main id="main">\n{content}\n</main>\n' + foot()
    write(("." + path + "index.html") if path.endswith("/") else "." + path, out)


# ------------------------------------------------------------------ components
def film_card(f, big=False):
    th = THEME_LABEL[f["theme"]]
    return (f'<a class="fcard{" big" if big else ""}" href="/films/{f["id"]}/" data-film="{f["id"]}">'
            f'{cover(f)}<span class="dur">{"Soon" if (CFG.get("youtube") and f["id"] not in CFG["youtube"]) else mins(f["duration"])}</span><span class="fprog" hidden><i></i></span>'
            f'<span class="fbody"><span class="chip">{esc(th)}</span><b>{esc(f["title"])}</b><span class="fk">{esc(f["kicker"])}</span></span></a>')


def lesson_card(l):
    return (f'<a class="lcard" href="/lessons/{l["id"]}/" data-lesson="{l["id"]}"><span class="lnum">{l["order"]:02d}</span>'
            f'<span class="lbody"><b>{esc(l["title"])}</b><span>{esc(l["summary"])}</span>'
            f'<span class="lmeta">{esc(l["level"])} · {l["minutes"]} min</span></span><span class="tick" hidden>✓</span></a>')


def note_card(n):
    return (f'<a class="ncard" href="/notes/{n["id"]}/"><span class="chip">{nice_date(n["date"])} · {n["minutes"]} min</span>'
            f'<b>{esc(n["title"])}</b><span>{esc(n["summary"])}</span></a>')


def shelf(theme, films):
    t, d = THEMES[theme]
    cards = "".join(film_card(f) for f in films)
    return f'<section class="shelf"><header><h3>{esc(t)}</h3><p>{esc(d)}</p></header><div class="fgrid">{cards}</div></section>'


# ------------------------------------------------------------------ pages
def ordered(films, track):
    return [films[i] for i in TRACK_ORDER[track] if i in films]


def home(films, lessons, notes=None):
    n_hours = sum(f["duration"] for f in films.values()) / 3600
    ms, mn = ordered(films, "machines"), ordered(films, "minds")
    featured = films["frontier-training"]
    cont = ('<section class="wrap continue" id="continue" hidden><h2>Pick up where you left off</h2><div class="fgrid" id="continue-grid"></div></section>')
    path_cards = "".join(lesson_card(l) for l in list(lessons.values())[:6])
    bridge = "".join(film_card(f) for f in ordered(films, "bridge"))
    notes_band = ""
    if notes:
        notes_band = ('<section class="wrap block"><header class="sec-h"><p class="eyebrow">Notes</p><h2>From the cluster</h2>'
                      '<p class="lede">Short essays on the practice of training models, and what the papers leave out.</p></header>'
                      f'<div class="ngrid">{"".join(note_card(n) for n in list(notes.values())[:3])}</div></section>')
    c = f"""
<section class="hero">
  <svg class="hero-sky" viewBox="0 0 1600 800" preserveAspectRatio="xMidYMid slice" aria-hidden="true">{hero_stars()}</svg>
  <div class="hero-glow a"></div><div class="hero-glow b"></div>
  <div class="wrap hero-in">
    <p class="eyebrow">Renaissance Labs · Learn</p>
    <h1>How intelligence is built.</h1>
    <p class="lede">Films and lessons on how language models are trained, and on how human minds learn, remember and heal. Free, in plain language, with the sources shown.</p>
    <div class="doors">
      <a class="door models" href="/models/"><span class="door-k">Machines</span><b>How models learn</b><span>{len(lessons)} lessons and {len(ms)} films on training large language models, from tokens to trillion-token runs.</span><i>Start the course</i></a>
      <a class="door minds" href="/minds/"><span class="door-k">Minds</span><b>How minds work</b><span>{len(mn)} films on memory, attachment, shame, burnout and the ordinary craft of being a person.</span><i>Explore the films</i></a>
    </div>
    <p class="hero-stats"><b>{len(films)}</b> films · <b>{n_hours:.1f}</b> hours · <b>{len(lessons)}</b> lessons · every claim sourced</p>
  </div>
</section>
{cont}
<section class="wrap block">
  <header class="sec-h"><p class="eyebrow">Featured film</p><h2>{esc(featured["title"])}</h2></header>
  <a class="feature" href="/films/{featured["id"]}/">{cover(featured)}<span class="feature-b"><span class="chip">{mins(featured["duration"])} · {esc(featured["level"])}</span><p>{esc(featured["description"])}</p><i>Watch the film</i></span></a>
</section>
<section class="wrap block">
  <header class="sec-h"><p class="eyebrow">The course</p><h2>From tokens to frontier runs</h2><p class="lede">Sixteen short lessons in four parts. Each one ends with the film chapters that cover the same ground.</p></header>
  <div class="lgrid">{path_cards}</div>
  <p class="more"><a href="/models/">See the full course map</a></p>
</section>
<section class="wrap block">
  <header class="sec-h"><p class="eyebrow">Minds</p><h2>The human side of intelligence</h2><p class="lede">Memory is rebuilt every time we use it. Fear and shame are signals, not verdicts. These films take the research seriously and the viewer gently.</p></header>
  <div class="fgrid">{"".join(film_card(f) for f in mn[:6])}</div>
  <p class="more"><a href="/minds/">All {len(mn)} films on minds</a></p>
</section>
{notes_band}<section class="wrap block bridge">
  <header class="sec-h"><p class="eyebrow">Where the two meet</p><h2>Machine and mind, one question</h2><p class="lede">Information, surprise and what we mean when we call something intelligent. Two short films that sit between the tracks.</p></header>
  <div class="fgrid two">{bridge}</div>
</section>"""
    ld = {"@context": "https://schema.org", "@type": "WebSite", "name": "Renaissance Labs · Learn", "url": SITE + "/",
          "description": "Films and lessons on how language models are trained and how human minds work.",
          "publisher": {"@type": "Organization", "name": "Renaissance Labs", "url": "https://renaissancelabs.eu/"}}
    page("/", "Learn · How intelligence is built · Renaissance Labs",
         "Films and lessons on how language models are trained, and on how human minds learn, remember and heal.", c, body_class="home", jsonld=ld)


def models_page(films, lessons):
    ms = ordered(films, "machines")
    parts = []
    for p in PARTS:
        ls = [l for l in lessons.values() if l.get("part") == p]
        if not ls: continue
        parts.append(f'<section class="part"><header><p class="eyebrow">Part {PARTS.index(p) + 1}</p><h2>{esc(p)}</h2><p>{esc(PART_BLURB[p])}</p></header><div class="lgrid">{"".join(lesson_card(l) for l in ls)}</div></section>')
    shelves = "".join(shelf(t, [f for f in ms if f["theme"] == t]) for t in THEME_ORDER["machines"] if any(f["theme"] == t for f in ms))
    total_min = sum(l["minutes"] for l in lessons.values())
    first = list(lessons.values())[0]
    c = f"""
<section class="head-band models"><div class="wrap">
  <p class="eyebrow">Machines</p><h1>How models learn</h1>
  <p class="lede">A course on how large language models are built and trained, written for curious people and working builders. About {total_min // 60} hours of reading across {len(lessons)} lessons, with {len(ms)} films to match.</p>
  <p class="cta"><a class="btn" href="/lessons/{first["id"]}/">Start with lesson 1</a><a class="btn ghost" href="#films">Watch the films</a></p>
</div></section>
<div class="wrap">{"".join(parts)}</div>
<section class="wrap block" id="films"><header class="sec-h"><p class="eyebrow">Films</p><h2>Watch the whole story</h2></header>{shelves}</section>"""
    ld = {"@context": "https://schema.org", "@type": "Course", "name": "How language models learn", "description": "A course on how large language models are built and trained.",
          "provider": {"@type": "Organization", "name": "Renaissance Labs", "url": "https://renaissancelabs.eu/"},
          "hasCourseInstance": {"@type": "CourseInstance", "courseMode": "online", "courseWorkload": f"PT{total_min}M"}, "isAccessibleForFree": True}
    page("/models/", "How models learn · a course on training LLMs · Learn", "Sixteen lessons and films on how large language models are trained: tokens, attention, data, scaling, GPUs, fine-tuning and reinforcement learning.", c, jsonld=ld, image="models")


def lessons_page(lessons):
    parts = []
    for p in PARTS:
        ls = [l for l in lessons.values() if l.get("part") == p]
        if not ls: continue
        parts.append(f'<section class="part"><header><p class="eyebrow">Part {PARTS.index(p) + 1}</p><h2>{esc(p)}</h2><p>{esc(PART_BLURB[p])}</p></header><div class="lgrid">{"".join(lesson_card(l) for l in ls)}</div></section>')
    total_min = sum(l["minutes"] for l in lessons.values())
    first = list(lessons.values())[0]
    c = f"""
<section class="head-band models"><div class="wrap">
  <p class="eyebrow">Course</p><h1>All lessons</h1>
  <p class="lede">{len(lessons)} written lessons on how large language models are built and trained, about {total_min // 60} hours of reading in total. Read them in order or jump to what you need. Each one links to the films that cover the same ground.</p>
  <p class="cta"><a class="btn" href="/lessons/{first["id"]}/">Start with lesson 1</a><a class="btn ghost" href="/models/">Course map and films</a></p>
</div></section>
<div class="wrap">{"".join(parts)}</div>"""
    page("/lessons/", "All lessons · a course on training LLMs · Learn", f"{len(lessons)} lessons on how large language models are trained, from tokens and attention to pre-training, post-training and GPUs.", c, image="models")


def minds_page(films):
    mn = ordered(films, "minds")
    shelves = "".join(shelf(t, [f for f in mn if f["theme"] == t]) for t in THEME_ORDER["minds"])
    c = f"""
<section class="head-band minds"><div class="wrap">
  <p class="eyebrow">Minds</p><h1>How minds work</h1>
  <p class="lede">Intelligence is not only something machines have. These films look at how people remember, fear, belong and recover, using the research where it is strong and saying so where it is not.</p>
</div></section>
<div class="wrap">{shelves}
  <section class="shelf"><header><h3>Where machine and mind meet</h3><p>{esc(THEMES["mind-machine"][1])}</p></header><div class="fgrid two">{"".join(film_card(f) for f in ordered(films, "bridge"))}</div></section>
</div>"""
    page("/minds/", "How minds work · psychology films · Learn", "Films on memory, attachment, shame, fear, burnout and emotional regulation: what the research says and what helps.", c, image="minds")


def films_page(films):
    allf = [films[i] for t in ("machines", "minds", "bridge") for i in TRACK_ORDER[t] if i in films]
    cards = "".join(
        f'<div class="fitem" data-track="{f["track"]}" data-theme="{f["theme"]}" data-min="{round(f["duration"] / 60)}" data-text="{esc(plain(f["title"] + " " + f["kicker"] + " " + f["blurb"]).lower())}">{film_card(f)}</div>' for f in allf)
    c = f"""
<section class="head-band"><div class="wrap"><p class="eyebrow">Library</p><h1>All films</h1>
  <p class="lede">{len(allf)} films, {sum(f["duration"] for f in allf) / 3600:.1f} hours. Every film has chapters, a transcript and its sources.</p>
  <div class="filters" id="filters"><button data-f="all" class="on">All</button><button data-f="machines">Models</button><button data-f="minds">Minds</button><button data-f="bridge">Both</button>
  <span class="sp"></span><button data-len="short">Under 8 min</button><button data-len="long">Over 12 min</button></div></div></section>
<section class="wrap block"><div class="fgrid" id="fgrid">{cards}</div><p class="none" id="none" hidden>No films match.</p></section>"""
    page("/films/", "All films · Learn · Renaissance Labs", "Every explainer film from Renaissance Labs on language model training and human minds.", c, image="home")


def related_films(l, films):
    out = []
    for ref in l["films"]:
        fid, _, sid = ref.partition(":")
        fid = re.sub(r"-video$", "", fid)
        f = films.get(fid)
        if not f: continue
        ch = next((c for c in f["chapters"] if c["scene"] == sid), None)
        if not ch: continue
        out.append((f, ch))
    return out


def lesson_page(l, lessons, films):
    ls = list(lessons.values()); idx = ls.index(l)
    prev_, next_ = (ls[idx - 1] if idx else None), (ls[idx + 1] if idx + 1 < len(ls) else None)
    toc = "".join(f'<li><a href="#{i}">{esc(t)}</a></li>' for i, t in l["toc"])
    rf = related_films(l, films)
    watch = ""
    if rf:
        watch = '<aside class="watch"><span class="watch-t">Prefer to watch?</span>' + "".join(
            f'<a href="/films/{f["id"]}/#t={int(c["start"])}"><span class="play">▶</span><b>{esc(c["title"])}</b><span>{esc(f["title"])} · {clock(c["start"])}</span></a>' for f, c in rf) + "</aside>"
    rel = [lessons[r] for r in l["related"] if r in lessons]
    src = ""
    if l["sources"]:
        li = "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)}</a></li>' if u else f"<li>{esc(t)}</li>" for t, u in l["sources"])
        src = f'<section class="sources"><h2 id="sources">Sources and further reading</h2><ul>{li}</ul></section>'
    nav = '<nav class="pn" aria-label="Lessons">' + (
        f'<a class="prev" href="/lessons/{prev_["id"]}/"><span>Previous</span><b>{esc(prev_["title"])}</b></a>' if prev_ else "<span></span>") + (
        f'<a class="next" href="/lessons/{next_["id"]}/"><span>Next</span><b>{esc(next_["title"])}</b></a>' if next_ else "<span></span>") + "</nav>"
    relhtml = ""
    if rel:
        relhtml = '<section class="relmore"><h2>Related lessons</h2><div class="lgrid">' + "".join(lesson_card(r) for r in rel) + "</div></section>"
    c = f"""
<div class="progress" id="progress"><i></i></div>
<article class="lesson" data-lesson="{l["id"]}">
<header class="lesson-h"><div class="wrap">
  <p class="crumb"><a href="/models/">Models</a> · {esc(l.get("part", ""))} · Lesson {l["order"]}</p>
  <h1>{esc(l["title"])}</h1><p class="lede">{esc(l["summary"])}</p>
  <p class="meta"><span>{esc(l["level"])}</span><span>{l["minutes"]} min read</span>{f"<span>{len(rf)} film chapters</span>" if rf else ""}</p>
</div></header>
<div class="wrap lesson-grid">
  <div class="prose">{l["html"]}{watch}{src}</div>
  <aside class="toc" aria-label="On this page"><p>On this page</p><ol>{toc}</ol></aside>
</div>
<div class="wrap">{relhtml}{nav}</div>
</article>"""
    ld = {"@context": "https://schema.org", "@type": "LearningResource", "name": l["title"], "description": l["summary"], "educationalLevel": l["level"],
          "learningResourceType": "lesson", "inLanguage": "en", "isAccessibleForFree": True, "timeRequired": f"PT{l['minutes']}M",
          "isPartOf": {"@type": "Course", "name": "How language models learn", "url": SITE + "/models/"},
          "publisher": {"@type": "Organization", "name": "Renaissance Labs"}, "dateModified": BUILD}
    page(f"/lessons/{l['id']}/", f"{l['title']} · Learn · Renaissance Labs", l["summary"], c, jsonld=ld, image="models",
         extra='<script src="/widgets.js?v=' + ASSETV + '" defer></script>\n<script src="/widgets2.js?v=' + ASSETV + '" defer></script>\n')


def film_page(f, films, lessons):
    order = TRACK_ORDER[f["track"]]
    i = order.index(f["id"]); nxt = [films[x] for x in (order[i + 1:] + order[:i]) if x in films][:3]
    chs = "".join(f'<li><button type="button" data-t="{int(c["start"])}"><span class="ct">{clock(c["start"])}</span><span class="cn">{esc(c["title"])}</span></button></li>' for c in f["chapters"])
    tr = []
    for c in f["chapters"]:
        ln = "".join(f'<p><button type="button" class="ln" data-t="{ts}">{esc(txt)}</button></p>' for ts, txt in c["lines"])
        tr.append(f'<section class="tchap" data-start="{int(c["start"])}" data-end="{int(c["end"])}"><h3><button type="button" data-t="{int(c["start"])}"><span class="ct">{clock(c["start"])}</span> {esc(c["title"])}</button></h3>{ln}</section>')
    take = "".join(f"<li>{esc(t)}</li>" for t in f["takeaways"])
    deeper = [lessons[s] for s in f.get("lessons", []) if s in lessons]
    dh = f'<section class="deeper"><h2>Go deeper</h2><div class="lgrid">{"".join(lesson_card(l) for l in deeper)}</div></section>' if deeper else ""
    src = ""
    if f.get("sources"):
        li = "".join(f'<li><a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["title"])}</a></li>' if s.get("url") else f'<li>{esc(s["title"])}</li>' for s in f["sources"])
        src = f'<section class="sources"><h2>Sources</h2><ul>{li}</ul><p class="fine">Where a source has no link, it is cited from the film\'s research notes. Estimates and unverified claims are labelled in the film.</p></section>'
    yt = CFG.get("youtube", {}).get(f["id"], "")
    yt_attr = f' data-yt="{esc(yt)}"' if yt else ""
    soon = bool(CFG.get("youtube")) and not yt
    if soon:
        yt_attr = ' data-soon="1"'
        player_inner = cover(f)
        miss_t, miss_s = "Coming to YouTube soon", "The chapters and transcript are below. The film will play here once it is uploaded."
    elif yt:
        player_inner = '<div id="yt"></div>'
        miss_t, miss_s = "The video could not be loaded.", f'<a href="https://www.youtube.com/watch?v={esc(yt)}" target="_blank" rel="noopener">Watch it on YouTube</a>'
    else:
        player_inner = f'<video id="video" controls preload="metadata" playsinline><source src="{esc(MEDIA + f["id"] + ".mp4")}" type="video/mp4"></video>'
        miss_t, miss_s = "The video is not available yet.", "It will appear here as soon as it is uploaded."
    note = '<p class="fine">Chapter times for this film are approximate.</p>' if f["approx"] else ""
    if f.get("auto"): note = '<p class="fine">This transcript comes from automatic captions and may contain small errors.</p>' + note
    th = THEME_LABEL[f["theme"]]
    c = f"""
<section class="cinema"><div class="wrap cinema-in">
  <div class="player" id="player" data-film="{f["id"]}" data-duration="{int(f["duration"])}"{yt_attr}>
    {player_inner}
    <div class="player-miss" id="miss"{"" if soon else " hidden"}><b>{miss_t}</b><span>{miss_s}</span></div>
  </div>
  <aside class="chapters" aria-label="Chapters"><p>Chapters</p><ol id="chapters">{chs}</ol></aside>
</div></section>
<article class="wrap film-main">
  <header><p class="crumb"><a href="/{"models" if f["track"] == "machines" else "minds"}/">{"Models" if f["track"] == "machines" else "Minds"}</a> · {esc(th)}</p>
  <h1>{esc(f["title"])}</h1><p class="lede">{esc(f["kicker"])}</p>
  <p class="meta"><span>{mins(f["duration"])}</span><span>{esc(f["level"])}</span><span>{len(f["chapters"])} chapters</span><button type="button" class="share" id="share">Copy link at this time</button></p></header>
  <div class="film-cols"><div>
    <p class="desc">{esc(f["description"])}</p>
    <h2>What to take away</h2><ul class="take">{take}</ul>
    {dh}
    <details class="transcript" id="transcript"><summary><span>Read the transcript</span><small>{sum(len(c["lines"]) for c in f["chapters"])} lines, click any line to jump</small></summary>
      <div class="tbody">{note}{"".join(tr)}</div></details>
    {src}
  </div></div>
  <section class="relmore"><h2>Keep watching</h2><div class="fgrid">{"".join(film_card(x) for x in nxt)}</div></section>
</article>"""
    ld = {"@context": "https://schema.org", "@type": "VideoObject", "name": f["title"], "description": f["description"],
          "thumbnailUrl": f"{SITE}/assets/og/film-{f['id']}.jpg", "uploadDate": f["date"], "duration": f"PT{int(f['duration'] // 60)}M{int(f['duration'] % 60)}S",
          "inLanguage": "en", "isAccessibleForFree": True, "publisher": {"@type": "Organization", "name": "Renaissance Labs", "url": "https://renaissancelabs.eu/"},
          **({"embedUrl": f"https://www.youtube.com/embed/{yt}"} if yt else {}),
          "hasPart": [{"@type": "Clip", "name": ch["title"], "startOffset": int(ch["start"]), "endOffset": int(ch["end"]), "url": f"{SITE}/films/{f['id']}/#t={int(ch['start'])}"} for ch in f["chapters"]]}
    page(f"/films/{f['id']}/", f"{f['title']} · Learn · Renaissance Labs", f["blurb"], c, jsonld=ld, image=f"film-{f['id']}", body_class="film")


def glossary_page(gl, lessons):
    seen = {}
    for term, sent, lid in gl:
        k = term.lower()
        if k in GLOSS_SKIP and k not in GLOSS_DEF: continue
        if k not in seen and lid in lessons: seen[k] = (term[0].upper() + term[1:], GLOSS_DEF.get(k, sent), lid)
    items = sorted(seen.values(), key=lambda x: x[0].lower())
    letters = sorted({x[0][0].upper() for x in items})
    rows = "".join(f'<div class="term" id="{slugify(t)}" data-l="{t[0].upper()}"><dt>{esc(t)}</dt><dd>{esc(s)} <a href="/lessons/{lid}/">{esc(lessons[lid]["title"])}</a></dd></div>' for t, s, lid in items)
    nav = "".join(f'<a href="#az-{x}">{x}</a>' for x in letters)
    body, last = [], None
    for t, s, lid in items:
        L = t[0].upper()
        if L != last: body.append(f'<h2 class="az" id="az-{L}">{L}</h2>'); last = L
        body.append(f'<div class="term" id="{slugify(t)}"><dt>{esc(t)}</dt><dd>{esc(s)} <a href="/lessons/{lid}/">{esc(lessons[lid]["title"])}</a></dd></div>')
    c = f"""
<section class="head-band"><div class="wrap"><p class="eyebrow">Reference</p><h1>Glossary</h1>
  <p class="lede">{len(items)} terms, each defined where it first appears in the course.</p><nav class="azn">{nav}</nav></div></section>
<section class="wrap block"><dl class="gloss">{"".join(body)}</dl></section>"""
    page("/glossary/", "Glossary of LLM training terms · Learn", "Plain-language definitions of the terms used in the course on training large language models.", c, image="models")
    return items


def note_page(n, lessons, films):
    toc = "".join(f'<li><a href="#{i}">{esc(t)}</a></li>' for i, t in n["toc"])
    rf = related_films(n, films)
    watch = ""
    if rf:
        watch = '<aside class="watch"><span class="watch-t">Related film</span>' + "".join(
            f'<a href="/films/{f["id"]}/"><span class="play">\u25b6</span><b>{esc(f["title"])}</b><span>{mins(f["duration"])} · {esc(f["kicker"])}</span></a>' for f, c in rf) + "</aside>"
    rel = [lessons[r] for r in n["related"] if r in lessons]
    relhtml = '<section class="relmore"><h2>Related lessons</h2><div class="lgrid">' + "".join(lesson_card(r) for r in rel) + "</div></section>" if rel else ""
    c = f"""
<div class="progress" id="progress"><i></i></div>
<article class="lesson note" data-lesson="note-{n["id"]}">
<header class="lesson-h note-h"><div class="wrap">
  <p class="crumb"><a href="/notes/">Notes</a> · {"From the labs · " if n.get("lab") else ""}{nice_date(n["date"])}</p>
  {'<p class="draftflag"><b>Draft for review.</b> Not yet reviewed by the lab. Not listed on the site and hidden from search engines.</p>' if n.get("status") == "draft" else ""}
  <h1>{esc(n["title"])}</h1><p class="lede">{esc(n["summary"])}</p>
  <p class="meta"><span>{esc(n.get("lab") or "Renaissance Labs")}</span>{f'<span>by {esc(n["author"])}</span>' if n.get("author") else ""}<span>{n["minutes"]} min read</span></p>
  {tag_row(n["tags"])}
</div></header>
<div class="wrap lesson-grid">
  <div class="prose">{n["html"]}{watch}</div>
  <aside class="toc" aria-label="On this page"><p>On this page</p><ol>{toc}</ol></aside>
</div>
<div class="wrap">{relhtml}</div>
</article>"""
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": n["title"], "description": n["summary"], "datePublished": n["date"],
          "dateModified": n["date"], "inLanguage": "en", "author": {"@type": "Organization", "name": "Renaissance Labs"},
          "publisher": {"@type": "Organization", "name": "Renaissance Labs", "url": "https://renaissancelabs.eu/"},
          "image": f"{SITE}/assets/og/note-{n['id']}.jpg"}
    page(f"/notes/{n['id']}/", f"{n['title']} · Notes · Renaissance Labs", n["summary"], c, jsonld=ld, image=f"note-{n['id']}",
         extra=('<meta name="robots" content="noindex">\n' if n.get("status") == "draft" else "") + ("".join(f'<script src="/{x}.js?v=' + ASSETV + '" defer></script>\n' for x in ("widgets", "widgets2", "widgets3")) if '<div class="widget"' in n["html"] else ""))


def notes_page(notes):
    cards = "".join(note_card(n) for n in notes.values())
    c = f"""
<section class="head-band"><div class="wrap"><p class="eyebrow">Notes</p><h1>Notes from the work</h1>
  <p class="lede">Short essays on the practice of training models: what the papers leave out, and what we learn by running things.</p></div></section>
<section class="wrap block">{topic_strip(notes.values())}<div class="ngrid">{cards}</div></section>"""
    page("/notes/", "Notes from the work · Learn · Renaissance Labs", "Short essays on the practice of training language models.", c, image="home")


def about_page(films, lessons):
    c = f"""
<section class="head-band"><div class="wrap"><p class="eyebrow">About</p><h1>About Learn</h1>
  <p class="lede">A small library from Renaissance Labs on how intelligence is built, in machines and in people.</p></div></section>
<section class="wrap block"><div class="prose narrow">
<h2>What this is</h2>
<p>Learn collects our explainer films and a written course on training large language models. The films are rendered from code: the scenes, narration and captions all come from the scripts that sit behind each one, which is why every film has an exact transcript.</p>
<p>The course is for people who use or build language models and want to understand what happens before the chat window. The minds section is for anyone who is curious about how memory, emotion and relationships work. It is education, not therapy. If something here resonates because you are struggling, a clinician can help in ways a film cannot.</p>
<h2>How we handle sources</h2>
<p>Every film starts from a research dossier. Claims are marked as reported, estimated or unverified. Where a figure comes from a secondary summary, or an estimate is our own arithmetic, the lesson says so in the sentence. If you find an error, tell us and we will correct it and note the change.</p>
<h2>Who makes it</h2>
<p>Renaissance Labs is an independent lab based in Europe working on open models, open data and open evaluation, and on making that work easier to understand. The psychology films are written with a licensed clinical psychologist.</p>
<h2>Related projects</h2>
<ul><li><a href="{ATLAS}/">Open Labs Atlas</a>, a map of independent AI labs committed to open source.</li><li><a href="https://huggingface.co/RenaissanceLabsEU">Renaissance Labs on Hugging Face</a></li><li><a href="https://renaissancelabs.eu/">renaissancelabs.eu</a></li></ul>
<h2>Using the material</h2>
<p>You are welcome to link to any page and to quote briefly with attribution. For reuse beyond that, such as embedding films or republishing lessons, please get in touch first.</p>
</div></section>"""
    page("/about/", "About Learn · Renaissance Labs", "What Learn is, how sources are handled, and who makes it.", c)


def not_found():
    c = '<section class="head-band"><div class="wrap"><p class="eyebrow">404</p><h1>That page has wandered off.</h1><p class="lede">Try the <a href="/models/">course</a>, the <a href="/minds/">minds films</a> or search with the / key.</p></div></section>'
    write("404.html", head("Not found · Learn", "Page not found", "/404.html") + f'<main id="main">{c}</main>' + foot())


# ------------------------------------------------------------------ recipes
def load_recipes():
    out = {}
    for p in sorted(glob.glob("data/recipes/*.json")):
        r = json.load(open(p, encoding="utf-8")); out[r["id"]] = r
    return out


def _n(x): return f"{x:,}"


def _chart(curve, col, lo, hi, label, marks, fmt):
    W, H, L, R, T, B = 560, 210, 44, 14, 14, 30
    X = lambda s: L + (W - L - R) * s / 11263
    Y = lambda v: T + (H - T - B) * (1 - (v - lo) / (hi - lo))
    pts = " ".join(f"{X(p[0]):.1f},{Y(p[col]):.1f}" for p in curve)
    grid = "".join(f'<line x1="{L}" x2="{W-R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/><text x="{L-8}" y="{Y(v)+4:.1f}" text-anchor="end">{fmt(v)}</text>'
                   for v in [lo + (hi - lo) * k / 4 for k in range(5)])
    xt = "".join(f'<text x="{X(s):.1f}" y="{H-8}" text-anchor="middle">{s//1000}k</text>' for s in (0, 3000, 6000, 9000))
    dots = ""
    for s in marks:
        p = min(curve, key=lambda q: abs(q[0] - s))
        dots += f'<circle cx="{X(p[0]):.1f}" cy="{Y(p[col]):.1f}" r="4"/>'
    area = f"{X(curve[0][0]):.1f},{H-B} " + pts + f" {X(curve[-1][0]):.1f},{H-B}"
    return (f'<figure class="rchart"><figcaption>{label}</figcaption><svg viewBox="0 0 {W} {H}" role="img" aria-label="{label} over 11,263 training steps">'
            f'<g class="rgrid">{grid}{xt}</g><polygon class="rarea" points="{area}"/><polyline class="rline" points="{pts}"/><g class="rdots">{dots}</g>'
            f'<text class="rax" x="{W-R}" y="{H-8}" text-anchor="end">step</text></svg></figure>')


def recipe_page(r):
    d, eq, ve = r["data"], r["equipment"], r["verify"]
    colors = ["#c79a3f", "#7b9a8a", "#b5654a", "#5f7396", "#8f7aa3", "#a9a08a"]

    def mix(srcs, total):
        bar = "".join(f'<i style="flex:{s["pairs"]};background:{colors[i % 6]}" title="{esc(s["name"])}: {_n(s["pairs"])}"></i>' for i, s in enumerate(srcs))
        rows = "".join(
            f'<li><span class="sw" style="background:{colors[i % 6]}"></span><div class="rs-main"><b>{esc(s["name"])}</b><code>{esc(s["id"])}</code><span class="rs-note">{esc(s["note"])} · {esc(s["licence"])}</span></div>'
            f'<div class="rs-num"><b>{_n(s["pairs"])}</b><span>{s["pairs"]/total*100:.1f}%</span></div>'
            f'<span class="pin {"ok" if s["pinned"] else "warn"}">{"Pinned" if s["pinned"] else "Not pinned"}</span></li>' for i, s in enumerate(srcs))
        return f'<div class="mixbar" role="img" aria-label="Share of each data source">{bar}</div><ul class="srcs">{rows}</ul>'
    groups = d.get("groups") or [{"sources": d["sources"], "total": d["total"]}]
    mixes = "".join((f'<h3 class="rgh">{esc(g["title"])}</h3><p class="rsub">{esc(g["sub"])}</p>' if g.get("title") else "") + mix(g["sources"], g["total"]) for g in groups)
    ing_sub = d.get("sub") or f'{_n(d["total"])} preference pairs from three sources, plus {_n(d["validation"])} held out for validation. {_n(d["removed"])} pairs (2.9%) were removed in cleaning.'
    langs_html = ""
    if d.get("languages"):
        mx = max(v for _, v in d["languages"])
        langs = "".join(f'<li><span>{c}</span><i style="width:{v/mx*100:.1f}%"></i><em>{v//1000}k</em></li>' for c, v in d["languages"])
        langs_html = f'<details class="more"><summary>Languages in the largest source</summary><ul class="langs">{langs}</ul><p class="fine">Training pairs per language in the translated source. The evaluation covers 36 languages, so most were not in the preference data.</p></details>'
    sums = "".join(f'<tr><td><code>{esc(n)}</code></td><td><code class="hash">{h[:12]}…{h[-6:]}</code><button type="button" class="cp mini" data-copy="{h}" aria-label="Copy fingerprint of {esc(n)}">Copy</button></td></tr>' for n, h in d["checksums"])
    pantry = "".join(f'<div class="kv"><dt>{esc(a)}</dt><dd><code>{esc(b)}</code>{f"<span>{esc(c)}</span>" if c else ""}</dd></div>' for a, b, c in r["pantry"])
    gpu = "".join('<div class="node"><b>Node ' + str(n + 1) + '</b><div class="gpus">' + "<i></i>" * eq["gpus_per_node"] + '</div>' + (f'<span>{eq["cpus"]} CPUs · {eq["ram"]}</span>' if eq.get("cpus") else "") + '</div>' for n in range(eq["nodes"]))
    kv2 = lambda rows: '<dl class="kvs two">' + "".join(f'<div class="kv"><dt>{esc(a)}</dt><dd>{esc(b)}</dd></div>' for a, b in rows) + '</dl>'
    settings = "".join(f'<h3 class="rgh">{esc(g["title"])}</h3>' + kv2(g["rows"]) for g in r["settings_groups"]) if r.get("settings_groups") else kv2(r["settings"])
    steps = ""
    for i, s in enumerate(r["steps"], 1):
        flag = f'<p class="sflag"><b>Check this.</b> {esc(s["flag"])}</p>' if s.get("flag") else ""
        steps += (f'<li class="step" id="step-{i}"><span class="num">{i}</span><div class="sbody"><h3>{esc(s["t"])}</h3><p>{esc(s["d"])}</p>'
                  f'<div class="code"><button type="button" class="cp" data-copy aria-label="Copy commands">Copy</button><pre><code>{esc(s["code"])}</code></pre></div>{flag}</div></li>')
    checks = "".join(f'<li><b>{esc(a)}</b><span>{esc(b)}</span></li>' for a, b, _ in ve["checks"])
    fin = ve.get("final")
    mets = ve.get("metrics") or [("Held-out accuracy", f'{fin["accuracy"]:.3f}'), ("Reward margin", f'{fin["margin"]:.2f}'), ("Held-out loss", f'{fin["loss"]:.3f}'), ("Held-out pairs", _n(fin["pairs"]))]
    metrics = "".join(f'<div class="met"><b>{esc(str(v))}</b><span>{esc(k)}</span></div>' for k, v in mets)
    charts = ""
    if ve.get("curve"):
        charts = '<div class="charts">' + (_chart(ve["curve"], 1, 0.2, 0.7, "Training loss", (1000, 9000, 11263), lambda v: f"{v:.2f}") +
                  _chart(ve["curve"], 2, 0.5, 0.9, "Batch accuracy", (1000, 9000, 11263), lambda v: f"{v*100:.0f}%")) + '</div>'
    gaps = "".join(f"<li>{esc(g)}</li>" for g in r["gaps"])
    files = "".join(f'<a href="{r["repo_files"]}{esc(f)}"><b>{esc(f)}</b><span>{esc(dsc)}</span></a>' for f, dsc in r["files"])
    glance = "".join(f'<div class="gl"><span>{esc(g["k"])}</span><b>{esc(g["v"])}</b><em>{esc(g["u"])}</em></div>' for g in r["glance"])
    sb = esc(r["sbatch"])
    toc = [("ingredients", "Ingredients"), ("pantry", "Pinned inputs"), ("equipment", "Equipment"), ("method", "Method"), ("settings", "Settings"), ("check", "What you should see"), ("gaps", "Known gaps"), ("variants", "Variants"), ("files", "Original files")]
    tochtml = "".join(f'<li><a href="#{i}">{t}</a></li>' for i, t in toc)
    c = f"""
<article class="recipe" data-lesson="recipe-{r["id"]}">
<header class="rhead"><div class="wrap">
  <p class="crumb"><a href="/recipes/">Recipes</a> · {esc(r["stage"])}</p>
  <h1>{esc(r["title"])}</h1>
  <p class="lede">{esc(r["lede"])}</p>
  <p class="rby"><span>From <b>{esc(r["lab"])}</b></span><span>Recipe by {esc(r["author"])}</span><span class="rstatus"><i></i>{esc(r["status"])}</span></p>
  {tag_row(tag_list(r.get("tags")))}
  <div class="glance">{glance}</div>
  <div class="rcta"><a class="btn" href="{r["checkpoint"]}">Open the checkpoint</a><a class="btn ghost" href="#method">Jump to the method</a><button type="button" class="btn ghost" onclick="window.print()">Print this card</button></div>
</div></header>
<div class="wrap rgrid2">
<div class="rmain">
<section id="ingredients" class="rsec"><h2><span>1</span>Ingredients</h2><p class="rsub">{esc(ing_sub)}</p>
  {mixes}
  {langs_html}
  <details class="more"><summary>{esc(d.get("checksums_title", "Fingerprints of the six staged files (SHA-256)"))}</summary><table class="hashes">{sums}</table></details>
</section>
<section id="pantry" class="rsec"><h2><span>2</span>Pinned inputs</h2><p class="rsub">Everything that must match for a faithful rerun.</p><dl class="kvs">{pantry}</dl></section>
<section id="equipment" class="rsec"><h2><span>3</span>Equipment</h2><p class="rsub">{esc(eq["sub"]) if eq.get("sub") else f'{eq["nodes"]} nodes with {eq["gpus_per_node"]} GPUs each ({esc(eq["gpu"])}). {esc(eq["wall"])} of wall time, {esc(eq["gcd_hours"])} GCD-hours. {esc(eq["note"])}'}</p><div class="nodes">{gpu}</div></section>
<section id="method" class="rsec"><h2><span>4</span>Method</h2><p class="rsub">Paths in angle brackets are yours to fill in. Account IDs and personal paths have been removed.</p><ol class="steps">{steps}</ol>
  <details class="more" open><summary>{esc(r.get("sbatch_title", "The launch script, with placeholders"))}</summary><div class="code"><button type="button" class="cp" data-copy aria-label="Copy launch script">Copy</button><pre><code>{sb}</code></pre></div></details>
</section>
<section id="settings" class="rsec"><h2><span>5</span>Settings</h2>{settings}</section>
<section id="check" class="rsec"><h2><span>6</span>What you should see</h2><p class="rsub">Numbers from the original run, so you can tell early whether yours is on track.</p>
  <ul class="checks">{checks}</ul>{charts}<div class="mets">{metrics}</div><p class="fine">{esc(ve["note"])}</p></section>
<section id="gaps" class="rsec"><h2><span>7</span>Known gaps</h2><p class="rsub">What stands between this card and an exact copy of the run.</p><ul class="gaps">{gaps}</ul></section>
<section id="variants" class="rsec"><h2><span>8</span>Variants</h2>
  <div class="empty"><b>No variants yet.</b><p>Reproduced it? Changed something? Fixed a problem or added a capability? Report it and it appears here, linked to this recipe.</p>
  <a class="btn ghost" href="https://github.com/RenaissanceLabs-EU/learn/issues/new?title=Recipe%20variant%3A%20{r["id"]}">Report a variant</a></div></section>
<section id="files" class="rsec"><h2><span>9</span>Original files</h2><p class="rsub">{esc(r.get("files_sub", "The frozen files from the run are the authority. They contain the original cluster paths."))}</p><div class="rfiles">{files}</div>
  <p class="fine">Background: <a href="{r["related_note"]}">{esc(r.get("related_note_title", "How models learned to prefer"))}</a>. Machine-readable: <a href="/data/recipes/{r["id"]}.json">this recipe as JSON</a>.</p></section>
</div>
<aside class="toc rtoc" aria-label="On this page"><p>On this page</p><ol>{tochtml}</ol></aside>
</div></article>"""
    ld = {"@context": "https://schema.org", "@type": "HowTo", "name": r["title"], "description": r["lede"],
          "step": [{"@type": "HowToStep", "name": s["t"], "text": s["d"]} for s in r["steps"]],
          "author": {"@type": "Person", "name": r["author"]}, "datePublished": r["date"]}
    page(f"/recipes/{r['id']}/", f"{r['title']} · Recipes · Renaissance Labs", r["lede"], c, jsonld=ld, image="home")


def recipe_card(r):
    return (f'<a class="rcard" href="/recipes/{r["id"]}/"><span class="chip">{esc(r["stage"])} · {esc(r["lab"])}</span><b>{esc(r["title"])}</b>'
            f'<span>{esc(r["lede"])}</span><span class="rmeta">{" · ".join(esc(g["v"] + " " + g["u"]) for g in r["glance"][1:])}</span></a>')


def topic_strip(items):
    seen = []
    for x in items:
        for t in tag_list(x.get("tags")):
            if t not in seen: seen.append(t)
    return '<div class="topics"><span>Browse by topic</span>' + "".join(f'<a class="tag" href="/tags/{t}/">{esc(tag_label(t))}</a>' for t in seen) + '<a class="tag all" href="/tags/">All topics</a></div>' if seen else ""


def tag_pages(lessons, notes, recipes):
    by = {}
    for kind, items in (("recipes", recipes), ("notes", notes), ("lessons", lessons)):
        for x in items.values():
            for t in tag_list(x.get("tags")): by.setdefault(t, {"recipes": [], "notes": [], "lessons": []})[kind].append(x)
    order = sorted(by, key=lambda t: (-sum(len(v) for v in by[t].values()), tag_label(t)))
    def count(t):
        parts = [(len(by[t][k]), w) for k, w in (("recipes", "recipe"), ("notes", "note"), ("lessons", "lesson")) if by[t][k]]
        return " · ".join(f'{c} {w}{"s" if c != 1 else ""}' for c, w in parts)
    cards = "".join(f'<a class="ncard tcard" href="/tags/{t}/"><b>{esc(tag_label(t))}</b><span>{esc(TAGS.get(t, ("", ""))[1])}</span><span class="chip">{count(t)}</span></a>' for t in order)
    page("/tags/", "Topics · Learn · Renaissance Labs", "Browse recipes, notes and lessons by topic.", f"""
<section class="head-band"><div class="wrap"><p class="eyebrow">Topics</p><h1>Browse by topic</h1>
  <p class="lede">Every recipe, note and lesson on one subject, in one place.</p></div></section>
<section class="wrap block"><div class="ngrid">{cards}</div></section>""", image="home")
    for t in order:
        g = by[t]; desc = TAGS.get(t, ("", ""))[1]
        secs = ""
        if g["recipes"]: secs += '<section class="tsec"><h2>Recipes</h2><div class="ngrid">' + "".join(recipe_card(r) for r in g["recipes"]) + "</div></section>"
        if g["notes"]: secs += '<section class="tsec"><h2>Notes</h2><div class="ngrid">' + "".join(note_card(x) for x in g["notes"]) + "</div></section>"
        if g["lessons"]: secs += '<section class="tsec"><h2>Lessons</h2><div class="lgrid">' + "".join(lesson_card(x) for x in g["lessons"]) + "</div></section>"
        others = "".join(f'<a class="tag" href="/tags/{o}/">{esc(tag_label(o))}</a>' for o in order if o != t)
        page(f"/tags/{t}/", f"{tag_label(t)} · Topics · Renaissance Labs", desc or f"Recipes, notes and lessons on {tag_label(t).lower()}.", f"""
<section class="head-band"><div class="wrap"><p class="eyebrow"><a href="/tags/">Topics</a></p><h1>{esc(tag_label(t))}</h1>
  <p class="lede">{esc(desc)}</p><p class="meta"><span>{count(t)}</span></p></div></section>
<div class="wrap block">{secs}<div class="topics more"><span>Other topics</span>{others}</div></div>""", image="home")
    return order


def recipes_page(recipes):
    cards = "".join(
recipe_card(r) for r in recipes.values())
    c = f"""<section class="wrap block"><header class="sec-h"><p class="eyebrow">Recipes</p><h1>Training runs you can reproduce</h1>
<p class="lede">Each recipe is a card: the data, the compute, the settings and the launch script, with what you should see along the way. Run one, change one, and report what happened.</p></header>
{topic_strip(recipes.values())}<div class="ngrid">{cards}</div></section>"""
    page("/recipes/", "Recipes · Reproducible training runs · Renaissance Labs", "Reproducible training runs as cards: data, compute, settings, launch scripts and expected results.", c, image="home")


def machine_files(films, lessons, gloss, notes, recipes=None, tags=()):
    urls = ["/", "/models/", "/lessons/", "/minds/", "/films/", "/glossary/", "/about/", "/notes/"] + [f"/notes/{i}/" for i in notes] + ["/recipes/"] + [f"/recipes/{i}/" for i in (recipes or {})] + ["/tags/"] + [f"/tags/{t}/" for t in tags] + [f"/lessons/{i}/" for i in lessons] + [f"/films/{i}/" for i in films]
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
          "".join(f"<url><loc>{SITE}{u}</loc><lastmod>{BUILD}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    write("CNAME", "learn.renaissancelabs.eu")
    write(".nojekyll", "")
    lines = ["# Renaissance Labs · Learn", "", "> Films and lessons on how language models are trained and how human minds work. Free, sourced, in plain language.", "", "## Course"]
    lines += [f"- [{l['title']}]({SITE}/lessons/{i}/): {l['summary']}" for i, l in lessons.items()]
    lines += ["", "## Notes"] + [f"- [{n['title']}]({SITE}/notes/{i}/): {n['summary']}" for i, n in notes.items()]
    lines += ["", "## Recipes"] + [f"- [{r['title']}]({SITE}/recipes/{i}/): {r['lede']}" for i, r in (recipes or {}).items()]
    lines += ["", "## Topics"] + [f"- [{tag_label(t)}]({SITE}/tags/{t}/): {TAGS.get(t, ('', ''))[1]}" for t in tags]
    lines += ["", "## Films"] + [f"- [{f['title']}]({SITE}/films/{i}/): {f['blurb']}" for i, f in films.items()]
    write("llms.txt", "\n".join(lines) + "\n")
    idx = []
    for i, l in lessons.items(): idx.append({"t": "Lesson", "title": l["title"], "url": f"/lessons/{i}/", "s": l["summary"], "x": l["text"][:900].lower()})
    for i, f in films.items():
        idx.append({"t": "Film", "title": f["title"], "url": f"/films/{i}/", "s": f["blurb"],
                    "x": plain(" ".join([f["kicker"], f["description"]] + f["takeaways"] + [c["title"] for c in f["chapters"]])).lower()})
    for i, n in notes.items(): idx.append({"t": "Note", "title": n["title"], "url": f"/notes/{i}/", "s": n["summary"], "x": n["text"][:900].lower()})
    for i, r in (recipes or {}).items(): idx.append({"t": "Recipe", "title": r["title"], "url": f"/recipes/{i}/", "s": r["lede"], "x": (r["title"] + " " + r["lede"] + " " + " ".join(x["name"] for g in (r["data"].get("groups") or [r["data"]]) for x in g["sources"])).lower()})
    for t in tags: idx.append({"t": "Topic", "title": tag_label(t), "url": f"/tags/{t}/", "s": TAGS.get(t, ("", ""))[1], "x": tag_label(t).lower()})
    for term, sent, lid in gloss: idx.append({"t": "Term", "title": term, "url": f"/glossary/#{slugify(term)}", "s": sent[:160], "x": sent.lower()})
    write("search.json", json.dumps(idx, ensure_ascii=False, separators=(",", ":")))


def validate(films, lessons):
    bad = []
    for l in lessons.values():
        n = len(related_films(l, films))
        if n != len(l["films"]): bad.append(f"{l['id']}: {len(l['films']) - n} film ref(s) unresolved ({l['films']})")
        for r in l["related"]:
            if r not in lessons: bad.append(f"{l['id']}: related lesson {r} missing")
        for m in re.finditer(r'href="(/lessons/[^"/#]+)/', l["html"]):
            if m.group(1)[9:] not in lessons: bad.append(f"{l['id']}: link to missing lesson {m.group(1)}")
    for f in films.values():
        for sl in f.get("lessons", []):
            if sl not in lessons: bad.append(f"film {f['id']}: lesson {sl} missing")
    for b in bad: print("WARN", b)
    return bad


def main():
    films = load_films(); lessons, gl = load_lessons(); all_notes = load_notes()
    notes = {k: v for k, v in all_notes.items() if v.get("status") != "draft"}
    validate(films, lessons)
    missing = [x for ids in TRACK_ORDER.values() for x in ids if x not in films and x not in CFG.get("hidden", [])]
    if missing: print("films missing:", missing)
    recipes = load_recipes()
    for d in ("lessons", "films", "notes", "recipes", "tags"): shutil.rmtree(d, ignore_errors=True)
    home(films, lessons, notes); models_page(films, lessons); lessons_page(lessons); minds_page(films); films_page(films)
    for l in lessons.values(): lesson_page(l, lessons, films)
    for f in films.values(): film_page(f, films, lessons)
    notes_page(notes); recipes_page(recipes)
    for r in recipes.values(): recipe_page(r)
    for n in all_notes.values(): note_page(n, lessons, films)
    items = glossary_page(gl, lessons); about_page(films, lessons); not_found()
    tags = tag_pages(lessons, notes, recipes)
    machine_files(films, lessons, [(a, b, c) for a, b, c in ((i[0], i[1], i[2]) for i in items)], notes, recipes, tags)
    print(f"built {len(films)} films, {len(notes)} notes, {len(lessons)} lessons, {len(items)} terms")


if __name__ == "__main__":
    main()
