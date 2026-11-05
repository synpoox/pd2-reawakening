"""Stage-1 extras: port three clean mod features into the merged tables.

1. TreasureClassEx: stacked-variant item swaps (r01->r01s, glb->glbs, skl->skls ...)
   Rule: swap when S14 value + 's' == mod value and the stacked code exists in merged Misc.
   Probability/quality boosts and map-tier scrambles are DEFERRED to Stage 2 (need a
   vanilla-S11 oracle to separate mod boosts from PD2 season evolution).

2. ItemRatio: mod's 4 rows verbatim (uniform ~0.77x divisors = deliberate drop-rate boost;
   headers and row set identical to S14).

3. CharStats: mod's starting items (item3..item6 + counts) — Horadric Cube + tomes at start.
   S14 keeps life/mana-per-level values (S14 balance).
"""
import os, re

REPO = r'..\reawakening-s14\data\global\excel'
MOD = r'extracted\s11_ra\data\global\excel'

def load(p):
    with open(p, 'r', encoding='latin1') as f:
        raw = f.read()
    nl = '\r\n' if '\r\n' in raw else '\n'
    lines = [ln for ln in raw.replace('\r\n', '\n').split('\n')]
    hdr = lines[0].split('\t')
    rows = [ln.split('\t') for ln in lines[1:] if ln.strip()]
    return hdr, rows, nl

def save(p, hdr, rows, nl):
    with open(p, 'w', encoding='latin1', newline='') as f:
        f.write(nl.join(['\t'.join(hdr)] + ['\t'.join(r) for r in rows]) + nl)

# --- 1. TC stacked swaps ---
hm, rm, _ = load(os.path.join(MOD, 'TreasureClassEx.txt'))
mod_tc = {r[0]: r for r in rm}
repo_path = os.path.join(REPO, 'TreasureClassEx.txt')
hr, rr, nl = load(repo_path)
# stacked codes available in merged Misc
hmisc, rmisc, _ = load(os.path.join(REPO, 'Misc.txt'))
ci = hmisc.index('code')
codes = {r[ci] for r in rmisc if ci < len(r) and r[ci]}
itemcol = re.compile(r'^Item ?\d+$')
swapped = []
n_swap = 0
for row in rr:
    name = row[0]
    if name not in mod_tc:
        continue
    m = mod_tc[name]
    for j, col in enumerate(hr):
        if not itemcol.match(col) or j >= len(row):
            continue
        try:
            i = hm.index(col)
        except ValueError:
            continue
        mv = m[i] if i < len(m) else ''
        if mv and row[j] and mv == row[j] + 's' and mv in codes:
            row[j] = mv
            n_swap += 1
            swapped.append((name, col, mv))
save(repo_path, hr, rr, nl)
print(f'TC: {n_swap} stacked-code swaps applied in {len(set(s[0] for s in swapped))} rows')

# --- 2. ItemRatio ---
mod_ir_path = os.path.join(MOD, 'ItemRatio.txt')
repo_ir_path = os.path.join(REPO, 'ItemRatio.txt')
hm2, rm2, _ = load(mod_ir_path)
hr2, rr2, nl2 = load(repo_ir_path)
assert [h for h in hm2 if h] == [h for h in hr2 if h], 'ItemRatio headers differ!'
assert sorted(r[0] for r in rm2) == sorted(r[0] for r in rr2), 'ItemRatio rows differ!'
save(repo_ir_path, hr2, rm2, nl2)
print(f'ItemRatio: replaced {len(rm2)} rows with mod values')

# --- 3. CharStats starting items ---
hm3, rm3, _ = load(os.path.join(MOD, 'CharStats.txt'))
mod_cs = {r[0]: r for r in rm3}
repo_cs_path = os.path.join(REPO, 'CharStats.txt')
hr3, rr3, nl3 = load(repo_cs_path)
ITEM_COLS = ['item3', 'item4', 'item5', 'item6', 'item3count', 'item4count', 'item5count', 'item6count']
n_cells = 0
for row in rr3:
    name = row[0]
    if name not in mod_cs:
        continue
    m = mod_cs[name]
    for c in ITEM_COLS:
        if c in hr3 and c in hm3:
            j, i = hr3.index(c), hm3.index(c)
            mv = m[i] if i < len(m) else ''
            if j < len(row) and row[j] != mv:
                row[j] = mv
                n_cells += 1
save(repo_cs_path, hr3, rr3, nl3)
print(f'CharStats: ported starting items for {sum(1 for r in rr3 if r[0] in mod_cs)} classes ({n_cells} cells)')
for row in rr3[:7]:
    j = hr3.index('item4')
    jj = hr3.index('item6')
    print(f'   {row[0]:12} item4={row[j]:5} item6={row[jj] if jj < len(row) else ""}')
