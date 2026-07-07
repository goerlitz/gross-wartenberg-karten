# Meßtischblätter – Kreis Groß Wartenberg

Interaktiver Kartenviewer für historische Karten des Kreises Groß Wartenberg
(heute Powiat Oleśnicki / Syców, Polen). Die App zeigt georeferenzierte
historische Kartenwerke als Kachel-Overlays über modernen Basiskarten, mit
Kreis-/Landesgrenzen, Ortsbeschriftungen und teilbaren Ansichten.

Es ist eine **statische Single-Page-App**: eine einzige `index.html` mit
Inline-CSS/JS auf Basis von [OpenLayers](https://openlayers.org/) (v7, per CDN).
Kein Build-Schritt, kein Backend.

## Features

- **Historische Overlays** (jeweils genau eines aktiv):
  - *Meßtischblätter* 1937–1940, 1:25 000 (Topografisch)
  - *Nationalitätenkarte*, Volkszählung 1910, 1:500 000 (Demografisch)
- **Basiskarte** (umschaltbar oder aus): OpenStreetMap, Esri World Imagery, Aus
- **Transparenz-Regler** für das Overlay (nur sinnvoll/aktiv über einer Basiskarte)
- **Umriss + Schatten** um das Topo25-Blatt für Kontrast zum Hintergrund
- **Kreis- und Landesgrenze** (GeoJSON) mit Legende
- **Ortslabels** (historische deutsche Namen) als Pills, die bei hohem Zoom ausblenden
- **Teilbare URL** (Permalink): Basiskarte, Overlay, Position und Zoom stehen im Hash
- **Nutzungs-Tracking** via [Umami](https://umami.is/) (Pageviews + Custom Events)

## Bedienung

- **Ebenen-Menü** (Button oben rechts): Overlay, Basiskarte, Orte, Transparenz.
  Auswahl schließt das Menü nicht; Klick außerhalb schließt es.
- **Zoom / Einpassen / Teilen** (Buttons oben links): Zoom +/−, „Einpassen" (auf
  das Gebiet des aktiven Overlays zentrieren) und „Teilen" (kopiert den Permalink
  zur aktuellen Ansicht in die Zwischenablage, mit „Link kopiert"-Feedback).
- **Quellen** (Footer rechts): ausklappbares Panel mit allen Quellenangaben; die
  Angabe zum aktiven Overlay wird hervorgehoben.

## Projektstruktur

```
index.html               # komplette App (HTML + CSS + JS)
cities.json              # Ortsliste: historical_name, modern_name, country_today, lat, lon
kreisgrenze.geojson      # Kreisgrenze (EPSG:3857)
landesgrenze.geojson     # Landesgrenze ab 1920 (EPSG:3857)
extend_topo25.geojson    # Footprint/Umriss des Topo25-Mosaiks (EPSG:3857)
tiles-extent.json        # Extent + min/maxZoom der Overlay-Kacheln
tiles_topo25/{z}/{x}/{y}.webp      # Kacheln Meßtischblätter (XYZ)
tiles_census1910/{z}/{x}/{y}.webp  # Kacheln Nationalitätenkarte (XYZ)
update-extent.py         # erzeugt/aktualisiert tiles-extent.json
```

Die Karten-Projektion ist Web Mercator (**EPSG:3857**); Kachel-Zoom bis 16.

## Ebenen-Logik (in `index.html`)

- **Overlays** `topo25Layer` / `census1910Layer`: genau eines ist sichtbar
  (Radiogruppe `name="overlay"`). Beide werden auf `tiles-extent.json` geclippt.
- **Basiskarten** `osmLayer` / `esriLayer`: Radiogruppe `name="base"` mit Wert
  `off`. Standard: **Aus** (dann zeigt der Hintergrund ein dezentes Rautenmuster).
- **Transparenz** (`updateTransparencyControl`): Slider ist nur sichtbar, wenn eine
  Basiskarte aktiv ist; bei „Aus" wird das Overlay auf 100 % gesetzt, der letzte
  Wert wird gemerkt. Wirkt auf Overlay **und** Topo-Umriss (`setMapOpacity`).
- **Topo-Umriss** `topoOutlineLayer` (aus `extend_topo25.geojson`): nur sichtbar,
  solange Topo25 aktiv ist (an `topo25Layer` `change:visible` gekoppelt).
- **Orte**: aus `cities.json`, als `ol.Overlay`-Pills; Sichtbarkeit über die
  Checkbox, plus Zoom-Fade zwischen Zoom 13 und 14 (`applyCityZoomFade`).

## Permalink (URL-Hash)

Kartenzustand wird als Hash gespeichert (via `history.replaceState`, ohne
History-Einträge) und beim Laden wiederhergestellt:

```
#z=15.00&lat=51.30700&lon=17.71980&base=osm&overlay=topo25
```

- `z` Zoom (2 Nachkommastellen), `lat`/`lon` Zentrum in EPSG:4326 (5 Stellen)
- `base` = `osm` | `esri` | `off`, `overlay` = `topo25` | `census1910`
- `updateHash()` schreibt bei `moveend` und bei Overlay-/Basiskarten-Wechsel.
- `applyState()` stellt den Zustand her — beim Laden und bei `hashchange`
  (manuelles Editieren/Einfügen der URL). Ein per URL vorgegebener Ausschnitt
  überschreibt das automatische Einpassen (`restoredFromUrl`).

## Tracking (Umami)

Das Umami-Script ist im `<head>` eingebunden (Pageviews). Es ist per
`data-domains="goerlitz.github.io"` auf die Produktionsdomain beschränkt und per
`data-exclude-hash="true"` so konfiguriert, dass Hash-Änderungen **keine**
zusätzlichen Pageviews erzeugen (der Permalink aktualisiert den Hash bei jeder
Kartenbewegung). Custom Events werden
über den Helper `track(name, data)` gesendet (No-Op, falls der Tracker fehlt/
geblockt ist). Es werden nur echte Nutzer-Aktionen erfasst — nicht der
Initial-Load oder das Wiederherstellen aus der URL.

Auswahl-Events laufen über `trackSelect(action, value)` und teilen sich einen
einzigen, als String normalisierten `value`-Property — so lässt sich im
Umami-Dashboard jedes Event einheitlich nach `value` auswerten/filtern. Reine
Aktions-Events (ohne Wert) nutzen `track(name)`.

| Aktion              | Event                 | Properties                          |
| ------------------- | --------------------- | ----------------------------------- |
| Overlay gewählt     | `overlay-select`      | `{ value: 'topo25' \| 'census1910' }` |
| Basiskarte gewählt  | `basemap-select`      | `{ value: 'osm' \| 'esri' \| 'off' }` |
| Städte getoggelt    | `cities-toggle`       | `{ value: 'true' \| 'false' }`        |
| Grenzen getoggelt   | `grenzen-toggle`      | `{ value: 'true' \| 'false' }`        |
| Transparenz gewählt | `transparency-select` | `{ value: '0','10',…,'100' }` (auf Zehner gerundet, nur bei Stufenwechsel) |
| Quellen geöffnet    | `sources-open`        | –                                   |
| Karte eingepasst    | `map-fit`             | –                                   |
| Ansicht geteilt     | `share`               | –                                   |

Auswertung im Umami-Dashboard unter **Events** (Zählung pro Event, Drilldown
über die `value`-Property).

## Lokal ausführen

Statische Dateien über einen lokalen Server ausliefern (nicht per `file://`, da
`fetch()` auf die JSON/GeoJSON/Kacheln zugreift):

```bash
python3 -m http.server 8000
# dann http://localhost:8000/ öffnen
```

## Kacheln / Extent aktualisieren

Nach Änderungen an den Kacheln den Extent neu erzeugen:

```bash
python3 update-extent.py   # schreibt tiles-extent.json (extent + min/maxZoom)
```

Neue Orte lassen sich in `cities.json` ergänzen (`historical_name`, `lat`, `lon`);
für Labels, die auf einer Linie liegen, gibt es in `index.html` optionale
Pixel-Verschiebungen (`LABEL_OFFSETS`).

## Quellen

- **Meßtischblätter** 1937–1940, 1:25 000 — Kartensammlung Herder-Institut
  ([herder-institut.de](https://www.herder-institut.de/)) & Staatsarchiv Posen
- **Nationalitätenkarte**, Volkszählung 1910, 1:500 000 — Wikipedia /
  Universitätsbibliothek in Wrocław
- **Basiskarten** — © OpenStreetMap-Mitwirkende · Esri World Imagery
  (Esri, Maxar, Earthstar Geographics)
