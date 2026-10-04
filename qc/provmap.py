"""Tile -> parent-micrograph map (issue #5.1). Derived numbers only: no pixels, thumbnails or edge strips leave this module.

The provided "fields" are tiles of larger parent micrographs, and several parents span more than one batch folder, so a
tile is not an independent sample: the statistical unit is the parent micrograph. Method (qc/provenance.py):
  1. group tiles by (image height in px, exact TIFF XResolution rational): tiles of one parent share both;
  2. order tiles inside a group by normalised cross-correlation of abutting BSE edge columns (right edge of A vs left
     edge of B); a link needs NCC >= ADJ_MIN (non-neighbours score about 0 +/- 0.15), greedily, without cycles;
  3. unlinked runs of one parent are kept as separate runs whose physical separation is unknown.
A parent is "in the approved reference" when it is one of the approved micrographs; tiles of such a parent found in other
batches are physical continuations of approved sections and carry no independent evidence (excluded from batch tests).
"""
import csv
import json
import os

from . import provenance
from .pipeline import REF_PATH, REPORTS, known_records

SCHEMA = 'tile-parent-map/1'
COLUMNS = ['tile', 'batch', 'field_id', 'parent_micrograph', 'run', 'position_in_run', 'run_length', 'parent_n_tiles',
           'parent_batches', 'left_neighbour', 'left_edge_ncc', 'right_neighbour', 'right_edge_ncc',
           'parent_in_approved_reference', 'height_px', 'width_px', 'px_nm', 'xres_signature_known']


def build_map(records, ref):
    """records: cached field records; ref: approved reference (cache/reference.json). Returns (rows, parents)."""
    prov = provenance.build(records, ref['name'])
    by_key = {r['key']: r for r in records}
    approved = {m['parent'] for m in ref['micrographs']}
    left_of = {l['right']: l for l in prov['links']}
    right_of = {l['left']: l for l in prov['links']}
    rows, parents = [], {}
    for pid, chain in sorted(prov['chains'].items()):
        runs, cur = [], []
        for k in chain:
            if k is None:
                runs.append(cur)
                cur = []
            else:
                cur.append(k)
        runs.append(cur)
        tiles = [k for k in chain if k]
        batches = sorted({by_key[k]['batch'] for k in tiles})
        parents[pid] = dict(runs=runs, n_tiles=len(tiles), batches=batches, in_approved_reference=pid in approved,
                            run_separation='unknown' if len(runs) > 1 else None)
        for ri, run in enumerate(runs):
            for pi, k in enumerate(run):
                r, L, R = by_key[k], left_of.get(k), right_of.get(k)
                rows.append(dict(tile=k, batch=r['batch'], field_id=r['fid'], parent_micrograph=pid, run=ri, position_in_run=pi,
                                 run_length=len(run), parent_n_tiles=len(tiles), parent_batches=';'.join(batches),
                                 left_neighbour=L['left'] if L else '', left_edge_ncc=L['ncc'] if L else '',
                                 right_neighbour=R['right'] if R else '', right_edge_ncc=R['ncc'] if R else '',
                                 parent_in_approved_reference=pid in approved, height_px=r['H'], width_px=r['W'],
                                 px_nm=round(r['px_nm'], 4), xres_signature_known=bool(r.get('xres_sig'))))
    return rows, parents


def export(out_dir=REPORTS, records=None, ref=None):
    """Write <out_dir>/provenance_map.csv and .json. Needs the local engine cache (edge strips) to compute; the output
    itself contains derived numbers only."""
    records = known_records() if records is None else records
    ref = json.load(open(REF_PATH)) if ref is None else ref
    rows, parents = build_map(records, ref)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'provenance_map.csv'), 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    doc = dict(schema=SCHEMA, statistical_unit='parent_micrograph', approved_reference=ref['name'],
               method=dict(grouping='image height (px) + exact TIFF XResolution rational',
                           ordering='NCC of abutting BSE edge columns (right edge of A vs left edge of B)',
                           adjacency_min_ncc=provenance.ADJ_MIN, non_neighbour_ncc='about 0 +/- 0.15',
                           runs='unlinked runs of one parent are separate; their separation is unknown',
                           reference_linked='tiles of a parent that is one of the approved micrographs are not independent evidence'),
               n_tiles=len(rows), n_parents=len(parents), parents=parents, tiles=rows)
    with open(os.path.join(out_dir, 'provenance_map.json'), 'w', encoding='utf-8') as fh:
        json.dump(doc, fh, indent=1)
    return doc
