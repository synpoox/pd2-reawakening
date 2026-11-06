#!/usr/bin/env python3
"""Apply Reawakening drop-rate TC edits onto merged (S14-based) TreasureClassEx.txt.

Rules:
- Good/Map Good TCs: adopt mod's pick structure (no Chipped in Hell, Orbs + Fate Drop injected,
  boosted gem/rune/map weights), using S14's rune-equiv TC names.
- Runes N TCs: keep S14 item codes, apply mod's reduced cascade probabilities.
- Junk TCs: halve potion/misc/junk-ref weights to mod's values; keep S14's ammo pick untouched.
- BR Arena Bodies/Chests: mod's quality scalars only.
- Treasure Fallen: mod's boosted weights + Orbs/Cards sub-TC refs; keep S14 NoDrop and sub-TC targets.
- Utility TCs (Horadric books, Larzuk puzzle, Lillith Mirror, SkeletonKey, Vial of Lightsong):
  mod's quality scalars.
- Corrupted Zone: mod's Unique scalar.
Boss/uber rows, Map Tier pools, Ammo restructure are NOT touched (explicit decision).

Preserves latin1 + CRLF + tab structure. Operates in place on the repo copy.
"""
import sys

PATH = 'reawakening-s14/data/global/excel/TreasureClassEx.txt'

with open(PATH, 'rb') as f:
    raw = f.read()
text = raw.decode('latin1')
crlf = '\r\n' in text
lines = text.replace('\r\n', '\n').split('\n')
header = lines[0].split('\t')

item_idx = [header.index(f'Item{i}') for i in range(1, 11)]
prob_idx = [header.index(f'Prob{i}') for i in range(1, 11)]
scal_idx = {k: header.index(k) for k in ('Unique', 'Set', 'Rare', 'Magic', 'NoDrop', 'Picks')}

def rowmap():
    rows = {}
    for i, ln in enumerate(lines):
        if i == 0 or not ln.strip():
            continue
        rows.setdefault(ln.split('\t')[0], []).append(i)
    return rows

def get_picks(cols):
    out = []
    for k in range(10):
        it = cols[item_idx[k]].strip() if item_idx[k] < len(cols) else ''
        pr = cols[prob_idx[k]].strip() if prob_idx[k] < len(cols) else ''
        if it:
            out.append((it, pr))
    return out

def set_picks(cols, picks):
    while len(cols) < len(header):
        cols.append('')
    for k in range(10):
        cols[item_idx[k]] = ''
        cols[prob_idx[k]] = ''
    for k, (it, pr) in enumerate(picks):
        cols[item_idx[k]] = it
        cols[prob_idx[k]] = str(pr)
    return cols

def set_scalar(cols, key, val):
    while len(cols) < len(header):
        cols.append('')
    cols[scal_idx[key]] = str(val)
    return cols

rows = rowmap()
changed = []
report = []

def edit(name, fn, desc):
    idxs = rows.get(name)
    if not idxs:
        report.append(f'!! MISSING: {name}')
        return
    for i in idxs:
        cols = lines[i].split('\t')
        before = list(cols)
        cols = fn(cols)
        lines[i] = '\t'.join(cols)
        changed.append(name)
        report.append(f'OK {name}: {desc}')

def good_edit(name, picks):
    edit(name, lambda c: set_picks(c, picks), f'picks -> {picks}')

def prob_edit(name, target_item, newprob):
    def fn(c):
        ps = [(it, (str(newprob) if it == target_item else pr)) for it, pr in get_picks(c)]
        return set_picks(c, ps)
    edit(name, fn, f'{target_item} prob -> {newprob}')

def scalar_edit(name, **kw):
    def fn(c):
        for k, v in kw.items():
            c = set_scalar(c, k, v)
        return c
    edit(name, fn, f'scalars {kw}')

# ---------- A. Good TCs (mod pick structures, S14 rune-equiv names) ----------
hgood = {'Act 1 (H) Good': 'Runes 13 equiv', 'Act 2 (H) Good': 'Runes 14 equiv',
         'Act 3 (H) Good': 'Runes 15 equiv', 'Act 4 (H) Good': 'Runes 16 equiv',
         'Act 5 (H) Good': 'Runes 17 equiv'}
for tc, runes in hgood.items():
    good_edit(tc, [('Jewelry C', 120), ('Flawed Gem', 27), ('Normal Gem', 28), ('Flawless Gem', 50),
                   ('Perfect Gem', 6), (runes, 30), ('wss', 4), ('Map Tier 1', 2),
                   ('Orbs', 4), ('Fate Drop', 2)])

