/* Interactive lesson widgets. Everything here is illustrative and says so on the page. */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  function el(html) { var d = document.createElement('div'); d.innerHTML = html.trim(); return d.firstChild; }
  function fmt(n) {
    if (n >= 1e12) return (n / 1e12).toFixed(n >= 1e13 ? 0 : 1).replace(/\.0$/, '') + 'T';
    if (n >= 1e9) return (n / 1e9).toFixed(n >= 1e10 ? 0 : 1).replace(/\.0$/, '') + 'B';
    if (n >= 1e6) return (n / 1e6).toFixed(n >= 1e7 ? 0 : 1).replace(/\.0$/, '') + 'M';
    return Math.round(n).toLocaleString('en-US');
  }
  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  var W = {};

  /* ---------- tokenizer (toy) ---------- */
  W.tokenizer = function (root) {
    var vocab = ('the of and to in is that it for as with was on be by this have from or one had not but what all were when we there can an your which their said if do will each about how up out them then she many some so these would other into has more her two like him see time could no make than first been its who now people my made over did down only way find use may water long little very after words called just where most know get through back much before go good new write our me man too any day same right look think also around another came come work three word must because does part even place well such here take why things help put years different away again off went old number great tell men say small every found still between name should home big give air line set own under read last never us left end along while might next sound below saw something thought both few those always looked show large often together asked house don world going want school important until form food keep children feet land side without boy once animal life enough took sometimes four head above kind began almost live page got earth need far hand high year mother light country father let night picture being study second soon story since white ever paper hard near sentence better best across during today however sure knew try told young sun thing whole hear example heard several change answer room sea against top turned learn point city play toward five using himself usually').split(' ');
    var sub = ['un', 're', 'in', 'dis', 'pre', 'over', 'ization', 'ation', 'ing', 'ed', 'er', 'est', 'ly', 'tion', 'sion', 'able', 'ible', 'ness', 'ment', 'ful', 'less', 'ous', 'ive', 'al', 'ity', 'ize', 'ise', 'believ', 'token', 'model', 'train', 'learn', 'neur', 'trans', 'form', 'atten', 'lang', 'uage', 'data', 'gpu', 'param', 'eter'];
    var set = {}; vocab.concat(sub).forEach(function (w, i) { set[w] = i; });
    var max = 8;
    function id(p) { var h = 7; for (var i = 0; i < p.length; i++) h = (h * 31 + p.charCodeAt(i)) % 50000; return h + 256; }
    function tokenize(text) {
      var out = [], i = 0, low = text;
      while (i < low.length) {
        var best = null, bl = Math.min(max, low.length - i);
        var lead = low[i] === ' ';
        for (var l = bl; l >= 1; l--) {
          var piece = low.substr(i, l), key = (lead ? piece.slice(1) : piece).toLowerCase();
          if (key && set.hasOwnProperty(key) && (key.length > 1 || !/[a-z]/i.test(key) || key === 'a' || key === 'i')) { best = piece; break; }
        }
        if (!best) best = low[i];
        out.push(best); i += best.length;
      }
      return out;
    }
    var node = el('<div><h4>Toy tokenizer</h4><input type="text" value="Unbelievable tokenization of language models" aria-label="Text to tokenize"><div class="toks" aria-live="polite"></div><div class="out"></div><p class="note">A toy: it matches the longest known piece from a small word list and falls back to single characters. Real tokenizers learn tens of thousands of pieces from data, so their splits differ.</p></div>');
    root.appendChild(node);
    var inp = $('input', node), toks = $('.toks', node), out = $('.out', node);
    function run() {
      var t = tokenize(inp.value), chars = inp.value.length;
      toks.innerHTML = t.map(function (p, i) { return '<span class="tok" style="background:hsl(' + ((i * 47) % 360) + ' 70% 88%)">' + esc(p).replace(/ /g, '␣') + '<sub>' + id(p) + '</sub></span>'; }).join('');
      out.innerHTML = '<div><b>' + t.length + '</b><span>tokens</span></div><div><b>' + chars + '</b><span>characters</span></div><div><b>' + (t.length ? (chars / t.length).toFixed(1) : '0') + '</b><span>characters per token</span></div>';
    }
    inp.addEventListener('input', run); run();
  };

  /* ---------- attention (illustrative weights) ---------- */
  W.attention = function (root) {
    var words = ['The', 'animal', "didn't", 'cross', 'the', 'street', 'because', 'it', 'was', 'too', 'tired'];
    var spec = {
      7: { 1: 0.46, 5: 0.14, 10: 0.1, 8: 0.08, 6: 0.07, 7: 0.1, 0: 0.02, 4: 0.03 },
      10: { 7: 0.26, 1: 0.24, 9: 0.18, 8: 0.14, 10: 0.1, 6: 0.05, 5: 0.03 },
      3: { 1: 0.3, 2: 0.24, 5: 0.2, 3: 0.1, 4: 0.1, 0: 0.06 },
      5: { 3: 0.34, 4: 0.22, 5: 0.12, 1: 0.14, 2: 0.1, 0: 0.08 },
      1: { 0: 0.42, 1: 0.32, 2: 0.14, 3: 0.12 },
      8: { 7: 0.4, 8: 0.14, 9: 0.2, 1: 0.14, 10: 0.12 }
    };
    function weights(i) {
      var w = spec[i], tot = 0, k;
      if (!w) { w = {}; for (k = 0; k < words.length; k++) w[k] = Math.exp(-Math.abs(k - i) * 0.9) * (k === i ? 1.3 : 1); }
      for (k in w) tot += w[k];
      var r = words.map(function (_, j) { return (w[j] || 0) / tot; }); return r;
    }
    var node = el('<div><h4>Attention, illustrated</h4><p style="margin:0 0 6px;color:var(--ink-soft)">Click a word to see where it looks.</p><div class="attn-words"></div><div class="out" style="margin-top:12px"></div><p class="note">The weights are illustrative, written by hand to show the idea. In a real model there are many heads in every layer, each with its own learned pattern.</p></div>');
    root.appendChild(node);
    var box = $('.attn-words', node), out = $('.out', node), sel = 7;
    box.innerHTML = words.map(function (w, i) { return '<button type="button" data-i="' + i + '">' + esc(w) + '<i></i></button>'; }).join('');
    function show() {
      var w = weights(sel), top = w.map(function (v, i) { return [v, i]; }).sort(function (a, b) { return b[0] - a[0]; }).slice(0, 3);
      $$('button', box).forEach(function (b, i) { b.classList.toggle('sel', i === sel); $('i', b).style.width = (w[i] / Math.max.apply(null, w) * 100) + '%'; b.style.background = 'rgba(199,154,63,' + (0.05 + w[i] * 1.1).toFixed(2) + ')'; });
      out.innerHTML = '<div style="grid-column:1/-1"><span>When the model processes <b style="display:inline;font-size:inherit;font-family:inherit;color:var(--ink)">“' + esc(words[sel]) + '”</b>, it attends most to:</span></div>' + top.map(function (t) { return '<div><b>' + esc(words[t[1]]) + '</b><span>' + Math.round(t[0] * 100) + '% of attention</span></div>'; }).join('');
    }
    box.addEventListener('click', function (e) { var b = e.target.closest('button'); if (b) { sel = +b.dataset.i; show(); } });
    show();
  };

  /* ---------- scaling ---------- */
  W.scaling = function (root) {
    var node = el('<div><h4>Compute-optimal budget</h4><label>Training compute <b id="c-v"></b></label><input id="c" type="range" min="21" max="26.5" step="0.05" value="24"><div class="seg" id="mode"><button type="button" class="on" data-m="20">Compute-optimal (20 tokens per parameter)</button><button type="button" data-m="200">Over-trained (200 tokens per parameter)</button></div><div class="out"></div><p class="note">Uses two rules of thumb: training compute C is about 6 × parameters × tokens, and the Chinchilla result of roughly 20 tokens per parameter. GPU time assumes 4×10¹⁴ useful FLOP/s per chip, an assumption for scale, not a measurement. Real runs vary.</p></div>');
    root.appendChild(node);
    var c = $('#c', node), cv = $('#c-v', node), out = $('.out', node), ratio = 20;
    function run() {
      var C = Math.pow(10, +c.value), N = Math.sqrt(C / (6 * ratio)), D = N * ratio, gpuSec = C / 4e14, gpuYears = gpuSec / 3.156e7;
      cv.textContent = '10^' + (+c.value).toFixed(1) + ' FLOPs';
      out.innerHTML = '<div><b>' + fmt(N) + '</b><span>parameters</span></div><div><b>' + fmt(D) + '</b><span>training tokens</span></div><div><b>' + (gpuYears >= 10 ? Math.round(gpuYears).toLocaleString('en-US') : gpuYears.toFixed(1)) + '</b><span>GPU-years</span></div><div><b>' + (gpuYears * 365 / 10000 < 1 ? (gpuYears * 365 * 24 / 10000).toFixed(1) + ' h' : (gpuYears * 365 / 10000).toFixed(1) + ' d') + '</b><span>on 10,000 GPUs</span></div>';
    }
    c.addEventListener('input', run);
    $('#mode', node).addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b) return; ratio = +b.dataset.m; $$('#mode button', node).forEach(function (x) { x.classList.toggle('on', x === b); }); run(); });
    run();
  };

  /* ---------- memory ---------- */
  W.memory = function (root) {
    var prec = [['FP32', 4], ['BF16', 2], ['FP8', 1], ['4-bit', 0.5]];
    var node = el('<div><h4>Will it fit?</h4><label>Model size <b id="p-v"></b></label><input id="p" type="range" min="0" max="3.4" step="0.02" value="2.15"><label style="margin-top:12px">Weight precision</label><div class="seg" id="prec"></div><div class="out"></div><p class="note">Weights only for inference. Training uses a common rule of thumb of about 16 bytes per parameter with mixed-precision Adam (weights, gradients and optimizer states), before activations. 4-bit formats also store block scales, which add roughly another 10 percent. GPU counts assume 80 GB per GPU.</p></div>');
    root.appendChild(node);
    var p = $('#p', node), pv = $('#p-v', node), out = $('.out', node), cur = 1;
    $('#prec', node).innerHTML = prec.map(function (x, i) { return '<button type="button" data-i="' + i + '"' + (i === cur ? ' class="on"' : '') + '>' + x[0] + '</button>'; }).join('');
    function gb(b) { return b >= 1e12 ? (b / 1e12).toFixed(1) + ' TB' : (b >= 1e11 ? Math.round(b / 1e9) : (b / 1e9).toFixed(1)) + ' GB'; }
    function run() {
      var N = Math.pow(10, +p.value + 8.7);
      pv.textContent = fmt(N) + ' parameters';
      var w = N * prec[cur][1], t = N * 16;
      out.innerHTML = '<div><b>' + gb(w) + '</b><span>weights at ' + prec[cur][0] + '</span></div><div><b>' + Math.max(1, Math.ceil(w / 80e9)) + '</b><span>80 GB GPUs for the weights</span></div><div><b>' + gb(t) + '</b><span>to train (rule of thumb)</span></div><div><b>' + Math.ceil(t / 80e9) + '</b><span>80 GB GPUs for training state</span></div>';
    }
    p.addEventListener('input', run);
    $('#prec', node).addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b) return; cur = +b.dataset.i; $$('#prec button', node).forEach(function (x) { x.classList.toggle('on', x === b); }); run(); });
    run();
  };

  /* ---------- temperature / top-p ---------- */
  W.temperature = function (root) {
    var toks = [['the smell', .30], ['that', .22], ['how', .15], ['watching', .12], ['sleeping', .08], ['listening', .06], ['puddles', .04], ['nothing', .03]];
    var node = el('<div><h4>Choosing the next token</h4><p style="margin:0;color:var(--ink-soft)">Prompt: <em style="font-family:var(--serif);font-size:18px;color:var(--ink)">“The best thing about rain is …”</em></p><label>Temperature <b id="t-v"></b></label><input id="t" type="range" min="0.1" max="2" step="0.05" value="1"><label>Top-p <b id="pp-v"></b></label><input id="pp" type="range" min="0.1" max="1" step="0.05" value="1"><div class="dist"></div><button type="button" class="btn" id="draw" style="margin-top:14px;padding:8px 18px;cursor:pointer">Sample a token</button><div class="sample" aria-live="polite"></div><p class="note">The probabilities are made up for illustration. Low temperature sharpens the distribution toward the most likely token, high temperature flattens it. Top-p keeps only the smallest set of tokens whose probability adds up to p.</p></div>');
    root.appendChild(node);
    var t = $('#t', node), pp = $('#pp', node), dist = $('.dist', node), cur = [], samp = $('.sample', node);
    function run() {
      var T = +t.value, P = +pp.value; $('#t-v', node).textContent = T.toFixed(2); $('#pp-v', node).textContent = P.toFixed(2);
      var l = toks.map(function (x) { return Math.log(x[1]) / T; }), m = Math.max.apply(null, l), e = l.map(function (v) { return Math.exp(v - m); }), s = e.reduce(function (a, b) { return a + b; }, 0);
      var pr = e.map(function (v, i) { return { w: toks[i][0], p: v / s }; }), srt = pr.slice().sort(function (a, b) { return b.p - a.p; }), cum = 0, keep = {};
      for (var i = 0; i < srt.length; i++) { keep[srt[i].w] = true; cum += srt[i].p; if (cum >= P - 1e-9) break; }
      var kt = 0; pr.forEach(function (x) { if (keep[x.w]) kt += x.p; });
      cur = pr.map(function (x) { return { w: x.w, p: x.p, k: !!keep[x.w], q: keep[x.w] ? x.p / kt : 0 }; });
      dist.innerHTML = cur.map(function (x) { return '<div class="row' + (x.k ? '' : ' cut') + '"><span>' + esc(x.w) + '</span><span class="track"><i style="width:' + (x.k ? x.q : x.p) * 100 + '%"></i></span><span class="p">' + Math.round((x.k ? x.q : 0) * 100) + '%</span></div>'; }).join('');
    }
    t.addEventListener('input', run); pp.addEventListener('input', run);
    $('#draw', node).addEventListener('click', function () {
      var r = Math.random(), a = 0, pick = cur.filter(function (x) { return x.k; }).pop();
      for (var i = 0; i < cur.length; i++) { a += cur[i].q; if (r <= a && cur[i].k) { pick = cur[i]; break; } }
      samp.textContent = 'The best thing about rain is ' + pick.w + ' …';
    });
    run();
  };

  window.LW = { W: W, $: $, $$: $$, el: el, esc: esc, fmt: fmt };
})();
