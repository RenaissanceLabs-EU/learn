"""Capability pages: /capabilities/ (map of what goes into a model) and /capabilities/<id>/.

Imported by build.py, which passes itself in as `B` so this module can use its helpers (esc, page, cards).
Data: data/capabilities.json. Recipes point at capabilities through their `effects` field.
"""
import json

PRE = ["#3f6f63", "#4f7d70", "#5f8a7a", "#6f9a8a", "#7ba596", "#86ad9f"]
POST = ["#9a7a48", "#b0893f", "#c79a3f", "#c2824a", "#b5654a", "#a8573f"]
HALF = {0: 0.7, 1: 3, 2: 7, 3: 12}          # ribbon half-width per stage weight
STATE = {"improved": "Improved", "mixed": "Mixed", "held": "Held steady", "worse": "Got worse", "trained": "Trained, not measured"}
GROUP = {}   # family id -> name, filled by load()
FAMS = []
SHORT = []
ISSUE = "https://github.com/RenaissanceLabs-EU/learn/issues/new?title="


def load():
    d = json.load(open("data/capabilities.json", encoding="utf-8"))
    caps = d["capabilities"]
    FAMS[:] = d["families"]; SHORT[:] = d.get("stages_short", d["stages"])
    GROUP.clear(); GROUP.update({f["id"]: f["name"] for f in FAMS})
    col = {f["id"]: f["color"] for f in FAMS}
    for c in caps: c["color"] = col[c["family"]]
    order = [f["id"] for f in FAMS]
    caps.sort(key=lambda c: order.index(c["family"]))   # stable: keeps the file's order inside a family
    return d["stages"], caps


def recipes_for(c, recipes):
    return [(r, r["effects"][c["id"]]) for r in recipes.values() if c["id"] in r.get("effects", {})]


def meter(c, stages, big=False):
    bars = "".join(f'<i class="w{w}" style="--c:{c["color"]}" title="{stages[i]}: {["not shaped here", "a little", "some", "a lot"][w]}"></i>' for i, w in enumerate(c["stages"]))
    if not big: return f'<span class="cmeter" aria-hidden="true">{bars}</span>'
    cols = "".join(f'<div class="sm-col"><div class="sm-bar"><i class="w{w}" style="--c:{c["color"]}"></i></div><b>{SHORT[i]}</b><span>{["Not here", "A little", "Some", "Most"][w]}</span></div>' for i, w in enumerate(c["stages"]))
    return f'<div class="smeter">{cols}</div>'


def ribbons(caps, stages, esc):
    """The hero figure: one ribbon per capability, flowing through the four training stages. Width = how much a stage shapes it."""
    W, X0, XS, X1, ROW, TOP, GAP = 1120, 318, [366, 510, 654, 798, 942, 1076], 1108, 31, 96, 42
    H = TOP + ROW * len(caps) + GAP * (len(FAMS) - 1) + 20
    out = [f'<svg class="capviz" viewBox="0 0 {W} {H}" role="img" aria-label="Capabilities as ribbons across the stages of building a model. A wider ribbon means the stage shapes the capability more.">']
    for i, s in enumerate(stages):
        out.append(f'<line class="cv-guide" x1="{XS[i]}" y1="{TOP - 30}" x2="{XS[i]}" y2="{H - 12}"/>')
        out.append(f'<text class="cv-num" x="{XS[i]}" y="26" text-anchor="middle">0{i + 1}</text><text class="cv-stage" x="{XS[i]}" y="48" text-anchor="middle">{esc(SHORT[i])}</text>')
    y, last = TOP, None
    for n, c in enumerate(caps):
        if c["family"] != last:
            if last is not None: y += GAP
            out.append(f'<text class="cv-group" x="0" y="{y - 14}">{GROUP[c["family"]]}</text>')
            last = c["family"]
        cy = y + ROW / 2
        hw = [HALF[w] for w in c["stages"]]
        top = f'M{X0},{cy - hw[0]:.1f} L{XS[0]},{cy - hw[0]:.1f}'
        bot = f'L{X1},{cy + hw[-1]:.1f} L{XS[-1]},{cy + hw[-1]:.1f}'
        for i in range(len(XS) - 1):
            mx = (XS[i] + XS[i + 1]) / 2
            top += f' C{mx},{cy - hw[i]:.1f} {mx},{cy - hw[i + 1]:.1f} {XS[i + 1]},{cy - hw[i + 1]:.1f}'
        for i in range(len(XS) - 2, -1, -1):
            mx = (XS[i] + XS[i + 1]) / 2
            bot += f' C{mx},{cy + hw[i + 1]:.1f} {mx},{cy + hw[i]:.1f} {XS[i]},{cy + hw[i]:.1f}'
        d = f'{top} L{X1},{cy - hw[-1]:.1f} {bot} L{X0},{cy + hw[0]:.1f} Z'
        dots = "".join(f'<circle cx="{XS[i]}" cy="{cy}" r="{1.8 + w * 0.75:.1f}"/>' for i, w in enumerate(c["stages"]) if w)
        out.append(f'<a href="/capabilities/{c["id"]}/" class="cv-row" style="--c:{c["color"]};--d:{n * 55}ms"><title>{esc(c["name"])}: {esc(c["one"])}</title>'
                   f'<rect class="cv-hit" x="0" y="{y}" width="{W}" height="{ROW}"/><text class="cv-name" x="0" y="{cy + 6}">{esc(c["name"])}</text>'
                   f'<path class="cv-rib" d="{d}"/><g class="cv-dots">{dots}</g></a>')
        y += ROW
    out.append("</svg>")
    return "".join(out)


