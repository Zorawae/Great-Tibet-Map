#!/usr/bin/env python3
"""Choose where each river and range name sits on its own line.

Eleven names competing with the towns, the country names and each other is not
something to place by eye, so it is searched: for every feature, how far along
its line the name sits and how far it is pushed off it.

Labels are rotated, so they are compared as oriented rectangles rather than by
their axis-aligned bounds -- an angled name's bounding box is several times its
real footprint, and using it rejects placements that are in fact clear.

Run tools/measure-labels.py first; it writes measured.json with each name's true
size and every obstacle, read from the rendered widget in SVG user units.

    python3 tools/measure-labels.py
    python3 tools/place-labels.py      # writes placement.json

The chosen numbers go back into the RANGES and RIVERS tables in
tools/build-physical.py.
"""
import json, math, os, re, sys, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('bp', os.path.join(HERE, 'build-physical.py'))
bp = importlib.util.module_from_spec(spec); spec.loader.exec_module(bp)

src = open(os.path.join(HERE, os.pardir, 'tibet-three-regions-map.html'), encoding='utf-8').read()
DATA = json.loads(re.search(r'var DATA = (\{.*?\});\n', src, re.S).group(1))
M = json.load(open(os.path.join(HERE, 'measured.json'))); SIZE = M['labels']

GANG = {'Duldza Zalmo gang', 'Tshawa gang', 'Markham gang',
        'Pobar gang', 'Mardza gang', 'Minya gang'}
TIBET = bp.rings_of(DATA['outline'])
KHAM = bp.rings_of(DATA['regions']['kham']['d'])
PAD = 2.5
FRACS = [i / 100 for i in range(4, 97, 2)]
# A name that cannot fit near its own crest may move further off it; the widget
# draws a leader line past 30 units so it stays clear which ridge it belongs to.
DYS = list(range(-64, -5, 3)) + list(range(8, 65, 3))


def corners(cx, cy, w, h, ang):
    a = math.radians(ang); c, s = math.cos(a), math.sin(a)
    return [(cx + dx * c - dy * s, cy + dx * s + dy * c)
            for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]


def label_quad(anchor, ang, w, h, dy):
    a = math.radians(ang)
    cx = anchor[0] - dy * math.sin(a) + (h * 0.30) * math.sin(a)
    cy = anchor[1] + dy * math.cos(a) - (h * 0.30) * math.cos(a)
    return corners(cx, cy, w + PAD * 2, h + PAD * 2, ang)


def overlap(A, B):
    """Separating-axis test; 0 when the two quads do not touch."""
    for P, Q in ((A, B), (B, A)):
        for i in range(len(P)):
            ex, ey = P[(i + 1) % len(P)][0] - P[i][0], P[(i + 1) % len(P)][1] - P[i][1]
            nx, ny = -ey, ex
            n = math.hypot(nx, ny) or 1; nx, ny = nx / n, ny / n
            pa = [x * nx + y * ny for x, y in P]; pb = [x * nx + y * ny for x, y in Q]
            if max(pa) < min(pb) or max(pb) < min(pa):
                return 0.0
    depth = 1e9
    for P, Q in ((A, B), (B, A)):
        for i in range(len(P)):
            ex, ey = P[(i + 1) % len(P)][0] - P[i][0], P[(i + 1) % len(P)][1] - P[i][1]
            nx, ny = -ey, ex
            n = math.hypot(nx, ny) or 1; nx, ny = nx / n, ny / n
            pa = [x * nx + y * ny for x, y in P]; pb = [x * nx + y * ny for x, y in Q]
            depth = min(depth, min(max(pa) - min(pb), max(pb) - min(pa)))
    return depth * depth


# Town names, rivers and other labels are hard obstacles: a name must not touch
# them.  The region titles are not obstacles at all.  They are set large and
# translucent and step back when a physical layer is on -- they are drawn to be
# underlapped, so a name crossing one is not a fault to be priced.  Scoring them
# even at 6% of a squared penetration depth was enough to push Mardza Gang 32
# units off its own crest to clear a title it was meant to sit under, so
# permeable obstacles are left out of the search entirely.
OB = [(o, corners(o['x'] + o['w'] / 2, o['y'] + o['h'] / 2, o['w'], o['h'], 0), 1.0)
      for o in M['obstacles'] if o['kind'] != 'region']

# A rim range clipped away to nothing -- Karakoram lies wholly outside the
# outline -- still needs a line to hang its name on, so fall back to the full
# spine. Without this the search raised ValueError and every later run
# silently reused the previous placement.
FEATURES = ([(g['en'], 'range',
             [r for r in bp.rings_of(g['d']) if len(r) > 1]
             or [r for r in bp.rings_of(g.get('dFull', '')) if len(r) > 1])
            for g in DATA['ranges']] +
            [(r['en'], 'river', bp.rings_of(r['d'])) for r in DATA['rivers']] +
            [(k['en'], 'peak', [[tuple(k['p'])]]) for k in DATA['peaks']])

