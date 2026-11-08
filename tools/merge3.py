"""Three-way merge of Reawakening's tables onto a new PD2 season.

    python merge3.py <base> <ours> <theirs> <out> <report.md>

base   = vanilla PD2 data Reawakening was built on (S11)
ours   = Reawakening data (v11.0.1, commit 308bca9)
theirs = vanilla PD2 data to port to (S14 Alliance)
Each is a directory holding data/global/excel. Writes <out>/data/global/excel/*.txt.

Rules
- A cell changed on one side only takes that side's value. Changed on both sides to
  different values is a conflict: resolved by RESOLVE (default ours) and reported.
- theirs rows keep their row index, since PD2's DLLs hardcode skill, stat and item ids.
  Rows only ours added go at the end, except in ANCHORED tables, where order matters
  (the first matching cube recipe wins) and they follow their Reawakening neighbour.
- A row ours deleted is deleted, unless theirs changed it (kept, reported).
  A row theirs deleted is deleted; if ours had changed it, that is reported.
- Id columns are renumbered to the row index; numeric skill ids in cells taken from
  ours are remapped through skill names.
- ItemStatCost has a 511-row cap and is placed by place_isc().
"""
import os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t3lib import Table, find, align
from resolutions import (RESOLVE, ISC_SLOTS, ISC_DROP, ROW_THEIRS, CELL_EDITS,
                         RESIST_CAP, RESIST_CAP_EXEMPT)
from slots import groups_for

ANCHORED = {'cubemain'}
# Tables whose row index is an id the DLLs or other tables use: S14 rows are never deleted.
NO_DELETE = {'itemstatcost', 'skills', 'missiles', 'states', 'monstats', 'levels', 'pettype',
             'itemtypes', 'misc', 'armor', 'weapons', 'runes', 'uniqueitems', 'setitems', 'sets',
             'magicprefix', 'magicsuffix', 'properties'}
ID_COLS = {'skills': 'Id', 'missiles': 'Id', 'itemstatcost': 'ID', 'states': 'id', 'pettype': 'idx'}

# (property code column, parameter column) pairs, per table, for skill-id remapping.
def prop_param_pairs(tn, hdr):
    pairs = []
    cols = set(hdr)
    def add(p, q):
        if p in cols and q in cols:
            pairs.append((p, q))
    for n in range(1, 13):
        add(f'prop{n}', f'par{n}')
        add(f'mod{n}code', f'mod{n}param')
        add(f'T1Code{n}', f'T1Param{n}')
        add(f'mod {n}', f'mod {n} param')
        for s in 'ab':
            add(f'aprop{n}{s}', f'apar{n}{s}')
            add(f'PCode{n}{s}', f'PParam{n}{s}')
        add(f'FCode{n}', f'FParam{n}')
    return pairs


def gap_pair(base, side, m):
    """Pair rows renamed in place: a run of unmatched base rows between two matched
    anchors, facing an equally long run of unmatched side rows."""
    used = set(j for j in m if j is not None)
    i, n = 0, len(base.rows)
    while i < n:
        if m[i] is not None:
            i += 1
            continue
        s = i
        while i < n and m[i] is None:
            i += 1
        prev = m[s - 1] if s > 0 else -1
        nxt = m[i] if i < n else len(side.rows)
        if nxt - prev - 1 == i - s and all(prev + 1 + k not in used for k in range(i - s)):
            for k in range(i - s):
                m[s + k] = prev + 1 + k
                used.add(prev + 1 + k)
    return m


HP_COLS = {'minHP', 'maxHP', 'MinHP(N)', 'MaxHP(N)', 'MinHP(H)', 'MaxHP(H)'}


def num(v):
    if v == '':
        return 0
    try:
        return int(v)
    except ValueError:
        return None


# Columns S14 rescaled globally: base and Reawakening values are multiplied before merging.
PRE_SCALE = {('MagicPrefix.txt', 'frequency'): 10, ('MagicSuffix.txt', 'frequency'): 10}


