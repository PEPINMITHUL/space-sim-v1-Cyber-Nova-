"""
Global configurations, color palettes, and settings for CYBER NOVA: ODYSSEY.
"""

import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
SOUNDS_DIR = BASE_DIR / "sounds"
SAVE_FILE = BASE_DIR / "cyber_nova_save.json"

# Window & Display Settings
SCREEN_WIDTH = 1080
SCREEN_HEIGHT = 720
TARGET_FPS = 60
FRAME_DELAY_MS = int(1000 / TARGET_FPS)

# Neon Synthwave Color Palette
COLOR_BG = "#060713"
COLOR_BG_DARK = "#03040a"
COLOR_GRID = "#0f132a"

COLOR_CYAN = "#00f0ff"
COLOR_MAGENTA = "#ff007f"
COLOR_YELLOW = "#ffe600"
COLOR_GREEN = "#00ff66"
COLOR_ORANGE = "#ff7700"
COLOR_PURPLE = "#b026ff"
COLOR_WHITE = "#ffffff"
COLOR_RED = "#ff2244"
COLOR_BLUE = "#1e90ff"
COLOR_SHIELD = "#00bfff"

COLOR_UI_BG = "#0d1024"
COLOR_UI_BORDER = "#00f0ff"
COLOR_UI_ACCENT = "#ff007f"
COLOR_TEXT_PRIMARY = "#ffffff"
COLOR_TEXT_SECONDARY = "#8b9bb4"

# Audio Settings
AUDIO_SAMPLE_RATE = 22050
DEFAULT_AUDIO_ENABLED = True

# Player Default Stats
PLAYER_DEFAULT_SPEED = 5.5
PLAYER_FRICTION = 0.92
PLAYER_ROTATION_SPEED = 0.15
PLAYER_MAX_HEALTH = 100
PLAYER_MAX_SHIELD = 60
PLAYER_SHIELD_REGEN_RATE = 15.0  # per second
PLAYER_SHIELD_REGEN_DELAY = 3.0   # seconds after damage before regen
PLAYER_DASH_SPEED = 18.0
PLAYER_DASH_DURATION = 0.18      # seconds
PLAYER_DASH_COOLDOWN = 1.4       # seconds

# Difficulty Definitions
DIFFICULTIES = {
    "cadet": {
        "id": "cadet",
        "name": "CADET (EASY)",
        "desc": "Casual Flight: 0.7x Enemy DMG, 0.8x Enemy HP, +30% Scrap Drops",
        "dmg_mult": 0.7,
        "hp_mult": 0.8,
        "spd_mult": 0.88,
        "scrap_mult": 1.3,
        "color": COLOR_GREEN
    },
    "pilot": {
        "id": "pilot",
        "name": "PILOT (NORMAL)",
        "desc": "Standard Flight: The authentic balanced arcade experience (1.0x)",
        "dmg_mult": 1.0,
        "hp_mult": 1.0,
        "spd_mult": 1.0,
        "scrap_mult": 1.0,
        "color": COLOR_CYAN
    },
    "veteran": {
        "id": "veteran",
        "name": "VETERAN (HARD)",
        "desc": "Hostile Sector: 1.3x Enemy DMG, 1.2x Enemy HP, 1.15x Speed",
        "dmg_mult": 1.3,
        "hp_mult": 1.2,
        "spd_mult": 1.15,
        "scrap_mult": 1.1,
        "color": COLOR_ORANGE
    },
    "cyber_hell": {
        "id": "cyber_hell",
        "name": "CYBER-HELL (NIGHTMARE)",
        "desc": "Bullet Hell: 1.6x Enemy DMG, 1.4x Enemy HP, High-Velocity Projectiles",
        "dmg_mult": 1.6,
        "hp_mult": 1.4,
        "spd_mult": 1.25,
        "scrap_mult": 1.4,
        "color": COLOR_MAGENTA
    }
}

# Controls Info
CONTROLS_INFO = [
    ("W, A, S, D / Arrow Keys", "Thruster Maneuvering"),
    ("Mouse Aim + Left Click", "Fire Active Weapon (or Spacebar)"),
    ("Right Click / Shift / E", "Quantum Blink Dash (Invulnerable)"),
    ("Q / F", "EMP Shockwave (Clears bullets & stuns)"),
    ("1, 2, 3, 4, 5 / Mouse Wheel", "Cycle Arsenal Weapons"),
    ("B", "Open Tech Bay / Rogue-lite Upgrades"),
    ("P / ESC", "Pause Menu & Settings"),
    ("M", "Toggle Sound Effects"),
]
