/* Interactive lesson widgets, part 2: training mechanics and the Agora 9B pipeline.
   Numbers marked "Agora" come from the model cards of birgermoell/oellm-9b-256k-stage5-w2-rl-step160 and the
   OpenEuroLLM 9B base. Everything else is a labelled illustration. */
(function () {
  'use strict';
  var LW = window.LW; if (!LW) return;
  var W = LW.W, $ = LW.$, $$ = LW.$$, el = LW.el, esc = LW.esc;

  function css(v, d) { try { return getComputedStyle(document.documentElement).getPropertyValue(v).trim() || d; } catch (e) { return d; } }
  function colors() { return { ink: css('--ink', '#1c1a17'), soft: css('--ink-soft', '#625b52'), faint: css('--ink-faint', '#958c80'), rule: css('--rule', '#e6dfd1'), gold: css('--gold', '#9a7a48'), bright: css('--gold-bright', '#c79a3f'), deep: css('--paper-deep', '#f6f0e2') }; }
  function fit(c) {
    var d = window.devicePixelRatio || 1, w = c.clientWidth, h = c.clientHeight;
    if (c.width !== Math.round(w * d) || c.height !== Math.round(h * d)) { c.width = Math.round(w * d); c.height = Math.round(h * d); }
    var g = c.getContext('2d'); g.setTransform(d, 0, 0, d, 0, 0); return [g, w, h];
  }
  function segHtml(items, cur) { return items.map(function (x, i) { return '<button type="button" data-i="' + i + '"' + (i === cur ? ' class="on"' : '') + '>' + esc(x) + '</button>'; }).join(''); }
  function bindSeg(box, f) { box.addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b || !box.contains(b)) return; $$('button', box).forEach(function (x) { x.classList.toggle('on', x === b); }); f(+b.dataset.i); }); }
  function rn() { var u = 0, v = 0; while (!u) u = Math.random(); while (!v) v = Math.random(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); }
  function sig(x) { return 1 / (1 + Math.exp(-x)); }
  function sci(x) { if (!x) return '0'; var e = Math.floor(Math.log10(x)); var m = x / Math.pow(10, e); return m.toFixed(1) + 'e' + e; }
  function onResize(f) { window.addEventListener('resize', f); }

  /* ---------- gradient descent ---------- */
  W.gradient = function (root) {
    var A = 1, B = 12, XR = 3, YR = 1.5, opt = 0, timer = null, st;
    var node = el('<div><h4>Walking down the loss</h4>' +
      '<p class="wd-lead">Training is a walk downhill. Click the plot to choose a starting point, then step. The valley is steep one way and shallow the other, as many real loss surfaces are.</p>' +
      '<canvas class="wd-cv" style="aspect-ratio:2/1" aria-label="Loss contours with the path of the optimizer"></canvas>' +
      '<div class="seg wd-opt"></div>' +
      '<label>Learning rate <b class="lrv"></b></label><input class="lr" type="range" min="-3" max="-0.2" step="0.02" value="-1.2" aria-label="Learning rate">' +
      '<label class="wd-chk"><input type="checkbox" class="noise"> Add minibatch noise to the gradient</label>' +
      '<div class="wd-btns"><button type="button" class="wd-btn" data-a="step">Step</button><button type="button" class="wd-btn" data-a="run">Run 200 steps</button><button type="button" class="wd-btn ghost" data-a="reset">Reset</button></div>' +
      '<canvas class="wd-cv wd-cv2" style="aspect-ratio:5/1" aria-label="Loss over steps"></canvas>' +
      '<div class="out"></div>' +
      '<p class="note">A two-parameter toy. Real models have billions of parameters, but the same things happen: too small a learning rate is slow, too large a rate overshoots and can diverge, and Adam rescales each parameter so the steep and shallow directions move at similar speeds. Adam here uses beta1 0.9 and beta2 0.95, the values in the Agora base-model recipe.</p></div>');
    root.appendChild(node);
    var cv = $('.wd-cv', node), cv2 = $('.wd-cv2', node), lrEl = $('.lr', node), noise = $('.noise', node), out = $('.out', node);
    $('.wd-opt', node).innerHTML = segHtml(['Plain gradient descent', 'With momentum', 'Adam'], 0);
    bindSeg($('.wd-opt', node), function (i) { opt = i; reset(st && [st.path[0][0], st.path[0][1]]); });
    function L(x, y) { return 0.5 * (A * x * x + B * y * y); }
    function reset(p) { stop(); st = { x: p ? p[0] : -2.4, y: p ? p[1] : 0.9, mx: 0, my: 0, vx: 0, vy: 0, t: 0, path: [], loss: [], dead: false }; st.path.push([st.x, st.y]); st.loss.push(L(st.x, st.y)); draw(); }
    function step() {
      if (st.dead) return;
      var gx = A * st.x, gy = B * st.y, lr = Math.pow(10, +lrEl.value);
      if (noise.checked) { gx += rn() * 0.6; gy += rn() * 1.5; }
      if (opt === 0) { st.x -= lr * gx; st.y -= lr * gy; }
      else if (opt === 1) { st.mx = 0.9 * st.mx + gx; st.my = 0.9 * st.my + gy; st.x -= lr * st.mx; st.y -= lr * st.my; }
      else {
        st.t++; st.mx = 0.9 * st.mx + 0.1 * gx; st.my = 0.9 * st.my + 0.1 * gy; st.vx = 0.95 * st.vx + 0.05 * gx * gx; st.vy = 0.95 * st.vy + 0.05 * gy * gy;
        var b1 = 1 - Math.pow(0.9, st.t), b2 = 1 - Math.pow(0.95, st.t);
        st.x -= lr * (st.mx / b1) / (Math.sqrt(st.vx / b2) + 1e-8); st.y -= lr * (st.my / b1) / (Math.sqrt(st.vy / b2) + 1e-8);
      }
      var l = L(st.x, st.y); if (!isFinite(l) || l > 1e4) st.dead = true;
      st.path.push([st.x, st.y]); st.loss.push(Math.min(l, 1e4));
    }
    function stop() { if (timer) { clearInterval(timer); timer = null; $('[data-a=run]', node).textContent = 'Run 200 steps'; } }
    function status() {
      var n = st.loss.length - 1, l = st.loss[n];
      if (st.dead) return 'Diverged: each step overshoots further than the last';
      if (l < 1e-3) return 'Converged';
      var r = st.path.slice(-7), flips = 0; for (var i = 1; i < r.length; i++) if (r[i][1] * r[i - 1][1] < 0) flips++;
      if (n > 6 && flips >= 4 && l > 0.02) return 'Bouncing across the valley';
      if (n === 0) return 'Ready';
      return noise.checked && l < 0.5 ? 'Hovering near the bottom (noise keeps it moving)' : 'Descending';
    }
    function draw() {
      var C = colors(), f = fit(cv), g = f[0], w = f[1], h = f[2];
      function P(x, y) { return [(x + XR) / (2 * XR) * w, (YR - y) / (2 * YR) * h]; }
      g.clearRect(0, 0, w, h); g.fillStyle = C.deep; g.fillRect(0, 0, w, h);
      [0.03, 0.1, 0.3, 0.8, 1.6, 3, 5, 8].forEach(function (c, k) {
        var rx = Math.sqrt(2 * c / A), ry = Math.sqrt(2 * c / B), o = P(0, 0);
        g.beginPath(); g.ellipse(o[0], o[1], rx / (2 * XR) * w, ry / (2 * YR) * h, 0, 0, 7); g.strokeStyle = 'rgba(154,122,72,' + (0.18 + 0.05 * (8 - k)) + ')'; g.lineWidth = 1; g.stroke();
      });
      var m = P(0, 0); g.fillStyle = C.gold; g.beginPath(); g.arc(m[0], m[1], 4, 0, 7); g.fill();
      g.strokeStyle = C.bright; g.lineWidth = 2; g.lineJoin = 'round'; g.beginPath();
      st.path.forEach(function (p, i) { var q = P(Math.max(-XR, Math.min(XR, p[0])), Math.max(-YR, Math.min(YR, p[1]))); i ? g.lineTo(q[0], q[1]) : g.moveTo(q[0], q[1]); }); g.stroke();
      st.path.forEach(function (p, i) { if (i % (st.path.length > 60 ? 4 : 1)) return; var q = P(Math.max(-XR, Math.min(XR, p[0])), Math.max(-YR, Math.min(YR, p[1]))); g.fillStyle = C.ink; g.beginPath(); g.arc(q[0], q[1], i === 0 ? 5 : 2.2, 0, 7); g.fill(); });
      var f2 = fit(cv2), g2 = f2[0], w2 = f2[1], h2 = f2[2]; g2.clearRect(0, 0, w2, h2);
      g2.fillStyle = C.deep; g2.fillRect(0, 0, w2, h2);
      var ls = st.loss.map(function (v) { return Math.log10(Math.max(v, 1e-6)); }), lo = -6, hi = Math.max(2, Math.max.apply(null, ls));
      g2.strokeStyle = C.gold; g2.lineWidth = 2; g2.beginPath();
      ls.forEach(function (v, i) { var x = ls.length < 2 ? 0 : i / Math.max(ls.length - 1, 40) * w2, y = (hi - v) / (hi - lo) * (h2 - 8) + 4; i ? g2.lineTo(x, y) : g2.moveTo(x, y); }); g2.stroke();
      g2.fillStyle = C.faint; g2.font = '11px sans-serif'; g2.fillText('loss (log scale)', 8, 14);
      var l = st.loss[st.loss.length - 1];
      $('.lrv', node).textContent = sci(Math.pow(10, +lrEl.value));
      out.innerHTML = '<div><b>' + (st.loss.length - 1) + '</b><span>steps</span></div><div><b>' + (l < 1e-3 ? '< 0.001' : l >= 1e4 ? 'huge' : l.toFixed(3)) + '</b><span>loss</span></div><div style="grid-column:span 2"><b style="font-size:19px;padding-top:5px">' + status() + '</b><span>what is happening</span></div>';
    }
    cv.addEventListener('click', function (e) { var r = cv.getBoundingClientRect(); reset([((e.clientX - r.left) / r.width) * 2 * XR - XR, YR - ((e.clientY - r.top) / r.height) * 2 * YR]); });
    lrEl.addEventListener('input', draw);
    $('.wd-btns', node).addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return; var a = b.dataset.a;
      if (a === 'step') { stop(); step(); draw(); }
      else if (a === 'reset') reset();
      else if (a === 'run') {
        if (timer) { stop(); return; } b.textContent = 'Pause'; var k = 0;
        timer = setInterval(function () { step(); draw(); if (++k >= 200 || st.dead || st.loss[st.loss.length - 1] < 1e-4) stop(); }, 40);
      }
    });
    onResize(draw); reset();
  };

  /* ---------- learning-rate schedule ---------- */
  W.schedule = function (root) {
    var shape = 0, node = el('<div><h4>The learning-rate schedule</h4>' +
      '<div class="seg wd-shape"></div>' +
      '<label>Warm-up <b class="wv"></b></label><input class="wu" type="range" min="0" max="20" step="0.5" value="5">' +
      '<label>Peak learning rate <b class="pv"></b></label><input class="pk" type="range" min="-7" max="-3" step="any" value="-5.09691">' +
      '<label>Final learning rate, as a share of the peak <b class="fv"></b></label><input class="fi" type="range" min="0" max="100" step="1" value="10">' +
      '<div class="wd-svg"></div>' +
      '<label>Position in training <b class="cv"></b></label><input class="cur" type="range" min="0" max="100" step="0.5" value="30">' +
      '<div class="wd-btns"><button type="button" class="wd-btn ghost" data-a="agora">Agora 256K stage: 8e-6 to 8e-7, 5% warm-up, cosine</button></div>' +
      '<div class="out"></div>' +
      '<p class="note">Warm-up starts the rate at zero and raises it linearly so early, noisy updates do not wreck the model. Cosine and linear decay lower it smoothly. Warmup-stable-decay holds the peak and drops it only in the last fifth of training, which is convenient because you can stop and anneal at any time. The same shapes are used for pre-training, SFT and RL, at very different learning rates.</p></div>');
    root.appendChild(node);
    var shapes = ['Cosine', 'Linear', 'Constant', 'Warmup-stable-decay'];
    $('.wd-shape', node).innerHTML = segHtml(shapes, 0);
    var wu = $('.wu', node), pk = $('.pk', node), fi = $('.fi', node), cur = $('.cur', node), box = $('.wd-svg', node), out = $('.out', node);
    function lr(p) {
      var w = +wu.value / 100, peak = Math.pow(10, +pk.value), mn = peak * (+fi.value) / 100;
      if (w > 0 && p < w) return peak * p / w;
      var q = (p - w) / (1 - w); if (!(q >= 0)) q = 0;
      if (shape === 0) return mn + (peak - mn) * 0.5 * (1 + Math.cos(Math.PI * q));
      if (shape === 1) return peak + (mn - peak) * q;
      if (shape === 2) return peak;
      var d = 0.2; return q < 1 - d ? peak : peak + (mn - peak) * ((q - (1 - d)) / d);
    }
    function draw() {
      var C = colors(), peak = Math.pow(10, +pk.value), Wd = 640, H = 220, pl = 54, pr = 12, pt = 12, pb = 28, pw = Wd - pl - pr, ph = H - pt - pb, ymax = peak * 1.1, s = '';
      for (var k = 0; k <= 4; k++) { var y = pt + ph * k / 4; s += '<line x1="' + pl + '" x2="' + (Wd - pr) + '" y1="' + y + '" y2="' + y + '" stroke="' + C.rule + '"/><text x="' + (pl - 6) + '" y="' + (y + 4) + '" text-anchor="end" font-size="11" fill="' + C.faint + '">' + sci(ymax * (1 - k / 4)) + '</text>'; }
      for (k = 0; k <= 4; k++) { var x = pl + pw * k / 4; s += '<text x="' + x + '" y="' + (H - 8) + '" text-anchor="middle" font-size="11" fill="' + C.faint + '">' + (k * 25) + '%</text>'; }
      var d = ''; for (var i = 0; i <= 240; i++) { var p = i / 240; d += (i ? 'L' : 'M') + (pl + pw * p).toFixed(1) + ' ' + (pt + ph * (1 - lr(p) / ymax)).toFixed(1); }
      var cp = +cur.value / 100, cx = pl + pw * cp, cy = pt + ph * (1 - lr(cp) / ymax);
      s += '<path d="' + d + '" fill="none" stroke="' + C.bright + '" stroke-width="2.5"/><line x1="' + cx + '" x2="' + cx + '" y1="' + pt + '" y2="' + (pt + ph) + '" stroke="' + C.ink + '" stroke-dasharray="3 3" opacity=".5"/><circle cx="' + cx + '" cy="' + cy + '" r="5" fill="' + C.ink + '"/>';
      box.innerHTML = '<svg viewBox="0 0 ' + Wd + ' ' + H + '" style="width:100%;height:auto;display:block" role="img" aria-label="Learning rate over training">' + s + '</svg>';
      $('.wv', node).textContent = (+wu.value).toFixed(1) + '% of training'; $('.pv', node).textContent = sci(peak); $('.fv', node).textContent = fi.value + '% (' + sci(peak * fi.value / 100) + ')'; $('.cv', node).textContent = (+cur.value).toFixed(1) + '%';
      var now = lr(cp);
      out.innerHTML = '<div><b>' + sci(now) + '</b><span>learning rate here</span></div><div><b>' + Math.round(now / peak * 100) + '%</b><span>of the peak</span></div><div><b>' + (cp < +wu.value / 100 ? 'Warm-up' : (shape === 3 ? (((cp - +wu.value / 100) / (1 - +wu.value / 100)) < 0.8 ? 'Stable' : 'Decay') : (shape === 2 ? 'Flat' : 'Decay'))) + '</b><span>phase</span></div>';
    }
    bindSeg($('.wd-shape', node), function (i) { shape = i; draw(); });
    [wu, pk, fi, cur].forEach(function (x) { x.addEventListener('input', draw); });
    $('.wd-btns', node).addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b) return; wu.value = 5; pk.value = Math.log10(8e-6); fi.value = 10; shape = 0; $$('.wd-shape button', node).forEach(function (x, i) { x.classList.toggle('on', i === 0); }); draw(); });
    draw();
  };

  /* ---------- next-token loss ---------- */
  W.nexttoken = function (root) {
    var V = 262144;
    var steps = [['The', 'capital', 0.03], ['capital', 'of', 0.85], ['of', 'Sweden', 0.01], ['Sweden', 'is', 0.55], ['is', 'Stockholm', 0.62], ['Stockholm', '.', 0.40]];
    var node = el('<div><h4>Loss is surprise</h4>' +
      '<p class="wd-lead">At every position the model gives each of its 262,144 possible next tokens a probability. The loss for that position is minus the log of the probability it gave to the token that really came next. Drag to move through training.</p>' +
      '<label>Training progress <b class="sv"></b></label><input class="s" type="range" min="0" max="1" step="0.01" value="0" aria-label="Training progress">' +
      '<div class="wd-rows"></div><div class="out"></div>' +
      '<p class="note">The probabilities after training are invented to show the shape of the idea. The starting point is exact: a model that has learned nothing spreads its probability evenly over the vocabulary, so every token costs ln(262,144) = 12.48 nats. The average loss of a trained 9B model on real text ends up far lower, around 1 to 2 nats, but it never reaches zero because some next words, like which country, are genuinely uncertain.</p></div>');
    root.appendChild(node);
    var s = $('.s', node), rows = $('.wd-rows', node), out = $('.out', node);
    function run() {
      var t = +s.value, tot = 0, h = '';
      steps.forEach(function (x) {
        var lp = (1 - t) * Math.log(1 / V) + t * Math.log(x[2]), p = Math.exp(lp), l = -lp; tot += l;
        h += '<div class="r"><span class="ctx">' + esc(x[0]) + ' <em>→</em> <b>' + esc(x[1]) + '</b></span><span class="track"><i style="width:' + Math.min(100, l / 12.5 * 100) + '%"></i></span><span class="p">' + l.toFixed(2) + '</span><span class="pp">p = ' + (p < 0.0001 ? p.toExponential(1) : (p * 100).toFixed(p < 0.1 ? 1 : 0) + '%') + '</span></div>';
      });
      var m = tot / steps.length;
      rows.innerHTML = h;
      $('.sv', node).textContent = t === 0 ? 'before training' : t === 1 ? 'well trained' : Math.round(t * 100) + '%';
      out.innerHTML = '<div><b>' + m.toFixed(2) + '</b><span>mean loss (nats per token)</span></div><div><b>' + (m > 9 ? Math.round(Math.exp(m)).toLocaleString('en-US') : Math.exp(m).toFixed(1)) + '</b><span>perplexity: the model is as unsure as a fair die with this many sides</span></div>';
    }
    s.addEventListener('input', run); run();
  };

  /* ---------- packing ---------- */
  W.packing = function (root) {
    var ROW = 32, docs = [9, 14, 5, 22, 7, 31, 12, 4, 18, 8, 26, 11], mode = 1, longMode = 0, longOn = false;
    var node = el('<div><h4>Padding versus packing</h4>' +
      '<p class="wd-lead">Each coloured block is one training document. Every row is one sequence the GPU processes. Empty cells are padding: compute spent on nothing.</p>' +
      '<div class="seg wd-mode"></div>' +
      '<label class="wd-chk"><input type="checkbox" class="lg"> Add one document longer than a row</label><div class="seg wd-long" style="display:none"></div>' +
      '<div class="wd-grid"></div><div class="out"></div>' +
      '<p class="note">Cells stand in for tokens: the real Agora rows are 16,384 tokens (stage 1) or 32,768 (stage 2). Packing concatenates documents into full sequences and stops attention from crossing document boundaries, so no compute is wasted on padding. The Agora runs drop rows that are too long instead of truncating them, so the model never sees a cut-off answer.</p></div>');
    root.appendChild(node);
    $('.wd-mode', node).innerHTML = segHtml(['Padding: one document per row', 'Packing: fill each row'], 1);
    $('.wd-long', node).innerHTML = segHtml(['Drop it', 'Truncate it'], 0);
    var grid = $('.wd-grid', node), out = $('.out', node), lg = $('.lg', node);
    var pal = ['#e9c46a', '#e76f51', '#8ab17d', '#6c9bd1', '#c98bb9', '#f4a261', '#7fb7be', '#b5a642', '#d98880', '#9b8bd1', '#7dcea0', '#e59866', '#85c1e9'];
    function run() {
      var ds = docs.map(function (n, i) { return { n: n, id: i, c: pal[i % pal.length] }; }), note = '';
      if (lg.checked) { if (longMode === 0) note = 'One document of 40 cells was longer than a row and was dropped.'; else ds.push({ n: ROW, id: 12, c: pal[12], cut: true }); }
      var rows = [];
      if (mode === 0) ds.forEach(function (d) { rows.push({ free: ROW - d.n, items: [d] }); });
      else ds.forEach(function (d) { var r = rows.filter(function (x) { return x.free >= d.n; })[0]; if (!r) { r = { free: ROW, items: [] }; rows.push(r); } r.items.push(d); r.free -= d.n; });
      var used = 0; ds.forEach(function (d) { used += d.n; });
      grid.innerHTML = rows.map(function (r) { return '<div class="rw">' + r.items.map(function (d) { return '<i style="flex:' + d.n + ';background:' + d.c + '" title="' + d.n + ' cells' + (d.cut ? ', truncated' : '') + '">' + (d.cut ? '✂' : '') + '</i>'; }).join('') + (r.free ? '<i class="pad" style="flex:' + r.free + '"></i>' : '') + '</div>'; }).join('');
      out.innerHTML = '<div><b>' + rows.length + '</b><span>sequences to process</span></div><div><b>' + Math.round(used / (rows.length * ROW) * 100) + '%</b><span>of compute on real tokens</span></div><div><b>' + ds.length + '</b><span>documents kept</span></div>' + (note ? '<div style="grid-column:1/-1"><span>' + note + '</span></div>' : '');
    }
    bindSeg($('.wd-mode', node), function (i) { mode = i; run(); });
    bindSeg($('.wd-long', node), function (i) { longMode = i; run(); });
    lg.addEventListener('change', function () { $('.wd-long', node).style.display = lg.checked ? 'flex' : 'none'; run(); });
    run();
  };

  /* ---------- chat template and loss mask ---------- */
  W.chatmask = function (root) {
    var ids = { '<|im_end|>': 4, '<tool_call>': 11, '</tool_call>': 12, '<tools>': 13, '</tools>': 14, '<tool_response>': 15, '</tool_response>': 16, '</think>': 17, '<think>': 18 };
    var M = [
      { name: 'Direct mode', segs: [
        ['<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\nEtt tåg går 14:20 och kommer fram 16:05. Hur lång är resan?<|im_end|>\n<|im_start|>assistant\n', 0],
        ['Resan tar 1 timme och 45 minuter.<|im_end|>', 1]] },
      { name: 'Thinking mode', segs: [
        ['<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\nEtt tåg går 14:20 och kommer fram 16:05. Hur lång är resan?<|im_end|>\n<|im_start|>assistant\n<think>\n', 0],
        ['From 14:20 to 16:00 is 1 hour 40 minutes. Then 5 more minutes makes 1 hour 45 minutes.\n</think>\n\nResan tar 1 timme och 45 minuter.<|im_end|>', 1]] },
      { name: 'Tool call', segs: [
        ['<|im_start|>system\nYou can call tools.\n<tools>\n{"name": "get_weather", "parameters": {"city": "string"}}\n</tools><|im_end|>\n<|im_start|>user\nHur är vädret i Göteborg?<|im_end|>\n<|im_start|>assistant\n', 0],
        ['<tool_call>\n{"name": "get_weather", "arguments": {"city": "Göteborg"}}\n</tool_call><|im_end|>', 1],
        ['\n<|im_start|>user\n<tool_response>\n{"temp_c": 7, "sky": "rain"}\n</tool_response><|im_end|>\n<|im_start|>assistant\n', 0],
        ['Det är 7 grader och regnar i Göteborg.<|im_end|>', 1]] }
    ];
    var cur = 0, node = el('<div><h4>One conversation, as the model reads it</h4>' +
      '<div class="seg wd-m"></div><div class="wd-key"><span class="k0">read as context, no loss</span><span class="k1">trained: counts toward the loss</span></div>' +
      '<pre class="wd-chat" tabindex="0"></pre><div class="out"></div>' +
      '<p class="note">The tag names and the tag token ids (4 and 11 to 18) are the ones listed on the Agora model card; the example texts are made up. In thinking mode the template itself opens the think tag, so that opening is part of the prompt and is not trained. Tool results arrive in a user turn, so they are context too. Token counts here are rough, counting each tag and each word as one piece.</p></div>');
    root.appendChild(node);
    $('.wd-m', node).innerHTML = segHtml(M.map(function (m) { return m.name; }), 0);
    var pre = $('.wd-chat', node), out = $('.out', node);
    function run() {
      var tr = 0, all = 0, h = '';
      M[cur].segs.forEach(function (s) {
        var parts = s[0].split(/(<\|?\/?[a-z_]+\|?>|\n)/).filter(Boolean), cls = s[1] ? 't1' : 't0';
        parts.forEach(function (p) {
          if (p === '\n') { h += '<span class="' + cls + '">↵</span>\n'; return; }
          var tag = /^<\|?\/?[a-z_]+\|?>$/.test(p);
          var pieces = tag ? [p] : p.split(/(\s+)/).filter(function (x) { return x.trim(); });
          pieces.forEach(function (x) { all++; if (s[1]) tr++; h += '<span class="' + cls + (tag ? ' tg' : '') + '">' + esc(x) + (tag && ids[x] ? '<sub>' + ids[x] + '</sub>' : '') + '</span> '; });
        });
      });
      pre.innerHTML = h;
      out.innerHTML = '<div><b>' + all + '</b><span>pieces in the sequence</span></div><div><b>' + tr + '</b><span>pieces that count toward the loss</span></div><div><b>' + Math.round(tr / all * 100) + '%</b><span>of the sequence is trained on</span></div>';
    }
    bindSeg($('.wd-m', node), function (i) { cur = i; run(); });
    run();
  };

  /* ---------- RoPE and context extension ---------- */
  W.rope = function (root) {
    var ST = [['16K', 16384, 5e5], ['32K', 32768, 1e6], ['64K', 65536, 2e6], ['128K', 131072, 3.2e7], ['256K', 262144, 6.4e7]], cur = 4, D = 128;
    var node = el('<div><h4>Stretching the context window</h4>' +
      '<p class="wd-lead">Rotary position embeddings rotate each pair of query and key dimensions by an angle that grows with position. Fast pairs tell neighbours apart, slow pairs track long distances. Raising the base, theta, slows all the rotations. Agora\'s base was extended in five stages.</p>' +
      '<div class="seg wd-st"></div><div class="wd-svg"></div><div class="out"></div>' +
      '<p class="note">The five stages, sequence lengths and theta values are from the base model card. The wavelength of pair i is 2π × theta^(2i/128) tokens, the distance after which that pair has turned once. This is the standard formula and the chart is a calculation, not a measurement. Whether a model can really use 256K tokens of context is a separate question, answered by tests such as the needle-in-a-haystack check on the card: 12 of 12 correct at every length from 16K to 256K, a deliberately small test and not a benchmark.</p></div>');
    root.appendChild(node);
    $('.wd-st', node).innerHTML = segHtml(ST.map(function (s) { return s[0] + ' · θ ' + LW.fmt(s[2]); }), cur);
    var box = $('.wd-svg', node), out = $('.out', node);
    function wl(theta, i) { return 2 * Math.PI * Math.pow(theta, 2 * i / D); }
    function draw() {
      var C = colors(), Wd = 640, H = 250, pl = 46, pr = 12, pt = 14, pb = 34, pw = Wd - pl - pr, ph = H - pt - pb, lo = 0.5, hi = 9, s = '';
      for (var k = 0; k <= 9; k += 1) { if (k % 2) continue; var y = pt + ph * (1 - (k - lo) / (hi - lo)); if (y < pt || y > pt + ph) continue; s += '<line x1="' + pl + '" x2="' + (Wd - pr) + '" y1="' + y + '" y2="' + y + '" stroke="' + C.rule + '"/><text x="' + (pl - 6) + '" y="' + (y + 4) + '" text-anchor="end" font-size="11" fill="' + C.faint + '">10^' + k + '</text>'; }
      s += '<text x="' + (pl + pw / 2) + '" y="' + (H - 6) + '" text-anchor="middle" font-size="11" fill="' + C.faint + '">rotation pair (fast on the left, slow on the right)</text>';
      ST.forEach(function (t, j) {
        var d = ''; for (var i = 0; i < 64; i++) { var v = Math.log10(wl(t[2], i)); d += (i ? 'L' : 'M') + (pl + pw * i / 63).toFixed(1) + ' ' + (pt + ph * (1 - (v - lo) / (hi - lo))).toFixed(1); }
        s += '<path d="' + d + '" fill="none" stroke="' + (j === cur ? C.bright : C.rule) + '" stroke-width="' + (j === cur ? 3 : 1.5) + '"/>';
      });
      var cl = Math.log10(ST[cur][1]), cy = pt + ph * (1 - (cl - lo) / (hi - lo));
      s += '<line x1="' + pl + '" x2="' + (Wd - pr) + '" y1="' + cy + '" y2="' + cy + '" stroke="' + C.ink + '" stroke-dasharray="4 3"/><text x="' + (pl + 6) + '" y="' + (cy - 6) + '" font-size="11.5" fill="' + C.ink + '">context length ' + ST[cur][0] + '</text>';
      box.innerHTML = '<svg viewBox="0 0 ' + Wd + ' ' + H + '" style="width:100%;height:auto;display:block" role="img" aria-label="Rotation wavelengths for each pair">' + s + '</svg>';
      var n = 0; for (var i = 0; i < 64; i++) if (wl(ST[cur][2], i) > ST[cur][1]) n++;
      var n0 = 0; for (i = 0; i < 64; i++) if (wl(5e5, i) > ST[cur][1]) n0++;
      out.innerHTML = '<div><b>' + ST[cur][1].toLocaleString('en-US') + '</b><span>tokens of context</span></div><div><b>' + LW.fmt(ST[cur][2]) + '</b><span>RoPE theta</span></div><div><b>' + n + ' of 64</b><span>pairs turn less than once across the window</span></div><div><b>' + n0 + ' of 64</b><span>the same count with theta 500K</span></div>';
    }
    bindSeg($('.wd-st', node), function (i) { cur = i; draw(); });
    draw();
  };

  /* ---------- Agora pipeline ---------- */
  var ST = [
    { name: 'Instruct SFT', gpu: 394, what: 'Teaches the base model to answer instead of continue the page.', data: '3.14M rows, 2.37B tokens: OpenEuroLLM-Excellent-SFT core, Dolci translated into 12 languages, Aya human non-English, model-identity rows.', recipe: '1 epoch, learning rate 8e-6 cosine, 16K padding-free packing, FSDP, 8 nodes.' },
    { name: 'Reasoning SFT', gpu: 351, what: 'Adds an opt-in thinking mode: reason first, then answer.', data: '373K reasoning rows (1.74B tokens) plus 792K direct replay rows (0.6B tokens) so direct answers are not forgotten.', recipe: 'Learning rate 5e-6, 32K packing. The think tag is never supervised, it is part of the prompt.' },
    { name: 'Tool-use SFT', gpu: 68, what: 'Adds tool calling in the Qwen3/Hermes format.', data: '159K conversations in 16 translated languages, about 30% of them "do not call" rows, plus stage 2 replay and identity and safety rows.', recipe: 'Learning rate 3e-6, 397 steps, then a repair of the output rows for the tool and think tag tokens (ids 11 to 18).' },
    { name: 'DPO v2', gpu: 368, what: 'Learns from pairs: this answer is better than that one.', data: '249,996 preference pairs: Dolci DPO translated (176,292), HelpSteer3 (28,935), UltraFeedback cleaned (30,000), format-compliance pairs (14,769).', recipe: 'Sigmoid DPO, beta 0.1, learning rate 5e-7 cosine, global batch 128, 1 epoch. Held-out preference accuracy 0.85.' },
    { name: 'Merge', gpu: 0.2, what: 'Averages two checkpoints to win back the tool use that DPO weakened.', data: 'No new data.', recipe: '0.5 × stage 3 + 0.5 × DPO v2, tensor by tensor in fp32. Takes minutes.' },
    { name: 'RL window W1a', gpu: 39, what: 'Reinforcement learning against programs that check the answers.', data: '2,048 prompts: EU-language and English math, bare-answer math, letter-only exam questions, 348 code problems with hidden tests.', recipe: 'DAPO, 128 updates, 6K-token responses, 2 nodes, 4 h 26 min.' },
    { name: 'RL window W2 (Agora)', gpu: 30, what: 'More RL on broader tasks, with a length penalty. This checkpoint is Agora 9B.', data: '2,560 prompts: 896 thinking math, 384 instruction following, 384 code, 512 tool-call items, 384 strict-format items.', recipe: 'DAPO, 160 updates, 7K-token responses, concave length penalty, 3 h 41 min.' }
  ];
  var MET = [
    { k: 'EUROPA Eval', note: 'Chat capabilities in 36 European languages. It climbs through SFT, jumps at the merge and again in the first RL window, then holds.', v: [0.600, 0.609, 0.616, null, 0.655, 0.735, 0.727] },
    { k: 'EUROPA Alignment', note: 'Safety and behaviour. Reasoning SFT adds 0.15 and the tool-use stage 0.04; the first RL window adds another 0.05.', v: [0.455, 0.605, 0.642, null, 0.660, 0.711, 0.717] },
    { k: 'Math, thinking mode', note: 'Flat near 0.4 for five stages, then 0.43 to 0.62 in the first RL window. The reason is on the next tab: before RL, many reasoning traces never finished.', v: [null, 0.402, 0.435, 0.440, 0.426, 0.619, 0.630] },
    { k: 'Thinking traces that finish', note: 'Share of reasoning traces closed within 6K tokens. About half before RL, 86% after. RL taught the model to stop thinking and answer.', v: [null, 0.46, 0.51, 0.53, 0.53, 0.85, 0.86], pct: 1 },
    { k: 'Math, direct mode', note: 'Direct-mode math barely moves from stage 2 on. The gains are in thinking mode.', v: [null, 0.588, 0.581, 0.558, 0.568, 0.574, 0.575] },
    { k: 'Tool call decision', note: 'Right call or no call. Preference tuning dips it; the merge recovers it; RL adds a little.', v: [null, null, 0.870, 0.831, 0.878, 0.878, 0.886], v1: 0.496 },
    { k: 'Valid JSON in tool calls', note: 'The v1 row is the tool-use SFT before the repair of the tag rows: 0.000, because the model closed calls with the wrong tag. After the repair 0.995. DPO cut it to 0.898, the merge restored 0.985, and the final model reaches 1.000.', v: [null, null, 0.995, 0.898, 0.985, 0.991, 1.000], v1: 0.0 },
    { k: 'Valid tool arguments', note: 'DPO dropped valid arguments from 0.981 to 0.849. The merge restores it to 0.951 and RL brings it to 0.972.', v: [null, null, 0.981, 0.849, 0.951, 0.958, 0.972], v1: 0.0 },
    { k: 'Code, HumanEval+ (direct)', note: 'Measured at only three checkpoints. RL on code problems with hidden tests lifts it from 0.335 to 0.390.', v: [null, null, 0.335, null, null, 0.372, 0.390] },
    { k: 'GPU-hours spent', note: 'The two RL windows together cost about 69 GPU-hours, under a tenth of the 1,181 spent on the four supervised and preference stages, yet they produced the largest jump in thinking-mode math.', v: ST.map(function (s) { return s.gpu; }), gpu: 1 }
  ];
  W.pipeline = function (root) {
    var sel = 0, mi = 0;
    var node = el('<div><h4>Agora 9B: seven steps from base model to assistant</h4>' +
      '<div class="wd-steps"></div><div class="wd-detail"></div>' +
      '<div class="seg wd-met"></div><div class="wd-bars"></div><p class="wd-cap"></p>' +
      '<p class="note">All numbers are from the Agora (OpenEuroLLM 9B, step 160) model card: greedy decoding, scores on a 0 to 1 scale, GPU-hours are NVIDIA A100 64 GB on the CINECA Leonardo booster. A dash means the evaluation was not run at that stage. Step 6 and 7 numbers come from different RL windows of one lineage; the DPO model is private and was not run on every test.</p></div>');
    root.appendChild(node);
    $('.wd-steps', node).innerHTML = ST.map(function (s, i) { return '<button type="button" data-i="' + i + '"><i>' + (i + 1) + '</i><span>' + esc(s.name) + '</span></button>'; }).join('');
    $('.wd-met', node).innerHTML = segHtml(MET.map(function (m) { return m.k; }), 0);
    var det = $('.wd-detail', node), bars = $('.wd-bars', node), cap = $('.wd-cap', node);
    function fmtv(m, v) { return v == null ? '–' : m.gpu ? (v >= 10 ? Math.round(v) : v) + ' h' : m.pct ? Math.round(v * 100) + '%' : v.toFixed(3); }
    function draw() {
      $$('.wd-steps button', node).forEach(function (b, i) { b.classList.toggle('on', i === sel); });
      var s = ST[sel];
      det.innerHTML = '<h5>' + (sel + 1) + '. ' + esc(s.name) + '</h5><p>' + esc(s.what) + '</p><dl><dt>Data</dt><dd>' + esc(s.data) + '</dd><dt>Recipe</dt><dd>' + esc(s.recipe) + '</dd><dt>Compute</dt><dd>' + (s.gpu < 1 ? 'minutes' : s.gpu + ' GPU-hours') + '</dd></dl>';
      var m = MET[mi], max = m.gpu ? 400 : 1, h = '';
      function row(label, v, i, extra) { return '<div class="r' + (i === sel ? ' on' : '') + (v == null ? ' na' : '') + '"' + (i != null ? ' data-i="' + i + '"' : '') + '><span class="ctx">' + esc(label) + '</span><span class="track"><i style="width:' + (v == null ? 0 : Math.max(0.5, v / max * 100)) + '%"></i></span><span class="p">' + fmtv(m, v) + '</span></div>'; }
      m.v.forEach(function (v, i) { if (m.v1 != null && i === 2) h += row('3 before the tag repair (v1)', m.v1, null); h += row((i + 1) + ' ' + ST[i].name, v, i); });
      bars.innerHTML = h; cap.textContent = m.note;
    }
    $('.wd-steps', node).addEventListener('click', function (e) { var b = e.target.closest('button'); if (b) { sel = +b.dataset.i; draw(); } });
    bars.addEventListener('click', function (e) { var r = e.target.closest('.r[data-i]'); if (r) { sel = +r.dataset.i; draw(); } });
    bindSeg($('.wd-met', node), function (i) { mi = i; draw(); });
    draw();
  };

  /* ---------- DPO ---------- */
  W.dpo = function (root) {
    var node = el('<div><h4>The DPO loss</h4>' +
      '<p class="wd-lead">DPO looks at one pair: a chosen answer and a rejected one. It compares how much more likely the training model finds each answer than the frozen reference model does. The loss is low when the chosen answer has gained more than the rejected one.</p>' +
      '<label>Chosen answer: change in log-probability vs reference <b class="cv1"></b></label><input class="c" type="range" min="-30" max="30" step="0.5" value="4">' +
      '<label>Rejected answer: change in log-probability vs reference <b class="rv1"></b></label><input class="r" type="range" min="-30" max="30" step="0.5" value="-6">' +
      '<label>Beta <b class="bv"></b></label><input class="b" type="range" min="0.01" max="0.5" step="0.01" value="0.1">' +
      '<div class="wd-svg"></div><div class="out"></div>' +
      '<p class="note">Loss = −log σ(β × (Δchosen − Δrejected)), where Δ is how much more probable (in log terms, summed over the whole answer) the training model finds that answer compared with the reference. Start both at zero and the loss is ln 2 = 0.693. Agora used β = 0.1 and a tiny learning rate of 5e-7. The gradient weight σ(−margin) shows why the updates fade as the model gets pairs right.</p></div>');
    root.appendChild(node);
    var c = $('.c', node), r = $('.r', node), b = $('.b', node), box = $('.wd-svg', node), out = $('.out', node);
    function run() {
      var C = colors(), dc = +c.value, dr = +r.value, be = +b.value, z = be * (dc - dr), loss = Math.log(1 + Math.exp(-z)), gw = sig(-z);
      $('.cv1', node).textContent = (dc > 0 ? '+' : '') + dc.toFixed(1); $('.rv1', node).textContent = (dr > 0 ? '+' : '') + dr.toFixed(1); $('.bv', node).textContent = be.toFixed(2);
      var Wd = 640, H = 200, pl = 40, pr = 12, pt = 12, pb = 28, pw = Wd - pl - pr, ph = H - pt - pb, zr = 4, ymax = Math.log(1 + Math.exp(zr)), s = '';
      function X(v) { return pl + pw * (v + zr) / (2 * zr); } function Y(v) { return pt + ph * (1 - v / ymax); }
      s += '<line x1="' + X(0) + '" x2="' + X(0) + '" y1="' + pt + '" y2="' + (pt + ph) + '" stroke="' + C.rule + '"/>';
      for (var k = -4; k <= 4; k += 2) s += '<text x="' + X(k) + '" y="' + (H - 8) + '" text-anchor="middle" font-size="11" fill="' + C.faint + '">' + k + '</text>';
      s += '<text x="' + (Wd - pr) + '" y="' + (pt + 10) + '" text-anchor="end" font-size="11" fill="' + C.faint + '">vertical: loss</text><text x="' + (Wd - pr) + '" y="' + (pt + ph - 8) + '" text-anchor="end" font-size="11" fill="' + C.faint + '">horizontal: margin</text>';
      var d = ''; for (var i = 0; i <= 120; i++) { var v = -zr + 2 * zr * i / 120; d += (i ? 'L' : 'M') + X(v).toFixed(1) + ' ' + Y(Math.log(1 + Math.exp(-v))).toFixed(1); }
      var zz = Math.max(-zr, Math.min(zr, z));
      s += '<path d="' + d + '" fill="none" stroke="' + C.bright + '" stroke-width="2.5"/><circle cx="' + X(zz) + '" cy="' + Y(Math.log(1 + Math.exp(-zz))) + '" r="6" fill="' + C.ink + '"/>';
      box.innerHTML = '<svg viewBox="0 0 ' + Wd + ' ' + H + '" style="width:100%;height:auto;display:block" role="img" aria-label="DPO loss against margin">' + s + '</svg>';
      out.innerHTML = '<div><b>' + z.toFixed(2) + '</b><span>margin (β × gap)</span></div><div><b>' + loss.toFixed(3) + '</b><span>loss</span></div><div><b>' + (gw * 100).toFixed(0) + '%</b><span>size of the gradient push, relative to its maximum</span></div><div><b style="font-size:19px;padding-top:5px">' + (z > 0 ? 'Pair ranked correctly' : 'Pair ranked wrongly') + '</b><span>by the implicit reward</span></div>';
    }
    [c, r, b].forEach(function (x) { x.addEventListener('input', run); }); run();
  };

  /* ---------- group-relative advantages (GRPO / DAPO) ---------- */
  W.grpo = function (root) {
    var G = 8, rew = [1, 0, 0, 1, 0, 0, 0, 1];
    var node = el('<div><h4>Eight answers, one lesson</h4>' +
      '<p class="wd-lead">In each RL step the model writes 8 answers to one prompt and a program scores each. Click an answer to cycle its reward through 0, 0.5 and 1. The update raises answers that beat the group average and lowers the ones below it.</p>' +
      '<div class="wd-chips"></div><div class="seg wd-pre"></div><div class="wd-adv"></div><p class="wd-cap"></p>' +
      '<h4 style="margin-top:22px">How many prompts teach anything?</h4>' +
      '<label>Chance the model solves this prompt on a single try <b class="pv"></b></label><input class="p" type="range" min="0" max="100" step="1" value="10">' +
      '<div class="wd-svg"></div><div class="out"></div>' +
      '<p class="note">Group-relative advantage: (reward − group average) ÷ the spread of the group; variants of the method scale this slightly differently. If all 8 answers score the same, every advantage is zero and the prompt teaches nothing, so DAPO throws the group away and samples another (dynamic sampling). The curve assumes a fixed success chance per prompt, so it is a simplification. On Agora\'s second window about two thirds of the sampled groups scored all 8 the same, mostly all wrong, which is why that window picked prompts the previous model solved 1 to 7 times out of 8.</p></div>');
    root.appendChild(node);
    var chips = $('.wd-chips', node), advEl = $('.wd-adv', node), cap = $('.wd-cap', node), p = $('.p', node), box = $$('.wd-svg', node)[0], out = $$('.out', node)[0];
    $('.wd-pre', node).innerHTML = segHtml(['3 of 8 right', 'All wrong', 'All right', 'Mixed credit'], 0);
    bindSeg($('.wd-pre', node), function (i) { rew = [[1, 0, 0, 1, 0, 0, 0, 1], [0, 0, 0, 0, 0, 0, 0, 0], [1, 1, 1, 1, 1, 1, 1, 1], [1, 0.5, 0, 0.5, 1, 0, 0.5, 0]][i].slice(); draw(); });
    function draw() {
      var mean = rew.reduce(function (a, b) { return a + b; }, 0) / G, sd = Math.sqrt(rew.reduce(function (a, b) { return a + (b - mean) * (b - mean); }, 0) / G), flat = sd < 1e-9;
      var adv = rew.map(function (r) { return flat ? 0 : (r - mean) / sd; });
      chips.innerHTML = rew.map(function (r, i) { return '<button type="button" data-i="' + i + '" class="c' + (r === 1 ? ' hi' : r === 0 ? ' lo' : ' mid') + '"><small>answer ' + (i + 1) + '</small><b>' + r + '</b></button>'; }).join('');
      var mx = Math.max(1, Math.max.apply(null, adv.map(Math.abs)));
      advEl.innerHTML = adv.map(function (a) { return '<div class="a"><i class="' + (a >= 0 ? 'pos' : 'neg') + '" style="height:' + Math.abs(a) / mx * 46 + 'px;' + (a >= 0 ? 'bottom:50%' : 'top:50%') + '"></i><span>' + (a >= 0 ? '+' : '') + a.toFixed(2) + '</span></div>'; }).join('');
      cap.innerHTML = flat ? '<b>No learning signal.</b> All 8 answers scored ' + rew[0] + ', so every advantage is zero. Dynamic sampling discards this group and draws a new prompt.' : 'Group average <b>' + mean.toFixed(2) + '</b>. Answers above it get a positive advantage (made more likely), answers below it a negative one (made less likely).';
      var pp = +p.value / 100, same = Math.pow(pp, G) + Math.pow(1 - pp, G), C = colors(), Wd = 640, H = 170, pl = 40, pr = 12, pt = 10, pb = 28, pw = Wd - pl - pr, ph = H - pt - pb, s = '';
      function X(v) { return pl + pw * v; } function Y(v) { return pt + ph * (1 - v); }
      for (var k = 0; k <= 4; k++) s += '<line x1="' + pl + '" x2="' + (Wd - pr) + '" y1="' + Y(k / 4) + '" y2="' + Y(k / 4) + '" stroke="' + C.rule + '"/><text x="' + (pl - 6) + '" y="' + (Y(k / 4) + 4) + '" text-anchor="end" font-size="11" fill="' + C.faint + '">' + (k * 25) + '%</text><text x="' + X(k / 4) + '" y="' + (H - 8) + '" text-anchor="middle" font-size="11" fill="' + C.faint + '">' + (k * 25) + '%</text>';
      var d = ''; for (var i = 0; i <= 100; i++) { var q = i / 100; d += (i ? 'L' : 'M') + X(q).toFixed(1) + ' ' + Y(1 - (Math.pow(q, G) + Math.pow(1 - q, G))).toFixed(1); }
      s += '<path d="' + d + '" fill="none" stroke="' + C.bright + '" stroke-width="2.5"/><circle cx="' + X(pp) + '" cy="' + Y(1 - same) + '" r="6" fill="' + C.ink + '"/><text x="' + (Wd - pr) + '" y="' + (pt + 10) + '" text-anchor="end" font-size="11" fill="' + C.faint + '">share of groups with a learning signal</text>';
      box.innerHTML = '<svg viewBox="0 0 ' + Wd + ' ' + H + '" style="width:100%;height:auto;display:block" role="img" aria-label="Share of useful groups against success chance">' + s + '</svg>';
      $('.pv', node).textContent = Math.round(pp * 100) + '%';
      out.innerHTML = '<div><b>' + Math.round(same * 100) + '%</b><span>of groups would score all 8 the same</span></div><div><b>' + Math.round((1 - same) * 100) + '%</b><span>of groups carry a signal</span></div>';
    }
    chips.addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b) return; var i = +b.dataset.i; rew[i] = rew[i] === 0 ? 0.5 : rew[i] === 0.5 ? 1 : 0; $$('.wd-pre button', node).forEach(function (x) { x.classList.remove('on'); }); draw(); });
    p.addEventListener('input', draw); draw();
  };

  /* ---------- tool-call reward ---------- */
  W.toolreward = function (root) {
    var sc = 0;
    var node = el('<div><h4>Scoring a tool call</h4>' +
      '<p class="wd-lead">One of the rewards in Agora\'s second RL window. The user asked: <em>“What is the weather in Göteborg, in celsius?”</em> The correct call is <code>get_weather</code> with city Göteborg and unit celsius. Change what the model wrote and watch the reward.</p>' +
      '<div class="seg wd-sc"></div>' +
      '<div class="wd-form"><label>Closes the call with the right tags <input type="checkbox" class="ok" checked></label>' +
      '<label>Tool name <select class="nm"><option>get_weather</option><option>get_forecast</option><option>search_web</option></select></label>' +
      '<label>city <select class="ci"><option>Göteborg</option><option>Gothenburg</option><option>Stockholm</option></select></label>' +
      '<label>unit <select class="un"><option>celsius</option><option>fahrenheit</option></select></label></div>' +
      '<pre class="wd-chat"></pre><div class="out"></div>' +
      '<p class="note">Weights from the Agora card: 0.2 for a well-formed call, +0.3 for the right tool name, +0.5 × the share of calls with the right arguments, and 1 for a plain reply when no call is expected. This sketch treats the arguments as right only when every one matches, and gives a call no credit when none is expected; the card does not spell out those two details. Partial credit matters: a model that is nearly right still gets a signal to learn from, which an all-or-nothing score would not give.</p></div>');
    root.appendChild(node);
    $('.wd-sc', node).innerHTML = segHtml(['A call is expected', 'No call is expected'], 0);
    var ok = $('.ok', node), nm = $('.nm', node), ci = $('.ci', node), un = $('.un', node), pre = $('.wd-chat', node), out = $('.out', node), form = $('.wd-form', node);
    function run() {
      var r = 0, parts = '';
      if (sc === 1) { form.style.opacity = 0.5; pre.textContent = 'The user said hello and asked a general question.\nThe model replies in plain text, or it calls a tool anyway.'; }
      else form.style.opacity = 1;
      if (sc === 0) {
        pre.textContent = (ok.checked ? '<tool_call>\n' : '<tool_call>\n') + '{"name": "' + nm.value + '", "arguments": {"city": "' + ci.value + '", "unit": "' + un.value + '"}}\n' + (ok.checked ? '</tool_call>' : '(closed with a wrong tag, so the call cannot be read)');
        var w = ok.checked ? 0.2 : 0, n = nm.value === 'get_weather' ? 0.3 : 0, a = (ci.value === 'Göteborg' && un.value === 'celsius') ? 0.5 : 0;
        r = w + n + a;
        out.innerHTML = '<div><b>' + w.toFixed(1) + '</b><span>well formed</span></div><div><b>' + n.toFixed(1) + '</b><span>right tool name</span></div><div><b>' + a.toFixed(1) + '</b><span>right arguments</span></div><div><b>' + r.toFixed(1) + '</b><span>reward</span></div>';
      } else {
        out.innerHTML = '<div><b>1.0</b><span>plain reply, no call</span></div><div><b>0.0</b><span>any call (in this sketch)</span></div>';
      }
    }
    bindSeg($('.wd-sc', node), function (i) { sc = i; run(); });
    [ok, nm, ci, un].forEach(function (x) { x.addEventListener('input', run); }); run();
  };

  /* ---------- weight merge ---------- */
  W.merge = function (root) {
    var a = [0.8, -0.3, 0.5, 0.1, -0.6, 0.9, -0.2, 0.4, -0.7, 0.3, 0.6, -0.5], b = [0.2, 0.5, 0.7, -0.4, -0.1, 0.6, 0.3, -0.2, -0.3, 0.8, 0.1, -0.6];
    var M = [
      { k: 'Valid tool arguments', v: [0.981, 0.951, 0.849] },
      { k: 'Valid JSON in tool calls', v: [0.995, 0.985, 0.898] },
      { k: 'Tool call decision', v: [0.870, 0.878, 0.831] },
      { k: 'Math, thinking mode', v: [0.435, 0.426, 0.440] },
      { k: 'Math, direct mode', v: [0.581, 0.568, 0.558] }
    ], mi = 0;
    var node = el('<div><h4>Averaging two checkpoints</h4>' +
      '<p class="wd-lead">Preference tuning improved the model but weakened tool use. Agora averaged the weights of the checkpoint before DPO (stage 3) and the one after (DPO v2). Slide between them.</p>' +
      '<label>Weight on the DPO checkpoint <b class="av"></b></label><input class="al" type="range" min="0" max="1" step="0.05" value="0.5">' +
      '<div class="wd-svg wd-t"></div>' +
      '<div class="seg wd-mm"></div><div class="wd-svg wd-m2"></div><div class="out"></div>' +
      '<p class="note">Top: twelve invented numbers standing in for one weight tensor. Merging is a per-number weighted average, so the merged value always lies between the two. Bottom: measured results from the Agora card at three points only: stage 3 (0), the 50/50 merge, and DPO v2 (1). The dashed line is a straight guess between measured points, not data, and the vertical axis is zoomed. Averaging checkpoints from one lineage works because they stay close together in weight space; for unrelated models it does not.</p></div>');
    root.appendChild(node);
    $('.wd-mm', node).innerHTML = segHtml(M.map(function (m) { return m.k; }), 0);
    var al = $('.al', node), top = $('.wd-t', node), bot = $('.wd-m2', node), out = $('.out', node);
    function draw() {
      var C = colors(), t = +al.value, Wd = 640, H = 120, s = '', bw = 640 / 12;
      $('.av', node).textContent = t.toFixed(2) + (t === 0.5 ? ' (the Agora merge)' : '');
      for (var i = 0; i < 12; i++) {
        var m = (1 - t) * a[i] + t * b[i], x = i * bw + bw * 0.2, w = bw * 0.6, y0 = H / 2;
        s += '<rect x="' + x + '" y="' + (m >= 0 ? y0 - m * 50 : y0) + '" width="' + w + '" height="' + Math.abs(m) * 50 + '" fill="' + C.bright + '" rx="3"/>';
        s += '<line x1="' + x + '" x2="' + (x + w) + '" y1="' + (y0 - a[i] * 50) + '" y2="' + (y0 - a[i] * 50) + '" stroke="' + C.ink + '" stroke-width="2"/><line x1="' + x + '" x2="' + (x + w) + '" y1="' + (y0 - b[i] * 50) + '" y2="' + (y0 - b[i] * 50) + '" stroke="#b5503c" stroke-width="2"/>';
      }
      s += '<line x1="0" x2="640" y1="60" y2="60" stroke="' + C.rule + '"/>';
      top.innerHTML = '<svg viewBox="0 0 640 ' + H + '" style="width:100%;height:auto;display:block" role="img" aria-label="Merged weights">' + s + '</svg><div class="wd-key"><span style="--c:#1c1a17" class="kk">stage 3 value</span><span style="--c:#b5503c" class="kk">DPO v2 value</span><span style="--c:#c79a3f" class="kk">merged value</span></div>';
      var v = M[mi].v, mn = Math.min.apply(null, v) - 0.03, mx = Math.max.apply(null, v) + 0.03, H2 = 170, pl = 44, pr = 16, pt = 12, pb = 26, pw = 640 - pl - pr, ph = H2 - pt - pb, s2 = '';
      function X(q) { return pl + pw * q; } function Y(q) { return pt + ph * (1 - (q - mn) / (mx - mn)); }
      for (var k = 0; k <= 2; k++) s2 += '<text x="' + X(k / 2) + '" y="' + (H2 - 8) + '" text-anchor="' + ['start', 'middle', 'end'][k] + '" font-size="11" fill="' + C.faint + '">' + ['stage 3', 'merge', 'DPO v2'][k] + '</text>';
      s2 += '<path d="M' + X(0) + ' ' + Y(v[0]) + 'L' + X(0.5) + ' ' + Y(v[1]) + 'L' + X(1) + ' ' + Y(v[2]) + '" fill="none" stroke="' + C.bright + '" stroke-width="2" stroke-dasharray="5 4"/>';
      v.forEach(function (q, k) { s2 += '<circle cx="' + X(k / 2) + '" cy="' + Y(q) + '" r="6" fill="' + C.ink + '"/><text x="' + X(k / 2) + '" y="' + (Y(q) - 11) + '" text-anchor="middle" font-size="12" fill="' + C.ink + '">' + q.toFixed(3) + '</text>'; });
      s2 += '<line x1="' + X(t) + '" x2="' + X(t) + '" y1="' + pt + '" y2="' + (pt + ph) + '" stroke="' + C.gold + '" stroke-width="2"/>';
      bot.innerHTML = '<svg viewBox="0 0 640 ' + H2 + '" style="width:100%;height:auto;display:block" role="img" aria-label="Measured scores at the three checkpoints">' + s2 + '</svg>';
      var meas = t === 0 || t === 0.5 || t === 1;
      out.innerHTML = '<div><b>' + (meas ? v[t === 0 ? 0 : t === 0.5 ? 1 : 2].toFixed(3) : 'not measured') + '</b><span>' + esc(M[mi].k) + ' at this weight</span></div>';
    }
    al.addEventListener('input', draw); bindSeg($('.wd-mm', node), function (i) { mi = i; draw(); }); draw();
  };

  var mount = function () { $$('.widget').forEach(function (r) { var f = W[r.dataset.widget]; if (f && !r.firstChild) { try { f(r); } catch (e) { if (window.console) console.error(e); r.textContent = ''; } } }); };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();
})();
