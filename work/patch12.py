p = 'qc/spatial.py'; s = open(p, encoding='utf-8').read()
s = s.replace("""                      max_coherent_um=float(max((len(_runs(o)[0]) if _runs(o) else 0) for o in chains.values()) * 175.0))""",
"""                      max_coherent_um=float(max(sum(by_key[x]['spatial']['width_um'] for x in run if x in by_key)
                                                for o in chains.values() for run in _runs(o))))""")
open(p, 'w', encoding='utf-8').write(s)
p = 'qc/features.py'; s = open(p, encoding='utf-8').read()
s = s.replace("from .segment import pore_mask_se, segment\n", "from .segment import pore_mask_se, segment\nfrom .spatial import field_maps\n")
s = s.replace("THUMB = 4          # display downsampling\n", "THUMB = 4          # display downsampling\nFEATURE_VERSION = 2  # bump to invalidate cached field records\n")
s = s.replace("        if rec.get('stamp') == stamp:\n            return rec", "        if rec.get('stamp') == stamp and rec.get('v') == FEATURE_VERSION:\n            return rec")
s = s.replace("    rec = dict(key=key, batch=field['batch'], fid=field['fid'], H=H, W=W, px_nm=px_nm, xres_sig=sig, stamp=stamp,",
              "    rec = dict(key=key, v=FEATURE_VERSION, batch=field['batch'], fid=field['fid'], H=H, W=W, px_nm=px_nm, xres_sig=sig, stamp=stamp,")
s = s.replace("    rec['acq'] = acquisition(raw, s, a, px_nm)\n", "    rec['acq'] = acquisition(raw, s, a, px_nm)\n    rec['spatial'] = field_maps(lab, px_nm)\n")
open(p, 'w', encoding='utf-8').write(s)
print('ok')
