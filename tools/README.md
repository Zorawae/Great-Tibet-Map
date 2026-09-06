# tools

`build-physical.py` regenerates the rivers, lakes, ranges and peaks that the
widget carries in its `DATA` object, already projected into the 1180x745
viewBox.

The map's projection was never recorded anywhere, so the script recovers it by
fitting the ten labelled towns, then checks the result against the stored
graticule. It reproduces to 0.00-0.11 px in longitude and 0.17-0.58 px in
latitude across 25-40 N, the band Tibet occupies.

Source data is Natural Earth, which is public domain -- the reason the result
can stay under the project's CC0 dedication. The two files are a few megabytes
each and are not committed; fetch them into this directory first:

    B=https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson
    curl -O $B/ne_10m_rivers_lake_centerlines.geojson
    curl -O $B/ne_10m_lakes.geojson

Then, from the repository root:

    python3 tools/build-physical.py > physical.json

The output is spliced into `var DATA = {...}` in `tibet-three-regions-map.html`.
Range crests and peaks are listed in the script itself rather than taken from
Natural Earth, which ships no range centrelines; they carry the labels and are
not a claim about exact extent.

## Anchors

Every label is a pair: an **anchor** that belongs to the geometry and is measured
in the world, and an **offset** that belongs to the type and is measured in
line-heights. The anchor never moves to make room; only the offset is free, and
`OFFSET_CAP` bounds that.

Anchors are chosen by one interface in `build-physical.py`, with a strategy per
kind of geometry:

    strategy(geometry, metrics=None, ...) -> [{p, a, quality, inside}, ...]

`p` is the anchor point in viewBox units, `a` the tangent there in degrees,
`quality` how good the anchor is on its own terms before anything competes for
the space, and `inside` whether it falls in the core of the frame rather than
against an edge. A strategy returns a scored *set*, not a point: a long river
has several honest places to carry its name, and settling on one before knowing
what else wants that space throws away the freedom the search needs.

`line_anchors()` serves rivers and range crests -- a point along the course, set
at the tangent there. `point_anchors()` serves peaks -- the coordinate itself,
since which way round the dot the name goes is an offset, not an anchor.
`ANCHOR_STRATEGIES` maps a feature's kind to its strategy, and `anchors(kind,
geometry)` is what everything else calls; `place-labels.py` searches offsets
against whatever set it gets back and knows nothing about crests or coordinates.

A new kind of feature is a row in that table, and one more strategy only if its
geometry is a shape neither of these describes. A lake is a polygon and has
neither a course nor a single coordinate, which is why the five of them still
carry no name.

`quality` is computed but nothing reads it yet: the search still ranks
candidates by its own cost function. Introducing the interface was deliberately
a port -- `build-physical.py` reproduces the shipped `DATA` byte for byte and
`place-labels.py` reproduces the shipped placement.

## Where the range names sit

Each range carries two numbers: how far along its crest the name sits, and how
far the name is pushed off the crest. They are searched rather than hand-picked,
because eleven names competing with the towns, the region titles and the river
names is not something to eyeball:

    python3 tools/measure-labels.py    # true label sizes + obstacles, in SVG units
    python3 tools/place-labels.py      # searches each crest, writes placement.json

Labels are rotated, so the search compares them as oriented rectangles. Using
their axis-aligned bounds instead rejects placements that are actually clear --
a 124-unit name at 28 degrees has a bounding box roughly five times its own
footprint.

## Connectors

A name that has had to travel is tied back to its line with a short tick. What
triggers one is ambiguity, not distance: a name thirty units off a crest with
nothing else near it reads perfectly well, while one fourteen units off with a
river seventeen units away does not. So `mark_connectors()` compares the two
distances and draws a connector when the nearest foreign feature is less than
1.6 times as far as the name's own. The decision is made here, at build time,
and committed to `DATA` as `lead`, where it shows up in a diff; the widget only
draws what it is told.

Four names carry one: Duldza Zalmo Gang (ratio 0.18), Sangge Khabab (1.15),
Langchen Khabab (1.15) and Nyenchen Tanglha (1.43). Three more measure as
ambiguous but get nothing, because their names are already touching their own
crest and a tick would have no length to draw: Pobar Gang (0.18), Tshawa Gang
(0.44) and Markham Gang (1.45). Those three are a placement problem, not a
connector one, and they are what tier deferral is for -- a name that cannot be
served where it belongs should stand down, not be jammed in.

## How far a name may travel

`OFFSET_CAP` is one and a half lines, twenty-one units, and it is the same for
every label whatever the feature's importance. The offset belongs to the type,
not to the geography: past this the anchor stops being obvious and the name is
no longer reliably read as the feature's.

The cap is enforced twice. `place-labels.py` will not search past it -- it is
not a preference the cost function can outbid. That matters, because the cost
function would outbid it: overlap is priced as a squared penetration depth, so
a 20x20 overlap scores about 400 and justifies some 570 units of flight. No
weighting fixes that; it only moves the crossover. So distance past the cap is
not priced at all, it is refused.

`check_labels()` in `build-physical.py` then asserts it on the built output,
because the tables here are edited by hand as well as written by the placer,
and a number typed straight into them is the one thing no search ever sees. It
also checks that every anchor is a point on the feature the map actually draws,
and that no name is marked for a connector that has no room to draw one. A
violation stops the build.

Bringing Pobar Gang back inside the cap cost something honest: it had been
flying 25 units to clear the crowd at the Yarlung Tsangpo's great bend, and now
sits on its own crest with the river crossing under it. The search has nowhere
better within the cap. This is the crowding the cap makes visible rather than
hides.

The six gang are divisions of Kham, so the search also prefers to keep their
names inside the Kham polygon.

The region titles are not obstacles. They are set large and translucent and
step back when a physical layer is on, so a name crossing one is not a fault:
they are drawn to be underlapped. Scoring them even at a token weight was
enough to push Mardza Gang 32 units off its own crest to clear the "Kham"
title it was meant to sit under, so permeable obstacles are left out of the
search entirely and Mardza Gang now sits on its ridge.