def prescale(name, *tables):
    for (tbl, col), k in PRE_SCALE.items():
        if tbl != name:
            continue
        for tb in tables:
            i = tb.col[col]
            for r in tb.rows:
                if i < len(r) and r[i].isdigit():
                    r[i] = str(int(r[i]) * k)
            tb.lines = ['	'.join(r) for r in tb.rows]


def auto_rule(name, col, bv, ov, tv):
    """Default for a cell both sides changed.
    MonStats HP: S14 rescaled some monsters (bosses x10), so Reawakening's edit is
    applied as a ratio. Numbers both sides moved the same way: the bigger move wins
    (it satisfies both intents). Anything else: Reawakening's value."""
    b, o, t = num(bv), num(ov), num(tv)
    if name == 'MonStats.txt' and col in HP_COLS and b and o is not None and t is not None:
        return 'ratio'
    if None not in (b, o, t) and (o - b) * (t - b) > 0:
        return 'ours' if abs(o - b) >= abs(t - b) else 'theirs'
    return 'ours'


def fmt(g):
    return ' / '.join(','.join(v for v in s if v) for s in g if any(s)) or '(empty)'


class Merged:
    """A merged table: header plus rows, each row with per-cell source ('b','o','t')."""
    def __init__(self, name, hdr, colname, rows, theirs):
        self.name, self.hdr, self.colname, self.rows, self.theirs = name, hdr, colname, rows, theirs
        self.col = {c: i for i, c in enumerate(colname) if c}

    def get(self, row, c):
        i = self.col.get(c)
        return row[0][i] if i is not None and i < len(row[0]) else ''

    def set(self, row, c, v, src=None):
        i = self.col[c]
        row[0][i] = v
        if src:
            row[1][i] = src


