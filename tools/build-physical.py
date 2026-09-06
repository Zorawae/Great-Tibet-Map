#!/usr/bin/env python3
"""Build the physical-geography layers (rivers, lakes, ranges, peaks) for the widget.

The widget stores geometry already projected into its 1180x745 viewBox, so this
script does the projecting.  The map uses a Lambert Conformal Conic; the exact
parameters were not recorded anywhere, so they are recovered here by fitting the
ten labelled towns, then checked against the stored graticule -- which reproduces
to 0.00-0.11 px in longitude and 0.17-0.58 px in latitude across 25-40 N, the
band Tibet occupies.

Source data is Natural Earth (public domain), which is what lets the result stay
compatible with the project's CC0 dedication.  Download beside this script:

  ne_10m_rivers_lake_centerlines.geojson
  ne_10m_lakes.geojson
      from https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/

Usage:  python3 tools/build-physical.py  >  physical.json
"""
import json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WIDGET = os.path.join(HERE, os.pardir, 'tibet-three-regions-map.html')

# ---------------------------------------------------------------- projection

# Towns carried by the widget, with their real-world positions.  These are the
# control points the projection is recovered from.
TOWNS = {
    'Lhasa': (91.140, 29.650), 'Shigatse': (88.885, 29.267),
    'Ngari (Gar)': (80.100, 32.500), 'Chamdo': (97.178, 31.137),
    'Dartsedo': (101.964, 30.050), 'Jyekundo': (97.008, 33.010),
    'Gyalthang': (99.706, 27.826), 'Xining': (101.778, 36.617),
    'Labrang': (102.511, 35.196), 'Golog': (100.243, 34.472),
}


def _lcc(lon, lat, p1, p2, lon0):
    r = math.radians
    f = lambda p: math.tan(math.pi / 4 + r(p) / 2)
    n = (math.sin(r(p1)) if abs(p1 - p2) < 1e-9 else
         math.log(math.cos(r(p1)) / math.cos(r(p2))) / math.log(f(p2) / f(p1)))
    big_f = math.cos(r(p1)) * f(p1) ** n / n
    rho = big_f / f(lat) ** n
    theta = n * r(lon - lon0)
    return rho * math.sin(theta), -rho * math.cos(theta)


def fit_projection(data):
    """Recover the conic and the affine that maps it into the viewBox."""
    ties = [(TOWNS[c['name']][0], TOWNS[c['name']][1], c['p'][0], c['p'][1])
            for c in data['cities']]

    def solve(p1, p2, lon0):
        pts = [_lcc(lo, la, p1, p2, lon0) + (x, y) for lo, la, x, y in ties]

        def axis(i, j):                      # least squares  target = a*src + b
            n = len(pts)
            sx = sum(q[i] for q in pts); sy = sum(q[j] for q in pts)
            sxx = sum(q[i] * q[i] for q in pts); sxy = sum(q[i] * q[j] for q in pts)
            a = (n * sxy - sx * sy) / (n * sxx - sx * sx)
            b = (sy - a * sx) / n
            return a, b, sum((a * q[i] + b - q[j]) ** 2 for q in pts)

        ax, bx, ex = axis(0, 2); ay, by, ey = axis(1, 3)
        return math.sqrt((ex + ey) / len(pts)), (ax, bx, ay, by)

    best = None
    for i in range(240, 300):                # standard parallel 1: 24.0 - 30.0 N
        for j in range(360, 420):            # standard parallel 2: 36.0 - 42.0 N
            for k in range(880, 960):        # central meridian:    88.0 - 96.0 E
                err, aff = solve(i / 10, j / 10, k / 10)
                if best is None or err < best[0]:
                    best = (err, i / 10, j / 10, k / 10, aff)
    return best


# --------------------------------------------------------------- geometry ops

def simplify(pts, tol):
    """Douglas-Peucker."""
    if len(pts) < 3:
        return pts
    first, last = pts[0], pts[-1]
    dx, dy = last[0] - first[0], last[1] - first[1]
    span = math.hypot(dx, dy)
    worst, idx = -1.0, 0
    for i in range(1, len(pts) - 1):
        px, py = pts[i]
        if span == 0:
            d = math.hypot(px - first[0], py - first[1])
        else:
            d = abs(dy * px - dx * py + last[0] * first[1] - last[1] * first[0]) / span
        if d > worst:
            worst, idx = d, i
    if worst <= tol:
        return [first, last]
    return simplify(pts[:idx + 1], tol)[:-1] + simplify(pts[idx:], tol)


