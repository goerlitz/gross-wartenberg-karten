# Meßtischblätter – Kreis Groß Wartenberg

Interactive map viewer for historical maps of the district (Kreis) Groß Wartenberg
(today Powiat Oleśnicki / Syców, Poland). The app shows georeferenced historical
map sheets as tiled overlays on top of modern base maps, with district/state
borders, place labels and shareable views.

It is a **static single-page app**: a single `index.html` with inline CSS/JS,
built on [OpenLayers](https://openlayers.org/) (v7, via CDN). No build step,
no backend.

> UI labels are in German (the app is German-facing); code, comments and this
> document are in English.

## Features

- **Historical overlays** (exactly one active at a time) under the *Karten* section,
  sub-grouped into *Topografisch* and *Andere*. Ready maps include the *Meßtischblätter*
  (1937–1940, 1:25 000), *Reymanns Special-Karte* and the *Nationalitätenkarte*
  (Volkszählung 1910); further sheets appear disabled until their tiles are ready.
- **Base map** (switchable or off): OpenStreetMap, Esri World Imagery, or *Aus*.
- **Transparency slider** for the overlay (only shown/active over a base map).
- **Outline + shadow** around a tile sheet's footprint for contrast with the background.
- **Kreis- and Landesgrenze** (GeoJSON) with a legend, toggled together via *Grenzen*.
- **Place labels** (historical German names) as pills that fade out at high zoom.
- **Shareable URL** (permalink): base map, overlay, position and zoom live in the hash.
- **Usage tracking** via [Umami](https://umami.is/) (pageviews + custom events).

## Controls

- **Layer menu** (button top-right): *Karten* (overlay), *Basiskarte*, *Markierungen*
  (Orte: Städte/Kirchen/Standesämter, Grenzen: Verwaltungsgrenzen), *Transparenz*.
  Selecting an option does not close the menu; clicking outside does.
- **Zoom / Einpassen / Teilen** (buttons top-left): zoom +/−, *Einpassen* (fit to the
  active overlay's extent) and *Teilen* (copies the permalink of the current view to
  the clipboard, with a "Link kopiert" toast).
- **Quellen** (footer, right): an expandable panel with all source attributions;
  the entry for the active overlay is highlighted.

## Project structure

```
index.html               # complete app (HTML + CSS + JS)
cities.json              # place list: historical_name, modern_name, country_today, lat, lon
kreisgrenze.geojson      # district border (EPSG:3857)
landesgrenze.geojson     # state border, "ab 1920" (EPSG:3857)
extend_topo25.geojson    # footprint/outline of the Topo25 mosaic (EPSG:3857)
tiles-extent.json        # extent + min/maxZoom of the overlay tiles
tiles_topo25/{z}/{x}/{y}.webp      # Meßtischblätter tiles (XYZ)
tiles_census1910/{z}/{x}/{y}.webp  # Nationalitätenkarte tiles (XYZ)
tiles_reymann200/{z}/{x}/{y}.webp  # Reymanns Special-Karte tiles (XYZ)
update-extent.py         # generates/updates tiles-extent.json
```

Map projection is Web Mercator (**EPSG:3857**); tile zoom up to 16.

## Layer logic (in `index.html`)

- **Overlays** (`topo25Layer` / `reymann200Layer` / `census1910Layer`): exactly one
  is visible (radio group `name="overlay"`), each clipped to its extent.
- **Base maps** (`osmLayer` / `esriLayer`): radio group `name="base"` with an `off`
  value. Default is **Aus** (the background then shows a subtle diagonal pattern).
- **Transparency** (`updateTransparencyControl`): the slider is only visible while a
  base map is active; with *Aus* the overlay is forced to 100 % and the last value is
  remembered. Applies to the overlay **and** the tile-sheet outline (`setMapOpacity`).
- **Sheet outline** (`topoOutlineLayer` etc., from `extend_*.geojson`): visible only
  while its overlay is active (bound to the layer's `change:visible`).
- **Borders**: `kreisLayer` + `landesLayer` (GeoJSON), toggled together with the
  legend via the *Verwaltungsgrenzen* checkbox.
- **Places**: from `cities.json` as `ol.Overlay` pills; toggled via the *Städte*
  checkbox (in the *Markierungen* section), plus a zoom fade between zoom 13 and 14
  (`applyCityZoomFade`).

## Permalink (URL hash)

Map state is stored in the hash (via `history.replaceState`, so it doesn't spam
browser history) and restored on load:

```
#z=15.00&lat=51.30700&lon=17.71980&base=osm&overlay=topo25
```

- `z` zoom (2 decimals), `lat`/`lon` center in EPSG:4326 (5 decimals)
- `base` = `osm` | `esri` | `off`, `overlay` = `topo25` | `reymann200` | `census1910`
- `updateHash()` writes on `moveend` and on overlay/base-map changes.
- `applyState()` restores state — on load and on `hashchange` (manual URL edit/paste).
  A URL-provided view overrides the automatic fit (`restoredFromUrl`).

## Tracking (Umami)

The Umami script is in `<head>` (pageviews). It is limited to the production domain
via `data-domains="goerlitz.github.io"` and set to **not** count hash changes as extra
pageviews via `data-exclude-hash="true"` (the permalink updates the hash on every map
move). Custom events go through the helper `track(name, data)` (a no-op if the tracker
is missing/blocked). Only genuine user actions are recorded — not the initial load or
restoring from the URL.

Selection-type events go through `trackSelect(action, value)` and share a single,
stringified `value` property, so every event can be reported/filtered uniformly by
`value` in the Umami dashboard. Value-less action events use `track(name)`.

| Action              | Event                 | Properties                          |
| ------------------- | --------------------- | ----------------------------------- |
| Overlay selected    | `overlay-select`      | `{ value: 'topo25' \| 'reymann200' \| 'census1910' }` |
| Base map selected   | `basemap-select`      | `{ value: 'osm' \| 'esri' \| 'off' }` |
| Cities toggled      | `cities-toggle`       | `{ value: 'true' \| 'false' }`        |
| Borders toggled     | `borders-toggle`      | `{ value: 'true' \| 'false' }`        |
| Transparency set    | `transparency-select` | `{ value: '0','10',…,'100' }` (rounded to tens, only on step change) |
| Sources opened      | `sources-open`        | –                                   |
| Map fitted          | `map-fit`             | –                                   |
| View shared         | `share`               | –                                   |

Evaluate in the Umami dashboard under **Events** (count per event, drill down via
the `value` property).

## Run locally

Serve the static files via a local server (not `file://`, since `fetch()` reads the
JSON/GeoJSON/tiles):

```bash
python3 -m http.server 8000
# then open http://localhost:8000/
```

## Update tiles / extent

After changing the tiles, regenerate the extent:

```bash
python3 update-extent.py   # writes tiles-extent.json (extent + min/maxZoom)
```

New places can be added to `cities.json` (`historical_name`, `lat`, `lon`); for
labels that would sit on a line there are optional pixel nudges in `index.html`
(`LABEL_OFFSETS`).

## Sources

- **Meßtischblätter** 1937–1940, 1:25 000 — Kartensammlung Herder-Institut
  ([herder-institut.de](https://www.herder-institut.de/)) & Staatsarchiv Posen
- **Nationalitätenkarte**, Volkszählung 1910, 1:500 000 — Wikipedia /
  Universitätsbibliothek in Wrocław
- **Base maps** — © OpenStreetMap contributors · Esri World Imagery
  (Esri, Maxar, Earthstar Geographics)