def effect_map(caps, recipes, esc):
    if not recipes: return ""
    head = "".join(f'<th><a href="/capabilities/{c["id"]}/"><span>{esc(c["name"])}</span></a></th>' for c in caps)
    rows = ""
    for r in recipes.values():
        cells = ""
        for c in caps:
            e = r.get("effects", {}).get(c["id"])
            cells += (f'<td><span class="fx {e[0]}" tabindex="0"><span class="fx-tip"><b>{STATE[e[0]]}</b>{esc(e[1])}</span></span></td>' if e
                      else '<td><span class="fx none" title="Not measured"></span></td>')
        rows += f'<tr><th><a href="/recipes/{r["id"]}/">{esc(r["title"])}</a><span>{esc(r["lab"])}</span></th>{cells}</tr>'
    legend = "".join(f'<span><i class="fx {k}"></i>{v}</span>' for k, v in STATE.items()) + '<span><i class="fx none"></i>Not measured</span>'
    return f'<div class="fxwrap"><table class="fxmap"><thead><tr><th></th>{head}</tr></thead><tbody>{rows}</tbody></table></div><p class="fxlegend">{legend}</p>'


def counts(c, recipes):
    n = [(len(recipes_for(c, recipes)), "recipe"), (len(c.get("findings", [])), "finding"), (len(c.get("wanted", [])), "wanted")]
    return " · ".join(f'{k} {w}{"s" if k != 1 and w != "wanted" else ""}' for k, w in n if k)


