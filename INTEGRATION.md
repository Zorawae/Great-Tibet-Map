# Chöl-kha-sum map — integration guide

Three files, no build step, no dependencies beyond an optional webfont request.

| File | What it is |
|---|---|
| `tibet-three-regions-map.html` | The interactive widget. Open directly or embed. |
| `tibet-three-regions-dark.svg` | Static map, dark. Use in `<img>`, a CMS, or print. |
| `tibet-three-regions-light.svg` | Static map, light. |

The static SVGs carry Latin labels only. An SVG loaded through `<img>` can't
fetch a webfont, and most systems have no Tibetan font, so the script would
render as empty boxes. The interactive version shows both.

---

## Option 1 — iframe (fastest)

Drop the HTML file anywhere on your server and point an iframe at it.

```html
<iframe src="/maps/tibet-three-regions-map.html"
        style="width:100%;height:1050px;border:0"
        loading="lazy"
        title="The three regions of Tibet"></iframe>
```

Fully isolated from your site's CSS. The only cost is that you have to guess a
height. To make it self-sizing, add this to your page:

```html
<script>
window.addEventListener('message', function (e) {
  if (e.data && e.data.tibmapHeight) {
    document.querySelector('iframe[src*="tibet-three-regions"]')
            .style.height = e.data.tibmapHeight + 'px';
  }
});
</script>
```

…and this just before `</body>` inside the map file:

```html
<script>
new ResizeObserver(function () {
  parent.postMessage({ tibmapHeight: document.body.scrollHeight }, '*');
}).observe(document.body);
</script>
```

## Option 2 — inline (better, if you control the page)

Open `tibet-three-regions-map.html` and copy everything between

```
<!-- ══════════ COPY FROM HERE ══════════ -->
...
<!-- ══════════ COPY TO HERE ══════════ -->
```

Paste it into your page. That block contains the container div, the `<style>`,
and the `<script>` — nothing else is needed. Every selector is scoped to
`.tibmap` and every SVG class is prefixed `tm-`, so it will not collide with
your stylesheet. The widget fills its parent's width up to `--tm-max` (1180px).

## Option 3 — static image

```html
<picture>
  <source srcset="/maps/tibet-three-regions-dark.svg"
          media="(prefers-color-scheme: dark)">
  <img src="/maps/tibet-three-regions-light.svg"
       alt="The three traditional regions of Tibet: Ü-Tsang, Kham and Amdo"
       style="width:100%;height:auto">
</picture>
```

---

## Configuration

Set these on the container div. They can also be changed at runtime.

```html
<div class="tibmap" id="tibet-map"
     data-theme="auto"        <!-- dark | light | auto -->
     data-labels="both"       <!-- both | en | bo -->
     data-admin="false"       <!-- true shows current provincial borders -->
     data-cities="true"       <!-- true | false -->
     data-inset="true"        <!-- world locator box, bottom-left of the map -->
     data-rivers="false"      <!-- true draws the rivers, lakes and their names -->
     data-ranges="false"      <!-- true draws the range crests, peaks and names -->
                              <!-- independent attributes, one button: Physical
                                   cycles Off, Rivers, Ranges, Both. Set either
                                   by hand and the button reports it -->
     data-zoom="true"        <!-- false removes zoom, pan and the control -->
     data-selected="kham">    <!-- utsang | kham | amdo | "" -->
</div>
```

`data-theme="auto"` follows the visitor's `prefers-color-scheme`.

### Zoom and pan

The map scales between 1× (fit) and 8×. Content sits in a single transformed
`<g>` rather than a rewritten `viewBox`, so the sea and the locator inset stay
outside it: the background is always painted, and the inset stays pinned to its
corner at every zoom. Panning is clamped so the map always covers its own frame.

Gestures are chosen so an embedded map never fights the page around it:

| gesture | what happens |
|---|---|
| `+` / `−` / slider / `↺` | zoom about the centre, reset |
| drag with a mouse | pan |
| one finger | scrolls **your page** at fit zoom; pans the map once zoomed in |
| two fingers | pinch to zoom, always |
| wheel | scrolls **your page**; `Ctrl`/`⌘` and the wheel zooms |
| double-click | zoom in about the pointer |
| keyboard | focus the map, then `+` `−` `0` and the arrow keys |

A plain wheel is deliberately left to the page. Set `data-zoom="false"` to drop
the whole feature, including the control, for a fixed map.

## Restyling

Override the custom properties anywhere after the widget's `<style>`:

```css
#tibet-map {
  --tm-utsang: #8E2F3C;
  --tm-kham:   #26596F;
  --tm-amdo:   #35745A;
  --tm-gold:   #C9A227;
  --tm-max:    980px;         /* max width */
  --tm-radius: 10px;
  --tm-display: 'Your Display Face', Georgia, serif;
  --tm-ui:      'Your UI Face', system-ui, sans-serif;
}
```

Full list: `--tm-utsang --tm-kham --tm-amdo --tm-gold --tm-bg --tm-land
--tm-land-2 --tm-hair --tm-ink --tm-ink-dim --tm-rule --tm-panel --tm-display
--tm-ui --tm-bo --tm-radius --tm-max`.

## JavaScript API

```js
TibetMap.select('kham');        // or 'utsang', 'amdo', '' to clear
TibetMap.get();                 // 'kham' | null
TibetMap.setTheme('light');
TibetMap.setZoom(2.5);          // 1 (fit) to 8
TibetMap.getZoom();             // 2.5
TibetMap.resetView();           // back to fit, centred
TibetMap.on(function (region) { // fires on every selection change
  console.log('selected:', region);
});
TibetMap.regions;               // the descriptive copy, editable
TibetMap.data;                  // raw paths, areas, coordinates
```