def clip_runs(pts, box):
    """Split a polyline into the runs that fall inside box, keeping one vertex
    of slack either side so lines leave the frame cleanly."""
    x0, y0, x1, y1 = box
    inside = lambda p: x0 <= p[0] <= x1 and y0 <= p[1] <= y1
    runs, cur = [], []
    for i, p in enumerate(pts):
        if inside(p):
            if not cur and i:
                cur.append(pts[i - 1])
            cur.append(p)
        elif cur:
            cur.append(p); runs.append(cur); cur = []
    if cur:
        runs.append(cur)
    return [r for r in runs if len(r) > 1]


def label_anchor(runs, frac=0.45, core=(120.0, 60.0, 1060.0, 700.0)):
    """A point and tangent angle partway along the longest run, for placing the
    feature's name.  Preference is given to the part of the course that falls in
    the middle of the frame, so labels do not end up jammed against an edge."""
    x0, y0, x1, y1 = core
    inner = [r for r in runs
             if any(x0 <= p[0] <= x1 and y0 <= p[1] <= y1 for p in r)] or runs
    run = max(inner, key=lambda r: sum(math.hypot(b[0] - a[0], b[1] - a[1])
                                       for a, b in zip(r, r[1:])))
    seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(run, run[1:])]
    total = sum(seg)
    if total <= 0:
        return None
    want, acc = total * frac, 0.0
    for i, d in enumerate(seg):
        if acc + d >= want:
            t = (want - acc) / d if d else 0
            a, b = run[i], run[i + 1]
            ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
            if ang > 90:
                ang -= 180
            if ang < -90:
                ang += 180
            # A name set along a steep crest is barely readable -- the gang of
            # Kham run nearly north-south and were coming out at 70-80 degrees.
            # Lean it towards the crest without following it all the way.
            ang = max(-MAX_TILT, min(MAX_TILT, ang))
            return {'p': [round(a[0] + t * (b[0] - a[0]), 1),
                          round(a[1] + t * (b[1] - a[1]), 1)],
                    'a': round(ang, 1)}
        acc += d
    return None


KHAM_LONS = (93.0, 103.5)   # the gang all lie within this band


def lonlat_course(rivers_src, names, span, lons=KHAM_LONS):
    """The river's course over a latitude span, in degrees.  Bounded in
    longitude as well: Natural Earth carries the Yangtze's lower reach under the
    same course, and at 29 N 'Chang Jiang' is out at 106 E in Sichuan, which
    dragged the Markham gang midline a full four degrees east of Kham."""
    pts = []
    for feat in rivers_src['features']:
        if feat['properties'].get('name') not in names:
            continue
        geom = feat['geometry']
        parts = [geom['coordinates']] if geom['type'] == 'LineString' else geom['coordinates']
        for part in parts:
            pts += [(lo, la) for lo, la in part
                    if span[0] - 1 <= la <= span[1] + 1 and lons[0] <= lo <= lons[1]]
    return pts


def midline(a_pts, b_pts, span, steps=9):
    """Ridge between two rivers: at each latitude take the midpoint of where
    the two courses sit.  This is the definition of a gang, so deriving it this
    way keeps the ranges and the rivers coherent by construction."""
    out = []
    for i in range(steps):
        la = span[1] - (span[1] - span[0]) * i / (steps - 1.0)
        def lon_at(pts):
            near = sorted(pts, key=lambda p: abs(p[1] - la))[:4]
            return sum(p[0] for p in near) / len(near) if near else None
        la_, lb = lon_at(a_pts), lon_at(b_pts)
        if la_ is None or lb is None:
            continue
        out.append(((la_ + lb) / 2.0, la))
    return out


def build_ranges(rivers_src):
    """PEAK_RANGES as given, plus the six gang: four derived from the rivers
    that bound them and two anchored on their own high ground."""
    out = list(PEAK_RANGES)
    seg = {r[1]: r[2] for r in RIVERS}          # display name -> NE segment names
    for bo, name, frac, dy, a, b, span in GANG_BETWEEN:
        spine = midline(lonlat_course(rivers_src, seg[a], span),
                        lonlat_course(rivers_src, seg[b], span), span)
        if len(spine) > 1:
            out.append((bo, name, frac, dy, spine))
        else:
            sys.stderr.write('could not derive %s from %s/%s\n' % (name, a, b))
    out += GANG_ANCHORED
    return out


