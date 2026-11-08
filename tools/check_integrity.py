"""Referential integrity check on merged tables (v2).
Fixes from v1: property codes case-insensitive, itypes via Code col, clean item_codes.
"""
import os, re
from collections import Counter

ROOT = os.environ.get("CHK_ROOT", r"..\reawakening-s14\data\global\excel")

def load(fn):
    p = os.path.join(ROOT, fn)
    if not os.path.exists(p): return None, None
    with open(p, 'r', encoding='latin1') as f:
        lines = [ln.rstrip('\r\n') for ln in f]
    hdr = lines[0].split('\t')
    while hdr and hdr[-1] == '': hdr.pop()
    rows = [ln.split('\t') for ln in lines[1:] if ln.strip()]
    return hdr, rows

def col(hdr, name):
    try: return hdr.index(name)
    except ValueError: return None

def nameset(fn):
    _, rows = load(fn)
    return {r[0] for r in rows}

issues = []
def err(cat, msg): issues.append((cat, msg))

hdr_w, wrows = load('Weapons.txt')
hdr_a, arows = load('Armor.txt')
hdr_m, mrows = load('Misc.txt')
item_codes = set()
for rows, hdr in [(wrows, hdr_w), (arows, hdr_a), (mrows, hdr_m)]:
    ci = col(hdr, 'code')
    for r in rows:
        if r[0]: item_codes.add(r[0])
        if ci is not None and ci < len(r) and r[ci]: item_codes.add(r[ci])

_, itrows = load('ItemTypes.txt')
hdr_it, _ = load('ItemTypes.txt')
itypeset = {r[1] for r in itrows if len(r) > 1 and r[1]} | {r[0] for r in itrows}

propset = {p.lower() for p in nameset('Properties.txt')}
_, isc_rows = load('ItemStatCost.txt')
statset = {r[0] for r in isc_rows}
skillset = nameset('Skills.txt')
skilldescset = nameset('Skilldesc.txt')
missileset = nameset('Missiles.txt')
stateset = nameset('States.txt')
tcset = nameset('TreasureClassEx.txt')

# 1. Properties -> stats (case-sensitive; stat names are case-sensitive in D2)
hdr_p, prows = load('Properties.txt')
for r in prows:
    for i, h in enumerate(hdr_p):
        if re.fullmatch(r'stat[1-7]', h or '') and i < len(r) and r[i].strip():
            if r[i].strip() not in statset:
                err('PROP->STAT', f'{r[0]}: {r[i].strip()}')

# 2. item tables -> property codes (case-insensitive) + item codes
PROP_COL = re.compile(r'^(prop ?\d+|mod ?\d+ ?code|mod ?\d+|t1code ?\d+|pcode ?\d+[ab]?)$', re.I)
for fn in ['UniqueItems.txt','SetItems.txt','Sets.txt','Runes.txt','MagicPrefix.txt','MagicSuffix.txt','AutoMagic.txt','Gems.txt','MonProp.txt']:
    hdr, rows = load(fn)
    if hdr is None: continue
    for r in rows:
        for i, h in enumerate(hdr):
            if PROP_COL.match((h or '').strip()) and i < len(r) and r[i].strip():
                if r[i].strip().lower() not in propset:
                    err(f'{fn}->PROP', f'{r[0]}: {r[i].strip()}')
    ci = col(hdr, 'code')
    if ci is not None and fn not in ('Gems.txt','MonProp.txt'):
        for r in rows:
            if ci < len(r) and r[ci].strip() and r[ci].strip() not in item_codes:
                err(f'{fn}->ITEMCODE', f'{r[0]}: {r[ci].strip()}')

# Runes: rune item codes + itype/etype codes
hdr_r, rrows = load('Runes.txt')
GENERIC = {'weap','armo','mele','helm','shld','miss','h2h','h2h2','comb','char','pott','tpot','scro','body','ring','amul','jewl','gemm','runes','tors','belt','boot','glov','wand','orb','staff','stave','scep','club','hamm','swrd','axe','axe2','knif','tkni','spear','aspe','pole','jave','thro','bow','xbow','abow','mace','sword'}
for r in rrows:
    for i, h in enumerate(hdr_r):
        hl = (h or '').strip().lower()
        if re.match(r'^rune\d$', hl) and i < len(r) and r[i].strip():
            if r[i].strip() not in item_codes: err('RUNES->RUNEITEM', f'{r[0]}: {r[i].strip()}')
        if re.match(r'^(i|e)type\d$', hl) and i < len(r) and r[i].strip():
            v = r[i].strip()
            if v not in itypeset and v not in GENERIC and v not in item_codes:
                err('RUNES->TYPE', f'{r[0]}: {v}')

# 3. CubeMain: mod property codes
hdr_c, crows = load('CubeMain.txt')
for r in crows:
    for i, h in enumerate(hdr_c):
        if PROP_COL.match((h or '').strip()) and i < len(r) and r[i].strip():
            if r[i].strip().lower() not in propset:
                err('CUBE->PROP', f'{r[0]}: {r[i].strip()}')

# 4. base items -> itype (via Code)
for fn, rows, hdr in [('Weapons.txt', wrows, hdr_w), ('Armor.txt', arows, hdr_a), ('Misc.txt', mrows, hdr_m)]:
    ti = col(hdr, 'type')
    if ti is None: continue
    for r in rows:
        if ti < len(r) and r[ti].strip() and r[ti].strip() not in itypeset and r[ti].strip() not in GENERIC:
            err(f'{fn}->ITYPE', f'{r[0]}: {r[ti].strip()}')

# 5. Skills -> skilldesc / states / missiles
hdr_s, srows = load('Skills.txt')
sd_i = col(hdr_s, 'skilldesc')
for r in srows:
    if sd_i is not None and sd_i < len(r) and r[sd_i].strip() and r[sd_i].strip() not in skilldescset:
        err('SKILLS->DESC', f'{r[0]}: {r[sd_i].strip()}')
    for i, h in enumerate(hdr_s):
        hl = (h or '').strip().lower()
        if hl in ('aurastate', 'passivestate') and i < len(r) and r[i].strip():
            if r[i].strip() not in stateset: err('SKILLS->STATE', f'{r[0]}: {r[i].strip()}')
        if re.match(r'^(srv|clt|sub|cltsub)?missile[abcd]?$', hl) and i < len(r) and r[i].strip():
            if r[i].strip() not in missileset: err('SKILLS->MISSILE', f'{r[0]}: {r[i].strip()}')

# 6. Missiles -> submissiles
hdr_ms, msrows = load('Missiles.txt')
for r in msrows:
    for i, h in enumerate(hdr_ms):
        hl = (h or '').strip().lower()
        if 'missile' in hl and i < len(r) and r[i].strip():
            v = r[i].strip()
            if v.lower() not in ('none', '') and v not in missileset and not v.isdigit():
                err('MISSILES->MISSILE', f'{r[0]}: {h}={v}')

# 7. TCEx -> item codes / TC names / generic
for r in load('TreasureClassEx.txt')[1]:
    for i, h in enumerate(load('TreasureClassEx.txt')[0]):
        if re.match(r'^item ?\d+$', (h or '').strip().lower()) and i < len(r) and r[i].strip():
            v = r[i].strip()
            if v not in item_codes and v not in tcset and v not in GENERIC and not v.startswith('Act'):
                err('TC->ITEM', f'{r[0]}: {v}')

print(f'{len(issues)} issues')
print(Counter(c for c, _ in issues))
seen = set()
for c, m in issues:
    if (c, m) in seen: continue
    seen.add((c, m))
    print(f'[{c}] {m}')

