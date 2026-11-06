# TC drop-rate boosts — port record (Stage 2, part 1)

Applied by `tools/tc_apply_boosts.py` onto S14-based `TreasureClassEx.txt`. 84 rows changed.
Method: the mod repo has no vanilla baseline (initial import `9ab233a` is already modded; the
"backup s10 /data" commit is the *modded* S10 tree), so the mod's edits were isolated by
diffing mod-S11 vs S14-vanilla row by row and classifying each difference as mod edit,
S12–S14 upstream change, or code-scheme difference. Cross-check via git: the S11 import
(`4e03dc8`) → final (`308bca9`) touched no TC rows, so all TC edits predate the repo.

## Ported (live now)

### Good TCs — 18 rows (mod pick structure adopted)
- `Act 1–5 (H) Good`: Chipped Gem removed; Flawed 20→27; Runes equiv 28→30; Map Tier 1 1→2;
  **+ Orbs:4, + Fate Drop:2** (this is what makes awakening vials / fate cards actually drop).
- `Act 1–5 (N) Good`: all weights doubled (mod's values), + Fate Drop:2, + Orbs:1.
- `Act 1–5 Good` (normal): mod's boosted weights (e.g. Jewelry 60→240/320/320/400/400),
  + Fate Drop:2, + Orbs:1.
- `Map Good t1/t2/t3`: Chipped removed; Flawed 20→28; Flawless 48→50; Runes 17 equiv 28→30;
  wss 4→6; map drop 8→5 (mod's rebalance); **+ Map Orbs Drop:8, + Fate Drop:5**.

### Runes — 21 rows (the "+500%" rune boost)
Mod's reduced cascade probabilities applied to S14's rows (S14 item codes `rXX` kept, so
runes keep dropping the way S14 drops them):

| TC | cascade prob S14→ported | TC | cascade prob S14→ported |
|---|---|---|---|
| Runes 3 | 5→4 | Runes 12(+equiv) | 1066→631 |
| Runes 3 unstack | 5→4 | Runes 13(+equiv) | 1519/1517→899 |
| Runes 5 | 12→10 | Runes 14(+equiv) | 2170→1286 |
| Runes 6 | 22→12 | Runes 15(+equiv) | 2941→1743 |
| Runes 7 | 45→27 | Runes 16(+equiv) | 3957→2344 |
| Runes 8 | 90→54 | Runes 17(+equiv) | 5170→3063 |
| Runes 9 | 180→107 | Runes 10 | 360→214 |
| Runes 11 | 720→427 | | |

Net effect per rune roll matches the mod: e.g. top rune ~1.7× more likely per roll,
compounding down the ladder ≈ the advertised +500% for high runes.
Runes 1/2/4 differed only in stacked-code usage (`rXXs`) — S14 versions kept, no rate change needed.

### Junk TCs — 15 rows
Potion/Misc/Junk-ref weights halved to mod's values (less potion/misc clutter).
S14's `Ammo(H)`/`Ammo(N)` pick kept untouched (S14 restructured ammo; mod's plain `Ammo:45`
and the `gld:17` gold-in-ammo quirk were NOT ported — they're an S11-era structure).

### BR Arena — 6 rows (quality scalars only)
Bodies N/NM/H: Unique 1000→570, Set 850→400, Rare 1400→850, Magic 800→450.
Chests N/NM/H: Unique 1600→930, Set 1000→500, Rare 1400→840, Magic 500→260.
Mod's pick-level changes here (its own rune ladder refs, misc table) skipped — S14 restructured
BR Arena sub-TCs upstream.

### Treasure Fallen — 3 rows
Sub-drop weights 1→4 (Gem/Rune/Craft[/Map]), gold weight up (2→15 on N/NM, 1→4 on H),
**+ Treasure Fallen Orbs:1, + Treasure Fallen Cards:1** per difficulty. S14's NoDrop kept.
NOT ported: mod's rune-tier targets (S14 upgraded these upstream, e.g. Rune H rolls Runes 17
in S14 vs mod's Runes 13 — taking the mod's would be a nerf) and mod's map relic codes
(S14 restructured: `irma/irra/rrra/urma` vs mod's `imra/rera/imma`).

### Quality scalars on utility TCs — 20 rows
Mod's more generous Unique/Set divisors on: Horadric ID/TP Book N/NM/H, Larzuk Puzzlebox H/NM,
Larzuk Puzzlepiece N/NM/H, Lillith Mirror N/NM/H, SkeletonKey N/NM/H, Vial of Lightsong N/NM/H.
(`Lillith Mirror` Unique 37500/25000→15000 etc.)

### Corrupted Zone — 1 row
Unique 200→150.

## Deliberately skipped

- **All boss/uber TC rows** (user decision): Andariel/Baal/Diablo/Duriel/Mephisto + quest
  variants, Blood Raven, Bloodwitch, Countess, Izual, Nihlathak, Summoner, Map Boss T1–4,
  UberAncients (×4), lucb/lucc/lucd, Demonic Cube H, ShadowOfMendeln, Rathma Jawbone ×3,
  Unique Map MapBoss/Monsters. Note this also excludes the mod's **key-drop 10× boost**
  (`pk1/pk2/pk3` prob ~26→261) and its `bet`/`fed`→`dcso` material swap. Ask if you want these.
- **Map Tier 1/2/3 pool rows**: S14 reworked the map roster upstream (new maps t3a/t3b/t37–39);
  the mod's pools are an outdated S11 snapshot.
- **Map Boss TC / Replica / Map Boss Uber Relic**: mod-only TCs, present but unreferenced
  (only the skipped Map Boss T1–3 rows pointed at them).
- **Miss TC ammo restructure** (mod `Ammo:45` vs S14 `Ammo(H):20`) — S14's quiver system wins.
- **Flawless Gem / Perfect Gem / BR Arena Runes/Gem rows**: differences are only stacked
  (`gXXs`/`rXXs`/`skls`/`skzs`) vs unstacked codes — no rate change; S14 code scheme kept.

## Verification

- Integrity check after edit: 1269 issues — identical to pre-edit baseline (no new references
  introduced; Orbs/Fate Drop/Map Orbs Drop/Treasure Fallen Orbs/Cards all resolve to appended
  mod TC rows; all referenced item codes exist in merged tables).
- Diff confined to `TreasureClassEx.txt` (84 rows), zero boss-material codes in the diff.
- Stale `TreasureClassEx.bin` removed from repo and install; game recompiles on next launch.