def rings_of(dstr):
    out = []
    for sub in dstr.split('M')[1:]:
        v = [float(t) for t in re.findall(r'-?\d+\.?\d*', sub)]
        out.append(list(zip(v[0::2], v[1::2])))
    return out


def inside(rings, x, y):
    hit = False
    for ring in rings:
        for i in range(len(ring)):
            x1, y1 = ring[i]; x2, y2 = ring[(i + 1) % len(ring)]
            if (y1 > y) != (y2 > y) and x < x1 + (y - y1) / (y2 - y1) * (x2 - x1):
                hit = not hit
    return hit


def near_edge(rings, x, y, tol=7.0):
    """Inside, or within tol of the boundary.  Chomolungma stands on the
    Tibet-Nepal line and a strict inside-test drops it."""
    if inside(rings, x, y):
        return True
    for ring in rings:
        for i in range(len(ring)):
            ax_, ay_ = ring[i]; bx_, by_ = ring[(i + 1) % len(ring)]
            vx, vy = bx_ - ax_, by_ - ay_
            L = vx * vx + vy * vy
            t = 0.0 if L == 0 else max(0.0, min(1.0, ((x - ax_) * vx + (y - ay_) * vy) / L))
            if math.hypot(ax_ + t * vx - x, ay_ + t * vy - y) <= tol:
                return True
    return False


def clip_to_tibet(runs, tibet, tol=0.0):
    """Keep only the parts of each run that fall inside Tibet.  The map is about
    the three regions, so a river is drawn where it runs through them and not
    across the whole frame; the render also clips to the same outline, which
    tidies the cut ends this leaves at vertex granularity."""
    keep = (lambda x, y: near_edge(tibet, x, y, tol)) if tol else \
           (lambda x, y: inside(tibet, x, y))
    out = []
    for run in runs:
        cur = []
        for i, p in enumerate(run):
            if keep(p[0], p[1]):
                if not cur and i:
                    cur.append(run[i - 1])
                cur.append(p)
            elif cur:
                cur.append(p); out.append(cur); cur = []
        if len(cur) > 1:
            out.append(cur)
    return [r for r in out if len(r) > 1]


def to_path(runs, closed=False):
    out = []
    for r in runs:
        out.append('M' + 'L'.join('%.1f %.1f' % (x, y) for x, y in r) + ('Z' if closed else ''))
    return ''.join(out)


# ------------------------------------------------------------------ features

# Natural Earth splits each great river into locally-named segments; these are
# the segment names that make up one continuous course, upstream first.
# name in Tibetan script, name in Latin letters, the Natural Earth segments that
# make up the course, whether it draws as a main stem, where the label sits.
# Both names come from the author's list; the international names the segments
# carry (Brahmaputra, Mekong, Yangtze ...) are not shown on the map.  The last
# two numbers are where the label sits along the course and how far off it.
RIVERS = [
    ('ཡར་ཀླུང་གཙང་པོ་', 'Yarlung Tsangpo', ['Maquan', 'Yarlung', 'Dihang', 'Brahmaputra'], 1, 0.78, 8),
    ('རྨ་ཆུ་',           'Ma Chu',          ['Huang'],                                     1, 0.50, 8),
    ('འབྲི་ཆུ་',          'Drichu',          ['Tuotuo', 'Tongtian', 'Jinsha', 'Chang Jiang'],1, 0.04, 8),
    ('རྫ་ཆུ་',           'Za Qu',           ['Za', 'Lancang', 'Mekong'],                   1, 0.96, 11),
    ('རྒྱ་མོ་རྔུལ་ཆུ་',    'Gyalmo Ngulchu',  ['Nu', 'Salween'],                             1, 0.48, -10),
    ('སེང་གེ་ཁ་འབབ་',    'Sangge Khabab',   ['Shiquan', 'Indus'],                          1, 0.84, -22),
    ('གླང་ཆེན་ཁ་འབབ་',   'Langchen Khabab', ['Sutlej'],                                    0, 0.32, 20),
    # Macha Khabab is left out: Natural Earth's Ghaghara segment begins at the
    # border, so only about 15 px of it falls inside Tibet -- too little to read
    # as a river, while its name crowded the corner where the Sengge and Langchen
    # Khabab and Gang Rinpoche already compete. Add it back if a source with the
    # Tibetan headwater turns up.
]