class Merger:
    def __init__(self, B, O, T):
        self.B, self.O, self.T = B, O, T
        self.conflicts = []   # (table, key, column, base, ours, theirs, chosen, how)
        self.notes = collections.defaultdict(list)
        self.unused_resolutions = set(RESOLVE)

    def resolve(self, name, key, col, bv, ov, tv):
        rk = (name, key, col)
        how = RESOLVE.get(rk) or RESOLVE.get((name, '*', col))
        self.unused_resolutions.discard(rk)
        self.unused_resolutions.discard((name, '*', col))
        if how is None and col.startswith('*'):
            how = 'theirs'   # comment columns: no game effect
        if how is None:
            how = auto_rule(name, col, bv, ov, tv)
        if how == 'ratio':
            chosen = str(round(int(ov) * int(tv) / int(bv)))
        else:
            chosen = ov if how == 'ours' else tv if how == 'theirs' else how
        if not col.startswith('*'):
            self.conflicts.append((name, key, col, bv, ov, tv, chosen, how))
        return chosen

    def merge_group(self, name, key, slots, ident, kind, gb, go, gt):
        """3-way merge of one slot group. g* are lists of slot tuples (one per slot)."""
        empty = tuple([''] * len(slots[0]))
        if go == gb or go == gt:
            return gt, 't'
        if gt == gb:
            return go, 'o'
        label = slots[0][0]
        if kind == 'atomic':
            how = RESOLVE.get((name, key, label), 'ours')
            self.unused_resolutions.discard((name, key, label))
            res = go if how == 'ours' else gt
            self.conflicts.append((name, key, f'[{label}..]', fmt(gb), fmt(go), fmt(gt), fmt(res), how))
            return res, 'o' if how == 'ours' else 't'

        def keyed(g):
            occ = collections.Counter(); out = collections.OrderedDict()
            for s in g:
                if s == empty:
                    continue
                k = tuple(s[i] for i in ident)
                occ[k] += 1
                out[k + (occ[k],)] = s
            return out
        B, O, T = keyed(gb), keyed(go), keyed(gt)
        res = []
        for k, ts in T.items():
            if k in B:
                bs = B[k]
                if k not in O:
                    if ts == bs:
                        continue   # Reawakening removed it
                    how = RESOLVE.get((name, key, f'{label}:{k[0]}'), 'theirs')
                    self.unused_resolutions.discard((name, key, f'{label}:{k[0]}'))
                    self.conflicts.append((name, key, f'{label}:{k[0]}', fmt([bs]), 'removed', fmt([ts]),
                                           'removed' if how == 'drop' else 'kept S14 slot', how))
                    if how != 'drop':
                        res.append(ts)
                    continue
                os_ = O[k]
                merged = []
                for fi, (bv, ov, tv) in enumerate(zip(bs, os_, ts)):
                    if ov == bv or ov == tv:
                        merged.append(tv)
                    elif tv == bv:
                        merged.append(ov)
                    else:
                        merged.append(self.resolve(name, key, f'{slots[0][fi]}[{k[0]}]', bv, ov, tv))
                res.append(tuple(merged))
            elif k in O and O[k] != ts:
                ch = RESOLVE.get((name, key, f'{label}:{k[0]}'), 'ours')
                self.conflicts.append((name, key, f'{label}:{k[0]}', '', fmt([O[k]]), fmt([ts]), ch, 'both added'))
                res.append(O[k] if ch == 'ours' else ts)
            else:
                res.append(ts)
        for k, os_ in O.items():
            if k not in B and k not in T:
                res.append(os_)
            if k in B and k not in T and os_ != B[k]:
                self.conflicts.append((name, key, f'{label}:{k[0]}', fmt([B[k]]), fmt([os_]), 'removed', 'removed (S14)', 'auto'))
        if len(res) > len(slots):
            self.conflicts.append((name, key, f'[{label}..] overflow', fmt(gb), fmt(go), fmt(gt),
                                   'dropped ' + fmt(res[len(slots):]), 'OVERFLOW'))
            res = res[:len(slots)]
        res += [empty] * (len(slots) - len(res))
        return res, 'm'

    def merge_table(self, name):
        tn = name[:-4].lower()
        b = Table(find(self.B, name)); t = Table(find(self.T, name))
        op = find(self.O, name)
        o = Table(op) if op else None
        if o is None or (o.lines == b.lines and o.header_raw == b.header_raw):
            self.notes[name].append('Reawakening did not change it: S14 verbatim')
            return None
        if t.lines == b.lines and t.header_raw == b.header_raw:
            self.notes[name].append('S14 did not change it: Reawakening verbatim')
        prescale(name, b, o)
        mo = gap_pair(b, o, align(tn, b, o))
        mt = gap_pair(b, t, align(tn, b, t))

        hdr = list(t.header); colname = list(t.colname)
        extra = [c for c in o.colname if c and c not in t.col and c not in b.col]
        if extra:
            self.notes[name].append(f'Reawakening-only columns appended: {extra}')
            while hdr and hdr[-1] == '':
                hdr.pop(); colname.pop()
            hdr += [o.header[o.col[c]] for c in extra]; colname += extra
        W = len(hdr)

        def pad(cells):
            return list(cells[:W]) + [''] * (W - len(cells))

        def theirs_row(tj, origin):
            return [pad(t.rows[tj]), ['t'] * W, origin, t.lines[tj]]

        def ours_row(oj):
            orow = o.rows[oj]
            cells = [o.get(orow, c) if c in o.col else '' for c in colname]
            return [cells, ['o'] * W, 'ours-new', None]

        groups = groups_for(tn, set(colname))
        grouped = {c for slots, _, _ in groups for s in slots for c in s}
        cidx = {c: i for i, c in enumerate(colname) if c}

        def gval(tb, row, slots):
            return [tuple(tb.get(row, c) if c in tb.col else '' for c in s) for s in slots]

        def cellmerge(bi, oj, tj):
            br, orow, trow = b.rows[bi], o.rows[oj], t.rows[tj]
            key = trow[0] if trow else ''
            out, src = [None] * W, [None] * W
            for slots, ident, kind in groups:
                res, s = self.merge_group(name, key, slots, ident, kind,
                                          gval(b, br, slots), gval(o, orow, slots), gval(t, trow, slots))
                for slot, vals in zip(slots, res):
                    for c, v in zip(slot, vals):
                        out[cidx[c]] = v
                        src[cidx[c]] = 'o' if s in 'om' and v != t.get(trow, c) else 't'
            for ci, c in enumerate(colname):
                if c in grouped:
                    continue
                if not c:
                    out[ci] = trow[ci] if ci < len(trow) else ''; src[ci] = 't'; continue
                tv = t.get(trow, c) if c in t.col else None
                bv = b.get(br, c) if c in b.col else None
                ov = o.get(orow, c) if c in o.col else bv
                if tv is None:
                    out[ci] = ov or ''; src[ci] = 'o'
                elif bv is None or ov == bv or ov == tv:
                    out[ci] = tv; src[ci] = 't'
                elif tv == bv:
                    out[ci] = ov; src[ci] = 'o'
                else:
                    ch = self.resolve(name, key, c, bv, ov, tv)
                    out[ci] = ch; src[ci] = 'o' if ch == ov else 't'
            return [out, src, 'merged', t.lines[tj] if out == pad(trow) else None]

        inv_t = {j: i for i, j in enumerate(mt) if j is not None}
        inv_o = {j: i for i, j in enumerate(mo) if j is not None}
        rows, pos_of_base, split = [], {}, []
        for tj in range(len(t.rows)):
            bi = inv_t.get(tj)
            if bi is None:
                rows.append(theirs_row(tj, 'theirs-new'))
                continue
            oj = mo[bi]
            how = ROW_THEIRS.get((name, t.rows[tj][0]))
            if how:
                self.notes[name].append(f'{t.rows[tj][0]!r}: S14 row taken whole (decision)')
                rows.append(theirs_row(tj, 'theirs'))
                pos_of_base[bi] = len(rows) - 1
                if how == 'split' and oj is not None:
                    split.append(oj)
                    self.notes[name].append(f'{o.rows[oj][0]!r}: Reawakening row kept as its own row (decision)')
                continue
            if oj is None:
                same = all(t.get(t.rows[tj], c) == b.get(b.rows[bi], c) for c in b.col if c in t.col)
                if same and tn in NO_DELETE:
                    self.notes[name].append(f'Reawakening removed {b.rows[bi][0]!r}; S14 row kept (id table)')
                    rows.append(theirs_row(tj, 'theirs'))
                    pos_of_base[bi] = len(rows) - 1
                    continue
                if same:
                    self.notes[name].append(f'row deleted by Reawakening: {b.rows[bi][0]!r}')
                    continue
                self.conflicts.append((name, b.rows[bi][0], '<row>', 'present', 'deleted', 'changed', 'kept S14 row', 'auto'))
                rows.append(theirs_row(tj, 'theirs'))
            else:
                rows.append(cellmerge(bi, oj, tj))
            pos_of_base[bi] = len(rows) - 1
        for bi, tj in enumerate(mt):
            if tj is None and mo[bi] is not None and o.lines[mo[bi]] != b.lines[bi]:
                self.conflicts.append((name, b.rows[bi][0], '<row>', 'present', 'changed', 'deleted', 'deleted (S14)', 'auto'))
        added = sorted(split + [oj for oj in range(len(o.rows)) if oj not in inv_o])
        if tn in ANCHORED:
            inserts = collections.defaultdict(list)
            for oj in added:
                a, anchor = oj - 1, -1
                while a >= 0:
                    if a in inv_o and inv_o[a] in pos_of_base:
                        anchor = pos_of_base[inv_o[a]]; break
                    a -= 1
                inserts[anchor].append(oj)
            new = [ours_row(oj) for oj in inserts.get(-1, [])]
            for p, r in enumerate(rows):
                new.append(r)
                new += [ours_row(oj) for oj in inserts.get(p, [])]
            rows = new
        else:
            rows += [ours_row(oj) for oj in added]
        edited = sum(1 for r in rows if r[2] == 'merged' and 'o' in r[1])
        self.notes[name].append(f'{len(t.rows)} S14 rows; {edited} carry Reawakening edits; '
                                f'{len(added)} Reawakening rows added')
        m = Merged(name, hdr, colname, rows, t)
        m.ours = o
        return m


