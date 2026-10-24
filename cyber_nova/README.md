# 🚀 CYBER NOVA: ODYSSEY

> **A Neon Synthwave Rogue-lite Space Arcade Game coded 100% in pure Python.**
> Zero external third-party dependencies required. Runs instantly on any modern Python installation!

---

## 🌟 Highlights

- **Pure Python standard library implementation**: Powered by `tkinter`, `wave`, `struct`, `math`, `random`, and asynchronous Windows sound audio (`winsound`). Zero `pip install` required!
- **Smooth 60 FPS Vector Graphics**: High-octane arcade action with dynamic starfield 3D parallax, glowing neon polygon meshes, spark particle physics, dash ghost after-images, and expanding shockwaves.
- **5-Slot Save File Architecture**:
  - **Slot 1 [AUTO-SAVE]:** Automatically updates at every wave completion and upon quitting.
  - **Slots 2–5 [MANUAL SAVES 1–4]:** 4 dedicated manual save slots accessible from the in-flight pause menu.
  - **Unified "SAVE FILES" Browser:** Main Menu features a single `[ 💾 SAVE FILES (5 SLOTS) ]` terminal where you can inspect, load, or delete any of the 5 slots with complete telemetry data (Wave, Score, Scrap, Difficulty, and Timestamp).
- **Interactive Pause & Tactical Terminal (`P` / `ESC`)**:
  - Unfreezable, reliable pause state with both keyboard and clickable mouse controls.
  - Quick **Resume**, **Save to Manual Slot (2–5)**, **Difficulty Switching**, **Audio SFX Toggle**, and **Auto-Save & Quit to Menu**.
- **Deep Rogue-lite Tech Bay (`[B]` Key)**:
  - Spend collected **Scrap Cores** between or during combat waves.
  - Upgrade Hull Plating, Plasma Shields & auto-recharge rate, Thruster Speed, and Magnet Range.
  - Unlock deadly prototype weapons: **Scatter Flak**, **Homing Micro-Missiles**, and **Singularity Vortex**.
- **Tactical Flight Abilities**:
  - **Quantum Blink Dash (`Right Click` / `Shift` / `E`)**: Phase through bullet barrages with invulnerability frames.
  - **EMP Super Shockwave (`Q` / `F`)**: Annihilates all incoming hostile projectiles, deals area damage, and electro-stuns every enemy on screen.
- **Diverse Enemy Armada & Epic Boss Encounters**:
  - **Drone Kamikaze**: Relentless swarming chasers with high ramming damage.
  - **Viper Scout**: Strafing interceptors that circle and fire plasma bolts.
  - **Cruiser Battleship**: Armored juggernauts firing 3-way spread salvos.
  - **Stealth Phantom**: Cloaking ambush craft that fade into shadows and flank.
  - **Dreadnought Leviathan (Boss Waves)**: Flagship encounter featuring rotating orbital shield drones, multi-directional flower spiral bullet patterns, and a frantic Phase 2 Enrage protocol!
- **Built-In Procedural Sound Synthesizer**: Generates authentic 16-bit retro arcade `.wav` audio directly in memory and disk on startup.
- **Persistent High Scores & Statistics**: Run history and all-time records saved locally to JSON.

---

## 🎮 Flight Controls

| Action | Control |
|---|---|
| **Thrusters & Flight** | `W`, `A`, `S`, `D` or `Arrow Keys` |
| **Aim & Cannon Fire** | `Mouse Aim` + `Left Click` (or `Spacebar`) |
| **Quantum Blink Dash** | `Right Click` / `Left Shift` / `E` |
| **EMP Shockwave Super** | `Q` / `F` |
| **Switch Weapons** | `1`, `2`, `3`, `4`, `5` or `Mouse Scroll Wheel` |
| **Tech Bay Upgrades** | `B` |
| **Pause / Resume** | `P` or `ESC` |
| **Toggle Audio SFX** | `M` |

---

## 🛠️ Quick Launch

You have three convenient ways to launch:

### 1. 🚀 Direct Executable (No Python Required!)
Double-click:
```
CyberNova.exe
```
*(Located right inside the project root folder!)*

---

### 2. 🐍 Single-File Standalone Python Script
Run the all-in-one standalone Python script:
```powershell
py cyber_nova_standalone.py
```
*(This single file contains the complete engine, audio synthesizer, graphics, and gameplay in one file that can be distributed anywhere!)*

---

### 3. 📦 Modular Launcher
Double-click **`run.bat`** or run:
```powershell
py main.py
```

---

## 📂 Architecture Overview

```text
cyber_nova/
│
├── main.py            # Application entrypoint & high-DPI window setup
├── config.py          # Screen resolution, colors, stat balances, constants
├── game.py            # Master state machine, 60 FPS tick, collision resolution
├── player.py          # Inertial physics, shields, dash, and firing mechanics
├── weapons.py         # Pulse, Twin, Flak, Homing Missiles, Singularity projectile classes
├── enemies.py         # Drone, Viper, Cruiser, Phantom AI state routines
├── boss.py            # Dreadnought Leviathan boss & orbital shield drones
├── particles.py       # Starfield parallax, sparks, shockwaves, floating combat text
├── pickups.py         # Scrap Cores, Nanite repair, Shield recharges, Overclock powerups
├── upgrades.py        # Rogue-lite Tech Bay progression and store inventory
├── hud.py             # Cyberpunk telemetry gauges, combo bar, weapon dock
├── sound_engine.py    # Math-synthesized 16-bit WAV generator and async player
├── save_manager.py    # High score and stat persistence (JSON)
├── sounds/            # Generated procedural WAV audio assets
└── run.bat            # 1-click launcher script
```

---

## 🏆 Scoring & Strategy Tips

1. **Keep the Combo Alive**: Rapid successive kills multiply your score bonus up to **5x**!
2. **Prioritize Shield Nodes on the Boss**: The Dreadnought Leviathan has a 75% defense matrix active until all 3 orbiting shield drones are destroyed.
3. **Save Your EMP for Bullet Hell Waves**: When caught in a tight corner with a swarm of bullets, tap `Q` to instantly vaporize all hostile projectiles.
4. **Upgrade Early**: Open the Tech Bay (`B`) as soon as you collect 40-50 scrap to bolster your shields and unlock additional weapon slots.
