# S14 Alliance merge

`data/` is Reawakening 11.0.1 (commit 308bca9) merged three-way onto PD2 S14 Alliance, with vanilla PD2 S11 as the common base:

- A change made only by Reawakening, or only by S14, is kept.
- A cell both sides changed is a conflict. Each conflict is listed in [report.md](report.md) along with how it was resolved.
- Strings are merged the same way; see [patchstring_report.md](patchstring_report.md).

## Rerunning

Each input directory holds `data/global/excel` and `data/local/LNG/ENG`.

```
python tools/merge3.py <s11> <ra11> <s14> <out> report.md
python tools/merge_tbl.py <s11>/data/local/LNG/ENG/patchstring.tbl <ra11>/... <s14>/... <out>/... patchstring_report.md
CHK_ROOT=<out>/data/global/excel python tools/check_integrity.py
```

`string.tbl` and `expansionstring.tbl` come from Reawakening. `data/global/items/*.dc6` come from Reawakening. `data/local/ui/eng/ExpansionCredits.txt` comes from S14. After a merge, regenerate the `.bin` files (see the README).

## Rules

- **Row placement.** S14 rows keep their row index, because the PD2 DLLs hardcode skill, stat and item ids. Rows Reawakening added are appended. There are two exceptions:
  - **CubeMain**, where order matters: added rows follow their Reawakening neighbour.
  - **TreasureClassEx**, the one table where a reference must point up: the game links a treasure class only to classes listed above it, so a class appended below its users drops nothing (v14.0.1 shipped this way, with no Vials, orbs or fate cards). `place_tcs()` puts Reawakening's classes above their users, following `TC_INSERT_BEFORE`, `TC_SLOTS` and `TC_TO_END` in `tools/resolutions.py`. For each class inserted near the top, one S14 class that only MonStats uses moves to the end. Rows from `Andarielq (N)` on therefore keep their S14 index. The build fails when any class references one listed below it.
- **Slot groups merge by content, not by column.** This covers item properties, skill description lines and treasure class items: two rows that list the same property in different slots still merge correctly. The groups are defined in `tools/slots.py`.
- **S14's global rescales are applied to Reawakening's values before merging:**
  - affix `frequency` ×10;
  - boss and uber HP, scaled by the S14/S11 ratio.
- **Conflicts nobody decided** follow `auto_rule` in `tools/merge3.py`:
  - both sides moved a number the same way: the larger change wins;
  - otherwise Reawakening wins;
  - comment columns take S14's value.
- **Decisions** are recorded in `tools/resolutions.py`:
  - **Loyalty.** S14's Loyalty (spear and bow) and Reawakening's Loyalty helm (Cham Um Jah, `Runeword77`) are both kept, each in its own row.
  - **PvP charms.** Reawakening had removed them. The rows stay so ids don't shift, with `spawnable` set to 0.
  - **Resist cap on new monsters.** Monsters new in S14 get Reawakening's cap: resists ≥100 drop to 95 on killable monsters. The cap skips Prime Evils, uncounted event monsters, town NPCs and the Bitter Depths sarcophagus.
  - **PvP modifier tooltips** use S14's text.
  - **Dev generate recipe** takes 50 Vials of Awakening.

## ItemStatCost

S14 fills the 511-row table, so all 37 Reawakening stats take over rows nothing in S14 uses (`ISC_SLOTS`):
- The `*_bytime` rows from 286 to 304 already belonged to Reawakening and keep the same ids.
- All other S14 stats keep their S14 ids.
- CubeMain's stat ops (16, 17, 18) name a stat by id in `param`. `remap_cube_stats()` follows each Reawakening stat to its new id (v14.0.2 shipped without it, so awakening recipes still tested `awakener` at 509).

BH.dll hardcodes three of these stats:

| Constant | Old | New |
|---|---|---|
| `STAT_AWAKENED` | 508 | 313 |
| `STAT_AWAKENER` | 509 | 314 |
| `STAT_SKILLONEQUIP_DISPLAY` | 193 | 287 |
