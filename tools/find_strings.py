import mpqx, os, glob, sys
probes = ['data/local/LNG/ENG/string.tbl', 'data/local/LNG/ENG/expansionstring.tbl',
          'data/local/LNG/ENG/patchstring.tbl']
for mpq in sorted(glob.glob('../ProjectD2/*.mpq')):
    r = mpqx.MPQReader(mpq)
    for p in probes:
        p2 = p.replace('/', chr(92))
        try:
            d = r.read_file(p2)
            print(os.path.basename(mpq), p, len(d), 'bytes')
        except Exception:
            pass