def renumber(m):
    c = ID_COLS.get(m.name[:-4].lower())
    if not c:
        return
    for i, r in enumerate(m.rows):
        if m.get(r, c) != str(i):
            m.set(r, c, str(i))
            r[3] = None


def remap_ids(merged, ours_dir, notes):
    """Numeric skill/state ids in property params taken from Reawakening -> merged ids,
    through the names in Reawakening's own Skills/States tables."""
    props = merged['Properties.txt']
    kinds = {}  # property code -> id table
    for r in props.rows:
        code, func = props.get(r, 'code'), props.get(r, 'func1')
        if func in ('11', '19', '22'):
            kinds[code] = 'Skills.txt'
        elif code == 'state':
            kinds[code] = 'States.txt'
    maps = {}
    for tbl in ('Skills.txt', 'States.txt'):
        o_names = [r[0] for r in Table(find(ours_dir, tbl)).rows]
        m_idx = {r[0][0]: i for i, r in enumerate(merged[tbl].rows)}
        maps[tbl] = (o_names, m_idx)
    count = collections.Counter(); miss = []
    for name, m in merged.items():
        for p, q in prop_param_pairs(name[:-4].lower(), m.colname):
            pi, qi = m.col[p], m.col[q]
            for r in m.rows:
                kind = kinds.get(r[0][pi])
                if kind is None or r[1][qi] != 'o' or not r[0][qi].isdigit():
                    continue
                o_names, m_idx = maps[kind]
                v = int(r[0][qi])
                if v < len(o_names) and o_names[v] in m_idx:
                    nv = str(m_idx[o_names[v]])
                    if nv != r[0][qi]:
                        r[0][qi] = nv; r[3] = None; count[(name, kind)] += 1
                else:
                    miss.append((name, r[0][0], p, v))
    for (n, k), c in count.items():
        notes[n].append(f'{c} numeric {k[:-4].lower()} ids remapped')
    return miss


