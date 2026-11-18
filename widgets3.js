/* Interactive widgets, part 3: preference tuning and alignment (used by the note "How models learned to prefer").
   Numbers marked as card or benchmark results come from the model card of birgermoell/oellm-9b-threeway-dpo-full-v1.
   Everything else is a labelled illustration with invented values. */
(function () {
  'use strict';
  var LW = window.LW; if (!LW) return;
  var W = LW.W, $ = LW.$, $$ = LW.$$, el = LW.el, esc = LW.esc;

  function css(v, d) { try { return getComputedStyle(document.documentElement).getPropertyValue(v).trim() || d; } catch (e) { return d; } }
  function colors() { return { ink: css('--ink', '#1c1a17'), soft: css('--ink-soft', '#625b52'), faint: css('--ink-faint', '#958c80'), rule: css('--rule', '#e6dfd1'), gold: css('--gold', '#9a7a48'), bright: css('--gold-bright', '#c79a3f'), deep: css('--paper-deep', '#f6f0e2') }; }
  function segHtml(items, cur) { return items.map(function (x, i) { return '<button type="button" data-i="' + i + '"' + (i === cur ? ' class="on"' : '') + '>' + esc(x) + '</button>'; }).join(''); }
  function bindSeg(box, f) { box.addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b || !box.contains(b)) return; $$('button', box).forEach(function (x) { x.classList.toggle('on', x === b); }); f(+b.dataset.i); }); }
  function sig(x) { return 1 / (1 + Math.exp(-x)); }

  /* ---------- be the annotator ---------- */
  W.annotator = function (root) {
    var F = ['Substance', 'Flattery', 'Caution', 'Length'];
    var P = [
      { q: '"I wrote this poem. What do you think?"', a: ['Names two weak lines and suggests fixes.', [.9, .1, .2, .6]], b: ['"This is wonderful. You clearly have real talent."', [.1, 1, 0, .2]] },
      { q: '"Can I take ibuprofen with my blood pressure pills?"', a: ['"Yes, that is fine."', [.1, .5, 0, .1]], b: ['Explains the interaction risk and suggests asking a pharmacist.', [.8, 0, .9, .6]] },
      { q: '"My business plan cannot fail, right?"', a: ['"Absolutely. It sounds like a sure thing!"', [.1, 1, 0, .3]], b: ['Lists the three biggest risks and how to test them.', [.9, 0, .5, .7]] },
      { q: '"What causes inflation?"', a: ['A long, padded answer that repeats itself.', [.3, .2, .2, 1]], b: ['A short, accurate answer with one example.', [.8, 0, .1, .3]] },
      { q: '"Is my essay ready to submit?"', a: ['"It is perfect. Submit it!"', [0, 1, 0, .1]], b: ['"Mostly. The conclusion repeats the intro; fix that first."', [.7, .1, .3, .3]] },
      { q: '"Explain how vaccines work."', a: ['Clear explanation with a short note on side effects.', [.9, 0, .4, .6]], b: ['The same explanation, no caveats, very confident tone.', [.9, .3, 0, .6]] },
      { q: '"Should I quit my job tomorrow?"', a: ['"Follow your dreams! You deserve it."', [.1, 1, 0, .2]], b: ['Asks about savings and alternatives before advising.', [.8, 0, .6, .6]] },
      { q: '"How do I reverse a list in Python?"', a: ['One line of code and a one-sentence explanation.', [.9, 0, 0, .2]], b: ['The same code buried in four paragraphs.', [.6, 0, .1, 1]] }
    ];
    var C = [
      { t: 'Warm and encouraging: "Great idea, go for it!"', x: [.1, 1, 0, .3] },
      { t: 'Balanced: benefits, risks and what to check first.', x: [.8, .1, .5, .6] },
      { t: 'A very long answer with a warning on every line.', x: [.5, 0, 1, 1] },
      { t: 'Short and blunt: "Probably not. Here is why."', x: [.7, 0, .1, .2] }
    ];
    var w, n, node = el('<div><h4>Be the annotator</h4>' +
      '<p class="wd-lead">Reward models are trained on choices like these. Pick the answer you would prefer. A tiny reward model learns from each pick which features of an answer people reward. This one only sees four features, so the lesson is easy to read.</p>' +
      '<div class="wd-q"></div><div class="wd-pair"></div>' +
      '<div class="wd-btns"><button type="button" class="wd-btn ghost" data-a="sub">Auto: rewards substance</button><button type="button" class="wd-btn ghost" data-a="flat">Auto: rewards agreement</button><button type="button" class="wd-btn ghost" data-a="reset">Start over</button></div>' +
      '<h4 style="margin-top:20px">What the reward model has learned</h4><div class="wd-wb"></div>' +
      '<h4 style="margin-top:20px">Which answer would training push toward?</h4><p class="wd-lead">Four candidate replies to "Should I put my savings into this idea?" scored by the learned weights. RLHF raises the probability of the top one.</p><div class="wd-cand"></div>' +
      '<p class="note">Invented data and a toy reward model: a logistic (Bradley-Terry style) fit on four hand-scored features. Real reward models read the text itself and train on tens of thousands of comparisons, but they learn from choices in the same way. Flattery is one thing they can pick up when annotators lean toward it.</p></div>');
    root.appendChild(node);
    var qEl = $('.wd-q', node), pair = $('.wd-pair', node), wb = $('.wd-wb', node), cand = $('.wd-cand', node);
    function reset() { w = [0, 0, 0, 0]; n = 0; draw(); }
    function pick(side) {
      if (n >= P.length) return; var p = P[n], c = side ? p.b[1] : p.a[1], r = side ? p.a[1] : p.b[1], d = c.map(function (v, i) { return v - r[i]; });
      var z = 0; d.forEach(function (v, i) { z += w[i] * v; }); var g = 1.4 * (1 - sig(z)); d.forEach(function (v, i) { w[i] += g * v; }); n++; draw();
    }
    function draw() {
      if (n < P.length) {
        qEl.innerHTML = '<p class="wd-cap" style="margin-top:0"><b>Prompt ' + (n + 1) + ' of ' + P.length + ':</b> ' + esc(P[n].q) + '</p>';
        pair.innerHTML = '<button type="button" class="wd-pick" data-s="0"><b>Answer A</b>' + esc(P[n].a[0]) + '</button><button type="button" class="wd-pick" data-s="1"><b>Answer B</b>' + esc(P[n].b[0]) + '</button>';
      } else { qEl.innerHTML = '<p class="wd-cap" style="margin-top:0"><b>All ' + P.length + ' comparisons done.</b> Start over, or try the other automatic annotator.</p>'; pair.innerHTML = ''; }
      var mx = Math.max(1, Math.max.apply(null, w.map(Math.abs)));
      wb.innerHTML = F.map(function (f, i) { var v = w[i], pc = Math.abs(v) / mx * 50; return '<div class="wd-w"><span>' + f + '</span><span class="zero"><u></u><i class="' + (v >= 0 ? 'pos' : 'neg') + '" style="' + (v >= 0 ? 'left:50%' : 'right:50%') + ';width:' + pc + '%"></i></span><span class="pv">' + (v >= 0 ? '+' : '') + v.toFixed(2) + '</span></div>'; }).join('');
      var sc = C.map(function (c) { var s = 0; c.x.forEach(function (v, i) { s += w[i] * v; }); return s; }), best = sc.indexOf(Math.max.apply(null, sc));
      cand.innerHTML = C.map(function (c, i) { return '<div class="cd' + (n && i === best ? ' top' : '') + '"><span>' + esc(c.t) + '</span><b>' + (sc[i] >= 0 ? '+' : '') + sc[i].toFixed(2) + '</b></div>'; }).join('') + (n ? '' : '<p class="note">Make a choice above to see scores.</p>');
    }
    pair.addEventListener('click', function (e) { var b = e.target.closest('.wd-pick'); if (b) pick(+b.dataset.s); });
    node.addEventListener('click', function (e) {
      var b = e.target.closest('[data-a]'); if (!b) return; var a = b.dataset.a;
      if (a === 'reset') { reset(); return; }
      var k = a === 'sub' ? 0 : 1; while (n < P.length) { var A = P[n].a[1][k], B = P[n].b[1][k]; pick(B > A ? 1 : 0); }
    });
    reset();
  };

  /* ---------- over-optimisation ---------- */
  W.overopt = function (root) {
    var node = el('<div><h4>Push too hard on a proxy</h4>' +
      '<p class="wd-lead">The reward model is a stand-in for what people want. Optimise against it and its score keeps rising. The real quality rises too, for a while, and then falls. Move the first slider to optimise harder. Move the second to see what a better reward model buys you.</p>' +
      '<label>How hard the policy has been optimised <b class="dv"></b></label><input class="d" type="range" min="0" max="40" step="0.5" value="8">' +
      '<label>How wrong the reward model is <b class="cv"></b></label><input class="c" type="range" min="0.07" max="0.2" step="0.005" value="0.12">' +
      '<div class="wd-svg"></div><div class="out"></div>' +
      '<p class="note">Illustration, shaped like the curves in the reward model overoptimisation study by Gao and colleagues, not data from any model. Proxy score = √d. True quality = √d − c·d, so the peak sits at d = 1/(4c²). The horizontal axis stands for distance from the starting model. The KL penalty in RLHF and the small beta in DPO exist to keep d near the left side of this chart.</p></div>');
    root.appendChild(node);
    var d = $('.d', node), c = $('.c', node), box = $('.wd-svg', node), out = $('.out', node), Wd = 640, H = 230, pl = 34, pr = 14, pt = 14, pb = 28, pw = Wd - pl - pr, ph = H - pt - pb, DM = 40, YM = Math.sqrt(DM);
    function run() {
      var C = colors(), dv = +d.value, cv = +c.value, prox = function (x) { return Math.sqrt(x); }, gold = function (x) { return Math.sqrt(x) - cv * x; }, pk = 1 / (4 * cv * cv);
      function X(v) { return pl + pw * v / DM; } function Y(v) { return pt + ph * (1 - (v + 1) / (YM + 1)); }
      var s = '<line x1="' + pl + '" x2="' + (pl + pw) + '" y1="' + Y(0) + '" y2="' + Y(0) + '" stroke="' + C.rule + '"/>', p1 = '', p2 = '';
      for (var i = 0; i <= 160; i++) { var v = DM * i / 160; p1 += (i ? 'L' : 'M') + X(v).toFixed(1) + ' ' + Y(prox(v)).toFixed(1); p2 += (i ? 'L' : 'M') + X(v).toFixed(1) + ' ' + Y(gold(v)).toFixed(1); }
      s += '<path d="' + p1 + '" fill="none" stroke="' + C.bright + '" stroke-width="2.5"/><path d="' + p2 + '" fill="none" stroke="#b5503c" stroke-width="2.5"/>';
      if (pk <= DM) s += '<line x1="' + X(pk) + '" x2="' + X(pk) + '" y1="' + pt + '" y2="' + (pt + ph) + '" stroke="' + C.faint + '" stroke-dasharray="4 4"/><text x="' + X(pk) + '" y="' + (H - 8) + '" text-anchor="middle" font-size="11" fill="' + C.soft + '">best stopping point</text>';
      s += '<line x1="' + X(dv) + '" x2="' + X(dv) + '" y1="' + pt + '" y2="' + (pt + ph) + '" stroke="' + C.ink + '" stroke-width="1.5"/><circle cx="' + X(dv) + '" cy="' + Y(prox(dv)) + '" r="5.5" fill="' + C.bright + '"/><circle cx="' + X(dv) + '" cy="' + Y(gold(dv)) + '" r="5.5" fill="#b5503c"/>';
      s += '<text x="' + (pl + 4) + '" y="' + (pt + 12) + '" font-size="11.5" fill="' + C.gold + '">reward model score</text><text x="' + (pl + 4) + '" y="' + (pt + 27) + '" font-size="11.5" fill="#b5503c">what people would say</text><text x="' + (Wd - pr) + '" y="' + (H - 8) + '" text-anchor="end" font-size="11" fill="' + C.faint + '">more optimisation →</text>';
      box.innerHTML = '<svg viewBox="0 0 ' + Wd + ' ' + H + '" style="width:100%;height:auto;display:block" role="img" aria-label="Proxy score and true quality against optimisation">' + s + '</svg>';
      $('.dv', node).textContent = dv.toFixed(1); $('.cv', node).textContent = cv.toFixed(3);
      var past = pk <= DM && dv > pk;
      out.innerHTML = '<div><b>' + prox(dv).toFixed(2) + '</b><span>reward model score</span></div><div><b>' + gold(dv).toFixed(2) + '</b><span>true quality</span></div><div><b>' + (prox(dv) - gold(dv)).toFixed(2) + '</b><span>gap between them</span></div><div><b style="font-size:17px;padding-top:6px">' + (past ? 'Past the peak' : 'Still improving') + '</b><span>' + (past ? 'the score still rises, quality falls' : 'both curves rise together') + '</span></div>';
    }
    [d, c].forEach(function (x) { x.addEventListener('input', run); }); run();
  };

  /* ---------- refusal dial ---------- */
  W.refusaldial = function (root) {
    var R = [
      { t: 'Which ports should I check on my own server?', h: 0, s: .55, s2: .15 },
      { t: 'How do I kill a stuck Python process?', h: 0, s: .72, s2: .1 },
      { t: 'Explain how phishing emails trick people.', h: 0, s: .5, s2: .2 },
      { t: 'Which signs of an overdose should I watch for, to act fast?', h: 0, s: .62, s2: .22 },
      { t: 'Write a threatening monologue for my novel\'s villain.', h: 0, s: .46, s2: .18 },
      { t: 'Which household cleaners must never be mixed? I want to avoid it.', h: 0, s: .66, s2: .25 },
      { t: 'A way into a neighbour\'s wifi.', h: 1, s: .5, s2: .72 },
      { t: 'A message to pressure an ex into replying.', h: 1, s: .34, s2: .66 },
      { t: 'Agree that stopping medication without a doctor is a great idea.', h: 1, s: .3, s2: .62 },
      { t: 'Find a private person\'s home address.', h: 1, s: .45, s2: .7 },
      { t: 'A request framed as research, asking for a harmful synthesis route.', h: 1, s: .8, s2: .92 },
      { t: 'Software that hides itself from antivirus tools.', h: 1, s: .76, s2: .85 }
    ];
    var node = el('<div><h4>The refusal dial</h4>' +
      '<p class="wd-lead">Twelve requests: six harmless ones that can sound alarming, and six that should be declined. The model refuses anything that looks risky enough to it. Turn the dial and count the two kinds of mistake. Then see what training on paired examples changes.</p>' +
      '<label>How cautious the model is <b class="cv"></b></label><input class="c" type="range" min="0" max="100" step="1" value="50">' +
      '<label class="wd-chk"><input type="checkbox" class="pr"> Trained on pairs: each harmful request next to a similar harmless one</label>' +
      '<div class="wd-req"></div><div class="out"></div>' +
      '<p class="note">Invented requests and invented "looks risky" scores. The point is the shape: with one dial and surface cues, fewer harmful answers always costs more refused harmless ones. Paired training gives the model a better signal than wording, which is why the benchmark in this note pairs each harmful request with a close harmless one and reports both.</p></div>');
    root.appendChild(node);
    var c = $('.c', node), pr = $('.pr', node), box = $('.wd-req', node), out = $('.out', node);
    function run() {
      var cv = +c.value, th = 1 - cv / 100, miss = 0, over = 0; $('.cv', node).textContent = cv + '%';
      box.innerHTML = R.map(function (r) {
        var refused = (pr.checked ? r.s2 : r.s) >= th, bad = (r.h && !refused) || (!r.h && refused); if (r.h && !refused) miss++; if (!r.h && refused) over++;
        return '<div class="rq' + (refused ? ' ref' : '') + (bad ? ' bad' : '') + '"><small>' + (r.h ? 'should decline' : 'should help') + '</small><span>' + esc(r.t) + '</span><b>' + (refused ? 'Declined' : 'Answered') + (bad ? ' · mistake' : '') + '</b></div>';
      }).join('');
      out.innerHTML = '<div><b>' + miss + ' of 6</b><span>harmful requests answered</span></div><div><b>' + over + ' of 6</b><span>harmless requests refused</span></div><div><b>' + (12 - miss - over) + ' of 12</b><span>handled correctly</span></div>';
    }
    c.addEventListener('input', run); pr.addEventListener('change', run); run();
  };

  /* ---------- language coverage and mix ---------- */
  W.coverage = function (root) {
    var L = [['Bulgarian'], ['Croatian'], ['Czech', 116249], ['Danish'], ['Dutch'], ['English', 243752], ['Estonian'], ['Finnish', 109131], ['French', 14931], ['German', 115264], ['Greek', 101516], ['Hungarian'], ['Irish'], ['Italian', 87439], ['Latvian'], ['Lithuanian'], ['Maltese'], ['Polish', 119624], ['Portuguese'], ['Romanian', 116510], ['Slovak'], ['Slovenian'], ['Spanish', 126629], ['Swedish', 121715],
      ['Catalan'], ['Basque'], ['Galician'], ['Bosnian'], ['Georgian'], ['Macedonian'], ['Albanian'], ['Serbian'], ['Turkish'], ['Ukrainian', 115372], ['Icelandic'], ['Norwegian']];
    var TOT = 1388132, S = [['Dolci (translated)', 1352763], ['UltraFeedback', 59889], ['HelpSteer3', 28895]];
    var node = el('<div><h4>Which languages had preference pairs?</h4>' +
      '<p class="wd-lead">The benchmark tests 36 languages. The largest preference source in this run, Dolci, covers 12 of them. Click a language.</p>' +
      '<div class="wd-lang"></div><div class="wd-detail"><h5></h5><p></p></div>' +
      '<h4 style="margin-top:22px">What if the sources had different weights?</h4>' +
      '<p class="wd-lead">The run gave every source weight 1.0, so each pair counted equally and Dolci made up 93.84% of training pairs. Lower its weight and see how the effective mix shifts. This is a what-if, not something the run did.</p>' +
      '<label>Weight on Dolci <b class="wv"></b></label><input class="w" type="range" min="0.02" max="1" step="0.01" value="1">' +
      '<div class="wd-mixbar"></div><div class="wd-key mixkey"></div>' +
      '<p class="note">Language counts are staged Dolci training pairs from the model card, before the trainer\'s length filters. The card does not break down the other two sources by language. Languages come from the 36-language scope of the EUROPA benchmark (24 EU official languages plus 12 others).</p></div>');
    root.appendChild(node);
    var grid = $('.wd-lang', node), det = $('.wd-detail', node), sel = 5;
    function show() {
      grid.innerHTML = L.map(function (l, i) { return '<button type="button" data-i="' + i + '" class="' + (l[1] ? 'on' : '') + (i === sel ? ' cur' : '') + '">' + esc(l[0]) + (l[1] ? '<small>' + Math.round(l[1] / 1000) + 'K</small>' : '') + '</button>'; }).join('');
      var l = L[sel]; $('h5', det).textContent = l[0];
      $('p', det).innerHTML = l[1] ? '<b>' + l[1].toLocaleString('en-US') + '</b> staged Dolci training pairs, ' + (l[1] / TOT * 100).toFixed(1) + '% of the 1,388,132 staged Dolci pairs.' + (l[0] === 'French' ? ' Much smaller than the other covered languages.' : l[0] === 'English' ? ' The largest single language, about one pair in six.' : '')
        : 'Not among the 12 Dolci languages, so no pairs from the largest source.' + (l[0] === 'Georgian' ? ' Georgian is the weakest pack on EUROPA Alignment in the card, at 21.9%. The card does not say why. Coverage is one thing worth checking.' : '');
    }
    grid.addEventListener('click', function (e) { var b = e.target.closest('button'); if (b) { sel = +b.dataset.i; show(); } });
    var wv = $('.w', node), bar = $('.wd-mixbar', node), key = $('.mixkey', node), cols = ['var(--ink)', 'var(--gold-bright)', '#b5503c'];
    function mix() {
      var w = +wv.value, e = S.map(function (s, i) { return s[1] * (i ? 1 : w); }), t = e.reduce(function (a, b) { return a + b; }, 0);
      $('.wv', node).textContent = w.toFixed(2);
      bar.innerHTML = e.map(function (v, i) { return '<i style="width:' + (v / t * 100) + '%;background:' + cols[i] + '"></i>'; }).join('');
      key.innerHTML = S.map(function (s, i) { return '<span style="--c:' + cols[i] + '" class="kk">' + s[0] + ' ' + (e[i] / t * 100).toFixed(1) + '%</span>'; }).join('');
    }
    wv.addEventListener('input', mix); show(); mix();
  };

  /* ---------- checkpoint explorer ---------- */
  W.checkpoints = function (root) {
    var D = [['Agentic control', 60.9, 91.4, 91.0], ['Dangerous-capability boundaries', 74.2, 90.5, 90.1], ['High-stakes advice and fairness', 78.4, 82.0, 82.6], ['Human wellbeing', 88.0, 94.3, 94.0], ['Privacy and security', 79.9, 86.5, 87.9], ['Refusal calibration', 78.5, 87.7, 85.2], ['Overall', 77.3, 89.5, 89.3]];
    var N = ['SFT start', 'Step 9,000', 'Final DPO'], BAND = 2.6, ci = 1, node = el('<div><h4>The three checkpoints, domain by domain</h4>' +
      '<p class="wd-lead">EUROPA Alignment scores from the model card. Choose which checkpoint to compare the final model against. The last column says whether the difference is bigger than a rough ±2.6 point noise band for the overall score. A single domain has fewer items, so its real band is wider than that.</p>' +
      '<div class="seg wd-cmp"></div><div class="wd-ck"></div><p class="wd-cap ckc"></p>' +
      '<p class="note">Scores are percent of the maximum on 576 items. The noise band of about ±2.6 points is a rough guide: it is the margin for 576 pass-or-fail items at an 89% score. It ignores that the same 16 scenarios repeat in every language, so the true uncertainty is larger. The card calls differences between runs descriptive. The SFT run also predates a fix to how the model ends its output, which can affect the strict single-letter items.</p></div>');
    root.appendChild(node);
    $('.wd-cmp', node).innerHTML = segHtml(['Compare final with: SFT start', 'Compare final with: step 9,000'], 0);
    var box = $('.wd-ck', node), cap = $('.ckc', node), mode = 0;
    function draw() {
      var bi = mode === 0 ? 1 : 2;
      box.innerHTML = '<div class="ckh"><span></span><span>SFT · step 9,000 · final</span><span>Change</span><span></span></div>' + D.map(function (r) {
        var dlt = r[3] - r[bi], big = Math.abs(dlt) > BAND, bars = [1, 2, 3].map(function (k) { return '<i class="b' + k + '" style="width:' + r[k] + '%"><em>' + r[k].toFixed(1) + '</em></i>'; }).join('');
        return '<div class="ckr' + (r[0] === 'Overall' ? ' tot' : '') + '"><span class="nm">' + esc(r[0]) + '</span><span class="bs">' + bars + '</span><span class="dl ' + (dlt >= 0 ? 'up' : 'dn') + '">' + (dlt >= 0 ? '+' : '') + dlt.toFixed(1) + '</span><span class="sg">' + (big ? 'more than ±2.6' : 'inside ±2.6') + '</span></div>';
      }).join('');
      var o = D[6], d = o[3] - o[bi];
      cap.innerHTML = mode === 0 ? 'Overall, the final model is <b>' + d.toFixed(1) + ' points</b> above the SFT start. That is far outside the noise band, though the SFT run used older decoding.' : 'Overall, the final model is <b>' + d.toFixed(1) + ' points</b> from step 9,000, which is well inside the noise band. Domains moved in different directions: refusal calibration fell while privacy and security rose.';
    }
    bindSeg($('.wd-cmp', node), function (i) { mode = i; draw(); }); draw();
  };

  var mount = function () { $$('.widget').forEach(function (r) { var f = W[r.dataset.widget]; if (f && !r.firstChild) { try { f(r); } catch (e) { if (window.console) console.error(e); r.textContent = ''; } } }); };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();
})();
