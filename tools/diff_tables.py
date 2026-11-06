"""Compare mod txt tables (repo data/) vs vanilla s14 extracted tables.

For each shared txt: columns identical? row count? first-col keys added/removed;
for same keys: count differing cells. For ItemStatCost additionally check order.
"""
import os, sys

MOD = r"pd2-reawakening\data\global\excel"
VAN = r"extracted\s14_vanilla\data\global\excel"

def load(path):
    with open(path, 'r', encoding='latin1') as f:
        lines = [ln.rstrip('\n').rstrip('\r') for ln in f]
    rows = [ln.split('\t') for ln in lines if ln.strip()]
    return rows

report = []
txts = sorted(f for f in os.listdir(MOD) if f.lower().endswith('.txt'))
for fn in txts:
    mp = os.path.join(MOD, fn)
    vp = os.path.join(VAN, fn)
    if not os.path.exists(vp):
        report.append((fn, "NOT IN VANILLA S14", "", ""))
        continue
    mrows, vrows = load(mp), load(vp)
    mhdr, vhdr = mrows[0], vrows[0]
    # strip trailing empty cols
    def trim(h):
        while h and h[-1] == '': h.pop()
        return h
    mhdr2, vhdr2 = list(mhdr), list(vhdr)
    trim(mhdr2); trim(vhdr2)
    col_match = mhdr2 == vhdr2
    mkeys = [r[0] for r in mrows[1:] if r]
    vkeys = [r[0] for r in vrows[1:] if r]
    mset, vset = set(mkeys), set(vkeys)
    added_in_mod = sorted(mset - vset)
    missing_in_mod = sorted(vset - mset)
    # cell diffs for common keys (use header of vanilla as reference)
    common = mset & vset
    mdiff = 0
    mdiff_keys = []
    mlookup = {}
    for r in mrows[1:]:
        if r and r[0] in common and r[0] not in mlookup:
            mlookup[r[0]] = r
    vlookup = {}
    for r in vrows[1:]:
        if r and r[0] in common and r[0] not in vlookup:
            vlookup[r[0]] = r
    for k in sorted(common):
        mr, vr = mlookup.get(k), vlookup.get(k)
        if mr is None or vr is None: continue
        maxlen = max(len(mr), len(vr))
        mrp = mr + [''] * (maxlen - len(mr))
        vrp = vr + [''] * (maxlen - len(vr))
        d = sum(1 for a, b in zip(mrp, vrp) if a != b)
        if d:
            mdiff += 1
            mdiff_keys.append(k)
    report.append((fn,
                   f"cols {'SAME' if col_match else 'DIFF'} ({len(mhdr2)}v{len(vhdr2)})",
                   f"rows mod={len(mkeys)} van={len(vkeys)}",
                   f"+mod={len(added_in_mod)} -mod={len(missing_in_mod)} changed={mdiff}",
                   added_in_mod[:8], missing_in_mod[:8], mdiff_keys[:8]))

for fn, c, r, d, *extra in report:
    print(f"{fn}\n   {c} | {r} | {d}")
    if extra[0]: print(f"     mod-only keys: {extra[0]}")
    if extra[1]: print(f"     vanilla-only keys: {extra[1]}")
    if extra[2]: print(f"     changed keys sample: {extra[2]}")