# A peak is a point, so its name is tried on a ring of positions round the
# marker rather than slid along a line.  This is what moves Chomolungma off
# the Himalayan crest, which its fixed "below the marker" position sat on.
PEAK_SPOTS = [(dx, dy) for r in (14, 24, 38, 54)
              for dx, dy in ((0, r), (0, -r), (r, 6), (-r, 6),
                             (r * 0.7, -r * 0.7), (-r * 0.7, -r * 0.7),
                             (r * 0.7, r * 0.7), (-r * 0.7, r * 0.7))]

def place_one(name, kind, runs, others):
    """Best position for one label given every other label's current box."""
    w, h = SIZE[name]['w'], SIZE[name]['h']
    if kind == 'peak':
        px, py = runs[0][0]
        cands = [({'p': (px + dx, py + dy), 'a': 0.0}, 0, (dx, dy)) for dx, dy in PEAK_SPOTS]
    else:
        runs = [r for r in runs if len(r) > 1]
        cands = []
        for dy in DYS:
            for f in FRACS:
                lab = bp.label_anchor(runs, f)
                if lab:
                    cands.append((lab, dy, (f, dy)))
    best = None
    for lab, dy, key in cands:
        if True:
            Q = label_quad(lab['p'], lab['a'], w, h, dy)
            cost = sum(overlap(Q, q) * wt for _, q, wt in OB) + sum(overlap(Q, q) for q in others)
            xs = [p[0] for p in Q]; ys = [p[1] for p in Q]
            cx, cy = sum(xs) / 4, sum(ys) / 4
            # the layers are clipped to Tibet, so the names belong inside it too
            if not bp.inside(TIBET, cx, cy):
                cost += 4000
            if name in GANG and not bp.inside(KHAM, cx, cy):
                cost += 150
            if kind == 'peak':
                cost += (abs(key[0]) + abs(key[1])) * 1.2   # prefer close to the marker
            else:
                # gentle: clearing a real overlap must beat hugging the crest
                cost += abs(key[0] - 0.5) * 6 + abs(abs(dy) - 9) * 0.7
            if best is None or cost < best[0]:
                best = (cost, key, Q)
    return best


ITEMS = [(n, k, r) for n, k, r in FEATURES if n in SIZE]
for n, k, r in FEATURES:
    if n not in SIZE:
        sys.stderr.write('no measurement for %r, skipped\n' % n)

boxes, chosen = {}, {}
order = sorted(ITEMS, key=lambda r: -SIZE[r[0]]['w'])
for name, kind, runs in order:                       # first pass, largest first
    got = place_one(name, kind, runs, [boxes[k] for k in boxes])
    if got:
        chosen[name] = list(got[1]); boxes[name] = got[2]

for sweep in range(6):                               # refine until settled
    resid = {n: sum(overlap(boxes[n], q) * wt for _, q, wt in OB)
              + sum(overlap(boxes[n], boxes[m]) for m in boxes if m != n) for n in boxes}
    worst = sorted(resid, key=lambda n: -resid[n])
    if resid[worst[0]] <= 0:
        break
    moved = False
    for name in worst:
        if resid[name] <= 0:
            break
        kind, runs = next((k, r) for n, k, r in ITEMS if n == name)
        got = place_one(name, kind, runs, [boxes[m] for m in boxes if m != name])
        if not got:
            continue
        after = sum(overlap(got[2], q) * wt for _, q, wt in OB) \
              + sum(overlap(got[2], boxes[m]) for m in boxes if m != name)
        if after < resid[name] - 1e-9:
            chosen[name] = list(got[1]); boxes[name] = got[2]; moved = True
    if not moved:
        break

total = 0.0
for name, kind, runs in order:
    if name not in boxes:
        continue
    Q = boxes[name]
    r = sum(overlap(Q, q) * wt for _, q, wt in OB) + sum(overlap(Q, boxes[m]) for m in boxes if m != name)
    total += r
    key = tuple(chosen[name])
    hits = [o['t'][:16] for o, q, wt in OB if overlap(Q, q) > 0] + \
           [m for m in boxes if m != name and overlap(Q, boxes[m]) > 0]
    print('  %-20s %-6s %-18s overlap %6.1f  %s'
          % (name, kind, ('dx %+d dy %+d' % key) if kind == 'peak'
             else ('frac %.2f dy %+d' % key), r,
             ('hits: ' + ', '.join(hits)) if hits else 'clear'))
print('\n  total residual overlap: %.1f'% total)
json.dump(chosen, open(os.path.join(HERE, 'placement.json'), 'w'))
