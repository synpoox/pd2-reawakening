"""Find reclaimable ItemStatCost rows.

Build the union stat set (mod S11 + vanilla S14) = 552 names, cap is 511.
A row is reclaimable if its stat is not referenced anywhere:
  - Properties.txt stat1..stat7 (and the property must itself be used by items/recipes)
  - Skills.txt any column containing 'stat'
  - ItemStatCost self-references (op stat columns)
  - AutoMagic / MagicPrefix / MagicSuffix / Runes / SetItems / UniqueItems / CubeMain
    reference PROPERTY codes -> map to stats via Properties.
Stats referenced by hardcoded game code (legacy core stats) are NOT reclaimable
even if unreferenced in tables - flagged separately by row index (<180 = risky).
"""
import os, re, json

SETS = {
    'mod': r"pd2-reawakening\data\global\excel",
    's14': r"extracted\s14_vanilla\data\global\excel",
}

def load(path):
    with open(path, 'r', encoding='latin1') as f:
        lines = [ln.rstrip('\r\n') for ln in f]
    hdr = lines[0].split('\t')
    while hdr and hdr[-1] == '': hdr.pop()
    rows = []
    for ln in lines[1:]:
        if not ln.strip(): continue
        r = ln.split('\t')
        rows.append(r)
    return hdr, rows

def isc_stats(root):
    _, rows = load(os.path.join(root, 'ItemStatCost.txt'))
    return [r[0] for r in rows]

# 1. direct stat references from any column whose header contains 'stat'
STAT_COL_HINT = re.compile(r'stat', re.I)
def direct_stat_refs(root):
    refs = set()
    for fn in os.listdir(root):
        if not fn.lower().endswith('.txt'): continue
        if fn.lower() == 'properties.txt': continue  # circular: only count via used codes
        try: hdr, rows = load(os.path.join(root, fn))
        except Exception: continue
        cols = [i for i, h in enumerate(hdr) if STAT_COL_HINT.search(h or '') and i != 0]
        if not cols: continue
        for r in rows:
            for i in cols:
                if i < len(r) and r[i].strip():
                    refs.add(r[i].strip())
    return refs

# 2. property codes referenced by content tables -> resolve to stats via Properties
PROP_COL_HINT = re.compile(r'^(mod ?\d+ ?code|mod ?\d+|prop ?\d+|t1code ?\d+)$', re.I)
def used_property_codes(root):
    codes = set()
    # tables that carry property codes in modNcode / prop columns
    for fn in ['UniqueItems.txt','SetItems.txt','Runes.txt','MagicPrefix.txt',
               'MagicSuffix.txt','AutoMagic.txt','CubeMain.txt']:
        p = os.path.join(root, fn)
        if not os.path.exists(p): continue
        hdr, rows = load(p)
        cols = [i for i, h in enumerate(hdr) if PROP_COL_HINT.match((h or '').strip())]
        for r in rows:
            for i in cols:
                if i < len(r) and r[i].strip():
                    codes.add(r[i].strip())
    return codes

def property_to_stats(root, used_codes):
    p = os.path.join(root, 'Properties.txt')
    hdr, rows = load(p)
    stat_cols = [i for i, h in enumerate(hdr) if re.fullmatch(r'stat[1-7]', h or '')]
    stats = set()
    for r in rows:
        if r[0] in used_codes:
            for i in stat_cols:
                if i < len(r) and r[i].strip():
                    stats.add(r[i].strip())
    return stats

report = {}
all_names = {}
for label, root in SETS.items():
    stats = isc_stats(root)
    all_names[label] = stats
    direct = direct_stat_refs(root)
    props = used_property_codes(root)
    via_props = property_to_stats(root, props)
    used = direct | via_props
    report[label] = {'rows': len(stats), 'direct_refs': len(direct),
                     'used_prop_codes': len(props), 'via_props': len(via_props)}
    # store per-stat usage
    report[label]['unused'] = [s for s in stats if s not in used]

mod_set, s14_set = set(all_names['mod']), set(all_names['s14'])
union = mod_set | s14_set
print(f"mod rows={len(all_names['mod'])} s14 rows={len(all_names['s14'])} union={len(union)} overage={len(union)-511}")

# unused in BOTH datasets = strongest reclaim candidates
unused_mod = set(report['mod']['unused']); unused_s14 = set(report['s14']['unused'])
both_unused = sorted((unused_mod & unused_s14) )
print(f"unreferenced in mod tables: {len(unused_mod)}, in s14 tables: {len(unused_s14)}, in BOTH: {len(both_unused)}")

# positional info from S14 file (our base)
s14_idx = {n: i for i, n in enumerate(all_names['s14'])}
mod_idx = {n: i for i, n in enumerate(all_names['mod'])}
print("\nCandidates (unused in both), with row indices:")
for n in both_unused:
    mi = mod_idx.get(n, -1); vi = s14_idx.get(n, -1)
    zone = 'LEGACY' if (0 <= vi < 180 or 0 <= mi < 180) else 'custom-region'
    print(f"  {n:45s} mod_row={mi:4d} s14_row={vi:4d} {zone}")

with open('stat_usage.json', 'w', encoding='utf-8') as f:
    json.dump({'report': {k: {kk: vv for kk, vv in v.items() if kk != 'unused'} for k, v in report.items()},
               'unused_mod': sorted(unused_mod), 'unused_s14': sorted(unused_s14),
               'both_unused': both_unused}, f, indent=1)
print("\nsaved stat_usage.json")
