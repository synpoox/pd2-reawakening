# Reawakening — PD2 Season 14 port (Stage 1 + TC drop boosts done)

An AI-assisted port of [pd2-reawakening](https://github.com/synpoox/pd2-reawakening) (built for PD2 S11)
onto the PD2 Season 14 "Alliance" data. The game boots, characters enter the world, and the mod's
content (awakened items, replica/legacy items, fate cards, orbs, boosted rune/gem drops) is in place.

This document is written for the mod's original author (and anyone else who wants to polish it).

## How the port was done

The approach is a **data merge**, not a file swap: PD2 S14's data is the base (so all S12–S14
balance/content is preserved byte-for-byte), and Reawakening's additions are layered on top.

Sources:
- S14 vanilla data: extracted from `ProjectD2/Live/pd2data.mpq` (pristine S14 install)
- Mod S11 data: extracted from the installed modded `pd2data.mpq` (v11.0.1)

Merge rules (tools in `tools/`):
1. **S14 rows win all collisions** — any row present in both datasets stays S14-verbatim.
2. **Mod-only rows are appended**, with values remapped by *name* where they reference skills
   (skill IDs shifted between S11 and S14; 36 params remapped, 0 misses).
3. **ItemStatCost** (the table you warned about): both files sit at the 511-row cap. The 41 mod-only
   stats were placed into 41 *dead/unreferenced* S14 rows (full mapping in `docs/itemstatcost_mapping.md`).
   Every live S14 row keeps its exact position, so S14 items/characters are unaffected. Mod stat IDs
   changed as little as possible — but they DID change, so **old mod items are not compatible**
   (fresh characters required; S12+ save-format changes broke old saves anyway).
4. **patchstring.tbl**: format fully reverse-engineered (ELF-hash linear probing, NumLoops =
   max probe distance + 1, CRC16-CCITT over the string pool). S14 entries keep their original idx
   values; 453 mod-only keys appended; 83 value conflicts deferred (S14 wins, see
   `docs/patchstring_merge.md` — includes the mastery rename and awakened-summon strings, which must
   be reviewed together with their data rows).
5. 26 mod-only .dc6 item graphics copied verbatim.

## Bugs found & fixed (this is the hard-won knowledge)

1. **Experience.txt is positional.** The MaxLvl row must be the FIRST data row; a name-keyed merge
   put it last and the engine parsed level 0's row as the cap → crash on game creation.
   Fix: mod's file verbatim (MaxLvl=131, flat 100–131 curve).
2. **CRLF required.** D2's txt parser chokes on LF-only files. (This is why editing tables in a
   plain text editor bricks the game — editors also love stripping trailing tabs. All merging here
   is byte-exact programmatic.)
3. **Skills.txt / Missiles.txt: `Id` column must equal row index.** Appended mod rows kept their
   S11 Ids, colliding with S14 rows (e.g. Id 487: `NihlathakMapDeath` vs `Sentry Lightning Fury`).
   The engine builds Id-indexed arrays → duplicate Ids crash table compilation on game creation.
   Fixed: Id = row index for appended rows.
4. **Skilldesc.txt rows must be padded to the header width** (118 cols).

## Deliberately NOT ported yet (Stage 2)

See `docs/stage2_deferred.md` for the full list with recovery methods. Headlines:

- **Drop-rate boosts**: ✅ DONE — see `docs/tc_boosts.md`. Runes cascade probs, Good-TC
  gem/orb/fate-card injection, junk halving, Treasure Fallen, BR Arena + utility quality
  scalars are all ported (84 TC rows). Skipped per scope decision: boss/uber TC rows
  (including the mod's 10× key-drop boost and `bet`/`fed`→`dcso` material swap) and the
  outdated S11 map-tier pools — all recoverable if wanted.
- **Mastery rework**: your mod *replaced* skills 128/134 (One/Two-Hand Mastery → General Mastery /
  Polearm & Spear Mastery). The name-keyed merge treated the renames as *new* skills (now 614/615);
  S14's originals are still at 128/134. To restore the rework, replace those rows deliberately.
- **Density variants** (1x/2x/5x/10x): S14 base density currently; variants should be regenerated
  from S14 values using the per-row multipliers in your variant mpqs.
- 332 CubeMain label collisions kept as S14 (`docs/cubemain_conflicts.md`).

## Current install layout

```
C:\Diablo II - Lord of Destruction\
├─ reawakening-s14\        ← THIS REPO (merged data tree + tools + docs)
├─ ProjectD2\
│  ├─ data\                ← merged data on disk (the game reads this)
│  ├─ PlugY.ini            ← Param=-3dfx -plugy -direct -txt
│  ├─ BH.dll               ← your BH v11.0.1 (under test on the S14 client)
│  ├─ pd2data.mpq          ← vanilla S14 (fallback only; disk data wins)
│  └─ *.backup / *.before-s14mod-* ← originals
└─ scout\                  ← tooling workspace (mpq extractor, both extracted datasets,
                             clones of pd2-reawakening, BH source, ra-launcher)
```

Launch with `ProjectD2\PlugY.exe` directly. **Do not** click Play in the ra-launcher (it
re-downloads the S11 files per its manifest), and don't let the official PD2Launcher "repair".

### Editing workflow

1. Edit txt files in `reawakening-s14\data\` (programmatically or with a D2-safe editor only).
2. Copy `data\` over `ProjectD2\data\`, delete `ProjectD2\data\global\excel\*.bin`.
3. Launch once — the game recompiles all bins from txt. A crash during this writes bins up to the
   failing table, which pinpoints the culprit.
4. Commit in git after every working change (`.gitattributes` forces byte-exact storage;
   never let git's autocrlf touch these files).

## Known open items

- **BH.dll** is your S11 build running on the S14 client. `D2Game.dll` is byte-identical between
  S11 and S14, so hooks have a good chance; if anything's broken, rebuild from your BH source
  (his commits: awakened asterisk indicators, awakened proc tooltips, CARD filter keyword).
- **MPQ packaging**: a minimal MPQ writer was built (`tools/mpq_write.py`, read-back verified)
  but Storm.dll rejects the result ("file data is corrupt"). Currently unnecessary (txt mode),
  but packaging would restore the original distribution format + faster boot.
- GitHub mirror of this repo is pending (local-only for now).

## For the author

Everything above is reproducible from the scripts in `tools/` and the docs in `docs/`.
The fastest way for you to polish: review `docs/stage2_deferred.md` (your intent vs S14's
evolution, item by item), and decide the mastery-rework question. The scaffolding (merge,
integrity check, integrity-clean tbl writer) will re-apply cleanly on top of any decisions you make.
