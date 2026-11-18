/* Learn: search, film player (chapters, transcript sync, deep links, resume), reading progress, filters, small conveniences. */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var store = {
    get: function (k) { try { return JSON.parse(localStorage.getItem('learn:' + k)); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem('learn:' + k, JSON.stringify(v)); } catch (e) {} }
  };
  function clock(sec) { sec = Math.floor(sec); var m = Math.floor(sec / 60), s = sec % 60; return m + ':' + (s < 10 ? '0' : '') + s; }

  /* home: translucent bar turns solid after the hero */
  var bar = $('.bar');
  if (document.body.classList.contains('home') && bar) {
    var onScroll = function () { bar.classList.toggle('solid', window.scrollY > 40); };
    window.addEventListener('scroll', onScroll, { passive: true }); onScroll();
  }

  /* ---------- mobile menu ---------- */
  var toggle = $('.menu-toggle'), scrim = $('.menu-scrim'), mq = window.matchMedia('(max-width: 760px)');
  function setMenu(open) {
    if (!bar || !toggle) return;
    bar.classList.toggle('open', open); document.body.classList.toggle('menu-open', open);
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false'); toggle.setAttribute('aria-label', open ? 'Close menu' : 'Menu');
    if (scrim) {
      if (open) { scrim.hidden = false; requestAnimationFrame(function () { scrim.classList.add('show'); }); }
      else { scrim.classList.remove('show'); setTimeout(function () { if (!bar.classList.contains('open')) scrim.hidden = true; }, 260); }
    }
  }
  if (toggle) {
    var here = location.pathname.split('/')[1];
    $$('#mainnav a').forEach(function (a) { if (a.getAttribute('href').split('/')[1] === here && !a.classList.contains('ext')) a.setAttribute('aria-current', 'page'); });
    toggle.addEventListener('click', function () { setMenu(!bar.classList.contains('open')); });
    if (scrim) scrim.addEventListener('click', function () { setMenu(false); });
    $$('#mainnav a').forEach(function (a) { a.addEventListener('click', function () { setMenu(false); }); });
    $$('[data-search]').forEach(function (b) { b.addEventListener('click', function () { setMenu(false); }); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && bar.classList.contains('open')) { setMenu(false); toggle.focus(); } });
    var leave = function () { if (!mq.matches) setMenu(false); };
    if (mq.addEventListener) mq.addEventListener('change', leave); else mq.addListener(leave);
  }

  /* ---------- search ---------- */
  var overlay = $('#search'), input = $('#q'), results = $('#results'), index = null, active = -1, lastFocus = null;
  function loadIndex(cb) {
    if (index) return cb();
    fetch('/search.json').then(function (r) { return r.json(); }).then(function (j) { index = j; cb(); }).catch(function () { index = []; cb(); });
  }
  function openSearch() {
    if (!overlay) return;
    lastFocus = document.activeElement; overlay.hidden = false; input.value = ''; results.innerHTML = ''; input.focus();
    loadIndex(function () { run(''); });
  }
  function closeSearch() { if (!overlay) return; overlay.hidden = true; if (lastFocus && lastFocus.focus) lastFocus.focus(); }
  function run(q) {
    q = q.trim().toLowerCase();
    var words = q.split(/\s+/).filter(Boolean), list = [];
    if (!words.length) list = index.filter(function (x) { return x.t === 'Lesson'; }).slice(0, 8).map(function (x) { return { x: x, s: 0 }; });
    else index.forEach(function (x) {
      var t = x.title.toLowerCase(), score = 0;
      for (var i = 0; i < words.length; i++) {
        var w = words[i];
        if (t.indexOf(w) === 0) score += 8; else if (t.indexOf(w) > -1) score += 5; else if (x.x.indexOf(w) > -1) score += 1; else return;
      }
      if (x.t === 'Term') score -= 0.5;
      list.push({ x: x, s: score });
    });
    list.sort(function (a, b) { return b.s - a.s; });
    active = -1;
    results.innerHTML = list.length ? list.slice(0, 12).map(function (r) {
      return '<li><a href="' + r.x.url + '"><small>' + r.x.t + '</small><b>' + r.x.title.replace(/</g, '&lt;') + '</b><span>' + r.x.s.replace(/</g, '&lt;') + '</span></a></li>';
    }).join('') : '<li class="res-empty">Nothing found. Try another word.</li>';
  }
  if (overlay) {
    $$('[data-search]').forEach(function (b) { b.addEventListener('click', openSearch); });
    $('[data-search-close]').addEventListener('click', closeSearch);
    overlay.addEventListener('click', function (e) { if (e.target === overlay) closeSearch(); });
    input.addEventListener('input', function () { loadIndex(function () { run(input.value); }); });
    input.addEventListener('keydown', function (e) {
      var items = $$('#results a');
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault(); if (!items.length) return;
        active = (active + (e.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length;
        items.forEach(function (a, i) { a.classList.toggle('on', i === active); }); items[active].scrollIntoView({ block: 'nearest' });
      } else if (e.key === 'Enter') { var t = items[active] || items[0]; if (t) location.href = t.getAttribute('href'); }
    });
  }
  document.addEventListener('keydown', function (e) {
    var tag = (e.target.tagName || '').toLowerCase(), typing = tag === 'input' || tag === 'textarea' || e.target.isContentEditable;
    if (e.key === '/' && !typing) { e.preventDefault(); openSearch(); }
    else if ((e.key === 'k' || e.key === 'K') && (e.metaKey || e.ctrlKey)) { e.preventDefault(); openSearch(); }
    else if (e.key === 'Escape' && overlay && !overlay.hidden) closeSearch();
  });

  /* ---------- film player (YouTube embed or self-hosted file) ---------- */
  var player = $('#player');
  if (player) {
    var id = player.dataset.film, ytId = player.dataset.yt, miss = $('#miss');
    var chBtns = $$('#chapters button'), chapters = chBtns.map(function (b) { return +b.dataset.t; });
    var lines = $$('.ln'), lineT = lines.map(function (l) { return +l.dataset.t; });
    var curCh = -1, curLn = -1, lastSave = 0, tickT = null, api = null, pending = null;
    var m = location.hash.match(/t=(\d+)/), saved = store.get('pos:' + id);
    var startAt = m ? +m[1] : (saved && saved.t > 15 ? saved.t : 0);

    function useFile() {
      var video = $('#video');
      var fail = function () { miss.hidden = false; video.style.visibility = 'hidden'; };
      video.addEventListener('error', fail, true);
      api = {
        time: function () { return video.currentTime || 0; },
        paused: function () { return video.paused; },
        seek: function (t, play) {
          var go = function () { video.currentTime = t; if (play !== false) { var p = video.play(); if (p && p.catch) p.catch(function () {}); } };
          if (video.readyState >= 1) go(); else { video.addEventListener('loadedmetadata', go, { once: true }); video.load(); }
        }
      };
      video.addEventListener('timeupdate', update);
      video.addEventListener('ended', ended);
      video.addEventListener('loadedmetadata', function () { if (startAt && startAt < video.duration - 20) video.currentTime = startAt; update(); }, { once: true });
    }

    function useYouTube() {
      var box = $('#yt'), yp = null;
      var make = function () {
        yp = new YT.Player('yt', {
          host: 'https://www.youtube-nocookie.com', videoId: ytId,
          playerVars: { rel: 0, modestbranding: 1, playsinline: 1, start: startAt || 0 },
          events: {
            onReady: function () { api.ready = true; if (pending != null) { yp.seekTo(pending, true); yp.playVideo(); pending = null; } update(); },
            onStateChange: function (e) {
              if (e.data === 1 && !tickT) tickT = setInterval(update, 400);
              if ((e.data === 2 || e.data === 0) && tickT) { clearInterval(tickT); tickT = null; update(); }
              if (e.data === 0) ended();
            },
            onError: function () { miss.hidden = false; box.style.visibility = 'hidden'; }
          }
        });
      };
      api = {
        time: function () { return yp && yp.getCurrentTime ? yp.getCurrentTime() : 0; },
        paused: function () { return !(yp && yp.getPlayerState && yp.getPlayerState() === 1); },
        seek: function (t) { if (yp && api.ready) { yp.seekTo(t, true); yp.playVideo(); } else pending = t; }
      };
      if (window.YT && YT.Player) make();
      else {
        window.onYouTubeIframeAPIReady = make;
        var s = document.createElement('script'); s.src = 'https://www.youtube.com/iframe_api'; s.async = true;
        s.onerror = function () { miss.hidden = false; box.style.visibility = 'hidden'; };
        document.head.appendChild(s);
      }
    }

    function ended() { store.set('pos:' + id, { t: 0, d: +player.dataset.duration, at: Date.now(), done: true }); }
    function update() {
      if (!api) return;
      var t = api.time(), c = -1, l = -1, i;
      for (i = 0; i < chapters.length; i++) if (t >= chapters[i] - 0.2) c = i;
      for (i = 0; i < lineT.length; i++) if (t >= lineT[i] - 0.2) l = i;
      if (c !== curCh) {
        if (curCh > -1) chBtns[curCh].classList.remove('on');
        if (c > -1) { chBtns[c].classList.add('on'); var list = chBtns[c].closest('ol'); if (list && list.scrollHeight > list.clientHeight) list.scrollTop = chBtns[c].offsetTop - list.offsetTop - 40; }
        curCh = c;
      }
      if (l !== curLn) {
        if (curLn > -1) lines[curLn].classList.remove('on');
        if (l > -1) { lines[l].classList.add('on'); var tb = lines[l].closest('.tbody'), d = $('#transcript'); if (d && d.open && tb) { var top = lines[l].offsetTop - tb.offsetTop; if (top < tb.scrollTop || top > tb.scrollTop + tb.clientHeight - 60) tb.scrollTop = top - 60; } }
        curLn = l;
      }
      if (Date.now() - lastSave > 4000 && !api.paused() && t > 1) { lastSave = Date.now(); store.set('pos:' + id, { t: Math.floor(t), d: +player.dataset.duration, at: Date.now() }); }
    }

    if (player.dataset.soon) { /* no player yet */ } else if (ytId) useYouTube(); else useFile();
    $$('[data-t]').forEach(function (b) {
      b.addEventListener('click', function () {
        if (!api) return; api.seek(+b.dataset.t); history.replaceState(null, '', '#t=' + Math.floor(+b.dataset.t));
        if (window.scrollY > 260) window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    });
    $('#share').addEventListener('click', function () {
      var t = Math.floor(api ? api.time() : 0), url = location.origin + location.pathname + '#t=' + t, b = this;
      (navigator.clipboard ? navigator.clipboard.writeText(url) : Promise.reject()).then(function () { b.textContent = 'Copied ' + clock(t); }, function () { prompt('Copy this link', url); });
      setTimeout(function () { b.textContent = 'Copy link at this time'; }, 2200);
    });
    window.addEventListener('hashchange', function () { var mm = location.hash.match(/t=(\d+)/); if (mm && api) api.seek(+mm[1]); });
  }

  /* ---------- lessons: reading progress, toc spy, mark as read ---------- */
  var prog = $('#progress i'), art = $('.lesson');
  if (prog && art) {
    var heads = $$('.prose h2'), links = $$('.toc a');
    var spy = function () {
      var r = $('.prose').getBoundingClientRect(), total = r.height - window.innerHeight * 0.6, done = Math.min(1, Math.max(0, -r.top / total));
      prog.style.width = (done * 100) + '%';
      var cur = null; heads.forEach(function (h) { if (h.getBoundingClientRect().top < 140) cur = h.id; });
      links.forEach(function (a) { a.classList.toggle('on', a.getAttribute('href') === '#' + cur); });
      if (done > 0.85) store.set('read:' + art.dataset.lesson, true);
    };
    window.addEventListener('scroll', spy, { passive: true }); spy();
  }

  /* ---------- cards: resume bars, read ticks ---------- */
  var cont = $('#continue'), grid = $('#continue-grid'), recent = [];
  $$('.fcard').forEach(function (c) {
    var p = store.get('pos:' + c.dataset.film);
    if (p && p.d) {
      var pct = p.done ? 100 : Math.min(100, p.t / p.d * 100), bar = $('.fprog', c);
      if (bar && pct > 1) { bar.hidden = false; $('i', bar).style.width = pct + '%'; }
      if (cont && !p.done && p.t > 15) recent.push({ c: c, at: p.at || 0 });
    }
  });
  $$('.lcard').forEach(function (c) { if (store.get('read:' + c.dataset.lesson)) { var t = $('.tick', c); if (t) t.hidden = false; } });
  if (cont && recent.length) {
    recent.sort(function (a, b) { return b.at - a.at; }).slice(0, 3).forEach(function (r) { grid.appendChild(r.c.cloneNode(true)); });
    cont.hidden = false;
  }

  /* ---------- films filter ---------- */
  var filters = $('#filters');
  if (filters) {
    var f = { track: 'all', len: null }, items = $$('.fitem'), none = $('#none');
    var apply = function () {
      var n = 0;
      items.forEach(function (it) {
        var ok = (f.track === 'all' || it.dataset.track === f.track) && (!f.len || (f.len === 'short' ? +it.dataset.min < 8 : +it.dataset.min > 12));
        it.hidden = !ok; if (ok) n++;
      });
      none.hidden = n > 0;
    };
    filters.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      if (b.dataset.f) { f.track = b.dataset.f; $$('[data-f]', filters).forEach(function (x) { x.classList.toggle('on', x === b); }); }
      else if (b.dataset.len) { f.len = f.len === b.dataset.len ? null : b.dataset.len; $$('[data-len]', filters).forEach(function (x) { x.classList.toggle('on', x.dataset.len === f.len); }); }
      apply();
    });
  }
})();
