"""Three-way merge of patchstring.tbl.

    python merge_tbl.py <base.tbl> <ours.tbl> <theirs.tbl> <out.tbl> <report.md>

theirs' entries keep their index (compiled .bin files reference strings by index);
keys only ours has are appended. A value changed on one side takes that side; changed
on both sides takes TBL_RESOLVE or else ours, and is reported.
"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from merge_patchstring import parse, build, verify
from resolutions import TBL_RESOLVE


def entries(path):
    _, _, e = parse(path)
    out = []
    occ = collections.Counter()
    for x in sorted(e, key=lambda x: x['idx']):
        occ[x['key']] += 1
        out.append(((x['key'], occ[x['key']]), x['val']))
    return out


def main():
    bp, op, tp, outp, rep = sys.argv[1:6]
    B = dict(entries(bp)); O = entries(op); T = entries(tp)
    Od = dict(O)
    pairs, conflicts, took_ours = [], [], 0
    for k, tv in T:
        bv, ov = B.get(k), Od.get(k)
        if ov is None or ov == bv or ov == tv:
            v = tv
        elif bv is not None and tv == bv:
            v = ov; took_ours += 1
        else:
            how = TBL_RESOLVE.get(k[0].decode('latin1'), 'ours')
            v = ov if how == 'ours' else tv if how == 'theirs' else how.encode('latin1')
            conflicts.append((k[0], bv, ov, tv, v))
        pairs.append((k[0], v))
    tkeys = {k for k, _ in T}
    added = [(k, v) for k, v in O if k not in tkeys and k not in B]
    dropped = [k for k, v in O if k not in tkeys and k in B]   # theirs removed it
    pairs += [(k[0], v) for k, v in added]
    blob, nl = build(pairs)
    bad, ok = verify(blob, pairs)
    assert bad == 0 and ok, (bad, ok)
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    open(outp, 'wb').write(blob)
    d = lambda b: '' if b is None else b.decode('latin1').replace('|', '\\|').replace('\n', '\\n')
    with open(rep, 'w', encoding='utf-8') as f:
        f.write(f'# patchstring.tbl merge\n\n- {len(T)} S14 strings (indexes kept), {took_ours} carry Reawakening text\n'
                f'- {len(added)} Reawakening strings appended\n- {len(dropped)} strings S14 removed\n'
                f'- {len(conflicts)} changed on both sides\n\n')
        f.write('## Changed on both sides\n\n| key | S11 | Reawakening | S14 | result |\n|---|---|---|---|---|\n')
        for k, bv, ov, tv, v in conflicts:
            f.write(f'| {d(k)} | {d(bv)} | {d(ov)} | {d(tv)} | {"Reawakening" if v == ov else "S14" if v == tv else d(v)} |\n')
    print(f'{len(pairs)} strings: {took_ours} Reawakening edits, {len(added)} added, {len(conflicts)} conflicts, NumLoops={nl}')


if __name__ == '__main__':
    main()
