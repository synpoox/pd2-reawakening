#!/usr/bin/env python3
"""Revert stacked item codes (rXXs/gXXs/skls/skzs) to S14's current codes (rXX/gXX/skl/skz)
in merged TreasureClassEx.txt and CubeMain.txt.

Why: stage-1 swap made TCs drop legacy 'Stack' items which S14 tags '(old)'; picking one up
yields 'bad inventory data' on next load. S14 vanilla references zero stacked codes in both
files, so every stacked reference is ours to convert.
Preserves latin1 + CRLF + tab structure; edits only exact code cells / quoted code tokens."""
import sys, re

RUNES = {f'r{i:02d}s': f'r{i:02d}' for i in range(1, 34)}
GEMS = {}
for pre in ('gz', 'gl', 'gp'):
    for c in 'vybgrw':
        GEMS[f'{pre}{c}s'] = f'{pre}{c}'
SKULLS = {'skls': 'skl', 'skzs': 'skz'}
CODES = {**RUNES, **GEMS, **SKULLS}

def fix_tc(path):
    with open(path, 'rb') as f:
        text = f.read().decode('latin1')
    crlf = '\r\n' in text
    lines = text.replace('\r\n', '\n').split('\n')
    ncell = 0
    touched = set()
    for i, ln in enumerate(lines):
        if i == 0 or not ln.strip():
            continue
        cols = ln.split('\t')
        hit = False
        for j, c in enumerate(cols):
            if c in CODES:
                cols[j] = CODES[c]
                ncell += 1
                hit = True
        if hit:
            lines[i] = '\t'.join(cols)
            touched.add(cols[0])
    out = '\n'.join(lines)
    if crlf:
        out = out.replace('\n', '\r\n')
    with open(path, 'wb') as f:
        f.write(out.encode('latin1'))
    print(f'TC: {ncell} code cells reverted across {len(touched)} rows')
    return len(touched)

def fix_cube(path):
    with open(path, 'rb') as f:
        text = f.read().decode('latin1')
    crlf = '\r\n' in text
    n = 0
    for old, new in CODES.items():
        for pat_old, pat_new in ((f'"{old},', f'"{new},'), (f'"{old}"', f'"{new}"')):
            cnt = text.count(pat_old)
            if cnt:
                text = text.replace(pat_old, pat_new)
                n += cnt
    lines = text.replace('\r\n', '\n').split('\n')
    out = '\n'.join(lines)
    if crlf:
        out = out.replace('\n', '\r\n')
    with open(path, 'wb') as f:
        f.write(out.encode('latin1'))
    print(f'CubeMain: {n} quoted code tokens converted')

M = 'reawakening-s14/data/global/excel/'
fix_tc(M + 'TreasureClassEx.txt')
fix_cube(M + 'CubeMain.txt')

# verify zero stacked refs remain
left_tc = 0
with open(M + 'TreasureClassEx.txt', 'rb') as f:
    for ln in f.read().decode('latin1').split('\n')[1:]:
        for c in ln.split('\t'):
            if c in CODES:
                left_tc += 1
with open(M + 'CubeMain.txt', 'rb') as f:
    cube = f.read().decode('latin1')
left_cube = sum(cube.count(f'"{c},') + cube.count(f'"{c}"') for c in CODES)
print(f'remaining stacked refs: TC={left_tc} CubeMain={left_cube}')
sys.exit(1 if (left_tc or left_cube) else 0)
