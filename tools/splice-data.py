#!/usr/bin/env python3
"""Put the built physical layers into the widget's `var DATA = {...}`.

tools/build-physical.py is the source of truth for the rivers, lakes, ranges
and peaks; the widget carries them as one JSON blob on a single line.  Getting
one into the other was a throwaway script in every session that has touched
this map, which is one script too many for a step the pipeline takes every
time.  So it lives here now.

    python3 tools/build-physical.py > physical.json
    python3 tools/splice-data.py physical.json

Only the four physical keys are replaced.  Everything else in DATA -- the
outline, the regions, the towns, the country names -- belongs to the widget and
is left exactly as it was found, key order included, so the diff on a rebuild
is the geometry that changed and nothing else.

Reads from stdin when given no file, so the build can be piped straight in.
`--check` reports whether the widget already matches without writing, which is
the byte-identity proof: a regeneration against unchanged tables must be a
no-op.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WIDGET = os.path.join(HERE, os.pardir, 'tibet-three-regions-map.html')
KEYS = ('rivers', 'lakes', 'ranges', 'peaks')
# The widget writes DATA on one line and the renderer below it reads the blob
# as a whole; matching the line rather than trying to balance braces keeps this
# from wandering into the JavaScript when a nested object gains a `};`.
PATTERN = re.compile(r'(var DATA = )(\{.*?\})(;\n)', re.S)


def main():
    argv = [a for a in sys.argv[1:] if a != '--check']
    check = '--check' in sys.argv[1:]
    built = json.load(open(argv[0], encoding='utf-8') if argv else sys.stdin)
    missing = [k for k in KEYS if k not in built]
    if missing:
        raise SystemExit('the build is missing %s -- is this physical.json?'
                         % ', '.join(missing))

    src = open(WIDGET, encoding='utf-8').read()
    m = PATTERN.search(src)
    if not m:
        raise SystemExit('no `var DATA = {...};` line in %s' % WIDGET)
    data = json.loads(m.group(2))

    changed = [k for k in KEYS if data.get(k) != built[k]]
    if check:
        print('DATA matches the build' if not changed else
              'DATA differs from the build in: ' + ', '.join(changed))
        return 0 if not changed else 1

    for k in KEYS:
        data[k] = built[k]
    # separators without spaces, and no ensure_ascii: this is how the blob was
    # already written, so an unchanged rebuild leaves the line byte for byte
    # identical rather than reflowing all eleven hundred characters of it.
    blob = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    open(WIDGET, 'w', encoding='utf-8').write(
        src[:m.start()] + m.group(1) + blob + m.group(3) + src[m.end():])
    sys.stderr.write('spliced: %s\n' % (', '.join(changed) if changed else 'nothing changed'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
