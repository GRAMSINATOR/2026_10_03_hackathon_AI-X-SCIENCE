p = 'qc/contract.py'; s = open(p, encoding='utf-8').read()
s = s.replace("""            im = Image.open(src).convert('L')
            im.resize((im.width // 2, im.height // 2)).save(os.path.join(out_dir, rel), quality=80)
            assets[fld['id']] = dict(image=rel, detector='BSE', downsample=8, image_px_um=fld['px_nm'] * 8 / 1000,
                                     width_um=fld['width_um'], height_um=fld['height_um'])""",
"""            im = Image.open(src).convert('L')
            im.resize((im.width // 2, im.height // 2)).save(os.path.join(out_dir, rel), quality=80)
            assets[fld['id']] = dict(image=rel, detector='BSE', downsample=8, image_px_um=fld['px_nm'] * 8 / 1000,
                                     width_um=fld['width_um'], height_um=fld['height_um'])
            lab = os.path.join(asset_src, f"{fld['id']}_lab.png")
            if os.path.exists(lab):   # registered segmentation produced by the engine (same frame as the BSE image)
                srel = f"assets/{fld['id']}_seg.png"
                L = Image.open(lab)
                L.resize((L.width // 2, L.height // 2), Image.NEAREST).save(os.path.join(out_dir, srel), optimize=True)
                assets[fld['id']]['segmentation'] = dict(image=srel, encoding={'0': 'pore', '1': 'matrix', '2': 'high_z'},
                                                         image_px_um=fld['px_nm'] * 8 / 1000)""")
open(p, 'w', encoding='utf-8').write(s)
