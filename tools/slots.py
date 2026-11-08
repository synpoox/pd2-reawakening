"""Slot groups: sets of numbered columns that hold a list (properties, TC items, desc lines).

A group is (slots, ident, kind): slots is a list of column-name lists, ident the field
indexes identifying what a slot holds, kind 'list' (match slots by ident) or 'atomic'
(order matters, e.g. monster AI skill slots or rune order: taken whole from one side).
"""


def _slots(fields, ns):
    return [[f.format(n=n) for f in fields] for n in ns]


def L(fields, ns, ident=(0,)):
    return (_slots(fields, ns), ident, 'list')


def A(fields, ns):
    return (_slots(fields, ns), (), 'atomic')


PROP = ['prop{n}', 'par{n}', 'min{n}', 'max{n}']
AFFIX = ['mod{n}code', 'mod{n}param', 'mod{n}min', 'mod{n}max']
R = range

GROUPS = {
    'uniqueitems': [L(PROP, R(1, 13), (0, 1))],
    # set bonuses: one group per bonus tier n, holding its a and b slots
    'setitems': [L(PROP, R(1, 10), (0, 1))] +
                [([[f'aprop{n}{s}', f'apar{n}{s}', f'amin{n}{s}', f'amax{n}{s}'] for s in 'ab'], (0, 1), 'list')
                 for n in R(1, 6)],
    'sets': [([[f'PCode{n}{s}', f'PParam{n}{s}', f'PMin{n}{s}', f'PMax{n}{s}'] for s in 'ab'], (0, 1), 'list')
             for n in R(2, 6)] +
            [L(['FCode{n}', 'FParam{n}', 'FMin{n}', 'FMax{n}'], R(1, 9), (0, 1))],
    'runes': [L(['T1Code{n}', 'T1Param{n}', 'T1Min{n}', 'T1Max{n}'], R(1, 8), (0, 1)),
              L(['itype{n}'], R(1, 7)), L(['etype{n}'], R(1, 4)), A(['Rune{n}'], R(1, 7))],
    'magicprefix': [L(AFFIX, R(1, 4), (0, 1)), L(['itype{n}'], R(1, 8)), L(['etype{n}'], R(1, 6))],
    'magicsuffix': [L(AFFIX, R(1, 4), (0, 1)), L(['itype{n}'], R(1, 8)), L(['etype{n}'], R(1, 6))],
    'automagic': [L(AFFIX, R(1, 4), (0, 1)), L(['itype{n}'], R(1, 8)), L(['etype{n}'], R(1, 6))],
    'qualityitems': [L(AFFIX, R(1, 3), (0, 1))],
    'cubemain': [A(['input {n}'], R(1, 8))] +
                [L([p + 'mod {n}', p + 'mod {n} chance', p + 'mod {n} param', p + 'mod {n} min', p + 'mod {n} max'],
                   R(1, 6), (0, 2)) for p in ('', 'b ', 'c ')],
    'treasureclassex': [L(['Item{n}', 'Prob{n}'], R(1, 11))],
    'monstats': [A(['Skill{n}', 'Sk{n}mode', 'Sk{n}lvl'], R(1, 9))],
    'skilldesc': [L(['descline{n}', 'desctexta{n}', 'desctextb{n}', 'desccalca{n}', 'desccalcb{n}'], R(1, 7), (0, 1, 2))] +
                 [L([f'dsc{d}line{{n}}', f'dsc{d}texta{{n}}', f'dsc{d}textb{{n}}', f'dsc{d}calca{{n}}', f'dsc{d}calcb{{n}}'],
                    R(1, 8), (0, 1, 2)) for d in (2, 3)],
    'skills': [L(['aurastat{n}', 'aurastatcalc{n}'], R(1, 7)), L(['passivestat{n}', 'passivecalc{n}'], R(1, 6)),
               L(['auraevent{n}', 'auraeventfunc{n}'], R(1, 4)), L(['reqskill{n}'], R(1, 4)),
               L(['sumskill{n}', 'sumsk{n}calc'], R(1, 6))],
    'gems': [L([k + 'Mod{n}Code', k + 'Mod{n}Param', k + 'Mod{n}Min', k + 'Mod{n}Max'], R(1, 4), (0, 1))
             for k in ('weapon', 'helm', 'shield')],
    'monprop': [L(['prop{n}' + d, 'chance{n}' + d, 'par{n}' + d, 'min{n}' + d, 'max{n}' + d], R(1, 7), (0, 2))
                for d in ('', ' (N)', ' (H)')],
    'charstats': [L(['item{n}', 'item{n}loc', 'item{n}count'], R(1, 11), (0, 1))],
    'properties': [A(['set{n}', 'val{n}', 'func{n}', 'stat{n}'], R(1, 8))],
    'itemtypes': [A(['Equiv{n}'], R(1, 3))],
    'misc': [L(['stat{n}', 'calc{n}'], R(1, 4))],
}


def groups_for(table, colnames):
    """Groups whose columns all exist (in at least one version) for this table."""
    out = []
    for slots, ident, kind in GROUPS.get(table, []):
        slots = [s for s in slots if all(c in colnames for c in s)]
        if slots:
            out.append((slots, ident, kind))
    return out
