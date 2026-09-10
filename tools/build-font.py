#!/usr/bin/env python3
"""Embed the Tibetan face in the widget, subset to the text it actually sets.

The map's Tibetan was load-bearing on a Google Fonts stylesheet: a network
fetch, at render time, for the one script the map cannot do without.  Where that
fetch fails -- an offline reader, a locked-down network, this repository's own
sandbox -- every Tibetan name on the map falls back to a font that does not have
the glyphs, and the reader gets rows of empty boxes.  Most systems ship no
Tibetan face, so the fallback list behind it was never a real fallback.

So the face is embedded instead, and the widget is self-contained in the way it
always claimed to be.  Whole, Monlam Uni OuChan2 is 1.8 MB, which is not
something to paste into a 176 KB widget; subset to the characters the map sets
it is about a tenth of that.  Subsetting keeps every glyph reachable from those
characters through the font's own GSUB closure, so the Tibetan still *shapes*
-- subjoined consonants stack, vowel signs sit where they belong -- rather than
being a picture of the strings it was cut for.

    python3 tools/build-font.py            # re-cut if the map needs characters
    python3 tools/build-font.py --force    # re-cut regardless
    python3 tools/build-font.py --check    # is the widget's subset still right?

Run it after splice-data.py, because the characters to cut for are read out of
the widget's own DATA plus its markup.  A name added later needs this run again,
and `--check` is what catches it if the run is forgotten: it reads the embedded
subset's own cmap back out of the widget and names any character the map sets
that the subset cannot, so the failure is a line of output rather than a row of
boxes on somebody's screen.
"""
import base64, io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WIDGET = os.path.join(HERE, os.pardir, 'tibet-three-regions-map.html')
# Where to re-cut from.  The face is committed at the repository root, so a
# fresh clone can run this with no arguments; tools/ is checked too, for a copy
# dropped in beside this script, and MONLAM_TTF overrides both.
CANDIDATES = [os.environ.get('MONLAM_TTF'),
              os.path.join(HERE, os.pardir, 'MonlamUniOuchan2.ttf'),
              os.path.join(HERE, 'MonlamUniOuchan2.ttf')]


def source():
    for p in CANDIDATES:
        if p and os.path.exists(p):
            return p
    return None
FAMILY = 'Monlam Uni OuChan2'
TIBETAN = range(0x0F00, 0x1000)
# The @font-face this writes, matched whole so a re-run replaces it rather than
# stacking another copy above it.
BLOCK = re.compile(r'/\* tibetan-face:start \*/.*?/\* tibetan-face:end \*/', re.S)


def tibetan_in(src):
    """Every Tibetan character the widget sets, DATA and markup alike."""
    return sorted({c for c in src if ord(c) in TIBETAN}, key=ord)


def cut(chars):
    """Subset the face to `chars` and return it as WOFF2 bytes."""
    from fontTools import subset
    from fontTools.ttLib import TTFont
    src = source()
    if not src:
        raise SystemExit(
            'no MonlamUniOuchan2.ttf found.  Looked at the repository root and\n'
            'in tools/; set MONLAM_TTF to point somewhere else.')
    font = TTFont(src)
    opts = subset.Options()
    opts.layout_features = ['*']      # keep ccmp/abvs/blws: the shaping IS the font
    # TrueType hinting, and the device tables that go with it, are for small
    # sizes on low-resolution screens.  The map sets this face at 10-11px inside
    # an SVG that is then scaled arbitrarily by the zoom, where the hints are
    # not consulted; dropping them is a quarter of the weight for nothing seen.
    opts.hinting = False
    subsetter = subset.Subsetter(options=opts)
    subsetter.populate(text=''.join(chars))
    subsetter.subset(font)
    # Setting Options.flavor alone does not reach the font: it is the writer
    # that compresses, so the flavor belongs on the TTFont.  Missed, this
    # silently writes an untransformed WOFF2 -- three times the size, and
    # correct enough that nothing complains.
    font.flavor = 'woff2'
    buf = io.BytesIO()
    font.save(buf)
    return buf.getvalue()


def embedded(src):
    """The characters the widget's embedded subset can set, or None if there
    is no subset in it yet."""
    from fontTools.ttLib import TTFont
    m = BLOCK.search(src)
    if not m:
        return None
    hit = re.search(r'base64,([A-Za-z0-9+/=]+)\)', m.group(0))
    if not hit:
        return None
    return set(TTFont(io.BytesIO(base64.b64decode(hit.group(1)))).getBestCmap())


def face_css(woff2, chars):
    b64 = base64.b64encode(woff2).decode('ascii')
    return ("/* tibetan-face:start */\n"
            "/* %s, subset by tools/build-font.py to the %d Tibetan characters\n"
            "   this map sets, and embedded so the script the map cannot do\n"
            "   without does not depend on a network fetch.  Re-cut it after\n"
            "   adding a name; build-physical.py asserts the coverage. */\n"
            "@font-face{font-family:'%s';font-style:normal;font-weight:400;\n"
            "  font-display:swap;\n"
            "  src:url(data:font/woff2;base64,%s) format('woff2');\n"
            "  unicode-range:U+0F00-0FFF;}\n"
            "/* tibetan-face:end */" % (FAMILY, len(chars), FAMILY, b64))


def main():
    check = '--check' in sys.argv[1:]
    src = open(WIDGET, encoding='utf-8').read()
    chars = tibetan_in(src)
    if not chars:
        raise SystemExit('the widget sets no Tibetan at all -- nothing to cut for')

    have = embedded(src)
    missing = [c for c in chars if have is not None and ord(c) not in have]

    if check:
        if have is None:
            print('no embedded Tibetan face in the widget'); return 1
        if missing:
            print('the embedded subset is missing %d character(s) the widget sets: %s'
                  % (len(missing), ' '.join('U+%04X' % ord(c) for c in missing)))
            return 1
        print('the embedded subset covers all %d Tibetan characters the widget sets'
              % len(chars))
        return 0

    # WOFF2 is not byte-stable: the same characters cut from the same file twice
    # give two blobs that differ in a handful of header bytes.  Rewriting on
    # every run would put a 94 KB base64 diff in front of a reviewer to say
    # nothing at all, so the re-cut happens when the coverage actually changed
    # -- which is the only thing about it that can.  --force re-cuts anyway,
    # for a new source file with the same repertoire.
    if have is not None and not missing and '--force' not in sys.argv[1:]:
        sys.stderr.write('unchanged: the embedded subset already covers all %d '
                         'characters the widget sets (--force to re-cut)\n' % len(chars))
        return 0

    woff2 = cut(chars)
    css = face_css(woff2, chars)
    if BLOCK.search(src):
        src = BLOCK.sub(lambda _: css, src, count=1)
    else:
        raise SystemExit('no /* tibetan-face:start */ ... :end */ block to write into')
    open(WIDGET, 'w', encoding='utf-8').write(src)
    sys.stderr.write('embedded %s: %d characters, %d KB of WOFF2, %d KB as base64\n'
                     % (FAMILY, len(chars), len(woff2) // 1024,
                        len(css) // 1024))
    return 0


if __name__ == '__main__':
    sys.exit(main())
