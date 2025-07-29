# PD2 SP Reawakening

Originally I just wanted to add some items to the game from 1.08, but after lurking in r/projectdiablo2 and the pd2’s #feedback channel I decided to implement a bunch of things that I either agreed with or just straight up thought would be fun.

Comments and feedback would be very appreciated, join the [Discord](https://discord.gg/rBCNMWaCNt) and share your thoughts!

Forked from the original sp mod [PD2 SP Plus](https://github.com/Lukaszpg/PD2-Single-Player-Plus-mod)

**[Discord](https://discord.gg/rBCNMWaCNt) | [Wiki](https://pd2reawakening.com/wiki/) | [Latest Patch Notes (v1.3.0)](https://docs.google.com/document/d/e/2PACX-1vRDu2Gy_l7OoS6e9lLMObaClzkdzAKwRE4AcmBfJ4X_PWjI8_5AeLVhZoQVeS_bwQG6SGnoWiRaAS-4/pub)**

## New Features

- **Awakening**: A new system similar to corruption. Equipment and unique charms can be awakened when cubed with a Vial of Awakening, awakening it with a new property.
- **Fate Cards:** Stackable uncommon drops, that upon collecting a certain amount, can be cubed together in exchange for a reward. Similar to Path of Exile’s [divination cards](https://pathofexile.fandom.com/wiki/Divination_card).
- **Legacy Items**: Obtained through a rare drop Relic of the Nephalem, these legacy items are extremely powerful items from Diablo 2 LoD patch 1.08.
- **Replica Items**: Reproductions of existing items that come with a twist.
- **New Orbs**:
  - _Ancient Orb_: Transforms Rare item to Unique (excluding charms)
  - _Regal Orb_: Transforms Rare item to Set
  - _Divine Orb_: Rerolls unique item, limited to: equipment, jewelry, grand charms
  - _Orb of Unmaking_: Allows an item to be Awakened once more, keeping existing properties intact.
  - _Tainted Jeweller's Orb_: Unpredictably unsockets an item, either keeping or destroying contents in the process.
  - _Coin_: Gold sink purchasable from Akara
- **Item Changes**: Introducing new uniques, new runewords, and updating old ones to bring them back into play
- **New Cube Recipes**: +2 class skill Circlet crafting, rune downgrading, and more.
- **Drop Rate Increases**:
  - Rune drops increased by 500%
  - Drop rates increased across the board, see TreasureClassEx.txt for specifics or see [this](https://docs.google.com/spreadsheets/d/e/2PACX-1vSmG2BYE-c6W7l0ha8OcyEQROgDSKFtR99mWHuT9XM6OXW_f4ym87x-d5GrhlO37msQqxt2IJj_XRbF/pubhtml) for a short comparison
- **Crafting League Option**:
  - Uniques, sets, and runewords are disabled (All unique charms are exceptions)
  - Mythic orbs, Divine orbs, Regal orbs, and certain Fate Cards no longer drop
  - Uber materials such as: Voidstone, Vision of Terror, Pandemonium Talisman are purchasable from Anya
  - Easily switch between Standard and Crafting modes through the PD2 Reawakening Launcher

![reptyrael](https://github.com/user-attachments/assets/846b48f1-51d7-424b-8893-f2286db8ecb2)

## Installation

If you've played PlugY or any other PD2 single player mod, your current characters/stash will likely be incompatible.

#### With Launcher (auto-updates Reawakening)

1. Create a copy of your PD2 installation in a new directory.
1. Install [PD2-PlugY](https://github.com/synpoox/PD2-PlugY)
1. Download and Install the [Latest Release](https://github.com/synpoox/pd2-ra-launcher/releases/latest) of [PD2 RA Launcher](https://github.com/synpoox/pd2-ra-launcher)
1. Run `pd2-ra-launcher.exe`
1. Set your `Project Diablo II Installation Directory` in the Settings by clicking the cog-wheel in the top right.
1. Click `Play`.
1. Go to Akara and look for an item with Alkor's quest potion. If it's there, then the mod was installed successfully.

#### Manual Install (No auto-updates)

1. Create a copy of your PD2 installation in a new directory.
1. Install [PD2-PlugY](https://github.com/synpoox/PD2-PlugY)
1. Go to [Releases](https://github.com/synpoox/pd2-reawakening/releases) and download the latest `pd2data.mpq` and `BH.dll`
1. Copy and paste `pd2data.mpq` and `BH.dll` into your new PD2-PlugY install, overwriting any old files.
1. Launch the game with `Plugy.exe`
1. Go to Akara and look for an item with Alkor's quest potion. If it's there, then the mod was installed successfully.

## Changing Save Folder Path

Following the above instructions will point your new PD2 Reawakening install your old PD2 save folders, which can cause errors with incomptable characters/stashes. To change your save folder path:

#### With Launcher
1. Click the `Settings` cog-wheel in the top right
1. In `Preferences`, under Save Folder Directory, click `Change directory`
1. Select your desired Save directory

![alt text](/images/H8wsF65.png)

#### Without Launcher

1. Open `ProjectDiablo.json` in your new `...\PD2-Reawakening\ProjectD2` folder
1. Look for `"save_path"` and edit it to your chosen directory:

```JSON
"other": {
  "lng_file": "",
  "installpath": "C:\\Program Files (x86)\\PD2-Reawakening\\",
  "save_path": "C:\\Program Files (x86)\\PD2-Reawakening\\Save\\"
}
```
**Note that double backslashes are required**

## Toggling Between Standard and Crafting

### [!] Crafting league will no longer be supported after game patch 1.3.0. It is currently unsupported in the new 2.0.0 launcher.

1. Click the `Settings` button in the top left
1. Toggle the checkbox to enable/disable Crafting League
1. Press `Save`

### **WARNING: Enabling Crafting league and logging into a character can sometimes cause runewords to be deleted from that character and your stash**

_Always make backups of your saves_

## Adding new orbs/cards to your filter

This contains the new misc item types (fate cards, new orbs, relics), stylized for Kryszard's filter.

1. In-game, set a hotkey for `Reload Loot Filter` and press it
1. Find and open the file that gets displayed in game
1. Paste the following somewhere near the top
```
//PD2 Single Player Reawakening
ItemDisplay[awst OR mfo OR exo OR dvo OR rgo OR cho OR tjo OR dvia]: %BORDER-0A%%DOT-62%%GREEN%*%PURPLE%*%RED%*       %NAME%       %RED%*%PURPLE%*%GREEN%*
//all cards
ItemDisplay[CARD]: %BORDER-0A%%DOT-62%*%PURPLE%      %NAME%          
//relics, orb of unmaking, prime evil embers
ItemDisplay[rotf OR rotv OR rofp OR oou OR teo OR heo OR deo]: %BORDER-68%%ORANGE%pick %PURPLE%*%RED%*%YELLOW%*%GREEN%*     %NAME%     %GREEN%*%YELLOW%*%RED%*%PURPLE%* %ORANGE%up
```
