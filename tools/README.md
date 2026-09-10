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

The Tibetan face is the same kind of thing: `tools/build-font.py` cuts the
subset the widget embeds out of Monlam Uni OuChan2, which is 1.8 MB and is not
committed either. Only a re-cut needs it -- the widget carries the subset and
renders without it -- so fetch a copy from Monlam and leave it at the repository
root, in this directory, or wherever `MONLAM_TTF` points. The script says as
much if it cannot find one, and `--check` works without it.

Then, from the repository root:

    python3 tools/build-physical.py > physical.json

The output is spliced into `var DATA = {...}` in `tibet-three-regions-map.html`
by `splice-data.py`, which replaces only the four physical keys and leaves the
outline, regions, towns and country names exactly as it found them:

    python3 tools/build-physical.py | python3 tools/splice-data.py

`--check` reports whether the widget already matches the build without writing
anything, which is the cheapest proof the pipeline is still faithful: a
regeneration against unchanged tables has to be a no-op.

    python3 tools/build-physical.py | python3 tools/splice-data.py --check

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
`polygon_anchors()` serves the lakes. `ANCHOR_STRATEGIES` maps a feature's kind
to its strategy and `ON_FEATURE` says whether that kind's name may sit on the
thing it names; `anchors(kind, geometry)` is what everything else calls, and
`place-labels.py` searches offsets against whatever set it gets back, knowing
nothing about crests, coordinates or shores.

A new kind of feature is a row in those two tables, and one more strategy only
if its geometry is a shape none of them describes.

`quality` is computed but nothing reads it yet: the search still ranks
candidates by its own cost function. `inside` is read, by the lakes.

## Where an area's name sits

A shape's anchor is its **pole of inaccessibility** -- the interior point
furthest from any edge -- found by quadtree subdivision, and never the centroid.
The centroid of a crescent lies in its bay and the centroid of a ring lies in
its hole; Yamdrok is dendritic enough that its own falls on dry land between two
arms. The pole answers the question a map actually asks, *where is the roomiest
interior point*, and the radius it comes with is what says whether a name fits.

None of these five lakes fits its own name. The radius of the circle inside each,
against half the diagonal of the name's box:

| Lake | Circle | Name needs | Fits |
|---|---:|---:|---|
| Tso Ngonpo | 8.9 | 41.6 | no |
| Namtso | 4.3 | 28.4 | no |
| Siling Tso | 4.3 | 34.1 | no |
| Yamdrok Tso | 1.4 | 44.3 | no |
| Mapham Yutso | 2.7 | 52.1 | no |

The specification asks for the radius against half the label's *height*, and
that test is wrong by exactly the width of the name: Tso Ngonpo's circle is 8.9
units and half its type is 8.2, so a half-height test would say an 82-unit name
fits a lake 31 units across. A name is a box, and the box is what has to fit.

So all five names stand beside their water, each tied to its own pole by a
connector, and their offsets are searched on the same ring of positions a peak
uses. The ring gained a radius at 20 units for this: with only the 14-unit ring
inside the cap, an area label had eight positions in the whole map and Yamdrok
Tso -- hemmed in by Lhasa and the Yarlung Tsangpo -- had nowhere to go.

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

## Zoom, and the names that wait for it

The map's zoom is one `scale()` on `.tm-zoom`, so without help everything inside
it grows together and zooming is a magnifying glass: no name that was not there
before ever appears, and the map has exactly one information density.

A label's anchor belongs to the world and should grow with it. Its type and its
offset are measured in line-heights and should not. So every label hangs in a
`.tm-cs` group that scales by `1/k`, and the two cancel. That gives the small
theorem the whole build-time solve rests on:

> Label boxes hold their size on screen while every separation between them
> grows with *k*. New collisions therefore cannot appear as the reader zooms in.
> Fit zoom is the worst case, which is what makes one solve, at build time,
> correct rather than merely a good approximation.

At `k = 1` the counter-scale is `scale(1)`, so nothing already placed moves.
Measured on the rendered widget, every physical name, town name and country name
holds its screen size to within 0.01px from `k = 1` to `k = 8`.

The region titles are deliberately left out. They are display type drawn to be
underlapped, they are excluded from the collision set entirely, so no
arrangement depends on their size -- and they are the one thing on this map the
labelling layer was asked to leave exactly as it is.

### Standing down

Two boxes that touch at fit zoom do not touch for ever: the separation between
their anchors scales with `k` while the boxes do not, so every collision comes
apart at some zoom. The only questions are which name waits and until when, and
`place-labels.py` answers both -- the tier decides who yields, and the first
zoom on the ladder at which the two boxes come apart decides when it returns.

The loser is not moved. It is not drawn until the zoom that has room for it,
which is what makes the offset cap affordable: nobody buys space with distance.
`TIERS` in `build-physical.py` holds the order -- region titles and towns first,
then ranges, rivers and lakes, then peaks -- and a tier-1 name never stands down,
because what it is entitled to is its place, not a longer leash.

Three names stand down today, all at 3x: **Duldza Zalmo Gang**, jammed against
Jyekundo; **Yamdrok Tso**, which cannot fit between Lhasa and the Yarlung
Tsangpo; and **Mapham Yutso**, in the crowd at the western corner with Gang
Rinpoche, the Gangdise and the Langchen Khabab. That is recorded in `GATES`,
committed to `DATA` as `minK`, and asserted at build time; the widget only draws
what it is told.

Twenty-six of the twenty-nine names are drawn at fit zoom, and the overlap
between them is **6.0** -- against 374.6 counting the three that are not drawn,
which is the number to watch when deciding whether the map is over-full rather
than the number the reader experiences.

## Connectors

