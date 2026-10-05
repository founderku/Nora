"""Speed optimisations applied on top of the pages, style.css and script.js.

Run AFTER tools/extract_images.py, from the repository root:
    python3 tools/optimize_pages.py
Safe to run more than once (each step skips what is already done).
"""
import glob, re, sys
from collections import Counter

def edit(path, pairs):
    s = open(path, encoding='utf-8').read()
    for old, new in pairs:
        if new in s:
            continue
        if s.count(old) != 1:
            sys.exit(f'{path}: expected block not found exactly once:\n{old[:80]}')
        s = s.replace(old, new)
    open(path, 'w', encoding='utf-8').write(s)

# ---------- style.css ----------
edit('style.css', [
("""  #dustCanvas{
    position:fixed; inset:0; z-index:55; pointer-events:none; opacity:0.5;
  }
""", """  #dustCanvas{
    position:fixed; inset:0; z-index:55; pointer-events:none; opacity:0.5;
  }
  /* Touch devices have no mouse cursor, and phones gain little from the dust
     effect while paying for a full-screen redraw every frame - skip both. */
  @media (hover:none), (pointer:coarse), (max-width:760px), (prefers-reduced-motion: reduce){
    #dustCanvas{display:none;}
  }
  @media (hover:none), (pointer:coarse){
    #cursor{display:none;}
  }
"""),
("""  .hero-slide{ animation:kenburns 14s ease-in-out infinite alternate; }""",
"""  /* Slow zoom only on the visible slide. Running it on every (blurred) slide
     made the browser re-render all of the blur filters on every frame. */
  .hero-slide.active{ animation:kenburns 14s ease-in-out infinite alternate; }
  @media (prefers-reduced-motion: reduce){
    .hero-slide.active{ animation:none; }
  }"""),
])

# ---------- script.js ----------
edit('script.js', [
("""  // Custom round cursor
  const cursor = document.getElementById('cursor');
  let mx=0, my=0, cx=0, cy=0;
  document.addEventListener('mousemove', e=>{
    mx=e.clientX; my=e.clientY;
    if (!cursor.classList.contains('visible')) { cx = mx; cy = my; cursor.classList.add('visible'); }
  });
  function animCursor(){
    cx += (mx-cx)*0.18; cy += (my-cy)*0.18;
    cursor.style.left = cx+'px'; cursor.style.top = cy+'px';
    requestAnimationFrame(animCursor);
  }
  animCursor();
  document.querySelectorAll('a, button, .menu-item').forEach(el=>{
    el.addEventListener('mouseenter', ()=>cursor.classList.add('grow'));
    el.addEventListener('mouseleave', ()=>cursor.classList.remove('grow'));
  });
""", """  // Devices with a real mouse; touch screens skip the cursor and tilt effects.
  const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

  // Custom round cursor. The animation loop only runs while the cursor is
  // still catching up with the mouse, and moves it with a GPU transform
  // instead of left/top so it never forces a page re-layout.
  const cursor = document.getElementById('cursor');
  if (cursor && finePointer){
    let mx=0, my=0, cx=0, cy=0, running=false;
    const place = ()=>{ cursor.style.transform = `translate3d(${cx}px, ${cy}px, 0) translate(-50%,-50%)`; };
    function animCursor(){
      cx += (mx-cx)*0.18; cy += (my-cy)*0.18;
      if (Math.abs(mx-cx) < 0.1 && Math.abs(my-cy) < 0.1){ cx = mx; cy = my; running = false; }
      place();
      if (running) requestAnimationFrame(animCursor);
    }
    document.addEventListener('mousemove', e=>{
      mx=e.clientX; my=e.clientY;
      if (!cursor.classList.contains('visible')) { cx = mx; cy = my; place(); cursor.classList.add('visible'); }
      if (!running){ running = true; requestAnimationFrame(animCursor); }
    }, { passive: true });
    document.querySelectorAll('a, button, .menu-item').forEach(el=>{
      el.addEventListener('mouseenter', ()=>cursor.classList.add('grow'));
      el.addEventListener('mouseleave', ()=>cursor.classList.remove('grow'));
    });
  }
"""),
("""  (function(){
    const canvas = document.getElementById('dustCanvas');
    const ctx = canvas.getContext('2d');""",
"""  // Skipped on phones/touch screens and for visitors who prefer reduced motion
  // (the canvas is also hidden by CSS there).
  (function(){
    const canvas = document.getElementById('dustCanvas');
    if (!canvas || getComputedStyle(canvas).display === 'none') return;
    const ctx = canvas.getContext('2d');"""),
("""  (function(){
    const tiltEls = document.querySelectorAll('.service-card, .product-cat-card, .blog-card, .partner-box');
    tiltEls.forEach(el=>{
      el.style.transition = 'transform .25s ease, box-shadow .25s ease';
      el.style.willChange = 'transform';
      el.addEventListener('mousemove', (e)=>{
        const rect = el.getBoundingClientRect();
        const px = (e.clientX - rect.left) / rect.width - 0.5;
        const py = (e.clientY - rect.top) / rect.height - 0.5;
        const rotX = (py * -6).toFixed(2);
        const rotY = (px * 8).toFixed(2);
        el.style.transform = `perspective(700px) rotateX(${rotX}deg) rotateY(${rotY}deg) scale(1.02) translateZ(0)`;
        el.style.boxShadow = `${(-px*18).toFixed(0)}px ${(12-py*10).toFixed(0)}px 34px rgba(0,0,0,0.45)`;
      });
      el.addEventListener('mouseleave', ()=>{
        el.style.transform = 'perspective(700px) rotateX(0deg) rotateY(0deg) scale(1)';
        el.style.boxShadow = 'none';
      });
    });
  })();""", """  // Updates are batched to at most one per animation frame.
  (function(){
    if (!finePointer) return;
    const tiltEls = document.querySelectorAll('.service-card, .product-cat-card, .blog-card, .partner-box');
    tiltEls.forEach(el=>{
      el.style.transition = 'transform .25s ease, box-shadow .25s ease';
      let pending = null;
      el.addEventListener('mousemove', (e)=>{
        const first = !pending;
        pending = e;
        if (!first) return;
        requestAnimationFrame(()=>{
          if (!pending) return;
          const rect = el.getBoundingClientRect();
          const px = (pending.clientX - rect.left) / rect.width - 0.5;
          const py = (pending.clientY - rect.top) / rect.height - 0.5;
          pending = null;
          const rotX = (py * -6).toFixed(2);
          const rotY = (px * 8).toFixed(2);
          el.style.transform = `perspective(700px) rotateX(${rotX}deg) rotateY(${rotY}deg) scale(1.02) translateZ(0)`;
          el.style.boxShadow = `${(-px*18).toFixed(0)}px ${(12-py*10).toFixed(0)}px 34px rgba(0,0,0,0.45)`;
        });
      }, { passive: true });
      el.addEventListener('mouseleave', ()=>{
        pending = null;
        el.style.transform = 'perspective(700px) rotateX(0deg) rotateY(0deg) scale(1)';
        el.style.boxShadow = 'none';
      });
    });
  })();"""),
])