def index(B, stages, caps, recipes):
    esc = B.esc
    def card(c):
        return (f'<a class="ccard" href="/capabilities/{c["id"]}/" style="--c:{c["color"]}"><span class="ccard-top">{meter(c, stages)}</span><b>{esc(c["name"])}</b>'
                f'<span>{esc(c["one"])}</span><span class="chip">{counts(c, recipes)}</span></a>')
    groups = "".join(
        f'<section class="cgroup" id="{f["id"]}" style="--c:{f["color"]}"><header><p class="eyebrow">{esc(f["name"])}</p><p>{esc(f["about"])}</p></header><div class="cgrid">' +
        "".join(card(c) for c in caps if c["family"] == f["id"]) + "</div></section>" for f in FAMS)
    wanted = "".join(f'<li><a href="/capabilities/{c["id"]}/#wanted" style="--c:{c["color"]}">{esc(c["name"])}</a><span>{esc(w)}</span></li>' for c in caps for w in c.get("wanted", []))
    body = f"""
<section class="head-band caphead"><div class="wrap"><p class="eyebrow">Capabilities</p><h1>What goes into a model</h1>
  <p class="lede">A language model is a bundle of separate abilities. Some are fixed when the model is designed. Some are learned from raw text in pre-training. Others are taught afterwards, one at a time, or decided when the model is served. For each one: how it is measured, what data it needs, which recipes improve it, and what is still missing.</p>
  <p class="capcount"><b>{len(caps)}</b> capabilities in <b>{len(FAMS)}</b> families{"".join(f'<a href="#{f["id"]}" style="--c:{f["color"]}">{esc(f["name"])}</a>' for f in FAMS)}</p></div></section>
<section class="wrap block capfig"><figure>{ribbons(caps, stages, esc)}
  <figcaption>Each ribbon is one capability, flowing left to right from the design of the model, through pre-training and the three kinds of post-training, to deployment. Where a ribbon is wide, that stage does most of the shaping. This is an editorial sketch, not a measurement. Select a ribbon to open the capability.</figcaption></figure></section>
<div class="wrap block">{groups}</div>
<section class="wrap block capsec"><header><p class="eyebrow">Capability map</p><h2>What each recipe changed</h2>
  <p>A recipe is aimed at one capability, and it moves others too. Most cells are empty because nobody measured them, and that is worth knowing before you reuse a recipe.</p></header>{effect_map(caps, recipes, esc)}</section>
<section class="wrap block capsec"><header><p class="eyebrow">Wanted</p><h2>What nobody has published yet</h2>
  <p>Open requests, one capability at a time. If your lab has one of these, a recipe, a dataset or a short finding answers it.</p></header>
  <ul class="wantlist">{wanted}</ul>
  <p class="fine capnote">The list follows how the field already splits things up: benchmark suites such as <a href="https://arxiv.org/abs/2211.09110">HELM</a> report accuracy next to calibration, robustness, fairness, bias, toxicity and efficiency, and model cards list languages, context length, modalities and tool use. It is not complete, and the family a capability sits in is a judgement.</p>
  <p class="capcta"><a class="btn" href="{ISSUE}Capability%3A%20">Add a capability, a finding or a recipe</a><a class="btn ghost" href="/data/capabilities.json">This map as JSON</a></p></section>"""
    B.page("/capabilities/", "Capabilities · What goes into a language model · Renaissance Labs",
           "The abilities that make up a language model, from pre-training to post-training: how each is measured, what data it needs and which recipes improve it.", body, image="home")


