/* Replays each terminal scene: my lines are typed out, agent lines appear whole.
   Without JS, or with reduced motion, the full text simply shows.
   Still cards (figure.term.still) are left alone: they show the final text at once. */
(function () {
  var figs = document.querySelectorAll('figure.term:not(.still)');
  var still = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!figs.length || still) return;
  var io = 'IntersectionObserver' in window && new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (e.isIntersecting) { io.unobserve(e.target); e.target.termPlay(); }
    });
  }, { threshold: 0.35 });

  [].forEach.call(figs, function (fig) {
    var pre = fig.querySelector('pre');
    var lines = [].slice.call(pre.querySelectorAll('span[data-kind]'));
    var texts = lines.map(function (s) { return s.textContent; });
    var run = 0;

    function finish() {
      run++;
      lines.forEach(function (s, i) {
        s.textContent = texts[i];
        s.classList.remove('off', 'typing');
      });
      pre.style.minHeight = '';
    }
    // Empty the screen (lines keep their space) and wait to be seen.
    function arm() {
      finish();
      lines.forEach(function (s) { s.classList.add('off'); });
      io.unobserve(fig);
      io.observe(fig);
    }

    function play() {
      finish();
      var id = run;
      pre.style.minHeight = pre.offsetHeight + 'px';
      var chars = 0, outs = 0, users = 0;
      lines.forEach(function (s, i) {
        s.classList.add('off');
        if (s.dataset.kind === 'user') { users++; chars += texts[i].length; } else outs++;
      });
      // About 4 seconds in all: output lines get a fixed pause, typing gets the rest.
      var pause = Math.max(150, Math.min(320, 2400 / Math.max(outs, 1)));
      var per = Math.max(10, Math.min(45, (4200 - outs * pause - users * 370) / Math.max(chars, 1)));
      var i = 0;
      function later(fn, ms) { setTimeout(function () { if (id === run) fn(); }, ms); }
      function next() {
        if (i >= lines.length) { finish(); return; }
        var s = lines[i], t = texts[i];
        i++;
        if (s.dataset.kind !== 'user') {
          later(function () { s.classList.remove('off'); next(); }, pause);
          return;
        }
        s.textContent = '';
        s.classList.remove('off');
        s.classList.add('typing');
        var c = 0;
        later(function step() {
          s.textContent = t.slice(0, ++c);
          if (c < t.length) later(step, per);
          else { s.classList.remove('typing'); later(next, 120); }
        }, 250);
      }
      next();
    }
    fig.termPlay = play;

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'term-replay';
    btn.textContent = 'replay';
    btn.setAttribute('aria-label', 'Replay this terminal scene');
    btn.addEventListener('click', play);
    fig.appendChild(btn);

    // Inside a fold-out card: play when the card opens, stop when it closes.
    var card = fig.closest('details');
    if (card) {
      card.addEventListener('toggle', function () {
        if (!card.open) finish();
        else if (io) arm();
        else play();
      });
    }
    if (io) arm();
  });
})();