# ---------- HTML pages ----------
c = Counter()
FONT_RE = re.compile(r'<link href="(https://fonts\.googleapis\.com/css2\?[^"]+)" rel="stylesheet">')
VERSION = '4'   # bump when style.css / script.js change
for f in sorted(glob.glob('**/*.html', recursive=True)):
    if f.startswith('google'):
        continue
    s = open(f, encoding='utf-8').read(); o = s
    s, k = re.subn(r'(href="(?:\.\./)?style\.css)(?:\?v=\d+)?"', rf'\1?v={VERSION}"', s); c['css-v'] += k
    s, k = re.subn(r'(src="(?:\.\./)?script\.js)(?:\?v=\d+)?"', rf'\1?v={VERSION}"', s); c['js-v'] += k
    def font(m):
        u = m.group(1)
        return (f'<link rel="preload" as="style" href="{u}" onload="this.onload=null;this.rel=\'stylesheet\'">'
                f'<noscript><link rel="stylesheet" href="{u}"></noscript>')
    s, k = FONT_RE.subn(font, s); c['fonts'] += k
    s, k = re.subn(r'<img src="((?:\.\./)?images/img-[^"]+)"(?! loading)', r'<img loading="lazy" decoding="async" src="\1"', s); c['lazy'] += k
    if f.endswith('index.html') and 'rel="preload" as="image"' not in s:
        m = re.search(r"img: '((?:\.\./)?images/[^']+)'", s)
        tag = f'<link rel="preload" as="image" href="{m.group(1)}" fetchpriority="high">\n'
        s, k = re.subn(r'(<link rel="preconnect" href="https://fonts\.googleapis\.com">)', lambda mm: tag + mm.group(1), s, count=1); c['hero-preload'] += k
    if s != o:
        open(f, 'w', encoding='utf-8').write(s); c['files'] += 1
print(dict(c))
