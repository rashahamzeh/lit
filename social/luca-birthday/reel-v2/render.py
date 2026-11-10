# Frame-by-frame renderer for Luca's birthday reel (1080x1920 @30fps, 120 BPM beat grid).
import math, random, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

W, H, FPS, DUR = 1080, 1920, 30, 44.0
BEAT = 0.5
GREEN = (11, 31, 23); CREAM = (242, 237, 228); YEL = (255, 207, 0); GOLD = (201, 150, 10)

def lo(p): return Image.open(p)
PH = {k: lo(f'ph/{v}.jpg').convert('RGB') for k, v in dict(
    beach='n1', dinner='n2', bday='n3', dinoday='n4', bowl='n5', dinonight='n6', studio='n7',
    interview='n9', signing='n10', fan='n12', selfie='n13', book='book', dsc='dsc').items()}
PH['book'] = PH['book'].crop((40, 0, PH['book'].width, PH['book'].height))
SP = {k: lo(f'sp/{k}.png').convert('RGBA') for k in [
    'today', 'voice', 'luca', 'allam', 'host', 'speaker', 'author', 'legend', 'bestseller', 'launch',
    'talkhuman', 'sig', 'role', 'husband', 'dad', 'best', 'dadw', 'ever', 'kingpin', 'gameon',
    'hbd', 'lucay', 'from', 'lit', 'butwe', 'remember', 'you', 'lucabox', 'logo_white']}
CUT = lo('../reel/Luca_Cutout.png').convert('RGBA')

# ---------- helpers ----------
cl = lambda x: max(0.0, min(1.0, x))
eo = lambda x: 1 - (1 - cl(x)) ** 3
ei = lambda x: cl(x) ** 3
def eob(x, s=1.9):
    x = cl(x) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
prog = lambda t, t0, d: cl((t - t0) / d)

def cover(img, zoom=1.0, fx=.5, fy=.5, w=W, h=H):
    iw, ih = img.size; ar = w / h
    cw, ch = (ih * ar, ih) if iw / ih > ar else (iw, iw / ar)
    cw /= zoom; ch /= zoom
    x = min(max(fx * iw - cw / 2, 0), iw - cw); y = min(max(fy * ih - ch / 2, 0), ih - ch)
    return img.resize((w, h), Image.BILINEAR, box=(x, y, x + cw, y + ch))

def paste(cv, spr, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if alpha <= 0.01 or scale <= 0.01: return
    s = spr
    if abs(scale - 1) > 1e-3: s = s.resize((max(1, int(s.width * scale)), max(1, int(s.height * scale))), Image.BILINEAR)
    if abs(rot) > 0.05: s = s.rotate(rot, Image.BICUBIC, expand=True)
    if alpha < 0.999:
        a = s.getchannel('A').point(lambda v: int(v * alpha)); s = s.copy(); s.putalpha(a)
    cv.paste(s, (int(cx - s.width / 2), int(cy - s.height / 2)), s)

def solid(c): return Image.new('RGB', (W, H), c)
def radial(c0, c1, cy=.42):
    y, x = np.mgrid[0:H, 0:W]; d = np.sqrt(((x - W / 2) / (W * .9)) ** 2 + ((y - H * cy) / (H * .55)) ** 2)
    k = np.clip(d / .72, 0, 1)[..., None]
    return Image.fromarray((np.array(c0) * (1 - k) + np.array(c1) * k).astype(np.uint8))
BG_DARK = radial((30, 67, 52), GREEN)
def grad_bottom(h=900, a=235):
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); arr = np.zeros((H, W, 4), np.uint8); arr[..., :3] = GREEN
    ramp = np.clip((np.arange(H) - (H - h)) / h, 0, 1) ** 1.3 * a; arr[..., 3] = ramp[:, None]
    return Image.fromarray(arr)
GRAD = grad_bottom(); GRAD_TOP = GRAD.transpose(Image.FLIP_TOP_BOTTOM); GRAD_LITE = grad_bottom(700, 150)

