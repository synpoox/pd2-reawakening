"""Merge all mod tables onto the S14 base (except ItemStatCost, already done).

Policies:
  A (default): S14 rows kept byte-verbatim; mod-only rows appended (column-mapped by name).
  B: S14 wholesale, mod ignored (monsters/levels/hirelings/etc).
  Special: Experience (append 100+ rows + mod MaxLvl), skill-ID param remap in mod rows
     of item tables (S14 reordered some custom skills), reanimate monster-ID remap.
Outputs -> ../reawakening-s14/data/global/excel/  + docs/merge_log.md
"""
import os, re, json

MOD = r"pd2-reawakening\data\global\excel"
S14 = r"extracted\s14_vanilla\data\global\excel"
OUT = r"..\reawakening-s14\data\global\excel"
LOG = r"..\reawakening-s14\docs\merge_log.md"

def load(p):
    """returns raw_header, trimmed header, rows(cells), raw_lines (one per row)"""
    with open(p, 'r', encoding='latin1') as f:
        lines = [ln.rstrip('\r\n') for ln in f]
    raw_header = lines[0]
    hdr = raw_header.split('\t')
    while hdr and hdr[-1] == '': hdr.pop()
    rows, raw = [], []
    for ln in lines[1:]:
        if ln.strip():
            rows.append(ln.split('\t'))
            raw.append(ln)
    return raw_header, hdr, rows, raw

# ---------- skill-ID remap (mod row idx -> merged row idx) ----------
_, _, m_skills, _ = load(os.path.join(MOD, 'Skills.txt'))
_, _, v_skills, _ = load(os.path.join(S14, 'Skills.txt'))
m_skill_names = [r[0] for r in m_skills]
v_skill_names = [r[0] for r in v_skills]
v_skill_set = set(v_skill_names)
mod_only_skills = [n for n in m_skill_names if n not in v_skill_set]
merged_skill_names = list(v_skill_names) + mod_only_skills
skill_new_idx = {n: i for i, n in enumerate(merged_skill_names)}
skill_remap = {i: skill_new_idx[n] for i, n in enumerate(m_skill_names)}

# ---------- monster-ID remap (reanimate params) ----------
_, _, m_mon, _ = load(os.path.join(MOD, 'MonStats.txt'))
_, _, v_mon, _ = load(os.path.join(S14, 'MonStats.txt'))
v_mon_idx = {r[0]: i for i, r in enumerate(v_mon)}
mon_remap = {i: v_mon_idx[r[0]] for i, r in enumerate(m_mon) if r[0] in v_mon_idx}

# ---------- property classification (which props take skill/monster-ID params) ----------
_, phdr, m_props, _ = load(os.path.join(MOD, 'Properties.txt'))
SKILL_STATS = {'item_skillonequip', 'item_skillonattack', 'item_skillonkill',
               'item_skillondeath', 'item_skillonstriking', 'item_skillonstruck',
               'item_skillonlevelup', 'item_aura', 'item_charged_skill',
               'item_nonclassskill', 'item_singleskill', 'item_skillonequip_display',
               'item_nonclassskill_display'}
MON_STATS = {'item_reanimate'}
sc = [i for i, h in enumerate(phdr) if re.fullmatch(r'stat[1-7]', h or '')]
propstats = {}
for r in m_props:
    propstats[r[0]] = {r[i].strip() for i in sc if i < len(r) and r[i].strip()}
SKILL_PARAM_PROPS = {c for c, ss in propstats.items() if ss & SKILL_STATS}
MON_PARAM_PROPS = {c for c, ss in propstats.items() if ss & MON_STATS}

PROP_COL = re.compile(r'^(prop ?\d+|mod ?\d+ ?code|mod ?\d+|t1code ?\d+|pcode ?\d+[ab]?)$', re.I)
def param_col_for(h, hdr):
    hl = h.strip().lower()
    if 'prop' in hl: tgt = hl.replace('prop', 'par')
    elif 'code' in hl: tgt = hl.replace('code', 'param')
    elif hl.startswith('mod'): tgt = hl + ' param'
    else: return None
    norm = {x.strip().lower(): j for j, x in enumerate(hdr)}
    return norm.get(tgt)

warnings = []
def remap_row(fn, r, hdr):
    r = list(r)
    for i, h in enumerate(hdr):
        if not PROP_COL.match((h or '').strip()) or i >= len(r): continue
        code = r[i].strip()
        if not code: continue
        j = param_col_for(h, hdr)
        if j is None or j >= len(r): continue
        pv = r[j].strip()
        if not pv.lstrip('-').isdigit(): continue
        pid = int(pv)
        if code in SKILL_PARAM_PROPS:
            if pid in skill_remap:
                new = skill_remap[pid]
                if new != pid:
                    warnings.append(f"SKILL-REMAP {fn}: {r[0]} [{code}] {pid} ({m_skill_names[pid]}) -> {new}")
                    r[j] = str(new)
            else:
                warnings.append(f"!! SKILL-REMAP MISS {fn}: {r[0]} [{code}] {pid}")
        elif code in MON_PARAM_PROPS:
            if pid in mon_remap:
                new = mon_remap[pid]
                if new != pid:
                    warnings.append(f"MON-REMAP {fn}: {r[0]} [{code}] {pid} -> {new}")
                    r[j] = str(new)
            else:
                warnings.append(f"!! MON-REMAP MISS {fn}: {r[0]} [{code}] {pid}")
    return r