def place_isc(m, notes):
    """S14 stats keep their ids. Reawakening's stats replace dead S14 rows (ISC_SLOTS)."""
    s14 = [r for r in m.rows if r[2] != 'ours-new']
    new = [r for r in m.rows if r[2] == 'ours-new']
    by_name = {m.get(r, 'Stat'): i for i, r in enumerate(s14)}
    placed = []
    for r in new:
        stat = m.get(r, 'Stat')
        if stat in ISC_DROP:
            notes['ItemStatCost.txt'].append(f'dropped {stat} (unused vanilla stat S14 removed)')
            continue
        slot = ISC_SLOTS[stat]
        old = m.get(s14[slot], 'Stat')
        assert s14[slot][2] != 'ours-new', (stat, slot)
        # new S12/S13 save columns mirror the live save layout
        for a, bcol in (('Save Bits S12', 'Save Bits'), ('Save Add S12', 'Save Add'),
                        ('Save Param Bits S12', 'Save Param Bits'), ('Save Bits S13', 'Save Bits'),
                        ('Save Adds S13', 'Save Add'), ('Save Param Bits S13', 'Save Param Bits')):
            m.set(r, a, m.get(r, bcol), 'o')
        s14[slot] = r
        placed.append((slot, old, stat))
    assert len(s14) == 511
    m.rows = s14
    return placed


def write(m, path):
    t = m.theirs
    lines = ['\t'.join(m.hdr) if m.hdr != t.header else t.header_raw]
    for cells, src, origin, raw in m.rows:
        lines.append(raw if raw is not None else '\t'.join(cells))
    data = '\r\n'.join(lines) + ('\r\n' if t.trailing else '')
    with open(path, 'wb') as f:
        f.write(data.encode('latin1'))


