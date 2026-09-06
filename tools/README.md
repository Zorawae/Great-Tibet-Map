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

The six gang are divisions of Kham, so the search also prefers to keep their
names inside the Kham polygon.

The region titles are not obstacles. They are set large and translucent and
step back when a physical layer is on, so a name crossing one is not a fault:
they are drawn to be underlapped. Scoring them even at a token weight was
enough to push Mardza Gang 32 units off its own crest to clear the "Kham"
title it was meant to sit under, so permeable obstacles are left out of the
search entirely and Mardza Gang now sits on its ridge.
