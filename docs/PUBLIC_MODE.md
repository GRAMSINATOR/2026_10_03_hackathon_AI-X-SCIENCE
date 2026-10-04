# Public mode: derived results only, no sponsor imagery

Issues #3 (hosting without raw TIFFs) and #4 (publication consent for micrograph-derived images).

Until Polaron confirms that derived SEM imagery may be published, the safe public default is **derived numbers only**.

## Modes

| Variable | Default | Effect |
|---|---|---|
| `QC_PUBLIC=1` | off | Derived results only. The batch list comes from `QC_REPORTS`. `data/` is never read. The pipeline never runs, and there is no run button. |
| `QC_PUBLIC_IMAGES` | `0` in public mode, `1` otherwise | Micrograph-derived imagery: micrographs, segmentation overlays and labels, thumbnails, mosaics, and image payloads embedded in the instrument page. |
| `QC_REF`, `QC_REPORTS`, `QC_CACHE` | `cache/reference.json`, `reports`, `cache/fields` | Every path the dashboard, the instrument host and the bundle use. |
| `QC_DATA` | `data` | Raw batch folders (local mode only). |
| `QC_DEV=1` or `?dev=1` | off | Dev popover with the legacy renderer switch and colour key. The legacy renderer embeds imagery, so it is unavailable without imagery. |

In every mode the pipeline runs only when **Run / refresh** is clicked. It never runs on page load.

## What public mode shows and withholds

| Shown (derived numbers) | Withheld (imagery) |
|---|---|
| Verdict, p-values, reasons, the decision leverage of each micrograph | Micrograph strip and pore / high-Z overlays |
| Evidence Instrument: every key, stage and rim, the NEXT CAPTURE actions, the detail panel | Segmentation overlay in "Why: evidence" |
| Spatial evidence: field footprints with ids and per-field KPI values, 100-µm profiles, the approved local band, observed / open extent, prospective capture, composition row | Provenance mosaic, replaced by a numeric chain table |
| Provenance: tile chains per parent micrograph (from `provenance_map.json`) | Field explorer images |
| Field explorer: KPI table, acquisition fingerprint | |
| State map, deviation heatmap, method, reference, sensitivity, self-audit | |

The deviation heatmap is drawn by Plotly as a raster of the KPI z-score cells. It is a chart, not micrograph content.

## Derived bundle

```bash
python -m qc bundle public_bundle      # git-ignored output
QC_PUBLIC=1 QC_REF=public_bundle/reference.json QC_REPORTS=public_bundle/reports \
  QC_CACHE=public_bundle/cache/fields streamlit run app.py
```

The bundle contains:
* the approved reference;
* for each batch, `result.json`, `field.json`, `report.md` and `instrument_public.html` (the instrument page without imagery);
* `provenance_map.csv` / `.json`;
* the numeric field records: KPIs, per-strip KPIs, histogram anchors, window variances, acquisition fingerprints;
* the verdict-sensitivity summary.

It excludes raw TIFFs, thumbnails, label images, edge strips (`*_edges.npy`, which are BSE pixel columns), mosaics and any
page with embedded imagery.

`qc.bundle.check()` rejects any image file extension, `.npy` / `.npz` file or embedded `data:image` string, and the
export fails if it finds one.

`tests/test_public.py` runs the dashboard headlessly from a bundle, with no `data/`. It asserts that no image element is
rendered and that the instrument payload has `imagery: false` and no embedded image. A positive control in local mode
proves the same probes do detect imagery.

## Repository exposure (issue #4): decision pending

* `.gitignore` now stops **new** imagery from being committed: `fixtures/assets/`, `work/viz/*.png|jpg`, and
  `work/instrument_*.html`, which embeds images.
* Ignore rules do not untrack files that are already in Git. At `fcb1607` the public `main` contains 21
  `fixtures/assets/*.jpg` and 34 `work/viz/*.png` (some are charts, many show micrograph content).
* Choices, after Polaron answers:
  1. **Permitted.** Keep the files, and say so in `NOTICE`.
  2. **Not permitted.** `git rm --cached` alone removes the files from future commits, but they stay in history.
     Rewrite this young repository's history, or publish a sanitised submission repository, and rotate any links. Both
     are destructive or outward-facing and need an explicit team decision.