def post_edits(merged, notes):
    """Decisions applied to the merged rows: CELL_EDITS, and Reawakening's resist cap
    on monsters that are new in S14."""
    for (tbl, key, col), v in CELL_EDITS.items():
        m = merged[tbl]
        hit = [r for r in m.rows if r[0][0] == key]
        assert hit, (tbl, key)
        for r in hit:
            m.set(r, col, v, 'o'); r[3] = None
        notes[tbl].append(f'{key}: {col} = {v} (decision)')
    m = merged['MonStats.txt']
    res = [c for c in m.col if c.startswith('Res')]
    for r in m.rows:
        if r[2] != 'theirs-new' or r[0][0] in RESIST_CAP_EXEMPT:
            continue
        if m.get(r, 'killable') != '1' or m.get(r, 'primeevil') or m.get(r, 'neverCount') or m.get(r, 'inTown'):
            continue
        for c in res:
            v = m.get(r, c)
            if v.isdigit() and int(v) >= 100:
                m.set(r, c, str(RESIST_CAP), 'o'); r[3] = None
                notes['MonStats.txt'].append(f'{r[0][0]}: {c} {v} -> {RESIST_CAP} (resist cap on new S14 monster)')


def main():
    B, O, T, OUT, REPORT = sys.argv[1:6]
    mg = Merger(B, O, T)
    excel_t = os.path.join(T, 'data', 'global', 'excel')
    out_x = os.path.join(OUT, 'data', 'global', 'excel')
    os.makedirs(out_x, exist_ok=True)
    merged = {}
    names = sorted(f for f in os.listdir(excel_t) if f.endswith('.txt'))
    for f in names:
        m = mg.merge_table(f)
        if m is not None:
            merged[f] = m
    for m in merged.values():
        if m.name.lower() != 'itemstatcost.txt':
            renumber(m)
    miss = remap_ids(merged, O, mg.notes)
    placed = place_isc(merged['ItemStatCost.txt'], mg.notes) if 'ItemStatCost.txt' in merged else []
    if 'ItemStatCost.txt' in merged:
        renumber(merged['ItemStatCost.txt'])
    post_edits(merged, mg.notes)
    for f in names:
        dst = os.path.join(out_x, f)
        if f in merged:
            write(merged[f], dst)
        else:
            with open(find(T, f), 'rb') as s, open(dst, 'wb') as d:
                d.write(s.read())
    # report
    with open(REPORT, 'w', encoding='utf-8') as r:
        r.write('# Table merge report\n\n## Tables\n\n')
        for f in names:
            for n in mg.notes.get(f, []) or ['S14 verbatim']:
                r.write(f'- **{f}**: {n}\n')
        r.write('\n## ItemStatCost placement (S14 row replaced -> Reawakening stat)\n\n| id | S14 stat replaced | Reawakening stat |\n|---|---|---|\n')
        for slot, old, stat in placed:
            r.write(f'| {slot} | {old} | {stat} |\n')
        r.write(f'\n## Conflicts ({len(mg.conflicts)})\n\n| table | row | column | S11 | Reawakening | S14 | result | rule |\n|---|---|---|---|---|---|---|---|\n')
        esc = lambda s: str(s).replace('|', '\\|')
        for c in mg.conflicts:
            r.write('| ' + ' | '.join(esc(x) for x in c) + ' |\n')
        if miss:
            r.write(f'\n## Unmapped numeric skill ids ({len(miss)})\n\n')
            for x in miss:
                r.write(f'- {x}\n')
        if mg.unused_resolutions:
            r.write('\n## Resolutions that matched nothing\n\n')
            for x in sorted(mg.unused_resolutions):
                r.write(f'- {x}\n')
    import json
    with open(os.path.splitext(REPORT)[0] + '.json', 'w', encoding='utf-8') as j:
        json.dump({'notes': mg.notes, 'conflicts': mg.conflicts, 'placed': placed}, j)
    print(f'merged {len(merged)} tables, {len(mg.conflicts)} conflicts, {len(miss)} unmapped skill ids, '
          f'{len(placed)} stats placed')


if __name__ == '__main__':
    main()