LAKES = [
    ('Tso Ngonpo',   'Qinghai Lake', 'Qinghai Hu'),
    ('Namtso',       'Nam Co',       'Nam Co'),
    ('Siling Tso',   'Siling Co',    'Siling Co'),
    ('Yamdrok Tso',  'Yamdrok',      'Yamzho Yumco'),
    ('Mapham Yutso', 'Manasarovar',  'Mapam Yumco'),
]

# Range spines, west to east (or north to south).  The number after the name is
# how far along the spine the label sits, and the next is how far it is pushed
# off the crest, perpendicular to it.  Both are chosen by tools/place-labels.py,
# which tests the rotated name against the towns, the region titles and the
# other names; they are not hand-picked.  Natural Earth ships no range
# centrelines, so these are drawn by hand from the ranges' mapped crests -- they
# carry the label, they are not a claim about exact extent.
# Mountain ranges.
#
# Earlier versions of this file carried spines drawn by hand, which put the
# Himalaya's western end about three degrees too far north and the Kunlun two
# degrees too far west.  They are built from Natural Earth now instead:
#
#   * a named range follows its own great peaks, taken with their real
#     coordinates from ne_10m_geography_regions_elevation_points.  A range's
#     crest is the line of its high summits, which is both accurate and
#     checkable -- every point below is a named mountain unless marked anchor.
#   * the six gang of Kham are the ridges between the rivers, which is what
#     "Chushi Gangdruk" says, so they are computed from the river courses at
#     build time rather than listed.  Nothing about them is placed by hand
#     except which two rivers bound each one.
#
# (lon, lat), west to east or north to south.
PEAK_RANGES = [
    ('ཧི་མ་ལ་སྒང་', 'Himalaya', 0.56, -10, [
        (74.60, 35.20),   # Nanga Parbat    8125 m
        (76.00, 34.00),   # Nun             7135 m
        (80.00, 30.50),   # Nanda Devi      7817 m
        (83.50, 28.70),   # Dhaulagiri      8172 m
        (86.93, 28.00),   # Chomolungma     8848 m
        (88.20, 27.70),   # Kanchenjunga    8586 m
        (90.50, 28.00),   # Gangkar Punsum  7570 m
        (92.50, 27.90),   # Kangto          7060 m
        (95.06, 29.63)]), # Namcha Barwa    7782 m
    ('\u0f41\u0f74\u0f0b\u0f53\u0f74\u0f0b\u0f62\u0f72\u0f0b\u0f62\u0f92\u0fb1\u0f74\u0f51\u0f0b', 'khunu ri rgyud', 0.50, -10, [
        # centreline of Natural Earth's KUNLUN MOUNTAINS polygon, smoothed
        (78.70, 36.50), (80.30, 36.20), (81.80, 36.10), (83.30, 36.60),
        (86.40, 37.00), (88.00, 36.80), (89.50, 37.20), (91.00, 37.20),
        (92.60, 36.80), (94.10, 36.45), (95.60, 36.40), (97.20, 35.90),
        (98.70, 35.70)]),
    ('', 'Karakoram', 0.50, -10, [
        (74.60, 36.50),   # Batura Mustagh I 7795 m
        (76.51, 35.88),   # K2               8611 m
        (77.80, 35.20),   # Shahi Kangri     6934 m
        (78.50, 33.80)]), # Kangju Kangri    6725 m
    ('\u0f42\u0f44\u0f66\u0f0b\u0f4f\u0f72\u0f0b\u0f66\u0f7a\u0f0b', 'Gangdise', 0.72, 8, [
        (81.00, 32.80),   # Nganglong Kangri 6720 m
        (81.31, 31.07),   # Gang Rinpoche    6638 m
        (83.50, 30.90),   # anchor
        (86.50, 30.70),   # anchor
        (88.50, 30.50)]), # anchor, meeting the Nyenchen Tanglha
    ('\u0f42\u0f49\u0f53\u0f0b\u0f46\u0f7a\u0f53\u0f0b\u0f50\u0f44\u0f0b\u0f63\u0fb7\u0f0b', 'Nyenchen Tanglha', 0.22, -10, [
        (90.57, 30.38),   # Nyenchen Tanglha 7162 m
        (92.50, 30.60),   # anchor
        (94.30, 30.20),   # anchor
        (95.00, 29.80)]), # Gyala Peri       7294 m
    # Natural Earth has no polygon for the Tanggula and only one named summit on
    # it, so this crest is Geladandong with anchors either side of it, the way
    # the Gangdise and the Nyenchen Tanglha are already built. It follows the
    # Qinghai/TAR border and the Drichu-Ngulchu divide, west to east.
    ('གདང་ལ་', 'Gdang La', 0.42, -10, [
        (89.80, 33.60),   # anchor, off the Changthang
        (91.08, 33.42),   # Geladandong     6621 m
        (92.50, 33.00),   # anchor, by the Tanggula pass
        (94.00, 32.80),   # anchor
        (95.50, 32.60),   # anchor
        (96.80, 32.40)]), # anchor, running into the Kham ranges
    # Centreline of Natural Earth's QUILIAN MOUNTAINS polygon, sliced by
    # longitude and smoothed -- the same construction as the Kunlun. It is a
    # check as well as a source: Kangze'gyai, the range's high point at
    # 97.716E 38.515N, sits 0.02 degrees off the line, which is under a
    # thousandth of the range's length.
    ('མདོ་ལ་རིང་མོ་', 'Dhola Ringmo', 0.60, -10, [
        (94.35, 39.18), (95.06, 39.13), (95.78, 38.90), (96.50, 38.81),
        (97.22, 38.70), (97.93, 38.43), (98.65, 38.38), (99.37, 38.03),
        (100.09, 38.02), (100.81, 37.32), (101.52, 37.22), (102.24, 37.16),
        (102.96, 37.32)]),
]