ngood = {'Act 1 (N) Good': 'Runes 8', 'Act 2 (N) Good': 'Runes 9', 'Act 3 (N) Good': 'Runes 10',
         'Act 4 (N) Good': 'Runes 11', 'Act 5 (N) Good': 'Runes 12 equiv'}
for tc, runes in ngood.items():
    good_edit(tc, [('Jewelry C', 120), ('Chipped Gem', 4), ('Flawed Gem', 20), ('Normal Gem', 28),
                   ('Flawless Gem', 56), ('wss', 4), (runes, 28), ('Fate Drop', 2), ('Orbs', 1)])

good_edit('Act 1 Good', [('Jewelry A', 240), ('Chipped Gem', 192), ('wss', 4), ('Fate Drop', 2), ('Orbs', 1)])
good_edit('Act 2 Good', [('Jewelry B', 320), ('Chipped Gem', 176), ('Flawed Gem', 64), ('wss', 4),
                         ('Runes 1', 48), ('Runes 2', 48), ('Fate Drop', 2), ('Orbs', 1)])
good_edit('Act 3 Good', [('Jewelry C', 320), ('Chipped Gem', 112), ('Flawed Gem', 128), ('wss', 4),
                         ('Runes 3', 48), ('Runes 4', 48), ('Fate Drop', 2), ('Orbs', 1)])
good_edit('Act 4 Good', [('Jewelry C', 400), ('Chipped Gem', 24), ('Flawed Gem', 80), ('Normal Gem', 112),
                         ('Flawless Gem', 224), ('wss', 4), ('Runes 5', 112), ('Runes 6', 56),
                         ('Fate Drop', 2), ('Orbs', 1)])
good_edit('Act 5 Good', [('Jewelry C', 400), ('Chipped Gem', 12), ('Flawed Gem', 40), ('Normal Gem', 112),
                         ('Flawless Gem', 112), ('wss', 4), ('Runes 7', 56), ('Fate Drop', 2), ('Orbs', 1)])

for t, mapdrop in (('Map Good t1', 'T1 Map Drop'), ('Map Good t2', 'T2 Map Drop'), ('Map Good t3', 'T3 Map Drop')):
    good_edit(t, [('Jewelry C', 120), ('Flawed Gem', 28), ('Normal Gem', 28), ('Flawless Gem', 50),
                  ('Perfect Gem', 6), ('Runes 17 equiv', 30), ('wss', 6), (mapdrop, 5),
                  ('Map Orbs Drop', 8), ('Fate Drop', 5)])

# ---------- B. Runes cascade probabilities (S14 codes kept) ----------
runes = {'Runes 3': ('Runes 2', 4), 'Runes 3 unstack': ('Runes 2 unstack', 4),
         'Runes 5': ('Runes 4', 10), 'Runes 6': ('Runes 5', 12), 'Runes 7': ('Runes 6', 27),
         'Runes 8': ('Runes 7', 54), 'Runes 9': ('Runes 8', 107), 'Runes 10': ('Runes 9', 214),
         'Runes 11': ('Runes 10', 427), 'Runes 12': ('Runes 11', 631),
         'Runes 12 equiv': ('Runes 11', 631), 'Runes 13': ('Runes 12', 899),
         'Runes 13 equiv': ('Runes 12 equiv', 899), 'Runes 14': ('Runes 13', 1286),
         'Runes 14 equiv': ('Runes 13 equiv', 1286), 'Runes 15': ('Runes 14', 1743),
         'Runes 15 equiv': ('Runes 14 equiv', 1743), 'Runes 16': ('Runes 15', 2344),
         'Runes 16 equiv': ('Runes 15 equiv', 2344), 'Runes 17': ('Runes 16', 3063),
         'Runes 17 equiv': ('Runes 16 equiv', 3063)}
for tc, (cascade, p) in runes.items():
    prob_edit(tc, cascade, p)

# ---------- C. Junk TCs (halve junk/potion/misc, keep S14 ammo pick) ----------
junk_edits = {
    'Act 1 Junk': {'Potion 1': 8, 'Misc 0': 4},
    'Act 2 Junk': {'Act 1 Junk': 2, 'Potion 2': 8, 'Misc 0': 4},
    'Act 3 Junk': {'Act 2 Junk': 2, 'Potion 3': 8, 'Misc 1': 4},
    'Act 4 Junk': {'Act 3 Junk': 2, 'Potion 4': 8, 'Misc 1': 4},
    'Act 5 Junk': {'Act 4 Junk': 2, 'Potion 5': 8, 'Misc 2': 4},
}
for act in range(1, 6):
    for diff in ('(N)', '(H)'):
        junk_edits[f'Act {act} {diff} Junk'] = {'Act 5 Junk': 2, 'Potion 6': 8, 'Misc 2': 4}
