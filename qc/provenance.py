"""Provenance: group fields into parent micrographs and recover their left-to-right tile order.

Fields of one parent micrograph share the image height and the exact TIFF XResolution rational, and abutting
tiles have continuous edges (high normalised cross-correlation between the right column of one tile and the
left column of the next). Non-neighbouring pairs score ~0 +/- 0.15.
"""
import itertools
import os

import numpy as np

from .features import CACHE

ADJ_MIN = 0.35   # edge NCC needed to call two tiles adjacent


def _ncc(a, b):
    a = a - a.mean()
    b = b - b.mean()
    return float((a * b).sum() / (np.sqrt((a * a).sum() * (b * b).sum()) + 1e-9))


def parent_id(rec):
    return f"M{rec['H']}" + ('' if rec.get('xres_sig') else '?')


def build(records, primary_batch='Batch_1'):
    """records: field records (any batches). Returns dict with parent of each key, chains and adjacency scores.
    Parents sharing a height get letter suffixes; signatures seen in `primary_batch` (the reference) keep the plain name."""
    groups = {}
    for r in records:
        groups.setdefault((r['H'], r.get('xres_sig')), []).append(r)
    # disambiguate parents that share a height but differ in XResolution
    by_h = {}
    for (h, sig), rs in groups.items():
        by_h.setdefault(h, []).append((0 if any(r['batch'] == primary_batch for r in rs) else 1, min(r['batch'] for r in rs), str(sig)))
    for h in by_h:
        by_h[h] = [x[2] for x in sorted(by_h[h])]
    parent_of, chains, links = {}, {}, []
    for (h, sig), rs in groups.items():
        i = by_h[h].index(str(sig))
        pid = f'M{h}' if i == 0 else f'M{h}{"bcdefghij"[i - 1]}'
        if sig is None:
            pid += '?'
        edges = {r['key']: np.load(os.path.join(CACHE, r['key'] + '_edges.npy')) for r in rs}
        cand = []
        for A, B in itertools.permutations(rs, 2):
            s = _ncc(edges[A['key']][1], edges[B['key']][0])  # right edge of A vs left edge of B
            if s >= ADJ_MIN:
                cand.append((s, A['key'], B['key']))
        right, left = {}, {}
        for s, a, b in sorted(cand, reverse=True):
            if a not in right and b not in left and not _reaches(right, b, a):
                right[a], left[b] = b, a
                links.append(dict(left=a, right=b, ncc=round(s, 3), parent=pid))
        heads = [r['key'] for r in rs if r['key'] not in left]
        order = []
        for hd in heads:
            k = hd
            while k is not None:
                order.append(k)
                k = right.get(k)
            order.append(None)  # gap marker between unconnected runs
        chains[pid] = order[:-1]
        for r in rs:
            parent_of[r['key']] = pid
    return dict(parent_of=parent_of, chains=chains, links=links)


def _reaches(right, start, target):
    k = start
    while k is not None:
        if k == target:
            return True
        k = right.get(k)
    return False
