"""Move every base64-embedded image out of the HTML pages into images/.

Each unique image is written once as a WebP file (the logo also as PNG for
the favicon) and every page then links to that file, so browsers download
each image a single time and cache it across pages.

Run from the repository root:  python3 tools/extract_images.py
Requires Pillow (pip install pillow).
"""
import base64, glob, hashlib, io, os, re
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(ROOT, 'images')
os.makedirs(IMG_DIR, exist_ok=True)

DATA_URI = re.compile(r'data:image/(jpeg|png);base64,([A-Za-z0-9+/=]+)')
MAX_SIDE = 1400        # nothing on the site is shown larger than this
CERT_FULL_W = 800      # certificates page grid
CERT_THUMB_W = 320     # small certificate tiles on the home page

written = {}           # (hash, variant) -> file name


def save(h, raw, variant):
    key = (h, variant)
    if key in written:
        return written[key]
    im = Image.open(io.BytesIO(raw))
    if variant == 'favicon':
        name = 'logo.png'
        im.save(os.path.join(IMG_DIR, name), optimize=True)
    else:
        if im.mode not in ('RGB', 'RGBA'):
            im = im.convert('RGBA' if 'A' in im.getbands() or im.mode == 'P' else 'RGB')
        target_w = {'cert': CERT_FULL_W, 'cert-thumb': CERT_THUMB_W}.get(variant)
        if target_w and im.width > target_w:
            im = im.resize((target_w, round(im.height * target_w / im.width)), Image.LANCZOS)
        elif max(im.size) > MAX_SIDE:
            im.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
        if variant == 'logo':
            name = 'logo.webp'
            im.save(os.path.join(IMG_DIR, name), 'WEBP', lossless=True, method=6)
        else:
            suffix = '' if variant == 'img' else '-' + variant
            name = f'img-{h}{suffix}.webp'
            im.save(os.path.join(IMG_DIR, name), 'WEBP', quality=80, method=6)
    written[key] = name
    return name


def variant_for(page, before):
    tail = before[-300:]
    if 'rel="icon"' in tail[-80:]:
        return 'favicon'
    if 'class="logo-img"' in tail[-60:]:
        return 'logo'
    is_img_tag = tail.endswith('<img src="')
    # On the home pages the only plain <img> tags (besides the logo) are the
    # small certificate tiles of the hl-cert-grid.
    if is_img_tag and os.path.basename(page) == 'index.html':
        return 'cert-thumb'
    if is_img_tag:
        return 'cert'
    return 'img'


total_refs = 0
for page in sorted(glob.glob(os.path.join(ROOT, '**', '*.html'), recursive=True)):
    rel = os.path.relpath(page, ROOT)
    prefix = '../' * rel.count(os.sep) + 'images/'
    s = open(page, encoding='utf-8').read()
    out, pos, n = [], 0, 0
    for m in DATA_URI.finditer(s):
        raw = base64.b64decode(m.group(2))
        h = hashlib.sha1(raw).hexdigest()[:10]
        name = save(h, raw, variant_for(rel, s[:m.start()]))
        out.append(s[pos:m.start()])
        out.append(prefix + name)
        pos = m.end()
        n += 1
    if n:
        out.append(s[pos:])
        open(page, 'w', encoding='utf-8').write(''.join(out))
        total_refs += n
    print(f'{rel}: {n} images replaced')

print(f'TOTAL: {total_refs} references replaced, {len(written)} image files written')
