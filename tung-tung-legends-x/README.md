# Tung Tung TungLegendss X

A native, offline clicker simulator for **Chromebook Linux (Intel / AMD, x86-64)**. The game opens in its own SDL desktop window. Python, a browser, a web server and an account are not needed to play the packaged version.

## Install on Chromebook Linux

1. Download `TungTungLegendsX-Chromebook-Linux.deb`.
2. In the Chromebook Files app, move it into **Linux files**.
3. Open **Terminal**, choose your Linux environment, and run:

```bash
sudo apt install ./TungTungLegendsX-Chromebook-Linux.deb
```

4. Open **Tung Tung TungLegendss X** from the Chromebook launcher / Linux apps. Alternatively, run:

```bash
tung-tung-legends-x
```

Linux must already be enabled on the Chromebook. Recent ChromeOS releases deprecated the graphical `.deb` installer; the Terminal method avoids relying on that interface. Official setup documentation: https://developers.google.com/chromeos/app-development/develop/setup and https://developers.google.com/chromeos/app-development/develop/news .

The compiled package is for Intel/AMD **x86-64** Linux with glibc 2.28 or newer (including Debian 11 and 12). It is not an ARM binary. For an ARM Linux Chromebook, use the editable Python source and install `pygame-ce` for that processor using the source instructions below. ARM builds have not been tested here.

## Portable version

If you prefer not to install a Debian package, extract `TungTungLegendsX-Linux-Portable.zip` into **Linux files**, open its `TungTungLegendsX-Linux` folder in Terminal, and run:

```bash
bash PLAY.sh
```

This uses the included Linux executable. It never opens a browser. The portable package includes the same game, editable source, tests, license notices and a preview image.

## Play

Click the wooden Tung character, click **KNOCK**, or hold **Space**. Tungs are both the enemies you farm and the currency you earn. Five regular kills clear a stage; every tenth stage has one timed boss. Buy heroes for continuous idle damage, or buy click levels to strengthen your own knocks. Every 25 levels doubles that hero's output.

You start with 65 gems. A Bamboo Egg costs 30. Use **Pets** to hatch your first team and **Quests** to claim more gems. Equipped pet multipliers multiply together, and hatching automatically equips your strongest team. Fusion consumes three identical pets of the same species, stars and shiny status to create one stronger pet. Unwanted pets can be recycled into crafting shards with confirmation.

If a boss escapes, the game returns to the previous stage and stays there. Buy upgrades and click **RETRY STAGE** in the ability tray when ready. **AUTO** advances as you clear stages; **STAY** keeps farming the current stage. Arrows travel among stages unlocked in the current run.

## Content and progression

- **12 themed realms / 1,200 campaign stages**, followed by continuing endless stages.
- **16 heroes**, 3,000 levels each, bulk purchases, milestones and passive damage.
- **36 pet species / 6 eggs / 6 rarities** from Common to Mythic.
- Multiplicative pet teams, shiny variants, eight fusion star ranks and up to five equipped pets.
- Visible base hatch odds: 58% Common, 24% Uncommon, 12% Rare, 5% Epic, 0.9% Legendary, 0.1% Mythic. Lucky Shell research improves the higher rarity weights.
- Every egg's hatch count guarantees at least Epic every 10 hatches, at least Legendary every 40, and Mythic every 120. Shiny chance is 2.5% independently.
- **11 items** across weapon, charm, engine and relic slots. Item ranks go to 50.
- **7 active abilities**: Tung Slam, Frenzy, Thunder, Rift Cut, Gold Rush, Echo and Overdrive. Equipment unlocks all abilities except the starting Slam.
- **Rebirth at stage 50** for souls, an earned base multiplier and ten soul research tracks. Spending souls does not remove the earned base multiplier.
- **Astral ascension at stage 300** for a second prestige layer. Each astral doubles damage.
- **22 permanent achievements** and an endlessly refreshing, gradually harder contract board.
- Autosaving, checksum validation, backup recovery, offline farming, fullscreen, optional sound/music, reduced motion and 30 FPS battery mode.
- No advertising, purchases, online services or account requirements.

