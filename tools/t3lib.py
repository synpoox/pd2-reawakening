"""Shared helpers: load D2 tables, align rows between two versions, cell diffs."""
import os, difflib, collections

# Key columns per table (combined with occurrence number). None = sequence alignment.
KEYS = {
    'armor': ['code'], 'weapons': ['code'], 'misc': ['code'],
    'automagic': ['Name'], 'charstats': ['class'], 'experience': ['Level'],
    'gamble': ['code'], 'itemstatcost': ['Stat'], 'itemtypes': ['Code'],
    'levels': ['Name'], 'missiles': ['Missile'], 'monprop': ['Id'], 'monstats': ['Id'],
    'monstats2': ['Id'], 'pettype': ['pet type'], 'properties': ['code'], 'runes': ['Name'],
    'setitems': ['index'], 'sets': ['index'], 'skilldesc': ['skilldesc'], 'skills': ['skill'],
    'states': ['state'], 'treasureclassex': ['Treasure Class'], 'uniqueitems': ['index', 'code'],
    'itemratio': ['Function', 'Version', 'Uber', 'Class Specific'],
    'superuniques': ['Superunique'], 'objects': ['Name'], 'shrines': ['Name'],
    'qualityitems': ['nummods', 'mod1code', 'mod2code'], 'gems': ['code'],
    'difficultylevels': ['Name'], 'hireling': ['Hireling', 'Version', 'Id', 'Difficulty', 'Level'],
    'monlvl': ['Level'], 'monai': ['AI'], 'monumod': ['uniquemod'], 'skillcalc': ['code'],
    'montype': ['type'], 'sounds': ['Sound'], 'lvltypes': ['Name'], 'lvlprest': ['Name', 'Def'],
}


def find(root, name):
    d = os.path.join(root, 'data', 'global', 'excel')
    for f in os.listdir(d):
        if f.lower() == name.lower():
            return os.path.join(d, f)
    return None


class Table:
    def __init__(self, path):
        self.path = path
        raw = open(path, 'rb').read()
        self.trailing = raw.endswith(b'\r\n')
        lines = raw.decode('latin1').split('\r\n')
        if self.trailing:
            lines = lines[:-1]
        self.header_raw = lines[0]
        self.header = lines[0].split('\t')
        self.rows = [l.split('\t') for l in lines[1:]]
        self.lines = lines[1:]
        # column identity = name, or name#N for the Nth repeat of a name; '' columns unnamed
        self.col = {}
        self.colname = []
        seen = collections.Counter()
        for i, c in enumerate(self.header):
            if not c:
                self.colname.append('')
                continue
            seen[c] += 1
            ident = c if seen[c] == 1 else f'{c}#{seen[c]}'
            self.col[ident] = i
            self.colname.append(ident)

    def get(self, r, c):
        i = self.col.get(c)
        if i is None or i >= len(r):
            return ''
        return r[i]

    def rowdict(self, r):
        return {c: (r[i] if i < len(r) else '') for c, i in self.col.items()}

    def keys(self, table):
        kc = KEYS.get(table.lower())
        if not kc or any(c not in self.col for c in kc):
            return None
        occ = collections.Counter()
        out = []
        for r in self.rows:
            k = tuple(self.get(r, c) for c in kc)
            occ[k] += 1
            out.append(k + (occ[k],))
        return out


def similarity(ta, ra, tb, rb):
    cols = [c for c in ta.col if c in tb.col]
    if not cols:
        return 0
    same = sum(1 for c in cols if ta.get(ra, c) == tb.get(rb, c))
    nonempty = sum(1 for c in cols if ta.get(ra, c) or tb.get(rb, c)) or 1
    same_ne = sum(1 for c in cols if (ta.get(ra, c) or tb.get(rb, c)) and ta.get(ra, c) == tb.get(rb, c))
    return same_ne / nonempty


def align(tbl_name, a, b):
    """Return list m where m[i] = index into b for a's row i (or None)."""
    ka, kb = a.keys(tbl_name), b.keys(tbl_name)
    m = [None] * len(a.rows)
    if ka is not None and kb is not None:
        idx = {k: j for j, k in enumerate(kb)}
        for i, k in enumerate(ka):
            m[i] = idx.get(k)
        return m
    # sequence alignment on whole lines, then pair within replace blocks by similarity
    la = [l for l in a.lines]
    lb = [l for l in b.lines]
    if a.header != b.header:  # project to common columns so header changes don't break matching
        cols = [c for c in a.col if c in b.col]
        la = ['\t'.join(a.get(r, c) for c in cols) for r in a.rows]
        lb = ['\t'.join(b.get(r, c) for c in cols) for r in b.rows]
    sm = difflib.SequenceMatcher(None, la, lb, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'equal':
            for k in range(i2 - i1):
                m[i1 + k] = j1 + k
        elif op == 'replace':
            pair_block(a, b, i1, i2, j1, j2, m)
    return m


def pair_block(a, b, i1, i2, j1, j2, m, thresh=0.5):
    """Monotonic best pairing of rows a[i1:i2] to b[j1:j2] (LCS weighted by similarity)."""
    n, k = i2 - i1, j2 - j1
    if n * k > 400000:  # too big: fall back to positional
        for t in range(min(n, k)):
            if similarity(a, a.rows[i1 + t], b, b.rows[j1 + t]) >= thresh:
                m[i1 + t] = j1 + t
        return
    S = [[similarity(a, a.rows[i1 + x], b, b.rows[j1 + y]) for y in range(k)] for x in range(n)]
    D = [[0.0] * (k + 1) for _ in range(n + 1)]
    for x in range(n - 1, -1, -1):
        for y in range(k - 1, -1, -1):
            best = max(D[x + 1][y], D[x][y + 1])
            if S[x][y] >= thresh:
                best = max(best, S[x][y] + D[x + 1][y + 1])
            D[x][y] = best
    x = y = 0
    while x < n and y < k:
        if S[x][y] >= thresh and abs(D[x][y] - (S[x][y] + D[x + 1][y + 1])) < 1e-9:
            m[i1 + x] = j1 + y; x += 1; y += 1
        elif D[x + 1][y] >= D[x][y + 1]:
            x += 1
        else:
            y += 1


def celldiff(ta, ra, tb, rb):
    """Columns (by name) whose values differ; columns missing on one side are ignored."""
    return [c for c in ta.col if c in tb.col and ta.get(ra, c) != tb.get(rb, c)]
