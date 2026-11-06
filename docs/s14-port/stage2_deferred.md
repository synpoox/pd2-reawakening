# Stage 2 deferred work

Items deliberately NOT ported in Stage 1 (bootability first). Each entry lists what, why, and the recovery method.

## 1. TreasureClassEx drop-rate boosts (HIGH priority — headline feature)

The mod's "Drop Rate Increases" (rune drops +500%, across-the-board boosts) live in shared TC rows
where Stage 1 kept S14 values. Classification from `tools/tc_classify.py` (mod-S11 vs S14-vanilla,
shared rows):

- `only_prob`: 29 rows — pure probability boosts (e.g. `Act 1 Miss A` Prob6: mod 45 vs S14 20)
- `both` (item+prob): 113 rows — incl. map-tier scrambles, Good-TC gem/rune upgrades, boss TC
  swaps (`bet`->`dcso` on Diablo(H), `fed`->`dcso` on Baal(H))
- `other_cols_only`: 46 rows — quality-ratio overrides (e.g. `Demonic Cube H` Unique: mod 5000 vs S14 1000)

**Why deferred:** the mod's numbers were tuned against vanilla S11; S14 rebalanced the same rows.
Applying mod deltas blindly would undo S14 changes; taking S14 blindly loses the boosts.

**Recovery method (git archaeology):** the mod repo (`scout/pd2-reawakening`) separates season
migrations (e.g. `4e03dc8 v11.0.0 data`) from hand edits (e.g. `0896f51 fate card changes`).
Reconstruct vanilla S11 TC = mod-S11 TC minus post-import hand edits, then compute per-row
multiplicative factors and apply them to S14 rows. Check `git log --follow -- data/global/excel/TreasureClassEx.txt`.

**CAUTION for `both` rows:** S14 boss drops (`bet`, `fed`, ...) may be required for S14 content
(e.g. Alliance/uber fights). The mod replaced some with its card pieces (`dcso`). Review row by row.

Already ported in Stage 1: 105 stacked-code swaps (`rXX`->`rXXs`, `gXX`->`gXXs`, `skl`->`skls`,
`skz`->`skzs`) across 44 rows — required for the stackable-rune/gem drop chain (mod's unstack
cube recipes + BH `CARD` keyword depend on these).

## 2. ItemRatio — PORTED in Stage 1

Mod's 6 rows verbatim (uniform ~0.77x divisors = better unique/rare/set odds). Structure identical
to S14 (v0 legacy + v1 rows).

## 3. CharStats — PARTIALLY ported

Ported: starting items (`item3..6` + counts) — Horadric Cube + TP/ID tomes at level 1.
NOT ported: mod's LifePerLevel/ManaPerLevel/ManaPerMagic values — ambiguous whether hand tweak or
stale pre-S12 values; S14 balance kept. Revisit if the mod feels wrong; values in
`scout/extracted/s11_ra/data/global/excel/CharStats.txt`.

## 4. Levels.txt density (MonDen) and MonLvl3Ex

The mod's installed mpq was a density variant (e.g. `Act 4 - Diablo 1` MonDen(H): mod 1600 vs S14 800).
Stage 1 keeps S14 density. The mod's density-variant feature (1x/2x/3x/5x/10x) should be
REGENERATED from S14 values using the per-row multipliers extracted from the mod's variant mpqs
(they live wherever the launcher stored them; check ra-launcher releases).
Also: mod raised some map levels (Zhar Kurast MonLvl3Ex 89 vs S14 87) — review with map content.

## 5. patchstring.tbl — 83 deferred value conflicts

See `docs/patchstring_merge.md`. S14 values kept for consistency with S14 data rows.
Includes the mod's mastery rename (General Mastery / Polearm And Spear Mastery) and awakened-summon
strings (`ExtraGolem` etc.) — review together with the corresponding Skills/ItemStatCost rows:
the mod's mastery REWORK rows (Skills.txt 128/134) were also not ported (S14 rows kept).

## 6. CubeMain label collisions — 332 rows

S14 versions kept. See `docs/cubemain_conflicts.md`.

## 7. Experience.txt MaxLvl / level 100+ rows

Mod adds levels 100-132 with its own exp curve; merged file has both S14 rows (100-131) and mod
rows appended. Verify in-game that leveling past 99 behaves (CharStats/Experience interplay).
