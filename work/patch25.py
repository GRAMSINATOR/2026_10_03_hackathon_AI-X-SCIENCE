p = 'qc/contract.py'; s = open(p, encoding='utf-8').read()
s = s.replace("import shutil\n", "\nfrom PIL import Image\n")
s = s.replace("""            shutil.copyfile(src, os.path.join(out_dir, rel))
            assets[fld['id']] = dict(image=rel, detector='BSE', downsample=4, image_px_um=fld['px_nm'] * 4 / 1000,""",
"""            im = Image.open(src).convert('L')
            im.resize((im.width // 2, im.height // 2)).save(os.path.join(out_dir, rel), quality=80)
            assets[fld['id']] = dict(image=rel, detector='BSE', downsample=8, image_px_um=fld['px_nm'] * 8 / 1000,""")
open(p, 'w', encoding='utf-8').write(s)