Useful if you want the map to drive other content — swapping a photo,
filtering a list of monasteries, scrolling to a section.

## Fonts

The widget `@import`s two families from Google Fonts:

- **Fraunces** (display) and **IBM Plex Sans** (UI) — cosmetic. Delete the
  `@import` line and they fall back to Georgia and your system UI font, and the
  widget makes no network request at all.

The Tibetan face is not one of them. **Monlam Uni OuChan2 is embedded in the
file** as a WOFF2 data URI, subset to the characters the map sets — about 94 KB.
Most systems ship no Tibetan font, so fetching it would have made half of every
name on the map depend on a network request that, when it fails, leaves rows of
empty boxes rather than degraded type. Nothing needs to be self-hosted, and the
Tibetan renders offline.

To use a different Tibetan face, point `--tm-bo` at your own `@font-face` and
re-cut the embedded subset with `tools/build-font.py`.

## Accessibility

Regions are keyboard-focusable (`Tab`, then `Enter`/`Space`). The panel is
`aria-live="polite"`. Each region also carries a distinct hatch angle, so the
three read apart without relying on colour. `prefers-reduced-motion` is
respected.

---

## Where the boundaries come from

Which prefectures and counties go into each region, how they were projected,
and the conventions their names follow are set out once in
[README.md](README.md#about-the-boundaries) and on the
[project page](https://zorawae.github.io/Great-Tibet-Map/#boundaries). What
follows here is the part that bears on embedding — what the paths do and do not
contain, and how the line was checked.

**Internationally recognised boundaries only.** Every region is clipped against
the boundaries of India, Nepal, Bhutan, Bangladesh and Myanmar, so nothing
administered by those states appears inside the highlight. The southern edge
follows the Himalayan frontier and the western edge stops short of Ladakh and
Jammu & Kashmir. This is done in the build step, not in CSS — the paths
themselves no longer contain that ground.

In the west the line is checked against Natural Earth 10m, which draws
boundaries as they are administered on the ground. That check moved the
Demchok salient — about 4,600 km² east of Ladakh that the source data placed
inside Ü-Tsang — back onto the Indian side, and the Ü-Tsang figure below
reflects the smaller shape.

The same rule applies to the **Current borders** overlay. Its dashed lines are
clipped to the same footprint, so no dashed boundary runs through territory
administered by India, Nepal, Bhutan, Bangladesh or Myanmar; where a provincial
line meets one of those states it is carried along the internationally
recognised boundary instead.

**These are traditional cultural regions, not administrative units.** Their
historical limits were never surveyed, shifted over time, and are drawn
differently by different sources — especially along the Gyalrong, Kongpo and
Kokonor margins. Treat the lines as indicative. The **Current borders** toggle
overlays today's TAR and provincial boundaries so a reader can compare.

**Northern rim.** The Changthang and Hoh Xil continue north of the Tibetan
prefectures into Xinjiang and Gansu, so grouping prefectures alone leaves
notches along that edge that no published cultural-area map draws. The northern
boundary is therefore closed to follow the continuous landform. Everywhere else
the outline is the prefecture mosaic as-is.

**Checked against the CTA's own map.** The Central Tibetan Administration
publishes [a map of Tibet under the PRC](https://tibet.net/about-tibet/map-of-tibet/).
Its silhouette is the TAR, plus Qinghai, plus the Tibetan prefectures of Gansu,
Sichuan and Yunnan — the same grouping used here — so its northern and western
edge is simply the TAR and Qinghai provincial boundary. That makes it something
this map can be measured against rather than eyeballed: the boundary is in
Natural Earth 10m admin-1, which is public domain.

Sampled every half-degree, the outline here sits within 0.25° of latitude of
that boundary from 79°E all the way round to 98°E — finer than the ink on the
printed map — with two exceptions.

The first is between 88.5°E and 90.5°E, where Xinjiang reaches south to 36°N in
a wedge 1.4° wide and 2.4° deep, separating the TAR from Qinghai. The CTA map
closes that wedge and so does this one: the line steps up across it instead of
tracing it.

The second was at the top of the Tsaidam. Between 93.4°E and 96.0°E the line
cut a chord 0.2–0.6° south of the smooth arc the CTA map draws over Tsonub,
clipping off the Lenghu and Mahai country. It now follows that arc, taken from
Natural Earth. About 7,000 km², to Amdo.

Khunu Ri Gyu, the Kunlun, is the wall this rim runs along, so most of the range
sits on the line rather than inside it; the widget draws the part that falls
outside faintly. Moving the rim north to put the whole range inside would have
put the line 0.6–3.0° north of where the CTA draws it, which is not a trade
this map makes: the boundary follows the CTA's, and the range is drawn where it
is.

**Checked against a reference.** The silhouette was compared with a published
Tibetan cultural-area map by extracting that map's outline and fitting the two
together: they agree over 92.9% of their combined area. The residual differences
are the fringe of a few tens of kilometres, plus Arunachal Pradesh, which lies
outside this map by design. That comparison predates the Tsaidam correction
described above, which added about 7,000 km².

**Areas as drawn:** Ü-Tsang 1,074,855 km² · Kham 540,293 km² ·
Amdo 576,079 km² · combined 2,191,227 km².
