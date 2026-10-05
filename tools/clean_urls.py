"""Make internal links use clean addresses (no 'index', no '.html').

  index        -> ./          en/index      -> en/        ../index -> ../
  about.html   -> about       https://norapaslanmazcelik.com/index -> https://norapaslanmazcelik.com/

Pairs with the redirect rules in tools/htaccess-new.txt, which send old
addresses to the clean ones. Safe to run more than once.
Run from the repository root:  python3 tools/clean_urls.py
"""
import glob, re
from collections import Counter

SITE = 'https://norapaslanmazcelik.com/'
c = Counter()

def clean(v):
    absolute = v.startswith('http')
    if absolute and not v.startswith(SITE):
        return v
    if v.startswith(('mailto:', 'tel:', '#', 'javascript:')):
        return v
    m = re.match(r'^([^#?]*)([#?].*)?$', v)
    path, tail = m.group(1), m.group(2) or ''
    if path.endswith('.html'):
        path = path[:-5]
    if path == 'index' or path.endswith('/index'):
        path = path[:-5]
        if path == '':
            path = './'
    return path + tail

def href(m):
    v = m.group(2)
    n = clean(v)
    if n != v:
        c['href'] += 1
    return f'{m.group(1)}"{n}"'

def jslink(m):
    v = m.group(2)
    n = clean(v)
    if n != v:
        c['js-link'] += 1
    return f"{m.group(1)}'{n}'"

for f in sorted(glob.glob('**/*.html', recursive=True)):
    if f.startswith('google'):
        continue
    s = open(f, encoding='utf-8').read(); o = s
    s = re.sub(r'(\bhref=)"([^"]*)"', href, s)
    s = re.sub(r"(\blink:\s*)'([^']*)'", jslink, s)
    if s != o:
        open(f, 'w', encoding='utf-8').write(s); c['files'] += 1
print(dict(c))
