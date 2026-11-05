#!/usr/bin/env python3
"""Full row-level diff: mod S11 TreasureClassEx vs S14 vanilla.
Shows picks/scalars side by side for every differing row."""
def load(path):
    with open(path, 'rb') as f:
        raw = f.read().decode('latin1')
    lines = raw.replace('\r\n', '\n').split('\n')
    header = lines[0].split('\t')
    rows = {}
    for ln in lines[1:]:
        if not ln.strip():
            continue
        cols = ln.split('\t')
        rows[cols[0]] = cols
    return header, rows

h14, s14 = load('scout/extracted/s14_vanilla/data/global/excel/TreasureClassEx.txt')
hm, mod = load('scout/extracted/s11_ra/data/global/excel/TreasureClassEx.txt')

def picks(cols, h):
    out = []
    for i in range(1, 11):
        ii = h.index(f'Item{i}') if f'Item{i}' in h else None
        ip = h.index(f'Prob{i}') if f'Prob{i}' in h else None
        if ii is None or ii >= len(cols):
            break
        it = cols[ii].strip()
        pr = cols[ip].strip() if ip is not None and ip < len(cols) else ''
        if it:
            out.append((it, pr))
    return out

def sc(cols, h, k):
    i = h.index(k) if k in h else 999
    return cols[i].strip() if i < len(cols) else ''

both = sorted(set(s14) & set(mod))
only_mod = sorted(set(mod) - set(s14))
only_s14 = sorted(set(s14) - set(mod))

diff_rows = []
for name in both:
    a, b = s14[name], mod[name]
    scal = []
    for k in ['Picks', 'NoDrop', 'Unique', 'Set', 'Rare', 'Magic']:
        va, vb = sc(a, h14, k), sc(b, hm, k)
        if va != vb:
            scal.append(f'{k} {va}->{vb}')
    pa, pb = picks(a, h14), picks(b, hm)
    if scal or pa != pb:
        diff_rows.append((name, scal, pa, pb))

print(f'rows only in S14: {len(only_s14)} | rows only in mod: {len(only_mod)} | differing shared rows: {len(diff_rows)}')
print()
for name, scal, pa, pb in diff_rows:
    print(f'### {name}')
    if scal:
        print('  scalars(S14->mod): ' + '  '.join(scal))
    if pa != pb:
        print(f'  S14 : {pa}')
        print(f'  mod : {pb}')
print()
print('=== mod-only TC rows ===')
for n in only_mod:
    print(' ', n)