POLICY_B = {'MonStats.txt','MonStats2.txt','MonProp.txt','Levels.txt','CharStats.txt',
            'Gamble.txt','ItemRatio.txt','DifficultyLevels.txt','Hireling.txt','MonAi.txt',
            'MonLvl.txt','MonType.txt','MonUMod.txt','SkillCalc.txt'}
REMAP_TABLES = {'UniqueItems.txt','SetItems.txt','Sets.txt','Runes.txt','MagicPrefix.txt',
                'MagicSuffix.txt','AutoMagic.txt','CubeMain.txt'}

log = ['# Merge log: S14 base + Reawakening content\n']
for fn in sorted(os.listdir(S14)):
    if not fn.lower().endswith('.txt') or fn == 'ItemStatCost.txt': continue
    vp, mp = os.path.join(S14, fn), os.path.join(MOD, fn)
    if fn in POLICY_B or not os.path.exists(mp):
        with open(vp, 'rb') as f: data = f.read()
        with open(os.path.join(OUT, fn), 'wb') as f: f.write(data)
        log.append(f'## {fn}: S14 wholesale' + ('' if fn in POLICY_B else ' (mod has no such table)'))
        continue
    vraw_hdr, vhdr, vrows, vraw = load(vp)
    mraw_hdr, mhdr, mrows, _ = load(mp)
    # ItemTypes is keyed by Code (col 1): the mod has a duplicate-name row
    # ('Amulet' code 'lmul') that a name-keyed merge would drop.
    keycol = 1 if fn == 'ItemTypes.txt' else 0
    vset = {(r[keycol] if keycol < len(r) else r[0]) for r in vrows}
    m2v = {i: vhdr.index(h) for i, h in enumerate(mhdr) if h in vhdr}
    missing_cols = [h for h in mhdr if h and h not in vhdr]
    if missing_cols:
        warnings.append(f"!! {fn}: mod columns dropped (not in S14): {missing_cols}")

    appended = []
    if fn == 'Experience.txt':
        extra = [r for r in mrows if r[0].isdigit() and int(r[0]) > 99]
        mmax = next((r for r in mrows if r[0] == 'MaxLvl'), None)
        # keep S14 rows but drop S14 MaxLvl (mod's replaces it)
        keep = [(r, raw) for r, raw in zip(vrows, vraw) if r[0] != 'MaxLvl']
        vrows = [r for r, _ in keep]
        vraw = [raw for _, raw in keep]
        for r in extra + ([mmax] if mmax else []):
            nr = [''] * len(vhdr)
            for mi, vi in m2v.items():
                if mi < len(r): nr[vi] = r[mi]
            appended.append(nr)
        log.append(f'## {fn}: S14 levels + mod levels {len(extra)} extra + mod MaxLvl')
    else:
        for r in mrows:
            if (r[keycol] if keycol < len(r) else r[0]) in vset: continue
            if fn in REMAP_TABLES:
                r = remap_row(fn, r, mhdr)
            nr = [''] * len(vhdr)
            for mi, vi in m2v.items():
                if mi < len(r): nr[vi] = r[mi]
            appended.append(nr)
        log.append(f'## {fn}: S14 {len(vrows)} rows + {len(appended)} mod rows')

    trail = vraw_hdr.endswith('\t')
    with open(os.path.join(OUT, fn), 'w', encoding='latin1', newline='') as f:
        f.write(vraw_hdr + '\r\n')
        for raw in vraw:
            f.write(raw + '\r\n')  # S14 rows byte-verbatim
        for r in appended:
            line = '\t'.join(r)
            if trail: line += '\t'
            f.write(line + '\r\n')

for fn in os.listdir(MOD):
    if fn.lower().endswith('.txt') and not os.path.exists(os.path.join(S14, fn)):
        warnings.append(f"!! mod-only table {fn} not in S14 - copied verbatim")
        with open(os.path.join(MOD, fn), 'rb') as f: data = f.read()
        with open(os.path.join(OUT, fn), 'wb') as f: f.write(data)

log.append('\n## Warnings / remaps\n')
for w in warnings: log.append('- ' + w)
with open(LOG, 'w', encoding='utf-8') as f:
    f.write('\n'.join(log))
print('\n'.join(x for x in log if x.startswith('## ')))
print(f'\nwarnings: {len(warnings)} (see docs/merge_log.md)')
print('mod-only skills appended:', len(mod_only_skills))
