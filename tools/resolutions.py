"""Decisions merge3.py applies. Every entry was reviewed against the conflict report.

RESOLVE: (table file, row key, column) -> 'ours' | 'theirs' | literal value.
Row key '*' matches every row. Unlisted conflicts take Reawakening's value ('ours');
comment columns (*name) take S14's.
"""

AURA = "(100+stat('aura_effect_increase'.accr)) / 100"
JOUST = ("\"max(max(104 - ((lvl * 5) / 2), 13) - (stat('joustreduction'.accr) + "
         "stat('joustreduction_leorics'.accr) + stat('joustreduction_zeraes'.accr)), 0)\"")
COMBUSTION = "63 - (stat('combustion_cd_reduction'.accr) * 25)"

RESOLVE = {
    # Reawakening's aura-effect scaling applied to S14's new base values.
    ('Skills.txt', 'Cleansing', 'aurastatcalc1[curse_effectiveness]'): f'(10 + lvl / 2) * {AURA}',
    ('Skilldesc.txt', 'cleansing', 'desccalca1[2]'): f'(10 + lvl / 2) * {AURA}',
    # Reawakening's cooldown-reduction stat on S14's shorter base cooldown (75 -> 63 frames).
    ('Skills.txt', 'Combustion', 'delay'): COMBUSTION,
    ('Skilldesc.txt', 'combustion', 'desccalca1[12]'): COMBUSTION,
    # Reawakening's rework (13-frame floor, reductions after the floor, never below 0) on
    # S14's base (104) and S14's reduction stats (Leoric's, Zerae's).
    ('Skills.txt', 'Joust', 'delay'): JOUST,
    ('Skilldesc.txt', 'joust', 'dsc2calca1[12]'): JOUST,
    # S14 added pvp_disable to sentry caps; keep Reawakening's +max stats as well.
    ('Skills.txt', 'Wake of Fire Sentry', 'petmax'): "5 + stat('extra_wakeoffire'.accr) - stat('pvp_disable'.accr)",
    ('Skills.txt', 'Chain Lightning Sentry', 'petmax'): "5 + stat('extra_chainlightningsentry'.accr) - stat('pvp_disable'.accr)",
    ('Skills.txt', 'Inferno Sentry', 'petmax'): "5 + stat('extra_wakeofinferno'.accr) - stat('pvp_disable'.accr)",
    ('Skills.txt', 'Lightning Sentry', 'petmax'): "5 + stat('extra_lightningsentry'.accr) - stat('pvp_disable'.accr)",
    # S14 dropped the S11 synergy term (archer base damage went 15-20 -> 20-25);
    # keep only Reawakening's dexterity scaling.
    ('Skills.txt', 'Raise Skeleton Archer', 'DmgSymPerCalc'): "(stat('dexterity'.accr)/5)*par6",
    # S14 removed Raven's physical damage, so its physical synergy has nothing to scale.
    ('Skills.txt', 'Raven', 'DmgSymPerCalc'): 'theirs',
    # S14 points Lightning Fury's item effect at a new handler (187).
    ('Skills.txt', 'Lightning Fury', 'ItemEffect'): 'theirs',
    # S14 uses nolimit=6 on String of Ears (a new flag value); keep it.
    ('UniqueItems.txt', 'String of Ears', 'nolimit'): 'theirs',
    # Reawakening replaced these slots; S14's tweaks to the removed slot don't apply.
    ('Runes.txt', 'Runeword106', 'T1Code1:gethit-skill'): 'drop',
    ('UniqueItems.txt', 'Shatterblade', 'prop1:kill-skill'): 'drop',
}

# Vanilla stats Reawakening never used and S14 removed.
ISC_DROP = {'item_slash_damage', 'item_slash_damage_percent', 'item_crush_damage', 'item_crush_damage_percent'}

