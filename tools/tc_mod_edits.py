#!/usr/bin/env python3
"""Diff vanilla S10 TreasureClassEx vs final mod TreasureClassEx, keyed by TC name.
Outputs the mod's hand edits, categorized."""
import sys

def load(path):
    with open(path, 'rb') as f:
        raw = f.read().decode('latin1')
    lines = raw.replace('\r\n', '\n').split('\n')
    header = lines[0].split('\t')
    rows = {}
    order = []
    for ln in lines[1:]:
        if not ln.strip():
            continue
        cols = ln.split('\t')
        name = cols[0]
        if name in rows:  # dup TC names possible (grouped TCs have same name? no - unique)
            name = name + '#dup'
        rows[name] = cols
        order.append(name)
    return header, rows, order

h_s10, s10, o_s10 = load('scout/tc_s10_vanilla.txt')
h_mod, mod, o_mod = load('scout/extracted/s11_ra/data/global/excel/TreasureClassEx.txt')

# column indexes (standard TreasureClassEx layout)
def idx(h, name):
    return h.index(name) if name in h else None

def getpicks(cols, h):
    """Return list of (item, prob) for the 10 pick slots."""
    out = []
    for i in range(1, 11):
        ii, ip = idx(h, f'Item{i}'), idx(h, f'Prob{i}')
        if ii is None: break
        it = cols[ii].strip() if ii < len(cols) else ''
        pr = cols[ip].strip() if ip < len(cols) else ''
        if it:
            out.append((it, pr))
    return out

def scalar(cols, h, name):
    i = idx(h, name)
    if i is None or i >= len(cols): return ''
    return cols[i].strip()

edited = []
new_rows = []
removed = []

for name in o_mod:
    base = name.replace('#dup', '')
    if base not in s10:
        new_rows.append(base)
        continue
    a, b = s10[base], mod[name]
    diffs = []
    for k in ['Picks', 'NoDrop', 'Unique', 'Set', 'Rare', 'Magic']:
        va, vb = scalar(a, h_s10, k), scalar(b, h_mod, k)
        if va != vb:
            diffs.append(f'{k}:{va}->{vb}')
    pa, pb = getpicks(a, h_s10), getpicks(b, h_mod)
    if pa != pb:
        diffs.append(f'PICKS {pa} -> {pb}')
    if diffs:
        edited.append((base, diffs))

for name in o_s10:
    if name not in [m.replace('#dup','') for m in o_mod]:
        removed.append(name)

print(f'=== EDITED TCs ({len(edited)}) ===')
for name, diffs in edited:
    print(f'[{name}]')
    for d in diffs:
        print(f'   {d}')
print(f'\n=== NEW TC ROWS IN MOD ({len(new_rows)}) ===')
for n in new_rows: print(f'  {n}')
print(f'\n=== TC ROWS REMOVED BY MOD ({len(removed)}) ===')
for n in removed: print(f'  {n}')
