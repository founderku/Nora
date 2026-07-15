  // Elegant page-to-page transition: intercept same-site link clicks, play a
  // short fade+lift exit animation, then navigate. Entrance animation on the
  // next page is handled purely by CSS (see pageEnter keyframes), so this
  // still degrades gracefully if JS is blocked, links just work instantly.
  (function(){
    document.addEventListener('click', function(e){
      if (e.defaultPrevented || e.button !== 0) return;
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      const a = e.target.closest('a[href]');
      if (!a) return;
      const href = a.getAttribute('href');
      if (!href || href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:')) return;
      if (a.target === '_blank' || a.hasAttribute('download')) return;
      if (/^https?:\/\//i.test(href) && href.indexOf(location.hostname) === -1) return;
      e.preventDefault();
      document.body.classList.add('page-leaving');
      setTimeout(()=>{ window.location.href = href; }, 300);
    });
    // Pages restored from bfcache (browser back/forward) skip the JS re-run,
    // so make sure they're never left stuck mid-exit-animation.
    window.addEventListener('pageshow', function(){
      document.body.classList.remove('page-leaving');
    });
  })();

  // Custom round cursor
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

  // Fullscreen menu toggle
  const menuBtn = document.getElementById('menuBtn');
  const fullMenu = document.getElementById('fullMenu');
  let savedScrollY = 0;
  function openMenu(){
    savedScrollY = window.scrollY;
    fullMenu.classList.add('open');
    menuBtn.classList.add('open');
    menuBtn.style.visibility = 'hidden';
    document.body.style.position = 'fixed';
    document.body.style.top = -savedScrollY + 'px';
    document.body.style.left = '0';
    document.body.style.right = '0';
  }
  function closeMenu(){
    fullMenu.classList.remove('open');
    menuBtn.classList.remove('open');
    menuBtn.style.visibility = 'visible';
    document.body.style.position = '';
    document.body.style.top = '';
    document.body.style.left = '';
    document.body.style.right = '';
    window.scrollTo(0, savedScrollY);
  }
  menuBtn.addEventListener('click', ()=>{
    if (fullMenu.classList.contains('open')) closeMenu(); else openMenu();
  });
  document.getElementById('menuClose').addEventListener('click', closeMenu);

  // Corporate submenu toggle
  const corpToggle = document.getElementById('corporateToggle');
  const corpSub = document.getElementById('corporateSub');
  corpToggle.addEventListener('click', ()=>{
    corpToggle.classList.toggle('active');
    corpSub.classList.toggle('open');
  });

  // Smooth scroll-reveal animations across the site
  const revealEls = document.querySelectorAll('.reveal, .reveal-stagger');
  const revealObserver = new IntersectionObserver((entries)=>{
    entries.forEach(entry=>{
      if (entry.isIntersecting){
        entry.target.classList.add('in');
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15, rootMargin: '0px 0px -60px 0px' });
  revealEls.forEach(el=> revealObserver.observe(el));

  // Ambient dust particles - subtle floating motes across the whole site,
  // drifting upward with gentle drift, giving the page a sense of life
  (function(){
    const canvas = document.getElementById('dustCanvas');
    const ctx = canvas.getContext('2d');
    let W, H, particles = [];
    const COUNT = 46;

    function resize(){
      W = canvas.width = window.innerWidth;
      H = canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    function makeParticle(){
      return {
        x: Math.random() * W,
        y: Math.random() * H,
        r: 0.6 + Math.random() * 1.8,
        speedY: 0.08 + Math.random() * 0.22,
        driftX: (Math.random() - 0.5) * 0.25,
        alpha: 0.15 + Math.random() * 0.35,
        twinkle: Math.random() * Math.PI * 2
      };
    }
    for (let i = 0; i < COUNT; i++) particles.push(makeParticle());

    function tick(){
      ctx.clearRect(0, 0, W, H);
      particles.forEach(p=>{
        p.y -= p.speedY;
        p.x += p.driftX;
        p.twinkle += 0.02;
        if (p.y < -10){ p.y = H + 10; p.x = Math.random() * W; }
        if (p.x < -10) p.x = W + 10;
        if (p.x > W + 10) p.x = -10;
        const flicker = (Math.sin(p.twinkle) + 1) / 2;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255,255,255,${(p.alpha * (0.5 + flicker * 0.5)).toFixed(3)})`;
        ctx.fill();
      });
      requestAnimationFrame(tick);
    }
    tick();
  })();

  // Cursor-reactive tilt on cards - a gentle 3D tilt following the pointer,
  // applied to every card-style element across the site (services, products, blog)
  (function(){
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
  })();
