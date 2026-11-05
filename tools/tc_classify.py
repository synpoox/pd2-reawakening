"""Classify TreasureClassEx diffs between mod-S11 and S14-vanilla for shared rows:
- item-code swaps (rXX -> rXXs style)
- probability/count changes
- structural (different items entirely)
"""
import os

def load(p):
    with open(p, 'r', encoding='latin1') as f:
        lines = [ln.rstrip('\r\n') for ln in f]
    hdr = lines[0].split('\t')
    rows = {}
    for ln in lines[1:]:
        if ln.strip():
            cells = ln.split('\t')
            rows.setdefault(cells[0], cells)   # first instance wins for dup labels
    return hdr, rows

hm, rm = load(r'extracted\s11_ra\data\global\excel\TreasureClassEx.txt')
hs, rs = load(r'extracted\s14_vanilla\data\global\excel\TreasureClassEx.txt')

import re
itemcol = re.compile(r'^Item ?\d+$')

cats = {'only_itemcode_swaps': [], 'only_prob': [], 'both': [], 'other_cols_only': []}
colcounter = {}
for name in sorted(set(rm) & set(rs)):
    a, b = rm[name], rs[name]
    item_changed, prob_changed, other_changed = [], [], []
    for i, col in enumerate(hm):
        if not col or col not in hs:
            continue
        j = hs.index(col)
        av = a[i] if i < len(a) else ''
        bv = b[j] if j < len(b) else ''
        if av == bv:
            continue
        colcounter[col] = colcounter.get(col, 0) + 1
        if itemcol.match(col):
            item_changed.append((col, av, bv))
        elif col.lower().startswith(('prob', 'nodrop', 'picks')):
            prob_changed.append((col, av, bv))
        else:
            other_changed.append((col, av, bv))
    if not (item_changed or prob_changed or other_changed):
        continue
    if item_changed and not prob_changed and not other_changed:
        cats['only_itemcode_swaps'].append(name)
    elif prob_changed and not item_changed and not other_changed:
        cats['only_prob'].append(name)
    elif (item_changed or prob_changed) and not other_changed:
        cats['both'].append(name)
    else:
        cats['other_cols_only'].append((name, other_changed[:4]))

for k, v in cats.items():
    print(f'{k}: {len(v)}')
print('\nsample only_itemcode_swaps:')
for n in cats['only_itemcode_swaps'][:10]:
    print('  ', n)
print('\nsample only_prob (with values):')
for n in cats['only_prob'][:6]:
    a, b = rm[n], rs[n]
    for i, col in enumerate(hm):
        if col in hs and i < len(a) and col.lower().startswith('prob'):
            j = hs.index(col)
            if a[i] != b[j]:
                print(f'   {n} {col}: mod={a[i]} s14={b[j]}')
print('\nsample other_cols_only:')
for n, ch in cats['other_cols_only'][:10]:
    print('  ', n, ch)
print('\nmost-changed columns:', sorted(colcounter.items(), key=lambda x: -x[1])[:15])
