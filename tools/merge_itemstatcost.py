"""Merge ItemStatCost: S14 vanilla base + mod-only stats placed into reclaimed dead rows.

Policy:
- S14 vanilla order and values preserved exactly for all kept stats.
- 41 mod-only stats are written into 41 reclaimed rows (stats unreferenced by any
  table in BOTH datasets, excluding core/code-driven ones).
- For reclaimed rows, the 6 new S12/S13 save columns copy the mod's Save Bits/Add/Param.
- Shared stats keep S14 values entirely (Stage 1 policy; mod display tweaks revisited later).
Outputs: reawakening-s14/data/global/excel/ItemStatCost.txt + docs/itemstatcost_mapping.md
"""
import json, os

S14 = r"extracted\s14_vanilla\data\global\excel\ItemStatCost.txt"
MOD = r"pd2-reawakening\data\global\excel\ItemStatCost.txt"
OUT = r"..\reawakening-s14\data\global\excel\ItemStatCost.txt"
DOC = r"..\reawakening-s14\docs\itemstatcost_mapping.md"

def load(p):
    with open(p, 'r', encoding='latin1') as f:
        lines = [ln.rstrip('\r\n') for ln in f]
    hdr = lines[0].split('\t')
    while hdr and hdr[-1] == '': hdr.pop()
    rows = [ln.split('\t') for ln in lines[1:] if ln.strip()]
    return hdr, rows

vhdr, vrows = load(S14)
mhdr, mrows = load(MOD)
NEWCOLS = ['Save Bits S12', 'Save Add S12', 'Save Param Bits S12',
           'Save Bits S13', 'Save Adds S13', 'Save Param Bits S13']
m2v = {}  # mod col index -> vanilla col index
for i, h in enumerate(mhdr):
    if h in vhdr:
        m2v[i] = vhdr.index(h)
assert len(m2v) == len(mhdr), [h for h in mhdr if h not in vhdr]

vset = {r[0] for r in vrows}
mod_only = [r for r in mrows if r[0] not in vset]
print('mod-only stats:', len(mod_only))

# reclaim candidates: unreferenced in both (from stat_usage.json), minus risky.
# Final selection is EXPLICIT (see below): every chosen row is table-driven only
# (nothing grants it in either dataset) and not known to be read by engine code
# via hardcoded ID. Excluded as engine/code risks: core stats (level, gold...),
# absorb-family hardcoded reads (item_absorbmagic_percent), resistance-bypass
# callbacks (skill_bypass_*), indestructible/durability/throwable item flags,
# per-frame unit state (missing_hp, source_unit_*, target*), PD2 systems likely
# code-driven (map_*, mon_cooldown*, pvp_*, *_count, *_idx, burningmin/max,
# firelength, damage_framerate), classic skill callbacks (ironmaiden_level,
# lifetap_level, skill_chillingarmor, manadrainmaxdam, stamdrain*), alignment.
RECLAIM_S14_ROWS = [
    82,   # item_timeduration
    88,   # item_doubleherbduration
    90,   # item_lightcolor
    183,  # equipped_eth            (PD2 helper, property-driven)
    203,  # item_skilloncrit        (event system is table-driven via itemevent cols)
    205,  # item_skillonpierce
    206,  # desecrated              (dead in S14)
    207,  # desecrator              (dead in S14)
    227, 228, 229,                  # item_*_damagemax_perlevel (op-evaluated only)
    235, 236, 237,                  # item_absorb_*_perlevel    (op-evaluated only)
    242,  # item_stamina_perlevel
    247,  # item_crushingblow_perlevel
    248,  # item_openwounds_perlevel
    249,  # item_kick_damage_perlevel
    251,  # item_find_gems_perlevel
    255,  # item_find_item
    260, 261, 262, 263, 264, 265, 266, 267,  # item_thrust/slash/crush absorb family (PD2, table-driven)
    305, 306, 307, 308,             # item_pierce_* (classic padding; real pierce uses passive_*_pierce)
    309, 310, 311, 312, 313, 314,   # item_*_vs_monster (classic padding)
    324,  # item_extra_charges      (classic padding)
    481,  # extra_holybolts         (PD2, property-driven)
    487,  # item_dmgpercent_permissinghppercent (PD2, property-driven)
]
both_unused = set(json.load(open('stat_usage.json'))['both_unused'])
vidx = {r[0]: i for i, r in enumerate(vrows)}
vname_by_idx = {i: r[0] for i, r in enumerate(vrows)}
for row in RECLAIM_S14_ROWS:
    assert vname_by_idx[row] in both_unused, f"row {row} ({vname_by_idx[row]}) is NOT unreferenced!"
reclaim = [vname_by_idx[row] for row in RECLAIM_S14_ROWS]
print('reclaiming', len(reclaim), 'rows')
assert len(reclaim) == len(mod_only), 'reclaim count != mod-only count!'

# build merged file: copy S14 rows verbatim (as raw cell lists padded to vhdr width)
merged = [(r + [''] * (len(vhdr) - len(r)))[:len(vhdr)] for r in vrows]
mapping = []
for mod_row, dead_name in zip(mod_only, reclaim):
    slot = vidx[dead_name]
    newr = [''] * len(vhdr)
    for mi, vi in m2v.items():
        newr[vi] = mod_row[mi] if mi < len(mod_row) else ''
    # mirror old save encoding into S12/S13 columns
    for old, new in [('Save Bits', 'Save Bits S12'), ('Save Add', 'Save Add S12'),
                     ('Save Param Bits', 'Save Param Bits S12'), ('Save Bits', 'Save Bits S13'),
                     ('Save Add', 'Save Adds S13'), ('Save Param Bits', 'Save Param Bits S13')]:
        newr[vhdr.index(new)] = newr[vhdr.index(old)]
    newr[vhdr.index('ID')] = str(slot)
    merged[slot] = newr
    mapping.append((slot, dead_name, mod_row[0]))

# validate
names = [r[0] for r in merged]
assert len(names) == 511 and len(set(names)) == 511, 'name collision!'
assert len(vset | {r[0] for r in mrows}) - len([s for s in vset if s in set(reclaim)]) == 511
for r in merged:
    assert len(r) == len(vhdr)

# write with CRLF, latin1, preserving the original header line byte-for-byte
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(S14, 'r', encoding='latin1') as f:
    raw_header = f.readline().rstrip('\r\n')
with open(OUT, 'w', encoding='latin1', newline='') as f:
    f.write(raw_header + '\r\n')
    for r in merged:
        # original rows have ncol-1 fields + trailing tab if header has trailing tab
        line = '\t'.join(r)
        if raw_header.endswith('\t'):
            line += '\t'
        f.write(line + '\r\n')

os.makedirs(os.path.dirname(DOC), exist_ok=True)
with open(DOC, 'w', encoding='utf-8') as f:
    f.write('# ItemStatCost merge mapping (S14 base + Reawakening stats)\n\n')
    f.write('S14 vanilla order preserved; mod stats occupy reclaimed dead rows.\n\n')
    f.write('| row | removed (dead S14 stat) | inserted mod stat |\n|---|---|---|\n')
    for slot, dead, mod in mapping:
        f.write(f'| {slot} | {dead} | {mod} |\n')
print('wrote', OUT)
print('wrote', DOC)
for slot, dead, mod in mapping:
    print(f'  row {slot:3d}: {dead:40s} -> {mod}')