def cap_page(B, stages, caps, c, recipes, notes, lessons):
    esc = B.esc
    def rows(items):
        return '<ul class="clist">' + "".join(
            f'<li><b>{f"<a href={chr(34)}{esc(u)}{chr(34)}>{esc(n)}</a>" if u else esc(n)}</b><span>{esc(d)}</span></li>' for n, d, u in items) + "</ul>"
    def empty(what, verb):
        return (f'<div class="empty"><b>No {what} yet.</b><p>If your lab has {verb}, add it and it appears here.</p>'
                f'<a class="btn ghost" href="{ISSUE}Capability%3A%20{c["id"]}">Add one</a></div>')
    secs = []
    if c.get("example"):
        e = c["example"]
        secs.append(("practice", "In practice", f'<p class="rsub">{esc(e["q"])}</p><div class="cex"><div class="bad"><span>Without it</span><p>{esc(e["bad"])}</p></div><div class="good"><span>With it</span><p>{esc(e["good"])}</p></div></div>'))
    secs.append(("origin", "Where it comes from", f'{meter(c, stages, big=True)}<div class="cwhere"><div><span>Design and pre-training</span><p>{esc(c["pre"])}</p></div><div><span>Post-training and deployment</span><p>{esc(c["post"])}</p></div></div>'))
    secs.append(("measure", "How to measure it", rows(c["measure"])))
    secs.append(("datasets", "Common datasets and methods", rows(c["datasets"]) if c.get("datasets") else empty("datasets listed", "a dataset for this")))
    rf = recipes_for(c, recipes)
    rhtml = "".join(f'<a class="crecipe" href="/recipes/{r["id"]}/"><span class="fxtag {e[0]}">{STATE[e[0]]}</span><b>{esc(r["title"])}</b><span>{esc(e[1])}</span><em>{esc(r["lab"])} · {esc(r["status"])}</em></a>' for r, e in rf)
    secs.append(("recipes", "Recipes", rhtml if rf else empty("recipes", "a training run that improves this")))
    if c.get("costs"):
        secs.append(("costs", "What it costs", '<ul class="gaps">' + "".join(f"<li>{esc(x)}</li>" for x in c["costs"]) + "</ul>"))
    fhtml = '<ul class="cfind">' + "".join(f'<li><a href="{esc(u)}">{esc(t)}</a><span>{esc(src)}</span></li>' for t, src, u in c.get("findings", [])) + "</ul>"
    secs.append(("findings", "Findings", fhtml if c.get("findings") else empty("findings", "a result on this, positive or negative")))
    secs.append(("wanted", "Wanted", '<ul class="cwant">' + "".join(f'<li><span>{esc(w)}</span><a href="{ISSUE}Wanted%3A%20{c["id"]}">I have this</a></li>' for w in c.get("wanted", [])) + "</ul>"))
    if c.get("labs"):
        secs.append(("labs", "Who works on it", '<p class="clabs">' + "".join(f'<a class="tag" href="{esc(u)}">{esc(n)}</a>' if u else f'<span class="tag plain">{esc(n)}</span>' for n, u in c["labs"]) +
                     '</p><p class="fine">Labs and people whose published work is cited on this page. Not a complete list.</p>'))
    more = ""
    ns = [notes[n] for n in c.get("notes", []) if n in notes]; ls = [lessons[x] for x in c.get("lessons", []) if x in lessons]
    if ns: more += '<div class="ngrid">' + "".join(B.note_card(n) for n in ns) + "</div>"
    if ls: more += '<div class="lgrid">' + "".join(B.lesson_card(x) for x in ls) + "</div>"
    if more: secs.append(("read", "Read more", more))
    body = "".join(f'<section id="{i}" class="rsec"><h2><span>{k}</span>{t}</h2>{h}</section>' for k, (i, t, h) in enumerate(secs, 1))
    toc = "".join(f'<li><a href="#{i}">{t}</a></li>' for i, t, _ in secs)
    idx = caps.index(c); prev_, next_ = caps[idx - 1], caps[(idx + 1) % len(caps)]
    html = f"""
<article class="recipe cap" style="--c:{c["color"]}">
<header class="rhead"><div class="wrap">
  <p class="crumb"><a href="/capabilities/">Capabilities</a> · {GROUP[c["family"]]}</p>
  <h1>{esc(c["name"])}</h1>
  <p class="lede">{esc(c["one"])}</p>
</div></header>
<div class="wrap rgrid2"><div class="rmain">{body}
  <nav class="pn" aria-label="Capabilities"><a class="prev" href="/capabilities/{prev_["id"]}/"><span>Previous</span><b>{esc(prev_["name"])}</b></a><a class="next" href="/capabilities/{next_["id"]}/"><span>Next</span><b>{esc(next_["name"])}</b></a></nav>
</div><aside class="toc rtoc" aria-label="On this page"><p>On this page</p><ol>{toc}</ol></aside></div></article>"""
    ld = {"@context": "https://schema.org", "@type": "DefinedTerm", "name": c["name"], "description": c["one"], "inDefinedTermSet": f"{B.SITE}/capabilities/"}
    B.page(f"/capabilities/{c['id']}/", f"{c['name']} · Capabilities · Renaissance Labs", c["one"], html, jsonld=ld, image="home")


def chips(B, caps, note=None, effects=None):
    """Capability chips for a note (by its id) or a recipe (by its `effects`)."""
    hit = [c for c in caps if (note is not None and note in c.get("notes", [])) or (effects is not None and effects.get(c["id"], [""])[0] == "improved")]
    return ('<p class="tags caps"><span>Capability</span>' + "".join(f'<a class="tag cap" href="/capabilities/{c["id"]}/" style="--c:{c["color"]}">{B.esc(c["name"])}</a>' for c in hit) + "</p>") if hit else ""