# Four of the gang are simply the ridge between two rivers, so their spines are
# midlines computed from the river courses; they cannot drift out of step with
# the water.  Pobar in the west and Minya in the east are not between a pair and
# are anchored on their own high ground instead.
GANG_BETWEEN = [
    ('དུལ་དབང་ཟལ་མོ་སྒང་', 'Duldza Zalmo Gang', 0.04, -44, 'Drichu',         'Za Qu',  (31.8, 33.6)),
    ('མར་རྫ་སྒང་', 'Mardza Gang',          0.84, -32, 'Ma Chu',         'Drichu', (32.0, 33.4)),
    ('ཚ་བ་སྒང་', 'Tshawa Gang',       0.70, 8, 'Gyalmo Ngulchu', 'Za Qu',  (28.2, 30.6)),
    ('རྨར་ཁམས་སྒང་', 'Markham Gang',      0.48, 8, 'Za Qu',          'Drichu', (28.2, 30.6)),
]
GANG_ANCHORED = [
    ('པོ་བར་སྒང་', 'Pobar Gang', 0.50, -19, [
        (94.40, 30.30), (95.30, 30.00), (96.20, 29.90), (97.00, 30.00)]),
    ('མི་ཉག་སྒང་', 'Minyag Gang', 0.34, 11, [
        (100.60, 30.80),
        (101.88, 29.60),   # Gongga Shan / Minyag Gangkar 7556 m
        (102.10, 29.10)]),
]


# Karakoram, Namcha Barwa and Amnye Machen are not on the author's list, so they
# carry the Latin name only and are marked as having no Tibetan yet. They are
# the last three features still in that state.
# Peak names are placed on a ring of positions round the marker by
# tools/place-labels.py; the last two numbers are the offset it chose.
PEAKS = [
    ('ཇོ་མོ་གླང་མ་', 'Chomo lungma', 86.925, 27.988, 14, 6),
    ('གངས་རིན་པོ་ཆེ་', 'Gang Rinpoche', 81.312, 31.067, 54, 6),
    ('', 'Namcha Barwa', 95.055, 29.628, 9, -9),
    ('', 'Amnye Machen', 99.478, 34.828, 0, -14),
]

BOX = (-40.0, -40.0, 1220.0, 785.0)      # viewBox plus a little slack
MAX_TILT = 34.0                          # degrees; steeper names stop reading
TOL_RIVER, TOL_LAKE, TOL_RANGE = 0.8, 0.4, 0.5


