# Great Tibet Map

**An interactive map of Ü-Tsang, Kham and Amdo — the three regions of Tibet.** ཆོལ་ཁ་གསུམ་ · *chöl-kha-sum*, "the three regions of Great Tibet": the way Tibetans have long
described their own country. Click a region and the panel tells you its Tibetan
name, its dialect, its landscape, its principal towns, its area as drawn, and
the present-day units it now falls under.

[![Code: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)
[![Map & text: CC0 1.0](https://img.shields.io/badge/map%20%26%20text-CC0%201.0-green.svg)](LICENSE)
[![Dependencies: none](https://img.shields.io/badge/dependencies-none-brightgreen.svg)](#requirements)
[![Build step: none](https://img.shields.io/badge/build%20step-none-brightgreen.svg)](#try-it)

**Live demo → <https://zorawae.github.io/Great-Tibet-Map/>**

The whole thing is one self-contained HTML file. No framework, no build step,
no `npm install`, no tracking, nothing to configure before it works. Drop it on
a server, or paste a single block into a page you already have.

![The three traditional regions of Tibet: Ü-Tsang, Kham and Amdo](tibet-three-regions-dark.svg)

---

## Contents

- [Try it](#try-it)
- [Use it on your site](#use-it-on-your-site)
- [Features](#features)
- [Configuration](#configuration)
- [Zoom and pan](#zoom-and-pan)
- [Restyling](#restyling)
- [JavaScript API](#javascript-api)
- [Requirements](#requirements)
- [Accessibility](#accessibility)
- [About the boundaries](#about-the-boundaries)
- [Contributing](#contributing)
- [License](#license)

## Try it

Open <https://zorawae.github.io/Great-Tibet-Map/> — that is the map, hosted.

To run it yourself, clone the repository and open `tibet-three-regions-map.html`
in any browser. Nothing to install, no server to start.

```sh
git clone https://github.com/Zorawae/Great-Tibet-Map.git
cd Great-Tibet-Map
open tibet-three-regions-map.html      # macOS; xdg-open on Linux, start on Windows
```

To publish your own copy, enable **GitHub Pages** on your fork (Settings → Pages
→ deploy from the default branch). Everything here is static; there is nothing
to build.

## Use it on your site

| File | What it is |
|---|---|
| `tibet-three-regions-map.html` | The interactive widget. Open directly or embed. |
| `tibet-three-regions-dark.svg` | Static map, dark. For `<img>`, a CMS, or print. |
| `tibet-three-regions-light.svg` | Static map, light. |
| `index.html` | The project's landing page, served by GitHub Pages. |
| `LICENSE` | MIT for the code, CC0 1.0 for the map and text. |
| `og-image.png`, `sitemap.xml` | Social-share card and sitemap for the hosted site. |

**Option 1 — iframe (fastest).** Drop the HTML file anywhere on your server and
point an iframe at it. Fully isolated from your CSS; the only cost is that you
have to pick a height.

```html
<iframe src="/maps/tibet-three-regions-map.html"
        style="width:100%;height:1050px;border:0"
        loading="lazy"
        title="The three regions of Tibet"></iframe>
```

To make it self-sizing instead, add this to your page:

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

**Option 2 — inline (better, if you control the page).** Open
`tibet-three-regions-map.html` and copy everything between

```
<!-- ══════════ COPY FROM HERE ══════════ -->
...
<!-- ══════════ COPY TO HERE ══════════ -->
```

Paste it into your page. That block is the container div, its `<style>` and its
`<script>` — nothing else is needed. Every selector is scoped to `.tibmap` and
every SVG class is prefixed `tm-`, so it will not collide with your stylesheet.
The widget fills its parent's width up to `--tm-max` (1180px).

**Option 3 — static image.** Use the two SVGs in a `<picture>` element so the
map follows the visitor's colour scheme:

```html
<picture>
  <source srcset="/maps/tibet-three-regions-dark.svg"
          media="(prefers-color-scheme: dark)">
  <img src="/maps/tibet-three-regions-light.svg"
       alt="The three traditional regions of Tibet: Ü-Tsang, Kham and Amdo"
       style="width:100%;height:auto">
</picture>
```

The static SVGs carry Latin labels only. An SVG loaded through `<img>` cannot
fetch a webfont, and most systems ship no Tibetan font, so the script would
render as empty boxes. The interactive version shows both.

## Features

- **Three selectable regions**, each with its own colour *and* its own hatch
  angle, so they read apart without depending on colour.
- **Bilingual labels** — English, Tibetan, or both.
- **Current borders overlay** — put today's TAR and provincial boundaries over
  the cultural regions to compare the two.
- **Rivers and ranges** — the great rivers that rise on the plateau and five of
  its lakes; the six gang of Kham, from *Chushi Gangdruk*, with the Himalaya,
  Kunlun, Gangdise, Nyenchen Tanglha, Gdang La and Dhola Ringmo; and four
  peaks. Named in Tibetan, and in Latin letters, following the same Labels
  toggle as the towns. Drawn only where they run through the three regions. Off
  by default; the regions come first and the physical layer is context you opt
  into. One *Physical* button cycles Off → Rivers → Ranges → Both.
- **Towns, world locator inset and dark/light themes**, each toggleable.
- **Zoom and pan** — a `+` / slider / `−` control at the map's corner, drag to
  pan, pinch on a touch screen, double-click, `Ctrl`/`⌘` and the wheel, or the
  keyboard. A plain wheel is left alone so the map never swallows the scroll of
  the page it sits in, and one finger only pans once you have zoomed in.
- **A proportional bar** across the top, sized by each region's share of the
  total area.
- **Keyboard accessible** — regions are focusable (`Tab`, then `Enter` or
  `Space`), the panel is `aria-live="polite"`, every shape carries a label, and
  `prefers-reduced-motion` is respected.
- **Responsive** down to phone widths through container queries.
- **A small JS API**, so the map can drive the rest of your page.

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

## Zoom and pan

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

Colours, fonts, maximum width and corner radius are CSS custom properties.
Override them anywhere after the widget's `<style>`:

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

Useful when you want the map to drive other content — swapping a photograph,
filtering a list of monasteries, scrolling to a section.

## Requirements

Any current browser. The widget uses CSS custom properties, container queries
and `ResizeObserver`, so Chrome/Edge 105+, Firefox 110+ and Safari 16+ are the
practical floor. No polyfills, no bundler, no runtime dependencies.

The one network request is an optional `@import` of two Google Fonts families.
**Fraunces** (display) and **IBM Plex Sans** (UI) are cosmetic: delete the
`@import` and they fall back to Georgia and your system UI font, and the widget
is then fully offline.

**The Tibetan face is embedded, not fetched.** Most systems ship no Tibetan font
at all, so a fallback list behind a failed fetch is not a fallback — every
ཆོལ་ཁ་གསུམ string on the map renders as empty boxes. Monlam Uni OuChan2 is
therefore carried in the file itself, subset by `tools/build-font.py` to the
characters the map sets and embedded as a WOFF2 data URI. That is about 94 KB,
and it is why the Tibetan is the one thing on this map that cannot fail to
render. Add a Tibetan name and re-run that script, or `--check` will tell you
the subset no longer covers the map.

To use a different Tibetan face, point `--tm-bo` at your own `@font-face` and
re-cut the embedded subset with the same script.

## Accessibility

Regions are keyboard-focusable (`Tab`, then `Enter`/`Space`). The panel is
`aria-live="polite"`. Each region also carries a distinct hatch angle, so the
three read apart without relying on colour. `prefers-reduced-motion` is
respected.

## About the boundaries

The regions are built by grouping present-day prefectures, then dissolving and
projecting them in an Albers equal-area conic (standard parallels 26°N / 41°N,
central meridian 92°E). The area figures are therefore measurements of the
shapes actually shown, not numbers quoted from elsewhere:

| Region | Area as drawn | Share |
|---|---:|---:|
| Ü-Tsang | 1,074,855 km² | 49.0% |
| Kham | 540,293 km² | 24.7% |
| Amdo | 576,079 km² | 26.3% |
| **Combined** | **2,191,227 km²** | |

Each region is the union of these present-day units:

- **Ü-Tsang** — Lhasa, Shigatse, Nyingtri, Lhoka, Nagchu, Ngari, plus the
  Gdang La(གདང་ལ་)/Changthang exclave administered from Na-gor-mo(ན་གོར་མོ་).
- **Kham** — Chamdo, Garzê, Yushu, Dêqên, Muli(རྨི་ལི་), and the Gyalrong counties
  of Ngawa (Barkham, Chuchen, Tsanlha, Li, Trochu(ཁྲོ་ཆུ་), Mowun, Lunggu(ལུང་དགུ་)).
- **Amdo** — the Tso Ngön(མཚོ་སྔོན་) prefectures: Ziling(ཟི་ལིང་།), Tsoshar(མཚོ་ཤར་),
  Tsojang(མཚོ་བྱང་), Malho(རྨ་ལྷོ་), Tsolho(མཚོ་ལྷོ་), Golog(མགོ་ལོག), Tsonub(མཚོ་ནུབ་); plus
  Kanlho(ཀན་ལྷོ་) in Gansu, and northern Ngawa (Ngawa, Dzoge, Marthang, Dzamthang,
  Zungchu, Zitsa Degu).

**Editor's note on the names.** Places are named in the form the map itself
uses, with the Tibetan in brackets wherever an established Tibetan name
exists. Three conventions keep the lists from drifting:

- The bracket after Ngawa lists that prefecture's **Gyalrong counties** and
  nothing else. A place inside a prefecture already named on the same line is
  covered by it and is not repeated — Lithang sits in Garzê, Gyalthang
  (Shangri-La) in Dêqên — and a town or a walled quarter is not an entry
  alongside a county.
- The units are **prefecture-level** unless a line says otherwise. Tso Ngön is
  the province, so it heads the prefectures that belong to it rather than
  standing beside them, and Kanlho, which is in Gansu, falls outside that group.
- **Yushu appears under Kham, not Amdo.** It is one of Qinghai's eight
  prefectures, which is why the Tso Ngön list has seven.

Romanisation is not standardised: the same name may be spelled one way in the
prose here and another in the widget's own data. The Tibetan is what binds them,
so where the two disagree the Tibetan is the name that counts.

**Internationally recognised boundaries only.** Every region is clipped against
the boundaries of India, Nepal, Bhutan, Bangladesh and Myanmar, so nothing
administered by those states appears inside the highlight. The southern edge
follows the Himalayan frontier and the western edge stops short of Ladakh and
Jammu & Kashmir. This is done in the build step, not in CSS — the paths
themselves no longer contain that ground.

In the west the line is checked against Natural Earth 10m, which draws
boundaries as they are administered on the ground. That check moved the
Demchok salient — about 4,600 km² east of Ladakh that the source data placed
inside Ü-Tsang — back onto the Indian side, and the Ü-Tsang figure above
reflects the smaller shape.

The same rule applies to the **Current borders** overlay. Its dashed lines are
clipped to the same footprint, so no dashed boundary runs through territory
administered by India, Nepal, Bhutan, Bangladesh or Myanmar; where a provincial
line meets one of those states it is carried along the internationally
recognised boundary instead.

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

**These are traditional cultural regions of Great Tibet.** Their
historical limits were never surveyed, they shifted over time, and different
sources draw them differently — especially along the Gyalrong, Kongpo and
Kokonor margins. Treat the lines as indicative; the *Current borders* toggle
overlays today's boundaries so a reader can compare.

**Map scope and context.** This map is intended to show how the historical
Tibetan territorial divisions correspond to, or overlap with, present-day Chinese
administrative divisions. It illustrates the traditional territorial divisions of
Tibet, overlaid onto the current provincial and administrative boundaries of the
People's Republic of China.

For clarity, this map includes only territories that are currently administered
by China. It does not depict or claim any Tibetan territories that historically
formed part of the broader Tibetan cultural or political sphere but are located
outside the present-day boundaries of Chinese governance.

**Checked against a reference.** The silhouette was compared with a published
Tibetan cultural-area map by extracting that map's outline and fitting the two
together; they agree over 92.9% of their combined area. The remainder is a
fringe of a few tens of kilometres, plus Arunachal Pradesh, which lies outside
this map by design. That figure predates the Tsaidam correction above, which
added about 7,000 km².

## Contributing

Issues and pull requests are welcome. There is no build step and no test suite:
edit the HTML file, open it in a browser, and check the widget still works in
both themes, in all three label modes, and with a keyboard.

Most useful contributions:

- **Boundary corrections.** Please cite a source — a published cultural-area
  map, a scholarly work, a prefecture list. "The line looks wrong near X" is a
  fine issue to open even without one.
- **Translations and Tibetan text.** Corrections to spelling, transliteration
  or wording in the region descriptions are very welcome.
- **Accessibility and browser bugs.** Say which browser, which version, and
  what you saw.
- **Integrations.** Wrappers for a CMS or framework, or a self-hosted-font
  build.

Two things to keep in mind. This map touches a contested subject, so keep issue
threads to the cartography, the sources and the code — political argument in
the tracker will be closed. And please keep the widget dependency-free and in
one file: that constraint is the point of the project.

## License

Two sets of terms, because this is part software and part cartographic work:

- **Code** — the widget's HTML, CSS and JavaScript — under the
  [MIT License](LICENSE).
- **Map and text** — the boundary geometry, the two static SVGs, the region
  descriptions and the documentation prose — dedicated to the public domain
  under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/).

In short: use it anywhere, commercially included. The map and the writing carry
no attribution requirement at all. Credit is welcome but not owed:

> Great Tibet Map by Zorawae, CC0 1.0 —
> [https://github.com/Zorawae/Great-Tibet-Map](https://zorawae.github.io/Great-Tibet-Map/)

The Google Fonts families are not part of this repository and carry their own
SIL Open Font License.


------------------ FREE TIBET ------------------ 