A name that has had to travel is tied back to its line with a short tick. What
triggers one is ambiguity, not distance: a name thirty units off a crest with
nothing else near it reads perfectly well, while one fourteen units off with a
river seventeen units away does not. So `mark_connectors()` compares the two
distances and draws a connector when the nearest foreign feature is less than
1.6 times as far as the name's own. The decision is made here, at build time,
and committed to `DATA` as `lead`, where it shows up in a diff; the widget only
draws what it is told.

A lake's name is answered by a plainer question, in `mark_lake_connectors()`:
whether the name still falls on the water it names. An area's name belongs in
the middle of its shape, and where it sits there nothing has to be drawn to say
whose it is; out beside the water the tie is not a matter of degree, because
without it the reader has a name adrift between two lakes and a river. All five
are tied.

Two line names carry one: Duldza Zalmo Gang (ratio 0.03) and Langchen Khabab
(0.43). Two more measure as ambiguous but get nothing, because their names are
already touching their own crest and a tick would have no length to draw:
Markham Gang (0.27) and Tshawa Gang (0.36). There are fewer of both than there
used to be, and for the same reason: a two-line box reaches much further back
over its own line than the one-line box this file used to assume, so a name has
to travel further before a tick has any length at all. Those three are a placement problem, not a
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

Labelling the lakes cost something honest too: five more names on an already
crowded map. What the numbers then said, though, was not to be believed -- see
below.

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

## What the search was actually measuring

Every placement this file has ever produced was searched against boxes half
their real height, and positioned by a box model that only described a one-line
label. Both are fixed now, and it is worth writing down what was wrong, because
the numbers before and after are not comparable and nothing in the earlier
reports meant what it appeared to mean.

**The measurement.** `measure-labels.py` recorded the Latin `<text>` alone and
then widened it by pairing each Tibetan run with `e.previousElementSibling`.
That pairing stopped finding anything the moment `bilabel()` wrapped the Tibetan
run in a `.tm-boslot` group -- the sibling is the slot, not the Latin name -- so
the widening silently never fired. In "both" mode, which is the default, a range
name is 26.7 units tall and was being collided as 13.7. It now measures the
label group's own bounding box: one measurement of the thing on screen, rather
than two and an assumption about the DOM between them.

**The box model.** The box was taken to ride 0.3 of a line above the baseline
its anchor sits on. That is right for one line. For the two-line block the map
actually draws, the middle of the box falls *below* the first baseline, and the
model was out by some ten units. Both `build-physical.py` and `place-labels.py`
now put the box's top edge `ASC` above the baseline and its middle `h/2` below
that, which is the same arithmetic for one line and the right arithmetic for
two. Checked against the rendered widget, the model now predicts every label's
centre to within 1.75 units, and most to within 0.25.

**What that revealed.** Measured honestly, the map at fit zoom was carrying
nearly 1270 units of overlap, and serving it by the rules would have meant eight
names standing down, the Yarlung Tsangpo and the Himalaya among them. The
physical names were set smaller instead -- 11.5 to 9.5px for the ranges, 13.5 to
11 for the water, with the Tibetan line coming up to match -- which is the trade
the author had already allowed for names that overlap, since the map zooms. That
took it to 374.6, of which 6.0 is between names actually drawn.

## What naming the lakes revealed

The five lakes were the last physical features carrying a Latin name only.
Giving them their Tibetan makes each a two-line block -- twenty-eight units tall
where it was fourteen -- and the map was re-solved against the taller boxes.
Total residual overlap fell from 374.6 to 275.3 and what a reader sees at fit
zoom is unchanged at 6.0, with 26 of 29 names drawn. But two things came out of
it that are not settled.

**Placement order is by width; yielding is by tier.** The placer fills the map
largest name first and never reconsiders a name that is not itself overlapped.
Yamdrok Tso sits in the most crowded corner on the map -- Lhasa to the north,
the Yarlung Tsangpo across its middle, the Himalayan crest to the south -- and
once its name is two lines tall, no position on the ring clears all three within
`OFFSET_CAP`. Being the wider name, it is placed first and takes the crest; the
Himalaya, reached later, is left with nowhere clear but the far west end of its
own spine, and stands down until 1.5x. Langchen Khabab yields to Mapham Yutso
the same way.

`TIERS` was meant to decide who stands down, and it does -- but only once the
arrangement is settled. It has no say in how the arrangement is reached, so a
lake can take a major range's crest on nothing but being twenty units wider.
Making the search tier-aware, or letting the refinement sweep move the name
*causing* an overlap rather than only the one suffering it, would change the
answer here. Both are changes to the placer, not to the tables.

**Connectors do not survive a two-line box.** `has_tick()` asks whether a tick
would have any length at all, and within a 21-unit cap a 28-unit box leaves
almost none: the seven connectors the map now draws measure 0.2, 0.2, 0.7, 0.8,
0.8, 0.8 and 6.6 units. The build believes it is drawing a tie; the renderer
draws a dot. The names all sit close enough to their features to read without
one, which is why this is not visible as a fault, but the mechanism is
effectively inert and `has_tick()` should probably be asking for a usable
length rather than a positive one.

**The Tibetan measurements are made without the Tibetan font.** The sandbox
cannot fetch the Google Fonts stylesheet and ships no Tibetan face, so every
Tibetan run measures as fallback boxes. Installing Noto Serif Tibetan and
re-measuring shows the widths are almost all unaffected -- the Latin line is the
wider of the two for every name but Himalaya, which narrows 51.7 to 49.2 -- but
the *heights* are not: a two-line block measures 23.3 units without the font and
34.3 with it. Every placement this repository has ever shipped was solved
against boxes some eleven units shorter than a reader with the font actually
sees. That is a whole-map re-solve and was left alone here.