def main():
    src = open(WIDGET, encoding='utf-8').read()
    data = json.loads(re.search(r'var DATA = (\{.*?\});\n', src, re.S).group(1))
    err, p1, p2, lon0, (ax, bx, ay, by) = fit_projection(data)
    sys.stderr.write('projection: parallels %.1f/%.1f N, meridian %.1f E, '
                     'town residual %.2f px\n' % (p1, p2, lon0, err))

    def project(lon, lat):
        x, y = _lcc(lon, lat, p1, p2, lon0)
        return ax * x + bx, ay * y + by

    tibet = rings_of(data['outline'])

    rivers_src = json.load(open(os.path.join(HERE, 'ne_10m_rivers_lake_centerlines.geojson')))
    lakes_src = json.load(open(os.path.join(HERE, 'ne_10m_lakes.geojson')))

    out = {'rivers': [], 'lakes': [], 'ranges': [], 'peaks': []}

    for bo, en, names, main_stem, frac, dy in RIVERS:
        runs = []
        for feat in rivers_src['features']:
            if feat['properties'].get('name') not in names:
                continue
            geom = feat['geometry']
            parts = [geom['coordinates']] if geom['type'] == 'LineString' else geom['coordinates']
            for part in parts:
                pts = [project(lo, la) for lo, la in part]
                for run in clip_to_tibet(clip_runs(pts, BOX), tibet):
                    runs.append(simplify(run, TOL_RIVER))
        if runs:
            out['rivers'].append({'bo': bo, 'en': en, 'main': main_stem, 'dy': dy,
                                  'd': to_path(runs), 'lab': label_anchor(runs, frac)})

    for bo, en, ne_name in LAKES:
        runs = []
        for feat in lakes_src['features']:
            if feat['properties'].get('name') != ne_name:
                continue
            geom = feat['geometry']
            polys = [geom['coordinates']] if geom['type'] == 'Polygon' else geom['coordinates']
            for poly in polys:
                pts = [project(lo, la) for lo, la in poly[0]]
                if not any(inside(tibet, x, y) for x, y in pts):
                    continue
                runs.append(simplify(pts, TOL_LAKE))
        if runs:
            out['lakes'].append({'bo': bo, 'en': en, 'd': to_path(runs, closed=True)})

    for bo, name, frac, dy, spine in build_ranges(rivers_src):
        pts = simplify([project(lo, la) for lo, la in spine], TOL_RANGE)
        # A range often forms the border rather than sitting inside it -- the
        # Himalayan crest is the frontier -- so crests are kept within a short
        # distance of the outline, not strictly inside it.
        runs = clip_to_tibet([pts], tibet, tol=14.0)
        # The border tolerance above keeps a range whose crest *is* the frontier,
        # such as the Himalaya.  It must not also keep one that merely passes
        # nearby: the Karakoram has no point inside Tibet at all, and was drawing
        # a full-size name out in Kashmir attached to a 51 px stub.
        # A rim range is kept whole. Clipping deleted the western two thirds of
        # Khunu Ri Gyu, whose crest runs along the plateau's northern wall just
        # outside the outline this map draws, and left its name stranded in the
        # north-centre. The full spine is carried as well as the clipped part;
        # the render draws what falls outside Tibet faintly.
        inside_any = any(inside(tibet, x, y) for r in runs for x, y in r)
        if not inside_any:
            sys.stderr.write('%s: outside the outline, drawn faint only\n' % name)
            runs = []
        out['ranges'].append({'bo': bo, 'en': name, 'd': to_path(runs), 'dy': dy,
                              'dFull': to_path([pts]),
                              'lab': label_anchor(runs or [pts], frac)})

    for bo, en, lon, lat, ldx, ldy in PEAKS:
        x, y = project(lon, lat)
        if not near_edge(tibet, x, y):
            continue
        out['peaks'].append({'bo': bo, 'en': en, 'p': [round(x, 1), round(y, 1)],
                             'ldx': ldx, 'ldy': ldy})

    json.dump(out, sys.stdout, ensure_ascii=False, separators=(',', ':'))
    sys.stderr.write('rivers %d  lakes %d  ranges %d  peaks %d\n'
                     % (len(out['rivers']), len(out['lakes']),
                        len(out['ranges']), len(out['peaks'])))


if __name__ == '__main__':
    main()