# Reawakening stat -> ItemStatCost id in the S14 layout. Every slot replaces a stat nothing
# in S14 uses: the *_bytime stats Reawakening already overwrote in S11 (286-304, which keep
# their v11 ids), and the never-implemented slash/crush/thrust absorbs, item_pierce_* and
# *_vs_monster stats. BH.dll hardcodes three of these (see docs).
ISC_SLOTS = {
    'extra_fireball': 260,
    'extra_wakeoffire': 261,
    'extra_wakeofinferno': 262,
    'extra_chainlightningsentry': 263,
    'extra_lightningsentry': 264,
    'item_physperenergy': 265,
    'item_gainmagicmastery': 266,
    'item_nonclassskill_display': 267,
    'extra_bonespear_teeth': 286,
    'item_skillonequip_display': 287,   # BH STAT_SKILLONEQUIP_DISPLAY (was 193)
    'extra_shadow_warrior': 288,
    'extra_shadow_master': 289,
    'es_absorb': 290,
    'aura_radius': 291,
    'thunderstorm_delay_reduction': 292,
    'aura_effect_increase': 293,
    'item_converteletomagic': 294,
    'combustion_cd_reduction': 295,
    'cannot_have_sockets': 296,
    'aura_delay_reduction': 297,
    'terror_influenced': 298,
    'hatred_influenced': 299,
    'prime_evil_influenced': 300,
    'awakened_skill_reduction': 301,
    'awakened_skill_duration': 302,
    'unmaking_num': 303,
    'jeweller_num': 304,
    'item_frwperenergy': 305,
    'item_magicmasteryperenergy': 306,
    'item_convertmasterytomagic': 307,
    'item_physextramagic': 308,
    'item_elepierceaddmastery': 309,
    'item_damagepercentmastery': 310,
    'extra_ice_lance': 311,
    'extra_poison_creeper': 312,
    'awakened': 313,                    # BH STAT_AWAKENED (was 508)
    'awakener': 314,                    # BH STAT_AWAKENER (was 509)
}
# patchstring.tbl keys changed on both sides. PvP modifier tooltips describe S14's PvP
# balance, which S14 maintains; Reawakening never changed PvP.
TBL_RESOLVE = {f'{d}{c}PVPModifiers': 'theirs'
               for d in ('Normal', 'Nightmare', 'Hell')
               for c in ('Amazon', 'Assassin', 'Barbarian', 'Druid', 'Necromancer', 'Paladin', 'Sorceress')}

# patchstring.tbl values set after merging: key -> value.
# pdreDesc: the version item's tooltip (lines show bottom-up).
TBL_EDITS = {'pdreDesc': 'ÿc8Alliance\nÿc;v14.0.0'}

# Rows taken whole from S14: (table, first-column key) -> 'theirs' drops Reawakening's
# version of the row; 'split' also appends Reawakening's version as a row of its own.
# Runes 'Loyalty Spear': Reawakening had its own helm runeword Runeword77 "Loyalty"
# (Cham Um Jah) in this row since its first version. Both runewords stay: S14's Loyalty
# (Pul Tir Dol, spear and bow) in its own rows, Reawakening's helm appended at the end.
ROW_THEIRS = {('Runes.txt', 'Loyalty Spear'): 'split'}

# Cells set after merging: (table, first-column key, column) -> value.
# PVP charms: Reawakening removed them; the rows stay so item ids don't shift, but never drop.
CELL_EDITS = {
    ('Misc.txt', 'Charm Small PVP', 'spawnable'): '0',
    ('Misc.txt', 'Charm Medium PVP', 'spawnable'): '0',
    ('Misc.txt', 'Charm Large PVP', 'spawnable'): '0',
}

# Reawakening caps every resist >= 100 at 95 on killable monsters that aren't Prime Evils,
# uncounted event monsters or in town. The same cap goes on monsters new in S14.
RESIST_CAP = 95
# Spawner objects Reawakening also leaves alone (like its bone walls and totems).
RESIST_CAP_EXEMPT = {'sarcophagusBitterDepths'}