for tc, changes in junk_edits.items():
    def fn(c, changes=changes):
        ps = [(it, str(changes[it]) if it in changes else pr) for it, pr in get_picks(c)]
        return set_picks(c, ps)
    edit(tc, fn, f'junk halved {list(changes)} (ammo kept)')

# ---------- D. BR Arena quality scalars ----------
for t in ('BR Arena Bodies N', 'BR Arena Bodies NM', 'BR Arena Bodies H'):
    scalar_edit(t, Unique=570, Set=400, Rare=850, Magic=450)
for t in ('BR Arena Chests N', 'BR Arena Chests NM', 'BR Arena Chests H'):
    scalar_edit(t, Unique=930, Set=500, Rare=840, Magic=260)

# ---------- E. Treasure Fallen ----------
def tf_edit(name, subs, goldcode, goldprob, orbs, cards):
    def fn(c):
        ps = [(it, pr) for it, pr in get_picks(c)]
        ps = [(it, str(subs[it]) if it in subs else (str(goldprob) if it == goldcode else pr))
              for it, pr in ps]
        ps.append((orbs, '1'))
        ps.append((cards, '1'))
        return set_picks(c, ps)
    edit(name, fn, f'boosted +{orbs}/{cards}')

tf_edit('Treasure Fallen H', {'Treasure Fallen Gem H': 4, 'Treasure Fallen Rune H': 4,
                              'Treasure Fallen Craft H': 4, 'Treasure Fallen Map': 4},
        '"gld,mul=4096"', 4, 'Treasure Fallen Orbs H', 'Treasure Fallen Cards H')
tf_edit('Treasure Fallen N', {'Treasure Fallen Gem N': 4, 'Treasure Fallen Rune N': 4,
                              'Treasure Fallen Craft N': 4},
        '"gld,mul=2048"', 15, 'Treasure Fallen Orbs N', 'Treasure Fallen Cards N')
tf_edit('Treasure Fallen NM', {'Treasure Fallen Gem NM': 4, 'Treasure Fallen Rune NM': 4,
                               'Treasure Fallen Craft NM': 4},
        '"gld,mul=3072"', 15, 'Treasure Fallen Orbs NM', 'Treasure Fallen Cards NM')

# ---------- F. Corrupted Zone ----------
scalar_edit('Corrupted Zone', Unique=150)

# ---------- G. Utility TC quality scalars ----------
scalar_edit('Horadric ID Book H', Set=100)
scalar_edit('Horadric ID Book N', Unique=5000, Set=100)
scalar_edit('Horadric ID Book NM', Unique=5000, Set=100)
scalar_edit('Horadric TP Book H', Set=100)
scalar_edit('Horadric TP Book N', Unique=5000, Set=100)
scalar_edit('Horadric TP Book NM', Unique=5000, Set=100)
scalar_edit('Larzuk Puzzlebox H', Unique=1000)
scalar_edit('Larzuk Puzzlebox NM', Unique=2000)
scalar_edit('Larzuk Puzzlepiece H', Unique=500)
scalar_edit('Larzuk Puzzlepiece N', Unique=2000)
scalar_edit('Larzuk Puzzlepiece NM', Unique=1000)
scalar_edit('Lillith Mirror H', Unique=15000, Set=100)
scalar_edit('Lillith Mirror N', Unique=15000, Set=100)
scalar_edit('Lillith Mirror NM', Unique=15000, Set=100)
scalar_edit('SkeletonKey H', Set=100)
scalar_edit('SkeletonKey N', Unique=5000, Set=100)
scalar_edit('SkeletonKey NM', Unique=5000, Set=100)
scalar_edit('Vial of Lightsong H', Set=100)
scalar_edit('Vial of Lightsong N', Unique=7500, Set=100)
scalar_edit('Vial of Lightsong NM', Unique=7500, Set=100)

# ---------- write back ----------
out = '\n'.join(lines)
if crlf:
    out = out.replace('\n', '\r\n')
with open(PATH, 'wb') as f:
    f.write(out.encode('latin1'))

uniq = sorted(set(changed))
print(f'changed rows: {len(changed)} edits across {len(uniq)} TCs')
for r in report:
    print(r)
missing = [r for r in report if r.startswith('!!')]
sys.exit(1 if missing else 0)
