"""For tables NOT merged (S14 wholesale): check whether mod-S11 rows that also exist in S14
carry different cell values (sign of hand-made mod tweaks) or are identical (mod didn't touch)."""
import os

def load(p):
    with open(p, 'r', encoding='latin1') as f:
        lines = [ln.rstrip('\r\n') for ln in f]
    hdr = lines[0].split('\t')
    rows = {}
    for ln in lines[1:]:
        if ln.strip():
            cells = ln.split('\t')
            rows[cells[0]] = cells
    return hdr, rows

MOD = r'extracted\s11_ra\data\global\excel'
S14 = r'extracted\s14_vanilla\data\global\excel'

for fn in ['MonStats.txt', 'MonStats2.txt', 'Levels.txt', 'CharStats.txt', 'Gamble.txt',
           'ItemRatio.txt', 'MagicPrefix.txt']:
    hm, rm = load(os.path.join(MOD, fn))
    hs, rs = load(os.path.join(S14, fn))
    shared = set(rm) & set(rs)
    only_mod = set(rm) - set(rs)
    changed = []
    for name in shared:
        # compare cell by cell over the mod's columns (S14 may add columns)
        diffs = []
        for i, col in enumerate(hm):
            if col == '':
                continue
            try:
                j = hs.index(col)
            except ValueError:
                continue
            a = rm[name][i] if i < len(rm[name]) else ''
            b = rs[name][j] if j < len(rs[name]) else ''
            if a != b:
                diffs.append(col)
        if diffs:
            changed.append((name, diffs))
    print(f'{fn}: shared={len(shared)} mod-only={len(only_mod)} changed={len(changed)}')
    for name, diffs in changed[:8]:
        print(f'    {name}: {diffs[:6]}')
    if len(changed) > 8:
        print(f'    ... and {len(changed)-8} more')
