# Build log

## 2026-11-05 — Stage 1 build installed

- `ProjectD2/pd2data.mpq` = merged S14+mod build (sha256 614e05d9..., 212 files incl. listfile,
  built by `tools/mpq_write.py` from this repo's data tree; 211/211 read-back verified)
- `ProjectD2/BH.dll` = mod's BH from pd2-reawakening repo v11.0.1 (sha256 ca17db07...)
  NOTE: built against S11 client DLLs. D2Game.dll is byte-identical S11<->S14; if BH
  features break or crash, fall back to S14 BH: `cp Live/BH.dll BH.dll` (sha256 4173b0c2...)
- PlugY.ini restored to normal mpq mode (Param=-3dfx -plugy)
- Loose data dir removed from ProjectD2 (data.removed-20261105-202331)
- Backups in ProjectD2: pd2data.mpq.reawakening-s11-backup (original S11 mod),
  pd2data.mpq.before-s14mod-20261105-202331 (S14 vanilla), BH.dll.before-s14mod-* (S14 vanilla),
  PlugY.ini.backup

### Crash fixes that got us here (in commit order)
1. Experience.txt: MaxLvl row must be first (table is positional)
2. TreasureClassEx/CharStats/ItemRatio: LF -> CRLF (parser requires CRLF)
3. Skills/Missiles: appended mod rows had duplicate Id values (Id must equal row index)
4. Skilldesc: 26 mod rows padded to 118-col header

### Not yet active
- ~~Mod's drop-rate boosts in shared TC rows~~ -> DONE (see below)
- Mastery rework (mod replaced skills 128/134; S14 versions kept, mod's appended as 614/615)
- Density variants (1x/2x/5x/10x mpqs)

## 2026-11-05 (later) — mpq install REVERTED; running in -direct -txt mode

The hand-built mpq was rejected by the game ("file data is corrupt" on load) - Storm.dll's
reader is stricter than our writer. User opted to stay in txt mode; mpq writer shelved
(scout/pd2data_new.mpq kept for reference, tools/mpq_write.py).

Current working install:
- ProjectD2/pd2data.mpq = vanilla S14 (fallback only; disk data takes precedence)
- ProjectD2/data/ = merged data tree from this repo (txt + tbl + dc6 + compiled bins)
- ProjectD2/PlugY.ini: Param=-3dfx -plugy -direct -txt
- ProjectD2/BH.dll = modded BH v11.0.1 (UNDER TEST - if boot crashes, `cp Live/BH.dll BH.dll`)

## 2026-11-05 (evening) — TC drop-rate boosts ported (84 rows)

- Mod's TC edits isolated by diffing mod-S11 vs S14-vanilla row by row (no vanilla baseline
  exists in the mod repo: initial import is already modded; "backup s10 /data" is the modded
  S10 tree; S11 import -> final touched no TC rows).
- Ported: Good TCs (chipped gems removed in Hell, Orbs + Fate Drop injected), Runes cascade
  probs (S14 codes kept), Junk halving (S14 ammo structure kept), Treasure Fallen boosts,
  BR Arena + utility quality scalars, Corrupted Zone.
- Skipped (documented in docs/tc_boosts.md): all boss/uber TC rows incl. 10x key-drop boost
  and bet/fed->dcso swap; S11 map-tier pools (S14 reworked the roster); ammo restructure.
- tools/tc_apply_boosts.py is the applicator; tc_diff_report.py / tc_mod_edits.py are the analysis.
- Integrity: 1269 issues, identical to pre-edit baseline. Only TreasureClassEx.txt changed.
- Deployed to ProjectD2/data; all bins deleted for recompile on next launch.
  TreasureClassEx.bin removed from repo (stale; game regenerates).