This is a 2D single-player idle/clicker game. Long progression comes from repeated prestige runs, collecting and improving pets, completing the campaign and pushing endless stages. Exact completion time depends strongly on the player's upgrade choices; no fixed playtime is promised.

## Prestige: what resets

| System | Rebirth | Astral ascension |
| --- | --- | --- |
| Coins, hero levels, click levels, current run stages | Reset | Reset |
| Equipped abilities' cooldowns and temporary buffs | Reset | Reset |
| Souls, earned soul base multiplier, soul research | Keep, gain more souls | Reset |
| Astrals | Keep | Keep, gain more astrals |
| Pets, fusion stars, shinies | Keep | Keep |
| Equipment ownership and ranks | Keep | Keep |
| Gems and crafting shards | Keep | Keep |
| Achievements, contracts and lifetime records | Keep | Keep |

## Controls

| Key | Action |
| --- | --- |
| Space | Hold to farm, seven manual knocks per second |
| 1-5 | Cast the corresponding equipped ability |
| H / P / F / R / Q / M / S | Heroes / Pets / Forge / Rebirth / Quests / Realms / Settings |
| A | Toggle automatic stage advancement |
| Mouse wheel | Scroll the open right-hand panel |
| F11 | Toggle fullscreen |
| Escape | Close a dialog or leave fullscreen |

## Saves and offline farming

Saves live in `~/.local/share/tung-tung-legends-x/`, or `$XDG_DATA_HOME/tung-tung-legends-x/` when that standard variable is set. They do not depend on the install folder. Autosaving happens every 30 seconds, on loss of window focus, after a confirmed prestige, and on normal exit. `save.backup.json` preserves the previous valid save; corrupt primary saves are archived before replacement.

Offline farming uses 25% of the current idle output, capped at eight hours and one million kills per return. Dream Farmer research raises efficiency up to 75%. Offline income never advances stages, defeats bosses, earns boss gems or activates temporary buffs. It deliberately uses a safe normal stage when you close the app during a boss.

**Reset all progress** requires confirmation and preserves the old state as `reset-recovery.json`. Restore that file as `save.json` while the game is closed if you reset by mistake.

## Editable source

Python 3.10+ and pygame-ce are required only for editing/running source. In the `source` folder (or the GitHub game folder), run:

```bash
sudo apt install python3-venv
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python game.py
```

The source can run on additional Linux processor architectures when compatible pygame-ce wheels are available. The packaged executable remains x86-64.

Run the gameplay and actual SDL input/render checks:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Build the native Linux application and download packages on x86-64 Debian 12 Linux (or another build environment whose Python/runtime satisfies the compatibility audit):

```bash
.venv/bin/python -m pip install -r requirements-build.txt
.venv/bin/python tools/build_linux.py
```

The build script creates a `.deb` and a portable ZIP under `release/`. It excludes build-machine C++ runtime copies so the application uses the Chromebook's compatible system runtime. Third-party components remain dynamically linked.

## Validation and limits

The release was checked with 43 passing automated gameplay/SDL interface tests, all seven panels at the top and bottom of their scroll ranges, fresh and advanced rendering previews, packaged-executable smoke tests, a package extraction check, and automated campaign progression. The ELF compatibility audit checks every bundled native library; actual gameplay on the user's Chromebook remains unverified until installed there. Audio output and ChromeOS window integration cannot be confirmed from a headless test environment.

An actual Chromebook, ARM device and touchscreen were not available during the build. The keyboard/mouse x86-64 Linux build is the tested target. The game uses finite floating-point currency up to `1e250`; its first 1,200 stages are well below that limit.

Original game code is MIT licensed. Fonts and bundled runtimes retain their own licenses; see `LICENSE`, `THIRD-PARTY-NOTICES.md`, and `licenses/` in the packaged application.