def card(img, w, fx=.5, fy=.5, ar=.8, border=22, bottom=70):
    h = int(w / ar); ph = cover(img, 1.0, fx, fy, w, h)
    c = Image.new('RGBA', (w + 2 * border + 60, h + border + bottom + 60), (0, 0, 0, 0))
    sh = Image.new('RGBA', c.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle((36, 42, 30 + w + 2 * border, 36 + h + border + bottom), fill=(0, 0, 0, 120))
    c = Image.alpha_composite(c, sh.filter(ImageFilter.GaussianBlur(14)))
    ImageDraw.Draw(c).rectangle((30, 30, 30 + w + 2 * border, 30 + h + border + bottom), fill=(255, 255, 255, 255))
    c.paste(ph, (30 + border, 30 + border)); return c

CARDS = dict(selfie=card(PH['selfie'], 520, .5, .42), dinner=card(PH['dinner'], 520, .5, .33),
             beach=card(PH['beach'], 470, .5, .55), bday=card(PH['bday'], 470, .55, .45),
             dinoday=card(PH['dinoday'], 520, .48, .5, ar=1.0))
BOOK = card(PH['book'], 620, .5, .5, ar=PH['book'].width / PH['book'].height, border=0, bottom=0)

def pulse(t, start=4.0):
    if t < start: return 1.0
    return 1 + .035 * math.exp(-((t - start) % BEAT) * 9)

# ---------- snippet frames ----------
def load_seg(ss, d):
    p = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(ss), '-t', str(d), '-i', 'src.mp4', '-vf', f'fps={FPS},scale=1080:-2',
                        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    fh = len(p) // (1080 * 3) // int(d * FPS)
    arr = np.frombuffer(p, np.uint8).reshape(-1, fh, 1080, 3); return [Image.fromarray(a) for a in arr]
SEG1 = load_seg(2.0, 2.1); SEG2 = load_seg(20.4, 5.1)
def snippet(seg, u):
    f = seg[min(len(seg) - 1, int(u * FPS))]
    bg = f.resize((54, 96), Image.BILINEAR, box=(f.width * .2, 0, f.width * .8, f.height)).filter(ImageFilter.GaussianBlur(3)).resize((W, H), Image.BILINEAR)
    bg = Image.blend(bg, solid((0, 0, 0)), .75)
    z = 1.08 - .08 * eo(u / .5) + .02 * u
    fg = f.resize((int(W * z), int(f.height * z)), Image.BILINEAR)
    bg.paste(fg, ((W - fg.width) // 2, (H - fg.height) // 2))
    d = ImageDraw.Draw(bg); y0 = (H - fg.height) // 2
    d.rectangle((0, y0 - 8, W, y0 - 2), fill=YEL); d.rectangle((0, y0 + fg.height + 2, W, y0 + fg.height + 8), fill=YEL)
    return bg

# ---------- particles ----------
rnd = random.Random(5)
BOKEH = [(rnd.random() * W, rnd.random() * H, 3 + rnd.random() * 9, .2 + rnd.random() * .6, rnd.random() * 6.28) for _ in range(40)]
def bokeh(cv, t, col=GOLD):
    d = ImageDraw.Draw(cv, 'RGBA')
    for x, y, r, sp, ph in BOKEH:
        yy = (y - t * 60 * sp) % H; xx = x + 20 * math.sin(t * sp + ph); a = int(90 + 80 * math.sin(t * 2 + ph))
        d.ellipse((xx - r, yy - r, xx + r, yy + r), fill=col + (max(0, a),))
CONF = []
for i in range(160):
    ang = rnd.uniform(-math.pi, 0); sp = rnd.uniform(900, 2300)
    CONF.append(dict(vx=math.cos(ang) * sp * .8, vy=math.sin(ang) * sp, w=rnd.uniform(12, 26), h=rnd.uniform(8, 14),
                     rot=rnd.uniform(0, 360), vr=rnd.uniform(-720, 720), col=[YEL, GOLD, CREAM, (62, 122, 94)][i % 4],
                     x0=W / 2 + rnd.uniform(-80, 80), y0=1000 + rnd.uniform(-40, 40)))
def confetti(cv, u):
    d = ImageDraw.Draw(cv)
    for c in CONF:
        tt = u; drag = math.exp(-tt * 1.6)
        x = c['x0'] + c['vx'] * (1 - drag) / 1.6; y = c['y0'] + c['vy'] * (1 - drag) / 1.6 + 380 * tt * tt * .5 + 120 * tt
        if y > H + 40: continue
        r = math.radians(c['rot'] + c['vr'] * tt); flip = abs(math.cos(tt * 6 + c['rot']))
        hw, hh = c['w'] / 2, c['h'] / 2 * (0.3 + .7 * flip)
        pts = [(x + px * math.cos(r) - py * math.sin(r), y + px * math.sin(r) + py * math.cos(r)) for px, py in [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]]
        d.polygon(pts, fill=c['col'])

# ---------- scenes (u = local time) ----------
def s_intro(u):
    cv = BG_DARK.copy(); bokeh(cv, u)
    p1 = eo(prog(u, .4, .6)); paste(cv, SP['today'], W / 2, 800 + 60 * (1 - p1), 1, p1)
    p2 = prog(u, 1.5, .55); paste(cv, SP['voice'], W / 2, 1010, .6 + .4 * eob(p2), cl(p2 * 2))
    if u > 2.5:  # little beat bounces as the riser builds
        k = math.exp(-((u - 2.5) % .25) * 14) * .03
        cv = zoom_frame(cv, 1 + k + .25 * ei(prog(u, 3.2, .8)))
    return cv

def s_portrait(u):
    t = 4 + u; z = 1.5 - .35 * eo(u / .7) - .04 * u
    cv = cover(PH['studio'], z * pulse(t), .47, .33).convert('RGBA')
    cv.alpha_composite(GRAD)
    p = eo(prog(u, .05, .35)); paste(cv, SP['luca'], -400 + (W / 2 + 400) * p, 1330)
    p = eo(prog(u, .3, .35)); paste(cv, SP['allam'], W + 500 - (W / 2 + 500) * p, 1560)
    return cv.convert('RGB')

WORDS = [('host', 'studio', 2.8, .47, .27, -4), ('speaker', 'interview', 2.2, .66, .34, 3),
         ('author', 'signing', 2.3, .58, .27, -3), ('legend', 'fan', 2.2, .2, .42, 4)]
def s_words(u):
    i = min(3, int(u / BEAT)); w, img, z, fx, fy, rot = WORDS[i]; v = u - i * BEAT
    cv = cover(PH[img], z * (1.12 - .12 * eo(v / .3)), fx, fy).convert('RGBA'); cv.alpha_composite(GRAD)
    paste(cv, SP[w], W / 2, 1500, 1.8 - .8 * eob(v / .22), 1, rot)
    return cv.convert('RGB')

def s_snip1(u): return snippet(SEG1, u)
def s_snip2(u): return snippet(SEG2, u)

def s_book(u):
    t = 10 + u; cv = BG_DARK.copy(); bokeh(cv, t, YEL)
    p = eob(prog(u, 0, .5), 1.4); fl = 8 * math.sin(u * 3)
    paste(cv, BOOK, W / 2, 860 + fl, (.35 + .65 * p) * pulse(t), cl(p * 3), -25 + 20 * p)
    q = prog(u, .75, .18); paste(cv, SP['bestseller'], W / 2, 1560, 2.0 - 1.28 * eo(q), cl(q * 3), 6 - 11 * eo(q))
    return cv

def s_interview(u):
    t = 12 + u; z = 1.15 + .7 * eo(u / 1.9); fx = .5 + (.66 - .5) * eo(u / 1.9); fy = .5 + (.36 - .5) * eo(u / 1.9)
    cv = cover(PH['interview'], z * pulse(t), fx, fy).convert('RGBA'); cv.alpha_composite(GRAD); cv.alpha_composite(GRAD_TOP)
    p = eo(prog(u, .2, .4)); paste(cv, SP['launch'], W / 2, 230 - 40 * (1 - p), 1, p)
    p = prog(u, .45, .4); paste(cv, SP['talkhuman'], W / 2, 1620, .7 + .3 * eob(p), cl(p * 2))
    return cv.convert('RGB')

def s_signing(u):
    t = 14 + u
    if u < 1.0: cv = cover(PH['signing'], (1.0 + .15 * u) * pulse(t), .47, .5)
    else:
        v = u - 1; cv = cover(PH['signing'], (2.6 - .5 * eo(v / .4)) * pulse(t), .58, .28)
    cv = cv.convert('RGBA'); cv.alpha_composite(GRAD)
    p = prog(u, .35, .45); paste(cv, SP['sig'], W / 2, 1600, .8 + .2 * eob(p), cl(p * 2))
    return cv.convert('RGB')

def s_split(u):
    t = 16 + u; cv = solid(GREEN); hh = 950
    p1 = eo(prog(u, 0, .35)); top = cover(PH['dsc'], 1.05 * pulse(t), .5, .38, W, hh)
    cv.paste(top, (int(-W * (1 - p1)), 0))
    p2 = eo(prog(u, .25, .35)); bot = cover(PH['fan'], 1.35 * pulse(t), .3, .45, W, H - hh - 20)
    cv.paste(bot, (int(W * (1 - p2)), hh + 20))
    ImageDraw.Draw(cv).rectangle((0, hh, int(W * eo(prog(u, .4, .4))), hh + 20), fill=YEL)
    return cv

def s_remember(u):
    t = 23 + u; cv = BG_DARK.copy().convert('RGBA'); bokeh(cv, t, YEL)
    m = eo(prog(u, 1.0, .35))  # lines glide up when the beat hits
    if u >= 1.0:
        g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse((90, 520, 990, 1420), fill=YEL + (60,))
        cv.alpha_composite(g.filter(ImageFilter.GaussianBlur(120)))
        q = eo(prog(u, 1.0, .45)); z = 1.06 - .06 * q
        cut = CUT.resize((int(1080 * z * pulse(t, 24)), int(1080 * z * pulse(t, 24) * CUT.height / CUT.width)), Image.BILINEAR)
        cv.alpha_composite(cut, (int(W / 2 - cut.width / 2), int(H - cut.height + 500 * (1 - q) + 40)))
        cv.alpha_composite(grad_bottom(520, 170) if False else GRAD_LITE)
    p = eo(prog(u, .05, .45)); paste(cv, SP['butwe'], W / 2, 770 - 530 * m + 40 * (1 - p), 1, p)
    p = prog(u, .5, .3); paste(cv, SP['remember'], W / 2, 930 - 520 * m, .75 + .25 * eob(p), cl(p * 2))
    q = prog(u, 1.0, .2); paste(cv, SP['you'], W / 2, 1290, (2.4 - 1.4 * eob(q)) * pulse(t, 24), cl(q * 3))
    q = prog(u, 1.5, .2); paste(cv, SP['lucabox'], W / 2, 1610, (2.4 - 1.4 * eob(q)) * pulse(t, 24), cl(q * 3), -3 * eo(q))
    return cv.convert('RGB')

def s_role(u):
    cv = solid(CREAM)
    p = eo(prog(u, .05, .5)); paste(cv, SP['role'], W / 2, 330 + 50 * (1 - p), 1, p)
    for name, t0, x, y, r in [('selfie', .75, 330, 1050, -8), ('dinner', 1.25, 760, 1100, 7)]:
        q = prog(u, t0, .4)
        if q > 0: paste(cv, CARDS[name], x, y - 900 * (1 - eob(q, 1.2)), .82, 1, r + 15 * (1 - eo(q)))
    q = prog(u, 1.5, .2); paste(cv, SP['husband'], W / 2, 1720, 2 - eob(q), cl(q * 3), -3)
    return cv

def s_dad(u):
    cv = solid(CREAM)
    for name, t0, x, y, r in [('beach', 0, 300, 640, -7), ('bday', .5, 790, 820, 6), ('dinoday', 1.0, 540, 1220, -3)]:
        q = prog(u, t0, .4)
        if q > 0: paste(cv, CARDS[name], x, y - 1000 * (1 - eob(q, 1.2)), .85, 1, r + 18 * (1 - eo(q)))
    q = prog(u, 1.25, .22); paste(cv, SP['dad'], W / 2, 1710, 2.4 - 1.4 * eob(q), cl(q * 3), -4)
    if u > 1.6: cv = zoom_frame(cv, 1 + .5 * ei(prog(u, 1.6, .4)))
    return cv

def s_best(u):
    t = 30 + u
    if u < 1.0: cv = cover(PH['dinoday'], (1.35 - .25 * eo(u / .5)) * pulse(t), .47, .5)
    else: cv = cover(PH['dinonight'], (1.25 - .15 * eo((u - 1) / .5)) * pulse(t), .55, .5)
    cv = cv.convert('RGBA'); cv.alpha_composite(GRAD)
    for i, (k, y) in enumerate([('best', 1330), ('dadw', 1500), ('ever', 1670)]):
        q = prog(u, i * BEAT, .2); paste(cv, SP[k], W / 2, y, 1.8 - .8 * eob(q), cl(q * 3))
    return cv.convert('RGB')

def s_bowl(u):
    t = 32 + u
    z = 2.4 if u < .5 else 2.4 - 1.3 * eo((u - .5) / .45)
    fy = .29 if u < .5 else .29 + (.45 - .29) * eo((u - .5) / .45)
    cv = cover(PH['bowl'], z * pulse(t), .47, fy).convert('RGBA'); cv.alpha_composite(GRAD)
    q = prog(u, .5, .2); paste(cv, SP['kingpin'], W / 2, 330, 2.2 - 1.2 * eob(q), cl(q * 3), -6)
    q = prog(u, 1.0, .4); paste(cv, SP['gameon'], W / 2, 1660, .7 + .3 * eob(q), cl(q * 2))
    return cv.convert('RGB')

GRID = [('selfie', .5, .45), ('bday', .6, .4), ('signing', .48, .5), ('studio', .47, .3)]
def s_grid(u):
    t = 34 + u; cv = solid(GREEN); tw, th = (W - 18) // 2, (H - 18) // 2
    pos = [(6, 6), (12 + tw, 6), (6, 12 + th), (12 + tw, 12 + th)]; dirs = [(-1, 0), (0, -1), (0, 1), (1, 0)]
    for i, ((k, fx, fy), (x, y), (dx, dy)) in enumerate(zip(GRID, pos, dirs)):
        q = eo(prog(u, i * .25, .3))
        if q <= 0: continue
        tile = cover(PH[k], 1.15 * pulse(t) + .05 * u, fx, fy, tw, th)
        cv.paste(tile, (int(x + dx * W * (1 - q)), int(y + dy * H * (1 - q))))
    if u > 1.5: cv = zoom_frame(cv, 1 + 1.0 * ei(prog(u, 1.55, .45)))
    return cv

FLIPS = [('dinner', .45, .33), ('beach', .5, .5), ('interview', .66, .36), ('fan', .22, .42),
         ('dinonight', .55, .45), ('bowl', .47, .35), ('dsc', .45, .4), ('studio', .47, .3)]
def s_flips(u):
    i = min(7, int(u / .25)); k, fx, fy = FLIPS[i]; v = u - i * .25
    return cover(PH[k], (1.6 - .35 * eo(v / .2)), fx, fy)

def s_finale(u):
    t = 38 + u; cv = BG_DARK.copy().convert('RGBA'); bokeh(cv, t, YEL)
    q = prog(u, .5, .7); cut = CUT.resize((980, int(980 * CUT.height / CUT.width)), Image.BILINEAR)
    cv.alpha_composite(cut, (int(W / 2 - 490), int(1180 + 600 * (1 - eo(q)))))
    g = grad_bottom(380, 200) if False else None
    paste(cv, SP['logo_white'], W / 2, 250, .55 * eob(prog(u, 0, .4)), 1)
    q = prog(u, .25, .35); paste(cv, SP['hbd'], W / 2, 560, (.6 + .4 * eob(q)) * pulse(t), cl(q * 3))
    q = prog(u, .75, .4); paste(cv, SP['lucay'], W / 2, 840, (1.7 - .7 * eob(q)) * pulse(t), cl(q * 3), 4 * (1 - eo(q)))
    q = prog(u, 1.6, .5); paste(cv, SP['from'], W / 2, 1040 + 20 * (1 - eo(q)), 1, q)
    q = prog(u, 2.0, .5); paste(cv, SP['lit'], W / 2, 1110, 1, q)
    confetti(cv, u)
    return cv.convert('RGB')

def zoom_frame(img, z):
    if z <= 1.001: return img
    cw, ch = W / z, H / z; return img.resize((W, H), Image.BILINEAR, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))

SCENES = [(0, 4, s_intro), (4, 6, s_portrait), (6, 8, s_words), (8, 10, s_snip1), (10, 12, s_book),
          (12, 14, s_interview), (14, 16, s_signing), (16, 18, s_split), (18, 23, s_snip2), (23, 26, s_remember),
          (26, 28, s_role), (28, 30, s_dad), (30, 32, s_best), (32, 34, s_bowl), (34, 36, s_grid), (36, 38, s_flips), (38, 44.1, s_finale)]
# transitions at scene starts: type, duration
TRANS = {8: ('whip', .2), 10: ('whip', .2), 12: ('push_l', .3), 14: ('push_u', .3), 16: ('whip', .2),
         18: ('push_l', .3), 32: ('push_l', .3), 34: ('whip', .2)}
FLASH = {4: 1.0, 6: .35, 24: 1.0, 24.5: .5, 26: .9, 30: 1.0, 31: .6, 36: .5, 36.25: .35, 36.5: .35, 36.75: .35, 37: .35, 37.25: .35, 37.5: .35, 37.75: .5, 38: 1.0}
SHAKE = [(4, 22), (6, 10), (6.5, 10), (7, 10), (7.5, 10), (10.75, 18), (17, 8), (24, 30), (24.5, 26), (27.5, 10), (29.25, 16), (30, 24), (30.5, 14), (31, 14), (32.5, 20), (38, 22), (38.75, 14)]

def scene_at(t):
    for a, b, f in SCENES:
        if a <= t < b: return a, f
    return SCENES[-1][0], SCENES[-1][2]

def whip(img, amt):
    a = np.asarray(img).astype(np.float32); acc = np.zeros_like(a); n = 7
    for k in range(n): acc += np.roll(a, int((k - n / 2) * amt / n), axis=1)
    return Image.fromarray((acc / n).astype(np.uint8))

def frame(t):
    a, f = scene_at(t); img = f(t - a)
    # transitions
    for T, (kind, d) in TRANS.items():
        if kind == 'whip' and abs(t - T) < d / 2:
            x = 1 - abs(t - T) / (d / 2); img = whip(img, 260 * x)
            img = img.transform(img.size, Image.AFFINE, (1, 0, (-1 if t < T else 1) * 140 * x, 0, 1, 0))
        if kind.startswith('push') and T <= t < T + d:
            pa, pf = scene_at(T - 1e-3); prev = pf(t - pa); e = eo((t - T) / d)
            cv = Image.new('RGB', (W, H))
            if kind == 'push_l': cv.paste(prev, (int(-W * e), 0)); cv.paste(img, (int(W * (1 - e)), 0))
            else: cv.paste(prev, (0, int(-H * e))); cv.paste(img, (0, int(H * (1 - e))))
            img = cv
    # shake
    sx = sy = 0
    for t0, amp in SHAKE:
        if 0 <= t - t0 < .3:
            k = amp * math.exp(-(t - t0) * 12); sx += k * math.sin(t * 97); sy += k * math.cos(t * 83)
    if sx or sy:
        img = zoom_frame(img, 1.04); img = img.transform(img.size, Image.AFFINE, (1, 0, sx, 0, 1, sy))
    # flash
    for T, a0 in FLASH.items():
        if 0 <= t - T < .25:
            img = Image.blend(img, solid((255, 255, 255)), a0 * (1 - (t - T) / .25) ** 2)
    # global fade in/out
    if t < .3: img = Image.blend(solid((0, 0, 0)), img, t / .3)
    if t > DUR - .8: img = Image.blend(img, solid((0, 0, 0)), (t - (DUR - .8)) / .8)
    return img

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'preview':
        ts = [float(x) for x in sys.argv[2].split(',')]
        ims = [frame(t).resize((270, 480)) for t in ts]
        cols = 8; rows = (len(ims) + cols - 1) // cols; S = Image.new('RGB', (cols * 275, rows * 485), 'white')
        for i, im in enumerate(ims): S.paste(im, ((i % cols) * 275, (i // cols) * 485))
        S.save('preview.png'); sys.exit()
    n = int(DUR * FPS)
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-i', 'music3.wav', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', 'reel3.mp4'], stdin=subprocess.PIPE)
    for i in range(n):
        ff.stdin.write(frame(i / FPS).tobytes())
        if i % 150 == 0: print(i, flush=True)
    ff.stdin.close(); ff.wait(); print('done')
