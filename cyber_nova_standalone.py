"""
CYBER NOVA: ODYSSEY - COMPLETE STANDALONE SINGLE-FILE EDITION
Retro Synthwave Space Combat Rogue-lite.
100% Pure Python - Zero external dependencies required.

Features:
- Instant unfreezing Pause Menu with interactive buttons (ESC / P / Mouse)
- 5 Distinct Save Slots: Slot 1 (Auto-Save) + Slots 2-5 (Manual Saves 1-4)
- Unified "SAVE FILES (5 SLOTS)" browser in Main Menu for loading/deleting any slot
- In-flight manual slot selector in Pause Menu
- Difficulty Settings: Cadet, Pilot, Veteran, Cyber-Hell
- In-memory 16-Bit PCM procedural sound synthesizer & 60 FPS vector engine

Run directly with:
    py cyber_nova_standalone.py
    or
    python cyber_nova_standalone.py
"""

import os
import sys
import math
import random
import time
import json
import wave
import struct
import tempfile
from datetime import datetime
from pathlib import Path
import tkinter as tk

# Add Game class import
from game import Game

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

# ==============================================================================
# CONFIGURATION & CONSTANTS
# ==============================================================================
SCREEN_WIDTH = 1080
SCREEN_HEIGHT = 720
TARGET_FPS = 60
FRAME_DELAY_MS = int(1000 / TARGET_FPS)

# Color Palette (Standard 6-digit hex for 100% Tkinter compatibility)
COLOR_BG = "#060713"
COLOR_CYAN = "#00f0ff"
COLOR_MAGENTA = "#ff007f"
COLOR_YELLOW = "#ffe600"
COLOR_GREEN = "#00ff66"
COLOR_ORANGE = "#ff7700"
COLOR_PURPLE = "#b026ff"
COLOR_WHITE = "#ffffff"
COLOR_RED = "#ff2244"
COLOR_SHIELD = "#00bfff"

PLAYER_DEFAULT_SPEED = 5.5
PLAYER_FRICTION = 0.92
PLAYER_MAX_HEALTH = 100
PLAYER_MAX_SHIELD = 60
PLAYER_SHIELD_REGEN_RATE = 15.0
PLAYER_SHIELD_REGEN_DELAY = 3.0
PLAYER_DASH_SPEED = 18.0
PLAYER_DASH_COOLDOWN = 1.4

STATE_MENU = "menu"
STATE_SAVES_MENU = "saves_menu"
STATE_PLAYING = "playing"
STATE_UPGRADES = "upgrades"
STATE_PAUSED = "paused"
STATE_PAUSE_SAVE = "pause_save"
STATE_GAMEOVER = "gameover"
STATE_CONTROLS = "controls"

DIFFICULTIES = {
    "cadet": {
        "id": "cadet",
        "name": "CADET (EASY)",
        "desc": "Casual Flight: 0.7x Enemy DMG, 0.8x Enemy HP, +30% Scrap",
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
        "desc": "Bullet Hell: 1.6x Enemy DMG, 1.4x Enemy HP, Fast Bullets",
        "dmg_mult": 1.6,
        "hp_mult": 1.4,
        "spd_mult": 1.25,
        "scrap_mult": 1.4,
        "color": COLOR_MAGENTA
    }
}

SAVE_SLOT_DEFS = [
    {"id": "auto", "name": "SLOT 1 [AUTO-SAVE]", "type": "auto", "filename": "save_slot_auto.json", "color": "#00f0ff"},
    {"id": "manual_1", "name": "SLOT 2 [MANUAL 1]", "type": "manual", "filename": "save_slot_manual_1.json", "color": "#00ff66"},
    {"id": "manual_2", "name": "SLOT 3 [MANUAL 2]", "type": "manual", "filename": "save_slot_manual_2.json", "color": "#ffe600"},
    {"id": "manual_3", "name": "SLOT 4 [MANUAL 3]", "type": "manual", "filename": "save_slot_manual_3.json", "color": "#ff7700"},
    {"id": "manual_4", "name": "SLOT 5 [MANUAL 4]", "type": "manual", "filename": "save_slot_manual_4.json", "color": "#b026ff"},
]

CONTROLS_INFO = [
    ("W, A, S, D / Arrow Keys", "Thruster Maneuvering"),
    ("Mouse Aim + Left Click", "Fire Active Weapon (or Spacebar)"),
    ("Right Click / Shift / E", "Quantum Blink Dash (Invulnerable)"),
    ("Q / F", "EMP Shockwave (Clears bullets & stuns)"),
    ("1, 2, 3, 4, 5 / Mouse Wheel", "Cycle Arsenal Weapons"),
    ("B", "Open Tech Bay / Rogue-lite Upgrades"),
    ("P / ESC", "Pause Menu & Save Slots"),
    ("M", "Toggle Sound Effects"),
]

# ==============================================================================
# AUDIO SYNTHESIZER ENGINE (Pure Python 16-bit PCM WAV)
# ==============================================================================
class SoundEngine:
    def __init__(self):
        self.enabled = HAS_WINSOUND
        self.temp_dir = Path(tempfile.gettempdir()) / "cyber_nova_audio"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self._cache = {}
        self._sample_rate = 22050
        self._ensure_sounds()

    def toggle_sound(self) -> bool:
        self.enabled = not self.enabled
        return self.enabled

    def _write_wav(self, filename: str, samples: list[float]):
        filepath = self.temp_dir / filename
        with wave.open(str(filepath), 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self._sample_rate)
            buf = bytearray()
            for s in samples:
                val = max(-1.0, min(1.0, s))
                buf.extend(struct.pack('<h', int(val * 32767.0)))
            wf.writeframes(buf)
        self._cache[filename] = str(filepath)

    def _ensure_sounds(self):
        rate = self._sample_rate

        # Laser pew
        if not (self.temp_dir / "laser.wav").exists():
            dur = 0.12
            total = int(rate * dur)
            s = []
            for i in range(total):
                t = i / total
                freq = 950 * math.exp(-3.8 * t)
                amp = (1.0 - t) * 0.4
                s.append(amp * math.sin(2 * math.pi * freq * (i / rate)))
            self._write_wav("laser.wav", s)
        else:
            self._cache["laser.wav"] = str(self.temp_dir / "laser.wav")

        # Plasma blast
        if not (self.temp_dir / "plasma.wav").exists():
            dur = 0.16
            total = int(rate * dur)
            s = []
            for i in range(total):
                t = i / total
                freq = 600 * math.exp(-4.2 * t)
                amp = (1.0 - t ** 0.8) * 0.45
                val = math.sin(2 * math.pi * freq * (i / rate)) + 0.3 * math.sin(4 * math.pi * freq * (i / rate))
                s.append(amp * val)
            self._write_wav("plasma.wav", s)
        else:
            self._cache["plasma.wav"] = str(self.temp_dir / "plasma.wav")

        # Flak Shotgun
        if not (self.temp_dir / "shotgun.wav").exists():
            dur = 0.18
            total = int(rate * dur)
            s = []
            for i in range(total):
                t = i / total
                freq = 480 * math.exp(-4.5 * t)
                noise = (random.random() * 2.0 - 1.0) * 0.4
                amp = (1.0 - t) * 0.5
                s.append(amp * (math.sin(2 * math.pi * freq * (i / rate)) * 0.6 + noise))
            self._write_wav("shotgun.wav", s)
        else:
            self._cache["shotgun.wav"] = str(self.temp_dir / "shotgun.wav")

        # Missile
        if not (self.temp_dir / "missile.wav").exists():
            dur = 0.22
            total = int(rate * dur)
            s = [math.sin(math.pi * (i / total)) * 0.4 * math.sin(2 * math.pi * (300 + 400 * (i / total)) * (i / rate)) for i in range(total)]
            self._write_wav("missile.wav", s)
        else:
            self._cache["missile.wav"] = str(self.temp_dir / "missile.wav")

        # Explosions
        if not (self.temp_dir / "explosion_sm.wav").exists():
            dur = 0.25
            total = int(rate * dur)
            s = [(1.0 - (i / total)) ** 1.8 * 0.45 * ((random.random() * 2.0 - 1.0) * 0.6 + math.sin(2 * math.pi * 150 * (i / rate)) * 0.4) for i in range(total)]
            self._write_wav("explosion_sm.wav", s)
        else:
            self._cache["explosion_sm.wav"] = str(self.temp_dir / "explosion_sm.wav")

        if not (self.temp_dir / "explosion_lg.wav").exists():
            dur = 0.60
            total = int(rate * dur)
            s = [(1.0 - (i / total)) ** 1.4 * 0.55 * ((random.random() * 2.0 - 1.0) * 0.5 + math.sin(2 * math.pi * 100 * math.exp(-1.5 * (i / total)) * (i / rate)) * 0.5) for i in range(total)]
            self._write_wav("explosion_lg.wav", s)
        else:
            self._cache["explosion_lg.wav"] = str(self.temp_dir / "explosion_lg.wav")

        # Dash whoosh
        if not (self.temp_dir / "dash.wav").exists():
            dur = 0.20
            total = int(rate * dur)
            s = [math.sin(math.pi * (i / total)) * 0.45 * math.sin(2 * math.pi * (280 + 1100 * math.sin(math.pi * (i / total))) * (i / rate)) for i in range(total)]
            self._write_wav("dash.wav", s)
        else:
            self._cache["dash.wav"] = str(self.temp_dir / "dash.wav")

        # EMP shockwave
        if not (self.temp_dir / "emp.wav").exists():
            dur = 0.45
            total = int(rate * dur)
            s = [(1.0 - (i / total)) * 0.55 * math.sin(2 * math.pi * (70 + 400 * (1.0 - i / total)) * (i / rate)) * math.sin(2 * math.pi * 90 * (i / rate)) for i in range(total)]
            self._write_wav("emp.wav", s)
        else:
            self._cache["emp.wav"] = str(self.temp_dir / "emp.wav")

        # Coin pickup
        if not (self.temp_dir / "pickup.wav").exists():
            dur = 0.10
            total = int(rate * dur)
            half = total // 2
            s = [(1.0 - i / total) * 0.35 * math.sin(2 * math.pi * (880 if i < half else 1320) * (i / rate)) for i in range(total)]
            self._write_wav("pickup.wav", s)
        else:
            self._cache["pickup.wav"] = str(self.temp_dir / "pickup.wav")

        # Powerup fanfare
        if not (self.temp_dir / "powerup.wav").exists():
            dur = 0.32
            total = int(rate * dur)
            notes = [523.25, 659.25, 783.99, 1046.50]
            seg = total // len(notes)
            s = [(1.0 - ((i % seg) / seg)) * 0.38 * math.sin(2 * math.pi * notes[min(len(notes)-1, i // seg)] * (i / rate)) for i in range(total)]
            self._write_wav("powerup.wav", s)
        else:
            self._cache["powerup.wav"] = str(self.temp_dir / "powerup.wav")

        # Boss Klaxon
        if not (self.temp_dir / "boss_alarm.wav").exists():
            dur = 0.40
            total = int(rate * dur)
            s = [(1.0 - (i / total) * 0.5) * 0.4 * math.sin(2 * math.pi * (440 if (i // (rate // 10)) % 2 == 0 else 330) * (i / rate)) for i in range(total)]
            self._write_wav("boss_alarm.wav", s)
        else:
            self._cache["boss_alarm.wav"] = str(self.temp_dir / "boss_alarm.wav")

    def play(self, sound_name: str):
        if not self.enabled or not HAS_WINSOUND:
            return
        fname = f"{sound_name}.wav" if not sound_name.endswith(".wav") else sound_name
        path = self._cache.get(fname)
        if path and os.path.exists(path):
            try:
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception:
                pass

sound_engine = SoundEngine()

# ==============================================================================
# PERSISTENT SAVE MANAGER (5 Slots: 1 Auto-Save + 4 Manual Saves)
# ==============================================================================
class SaveManager:
    def __init__(self):
        self.save_dir = Path.home() / ".cyber_nova"
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.profile_file = self.save_dir / "profile.json"

        self.profile = {
            "high_score": 0,
            "max_wave": 1,
            "total_kills": 0,
            "total_scrap_collected": 0,
            "games_played": 0
        }
        self.load_profile()

    def load_profile(self):
        if self.profile_file.exists():
            try:
                with open(self.profile_file, "r", encoding="utf-8") as f:
                    self.profile.update(json.load(f))
            except Exception:
                pass

    def save_profile(self):
        try:
            with open(self.profile_file, "w", encoding="utf-8") as f:
                json.dump(self.profile, f, indent=4)
        except Exception:
            pass

    def record_run(self, score: int, wave: int, kills: int, scrap: int) -> bool:
        is_new_high = score > self.profile.get("high_score", 0)
        if is_new_high:
            self.profile["high_score"] = score
        if wave > self.profile.get("max_wave", 1):
            self.profile["max_wave"] = wave

        self.profile["total_kills"] = self.profile.get("total_kills", 0) + kills
        self.profile["total_scrap_collected"] = self.profile.get("total_scrap_collected", 0) + scrap
        self.profile["games_played"] = self.profile.get("games_played", 0) + 1
        self.save_profile()
        return is_new_high

    def _get_slot_file(self, slot_id: str) -> Path:
        for s in SAVE_SLOT_DEFS:
            if s["id"] == slot_id:
                return self.save_dir / s["filename"]
        return self.save_dir / f"save_slot_{slot_id}.json"

    def save_slot(self, slot_id: str, state_dict: dict) -> bool:
        try:
            data = dict(state_dict)
            data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            data["slot_id"] = slot_id
            with open(self._get_slot_file(slot_id), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            return True
        except Exception:
            return False

    def load_slot(self, slot_id: str) -> dict | None:
        filepath = self._get_slot_file(slot_id)
        if not filepath.exists():
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def has_slot(self, slot_id: str) -> bool:
        return self._get_slot_file(slot_id).exists()

    def get_slot_metadata(self, slot_id: str) -> dict:
        slot_def = next((s for s in SAVE_SLOT_DEFS if s["id"] == slot_id), None)
        base_meta = {
            "id": slot_id,
            "name": slot_def["name"] if slot_def else slot_id.upper(),
            "type": slot_def["type"] if slot_def else "manual",
            "color": slot_def["color"] if slot_def else "#ffffff",
            "exists": False,
            "wave": 1,
            "score": 0,
            "scrap": 0,
            "difficulty": "pilot",
            "timestamp": "EMPTY SLOT",
            "health": 100,
            "max_health": 100
        }
        data = self.load_slot(slot_id)
        if data:
            base_meta.update({
                "exists": True,
                "wave": data.get("wave", 1),
                "score": data.get("score", 0),
                "scrap": data.get("scrap", 0),
                "difficulty": data.get("difficulty", "pilot"),
                "timestamp": data.get("timestamp", "Unknown"),
                "health": data.get("player", {}).get("health", 100),
                "max_health": data.get("player", {}).get("max_health", 100)
            })
        return base_meta

    def get_all_slots_metadata(self) -> list[dict]:
        return [self.get_slot_metadata(s["id"]) for s in SAVE_SLOT_DEFS]

    def has_any_save(self) -> bool:
        return any(self.has_slot(s["id"]) for s in SAVE_SLOT_DEFS)

    def delete_slot(self, slot_id: str):
        filepath = self._get_slot_file(slot_id)
        if filepath.exists():
            try:
                filepath.unlink()
            except Exception:
                pass

save_manager = SaveManager()

# ==============================================================================
# VISUAL FX & PARTICLE ENGINE
# ==============================================================================
class Star:
    def __init__(self, w: int, h: int, layer: int):
        self.w = w
        self.h = h
        self.layer = layer
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h)
        if layer == 1:
            self.spd = random.uniform(0.3, 0.7)
            self.sz = 1.0
            self.col = random.choice(["#222644", "#30355e", "#3a3f70"])
        elif layer == 2:
            self.spd = random.uniform(1.0, 1.8)
            self.sz = 1.8
            self.col = random.choice(["#556699", "#4488bb", "#6644aa"])
        else:
            self.spd = random.uniform(2.5, 4.0)
            self.sz = 2.5
            self.col = random.choice([COLOR_WHITE, COLOR_CYAN, "#aaddff"])

    def update(self, p_vx: float, p_vy: float, warp: float):
        self.x = (self.x - p_vx * (0.05 * self.layer)) % self.w
        self.y = (self.y + (self.spd * warp) - p_vy * (0.05 * self.layer)) % self.h

    def draw(self, canvas, warp: float):
        if warp > 1.5 and self.layer >= 2:
            trail = min(40.0, self.spd * warp * 3.0)
            canvas.create_line(self.x, self.y, self.x, self.y - trail, fill=self.col, width=self.sz)
        else:
            r = self.sz
            canvas.create_oval(self.x - r, self.y - r, self.x + r, self.y + r, fill=self.col, outline="")


class Starfield:
    def __init__(self, w: int = SCREEN_WIDTH, h: int = SCREEN_HEIGHT, count: int = 120):
        self.stars = [Star(w, h, 1) for _ in range(int(count * 0.5))] + \
                     [Star(w, h, 2) for _ in range(int(count * 0.35))] + \
                     [Star(w, h, 3) for _ in range(int(count * 0.15))]
        self.warp = 1.0
        self.target_warp = 1.0

    def trigger_warp(self):
        self.target_warp = 7.0

    def update(self, p_vx: float = 0.0, p_vy: float = 0.0):
        self.warp += (self.target_warp - self.warp) * 0.1
        if self.target_warp > 1.0:
            self.target_warp -= 0.15
            if self.target_warp < 1.0:
                self.target_warp = 1.0
        for s in self.stars:
            s.update(p_vx, p_vy, self.warp)

    def draw(self, canvas):
        for s in self.stars:
            s.draw(canvas, self.warp)


class SparkParticle:
    def __init__(self, x: float, y: float, vx: float, vy: float, col: str, sz: float = 3.0, life: int = 25):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.col = col
        self.sz = sz
        self.init_sz = sz
        self.life = life
        self.max_life = life
        self.alive = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.94
        self.vy *= 0.94
        self.life -= 1
        self.sz = self.init_sz * (self.life / self.max_life)
        if self.life <= 0 or self.sz <= 0.3:
            self.alive = False

    def draw(self, canvas):
        r = self.sz
        canvas.create_oval(self.x - r, self.y - r, self.x + r, self.y + r, fill=self.col, outline="")


class ShockwaveRing:
    def __init__(self, x: float, y: float, max_r: float, col: str, spd: float = 8.0, w: int = 3):
        self.x = x
        self.y = y
        self.curr_r = 4.0
        self.max_r = max_r
        self.spd = spd
        self.col = col
        self.w = w
        self.alive = True

    def update(self):
        self.curr_r += self.spd
        if self.curr_r >= self.max_r:
            self.alive = False

    def draw(self, canvas):
        line_w = max(1, int(self.w * (1.0 - (self.curr_r / self.max_r) * 0.7)))
        r = self.curr_r
        canvas.create_oval(self.x - r, self.y - r, self.x + r, self.y + r, outline=self.col, width=line_w)


class FloatingText:
    def __init__(self, x: float, y: float, text: str, col: str, sz: int = 12):
        self.x = x
        self.y = y
        self.text = text
        self.col = col
        self.sz = sz
        self.life = 35
        self.vy = -1.5
        self.alive = True

    def update(self):
        self.y += self.vy
        self.vy *= 0.95
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self, canvas):
        fnt = ("Impact" if "CRIT" in self.text or "BOSS" in self.text else "Consolas", self.sz, "bold")
        canvas.create_text(self.x, self.y, text=self.text, fill=self.col, font=fnt, anchor="center")


class DashGhost:
    def __init__(self, pts: list[tuple[float, float]], col: str):
        self.pts = pts
        self.col = col
        self.life = 12
        self.alive = True

    def update(self):
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self, canvas):
        if len(self.pts) >= 3:
            flat = [coord for pt in self.pts for coord in pt]
            canvas.create_polygon(flat, outline=self.col, fill="", width=1)


class ParticleManager:
    def __init__(self):
        self.sparks = []
        self.shockwaves = []
        self.texts = []
        self.ghosts = []

    def emit_sparks(self, x: float, y: float, count: int, colors: list[str],
                    speed_min: float = 2.0, speed_max: float = 6.0, sz_min: float = 2.0, sz_max: float = 4.0):
        for _ in range(count):
            ang = random.uniform(0, 2 * math.pi)
            spd = random.uniform(speed_min, speed_max)
            self.sparks.append(SparkParticle(x, y, math.cos(ang) * spd, math.sin(ang) * spd,
                                             random.choice(colors), random.uniform(sz_min, sz_max)))

    def emit_directional_sparks(self, x: float, y: float, count: int, base_ang: float,
                                spread: float, spd: float, colors: list[str]):
        for _ in range(count):
            ang = base_ang + random.uniform(-spread, spread)
            s = spd * random.uniform(0.7, 1.3)
            self.sparks.append(SparkParticle(x, y, math.cos(ang) * s, math.sin(ang) * s, random.choice(colors), 2.5, life=15))

    def emit_shockwave(self, x: float, y: float, max_r: float, col: str, spd: float = 8.0, w: int = 3):
        self.shockwaves.append(ShockwaveRing(x, y, max_r, col, spd, w))

    def add_floating_text(self, x: float, y: float, text: str, col: str = COLOR_YELLOW, sz: int = 12):
        self.texts.append(FloatingText(x, y, text, col, sz))

    def add_ghost(self, pts: list[tuple[float, float]], col: str = COLOR_CYAN):
        self.ghosts.append(DashGhost(pts, col))

    def update(self):
        for p in self.sparks: p.update()
        self.sparks = [p for p in self.sparks if p.alive]
        for s in self.shockwaves: s.update()
        self.shockwaves = [s for s in self.shockwaves if s.alive]
        for t in self.texts: t.update()
        self.texts = [t for t in self.texts if t.alive]
        for g in self.ghosts: g.update()
        self.ghosts = [g for g in self.ghosts if g.alive]

    def draw(self, canvas):
        for g in self.ghosts: g.draw(canvas)
        for s in self.shockwaves: s.draw(canvas)
        for p in self.sparks: p.draw(canvas)
        for t in self.texts: t.draw(canvas)

    def clear(self):
        self.sparks.clear()
        self.shockwaves.clear()
        self.texts.clear()
        self.ghosts.clear()

# ==============================================================================
# WEAPONS & PROJECTILES
# ==============================================================================
class Projectile:
    def __init__(self, x: float, y: float, vx: float, vy: float, damage: float,
                 col: str, r: float = 3.5, is_player: bool = True, piercing: int = 1, life: int = 70):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.damage = damage
        self.col = col
        self.radius = r
        self.is_player = is_player
        self.piercing = piercing
        self.life = life
        self.alive = True

    def update(self, bounds_w: int, bounds_h: int):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        if self.x < -30 or self.x > bounds_w + 30 or self.y < -30 or self.y > bounds_h + 30 or self.life <= 0:
            self.alive = False

    def draw(self, canvas):
        r = self.radius
        canvas.create_oval(self.x - r, self.y - r, self.x + r, self.y + r,
                          fill=self.col, outline=COLOR_WHITE if self.is_player else "")
        spd = math.hypot(self.vx, self.vy)
        if spd > 1.0:
            canvas.create_line(self.x, self.y, self.x - (self.vx / spd) * (r * 2.2),
                               self.y - (self.vy / spd) * (r * 2.2), fill=self.col, width=max(1, int(r * 0.7)))


class HomingMissile(Projectile):
    def __init__(self, x: float, y: float, ang: float, spd: float, dmg: float):
        super().__init__(x, y, math.cos(ang) * spd, math.sin(ang) * spd, dmg, COLOR_GREEN, r=4.0, is_player=True, life=90)
        self.speed = spd
        self.angle = ang
        self.turn_rate = 0.12
        self.trail_t = 0

    def update_homing(self, enemies: list, particle_mgr, bw: int, bh: int):
        closest = None
        closest_d = float('inf')
        for e in enemies:
            if getattr(e, 'alive', False):
                d = math.hypot(e.x - self.x, e.y - self.y)
                if d < closest_d:
                    closest_d = d
                    closest = e

        if closest:
            t_ang = math.atan2(closest.y - self.y, closest.x - self.x)
            diff = (t_ang - self.angle + math.pi) % (2 * math.pi) - math.pi
            self.angle += max(-self.turn_rate, min(self.turn_rate, diff))
            self.vx = math.cos(self.angle) * self.speed
            self.vy = math.sin(self.angle) * self.speed

        self.trail_t += 1
        if self.trail_t % 2 == 0 and particle_mgr:
            particle_mgr.emit_sparks(self.x - math.cos(self.angle)*6, self.y - math.sin(self.angle)*6,
                                     1, [COLOR_GREEN, COLOR_YELLOW], speed_min=0.5, speed_max=2.0)
        self.update(bw, bh)


class SingularityVortex(Projectile):
    def __init__(self, x: float, y: float, vx: float, vy: float, dmg: float):
        super().__init__(x, y, vx, vy, dmg, COLOR_PURPLE, r=14.0, is_player=True, life=130)
        self.pull_r = 160.0
        self.pulse = 0.0

    def update_vortex(self, enemies: list, particle_mgr, bw: int, bh: int):
        self.pulse += 0.2
        for e in enemies:
            if getattr(e, 'alive', False):
                dx = self.x - e.x
                dy = self.y - e.y
                d = math.hypot(dx, dy)
                if 0 < d < self.pull_r:
                    force = (1.0 - (d / self.pull_r)) * 2.8
                    e.x += (dx / d) * force
                    e.y += (dy / d) * force

        if particle_mgr and random.random() < 0.3:
            particle_mgr.emit_sparks(self.x, self.y, 2, [COLOR_PURPLE, COLOR_MAGENTA, COLOR_CYAN], speed_min=1.0, speed_max=4.0)

        self.vx *= 0.96
        self.vy *= 0.96
        self.update(bw, bh)

    def draw(self, canvas):
        r = self.radius + math.sin(self.pulse) * 3.0
        canvas.create_oval(self.x - r - 5, self.y - r - 5, self.x + r + 5, self.y + r + 5, outline=COLOR_MAGENTA, width=2)
        canvas.create_oval(self.x - r, self.y - r, self.x + r, self.y + r, fill="#050010", outline=COLOR_PURPLE, width=3)


class WeaponDefinition:
    def __init__(self, name: str, key: str, cd: float, cost: float, col: str, desc: str, unlocked: bool):
        self.name = name
        self.key = key
        self.cooldown = cd
        self.energy_cost = cost
        self.color = col
        self.description = desc
        self.unlocked = unlocked

WEAPONS_DATA = {
    "pulse": WeaponDefinition("PULSE CANNON", "1", 0.14, 3.0, COLOR_CYAN, "High-velocity particle needle.", True),
    "twin": WeaponDefinition("TWIN PLASMA", "2", 0.22, 7.0, COLOR_MAGENTA, "Dual synchronized heavy plasma bolts.", True),
    "flak": WeaponDefinition("SCATTER FLAK", "3", 0.44, 15.0, COLOR_YELLOW, "Conical spread of shrapnel pellets.", False),
    "homing": WeaponDefinition("HOMING PODS", "4", 0.38, 18.0, COLOR_GREEN, "Smart micro-missiles with target lock.", False),
    "singularity": WeaponDefinition("SINGULARITY CORE", "5", 1.20, 35.0, COLOR_PURPLE, "Micro-black hole tearing through targets.", False)
}

# ==============================================================================
# LOOT & PICKUPS
# ==============================================================================
class Pickup:
    def __init__(self, x: float, y: float, pu_type: str, val: int = 1):
        self.x = x
        self.y = y
        self.pickup_type = pu_type
        self.value = val
        ang = random.uniform(0, 2 * math.pi)
        spd = random.uniform(1.5, 4.0)
        self.vx = math.cos(ang) * spd
        self.vy = math.sin(ang) * spd
        self.alive = True
        self.life = 700
        self.pulse = random.uniform(0, 6.28)
        self.radius = 5.0 if pu_type == "scrap" else 8.0
        self.col = {"scrap": COLOR_YELLOW, "health": COLOR_GREEN, "shield": COLOR_CYAN,
                    "overclock": COLOR_ORANGE, "emp": COLOR_PURPLE}.get(pu_type, COLOR_WHITE)

    def update(self, px: float, py: float, magnet_range: float):
        self.pulse += 0.12
        self.life -= 1
        if self.life <= 0:
            self.alive = False
            return
        self.vx *= 0.94
        self.vy *= 0.94
        self.x += self.vx
        self.y += self.vy

        dx = px - self.x
        dy = py - self.y
        d = math.hypot(dx, dy)
        if 0.1 < d < magnet_range:
            pull = (1.0 - (d / magnet_range)) * 14.0 + 3.0
            self.x += (dx / d) * pull
            self.y += (dy / d) * pull

    def draw(self, canvas):
        if self.life < 100 and (self.life // 8) % 2 == 0:
            return
        r = self.radius + math.sin(self.pulse) * 1.5
        if self.pickup_type == "scrap":
            pts = [self.x, self.y - r, self.x + r, self.y, self.x, self.y + r, self.x - r, self.y]
            canvas.create_polygon(pts, fill=self.col, outline=COLOR_WHITE, width=1)
        elif self.pickup_type == "health":
            canvas.create_oval(self.x - r, self.y - r, self.x + r, self.y + r, fill="#003311", outline=self.col, width=2)
            arm = r * 0.6
            canvas.create_line(self.x - arm, self.y, self.x + arm, self.y, fill=self.col, width=2)
            canvas.create_line(self.x, self.y - arm, self.x, self.y + arm, fill=self.col, width=2)
        elif self.pickup_type == "shield":
            canvas.create_oval(self.x - r, self.y - r, self.x + r, self.y + r, fill="#001833", outline=self.col, width=2)
            canvas.create_oval(self.x - r*0.5, self.y - r*0.5, self.x + r*0.5, self.y + r*0.5, fill=COLOR_CYAN, outline="")
        elif self.pickup_type == "overclock":
            canvas.create_oval(self.x - r, self.y - r, self.x + r, self.y + r, fill="#331800", outline=self.col, width=2)
            canvas.create_text(self.x, self.y, text="⚡", fill=COLOR_ORANGE, font=("Arial", int(r * 1.2), "bold"))
        elif self.pickup_type == "emp":
            canvas.create_oval(self.x - r, self.y - r, self.x + r, self.y + r, fill="#220033", outline=self.col, width=2)
            canvas.create_text(self.x, self.y, text="Ω", fill=COLOR_PURPLE, font=("Consolas", int(r * 1.2), "bold"))

# ==============================================================================
# PLAYER SPACECRAFT
# ==============================================================================
class Player:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.angle = -math.pi / 2
        self.radius = 16.0

        self.max_health = PLAYER_MAX_HEALTH
        self.health = PLAYER_MAX_HEALTH
        self.max_shield = PLAYER_MAX_SHIELD
        self.shield = PLAYER_MAX_SHIELD
        self.shield_regen_rate = PLAYER_SHIELD_REGEN_RATE
        self.speed = PLAYER_DEFAULT_SPEED
        self.magnet_range = 140.0
        self.crit_chance = 0.10
        self.crit_multiplier = 1.8

        self.max_energy = 100.0
        self.energy = 100.0
        self.energy_regen = 32.0
        self.fire_cooldown = 0.0
        self.shield_delay_timer = 0.0
        self.invulnerable_timer = 0.0

        self.dash_cooldown = 0.0
        self.is_dashing = False
        self.dash_timer = 0.0
        self.dash_dir_x = 0.0
        self.dash_dir_y = 0.0

        self.emp_charges = 2
        self.max_emp_charges = 4
        self.overclock_timer = 0.0

        self.current_weapon = "pulse"
        self.unlocked_weapons = ["pulse", "twin"]
        self.thrusting = False
        self.shield_flash_alpha = 0.0

    def get_points(self) -> list[tuple[float, float]]:
        ca = math.cos(self.angle)
        sa = math.sin(self.angle)
        pts = [(22, 0), (-14, 15), (-8, 6), (-12, 0), (-8, -6), (-14, -15)]
        return [(self.x + (px * ca - py * sa), self.y + (px * sa + py * ca)) for px, py in pts]

    def handle_input(self, keys: dict, mx: float, my: float):
        dx = mx - self.x
        dy = my - self.y
        if math.hypot(dx, dy) > 8:
            self.angle = math.atan2(dy, dx)

        if self.is_dashing:
            return

        ax, ay = 0.0, 0.0
        mag = 1.1
        if keys.get("w") or keys.get("up"): ay -= mag
        if keys.get("s") or keys.get("down"): ay += mag
        if keys.get("a") or keys.get("left"): ax -= mag
        if keys.get("d") or keys.get("right"): ax += mag

        self.thrusting = (ax != 0.0 or ay != 0.0)
        if self.thrusting:
            norm = math.hypot(ax, ay)
            if norm > 0:
                ax = (ax / norm) * mag
                ay = (ay / norm) * mag
            self.vx += ax
            self.vy += ay
            spd = math.hypot(self.vx, self.vy)
            if spd > self.speed:
                self.vx = (self.vx / spd) * self.speed
                self.vy = (self.vy / spd) * self.speed

    def trigger_dash(self, particle_mgr) -> bool:
        if self.dash_cooldown > 0 or self.is_dashing:
            return False
        spd = math.hypot(self.vx, self.vy)
        if spd > 0.5:
            self.dash_dir_x = self.vx / spd
            self.dash_dir_y = self.vy / spd
        else:
            self.dash_dir_x = math.cos(self.angle)
            self.dash_dir_y = math.sin(self.angle)

        self.is_dashing = True
        self.dash_timer = 0.16
        self.dash_cooldown = PLAYER_DASH_COOLDOWN
        self.invulnerable_timer = max(self.invulnerable_timer, 0.25)
        sound_engine.play("dash")
        if particle_mgr:
            particle_mgr.emit_shockwave(self.x, self.y, 45.0, COLOR_CYAN, spd=10.0, w=2)
            particle_mgr.emit_sparks(self.x, self.y, 14, [COLOR_CYAN, COLOR_WHITE, COLOR_SHIELD])
        return True

    def trigger_emp(self, particle_mgr, enemies: list, projectiles: list) -> bool:
        if self.emp_charges <= 0:
            return False
        self.emp_charges -= 1
        sound_engine.play("emp")
        if particle_mgr:
            particle_mgr.emit_shockwave(self.x, self.y, 500.0, COLOR_PURPLE, spd=16.0, w=6)
            particle_mgr.emit_shockwave(self.x, self.y, 350.0, COLOR_CYAN, spd=12.0, w=4)
            particle_mgr.add_floating_text(self.x, self.y - 30, "EMP DETONATION!", COLOR_PURPLE, sz=18)

        for p in projectiles:
            if not p.is_player and p.alive:
                p.alive = False

        for e in enemies:
            if getattr(e, 'alive', False):
                e.take_damage(80, True, particle_mgr)
                if hasattr(e, 'stun_timer'):
                    e.stun_timer = 3.5
        return True

    def fire(self, particle_mgr) -> list[Projectile]:
        if self.fire_cooldown > 0:
            return []
        w_def = WEAPONS_DATA.get(self.current_weapon)
        if not w_def:
            return []

        cost = 0.0 if self.overclock_timer > 0 else w_def.energy_cost
        if self.energy < cost:
            return []

        self.energy -= cost
        self.fire_cooldown = w_def.cooldown * (0.5 if self.overclock_timer > 0 else 1.0)
        spawned = []
        ca = math.cos(self.angle)
        sa = math.sin(self.angle)
        nx = self.x + ca * 22
        ny = self.y + sa * 22

        is_crit = random.random() < self.crit_chance
        mult = self.crit_multiplier if is_crit else 1.0

        if self.current_weapon == "pulse":
            sound_engine.play("laser")
            spawned.append(Projectile(nx, ny, ca * 18.0 + self.vx * 0.2, sa * 18.0 + self.vy * 0.2,
                                      24.0 * mult, COLOR_YELLOW if is_crit else COLOR_CYAN, r=3.5))
            if particle_mgr:
                particle_mgr.emit_directional_sparks(nx, ny, 3, self.angle, 0.3, 4.0, [COLOR_CYAN, COLOR_WHITE])

        elif self.current_weapon == "twin":
            sound_engine.play("plasma")
            for ox, oy in [(-sa * 10, ca * 10), (sa * 10, -ca * 10)]:
                bx = self.x + ca * 14 + ox
                by = self.y + sa * 14 + oy
                spawned.append(Projectile(bx, by, ca * 16.0 + self.vx * 0.2, sa * 16.0 + self.vy * 0.2,
                                          20.0 * mult, COLOR_WHITE if is_crit else COLOR_MAGENTA, r=4.0))

        elif self.current_weapon == "flak":
            sound_engine.play("shotgun")
            for _ in range(6):
                ang = self.angle + random.uniform(-0.28, 0.28)
                spd = 15.0 * random.uniform(0.85, 1.15)
                spawned.append(Projectile(nx, ny, math.cos(ang) * spd + self.vx * 0.2, math.sin(ang) * spd + self.vy * 0.2,
                                          14.0 * mult, COLOR_YELLOW, r=2.5, life=45))

        elif self.current_weapon == "homing":
            sound_engine.play("missile")
            for side in (-0.35, 0.35):
                spawned.append(HomingMissile(nx, ny, self.angle + side, 11.0, 38.0 * mult))

        elif self.current_weapon == "singularity":
            sound_engine.play("emp")
            spawned.append(SingularityVortex(nx, ny, ca * 5.5, sa * 5.5, 15.0 * mult))

        return spawned

    def take_damage(self, amount: float, particle_mgr) -> bool:
        if self.invulnerable_timer > 0:
            return True
        self.shield_delay_timer = PLAYER_SHIELD_REGEN_DELAY
        self.invulnerable_timer = 0.45
        self.shield_flash_alpha = 1.0

        if self.shield > 0:
            sound_engine.play("shield_hit")
            if self.shield >= amount:
                self.shield -= amount
                if particle_mgr: particle_mgr.emit_shockwave(self.x, self.y, 35.0, COLOR_SHIELD, spd=6.0, w=2)
            else:
                rem = amount - self.shield
                self.shield = 0.0
                self.health -= rem
                sound_engine.play("explosion_sm")
                if particle_mgr:
                    particle_mgr.emit_shockwave(self.x, self.y, 45.0, COLOR_RED, spd=8.0, w=3)
                    particle_mgr.add_floating_text(self.x, self.y - 20, "SHIELD BROKEN!", COLOR_RED, sz=14)
        else:
            sound_engine.play("explosion_sm")
            self.health -= amount
            if particle_mgr: particle_mgr.emit_sparks(self.x, self.y, 16, [COLOR_RED, COLOR_YELLOW, COLOR_WHITE])

        if self.health <= 0:
            self.health = 0.0
            return False
        return True

    def update(self, dt: float, particle_mgr):
        if self.fire_cooldown > 0: self.fire_cooldown -= dt
        if self.dash_cooldown > 0: self.dash_cooldown -= dt
        if self.invulnerable_timer > 0: self.invulnerable_timer -= dt
        if self.overclock_timer > 0: self.overclock_timer -= dt

        if self.is_dashing:
            self.dash_timer -= dt
            self.vx = self.dash_dir_x * PLAYER_DASH_SPEED
            self.vy = self.dash_dir_y * PLAYER_DASH_SPEED
            if particle_mgr and random.random() < 0.6:
                particle_mgr.add_ghost(self.get_points(), COLOR_CYAN)
            if self.dash_timer <= 0:
                self.is_dashing = False
                self.vx *= 0.35
                self.vy *= 0.35
        else:
            self.vx *= PLAYER_FRICTION
            self.vy *= PLAYER_FRICTION

        self.x += self.vx
        self.y += self.vy

        margin = self.radius + 6
        self.x = max(margin, min(SCREEN_WIDTH - margin, self.x))
        self.y = max(margin, min(SCREEN_HEIGHT - margin, self.y))

        regen = self.energy_regen * (2.0 if self.overclock_timer > 0 else 1.0)
        self.energy = min(self.max_energy, self.energy + regen * dt)

        if self.shield_delay_timer > 0:
            self.shield_delay_timer -= dt
        elif self.shield < self.max_shield:
            self.shield = min(self.max_shield, self.shield + self.shield_regen_rate * dt)

        if (self.thrusting or self.is_dashing) and particle_mgr:
            ca = math.cos(self.angle)
            sa = math.sin(self.angle)
            particle_mgr.emit_directional_sparks(self.x - ca*12, self.y - sa*12, 2, self.angle + math.pi, 0.4, 4.5,
                                                 [COLOR_CYAN, COLOR_MAGENTA, COLOR_WHITE] if not self.is_dashing else [COLOR_CYAN, COLOR_SHIELD])

    def draw(self, canvas):
        if self.invulnerable_timer > 0 and int(self.invulnerable_timer * 20) % 2 == 0:
            return
        flat = [coord for pt in self.get_points() for coord in pt]
        hull_col = COLOR_CYAN if self.overclock_timer <= 0 else COLOR_ORANGE
        canvas.create_polygon(flat, fill="#091428", outline=hull_col, width=2)

        ca = math.cos(self.angle)
        sa = math.sin(self.angle)
        cx = self.x + ca * 2
        cy = self.y + sa * 2
        canvas.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill=COLOR_WHITE, outline=COLOR_MAGENTA, width=1)

        if self.shield > 0 and (self.shield_flash_alpha > 0 or self.shield < self.max_shield * 0.4):
            r = self.radius + 6.0
            canvas.create_oval(self.x - r, self.y - r, self.x + r, self.y + r, outline=COLOR_SHIELD, width=2)

# ==============================================================================
# ENEMY SHIPS & ARMADA
# ==============================================================================
class EnemyBase:
    def __init__(self, x: float, y: float, hp: float, spd: float, r: float, score: int):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.angle = 0.0
        self.health = hp
        self.max_health = hp
        self.speed = spd
        self.radius = r
        self.score_val = score
        self.alive = True
        self.stun_timer = 0.0
        self.hit_flash = 0.0

    def take_damage(self, amount: float, is_crit: bool, particle_mgr) -> bool:
        self.health -= amount
        self.hit_flash = 0.12
        if particle_mgr:
            particle_mgr.add_floating_text(self.x, self.y - 12, f"{int(amount)}" if not is_crit else f"CRIT {int(amount)}!",
                                           COLOR_YELLOW if not is_crit else COLOR_MAGENTA, sz=11 if not is_crit else 14)
            particle_mgr.emit_sparks(self.x, self.y, 4, [COLOR_WHITE, COLOR_RED, COLOR_ORANGE])

        if self.health <= 0:
            self.alive = False
            sound_engine.play("explosion_sm")
            if particle_mgr:
                particle_mgr.emit_sparks(self.x, self.y, 16, [COLOR_RED, COLOR_ORANGE, COLOR_YELLOW, COLOR_WHITE])
                particle_mgr.emit_shockwave(self.x, self.y, 35.0, COLOR_ORANGE, spd=7.0, w=2)
            return False
        return True

    def update_base(self, dt: float):
        if self.hit_flash > 0: self.hit_flash -= dt
        if self.stun_timer > 0:
            self.stun_timer -= dt
            self.vx *= 0.88
            self.vy *= 0.88
            self.x += self.vx
            self.y += self.vy
            return False
        return True


class DroneKamikaze(EnemyBase):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, 22.0, 4.2, 12.0, 100)

    def update(self, dt: float, px: float, py: float, particle_mgr) -> list[Projectile]:
        if not self.update_base(dt): return []
        dx = px - self.x
        dy = py - self.y
        d = math.hypot(dx, dy)
        if d > 0:
            self.angle = math.atan2(dy, dx)
            self.vx += math.cos(self.angle) * 0.4
            self.vy += math.sin(self.angle) * 0.4
            spd = math.hypot(self.vx, self.vy)
            if spd > self.speed:
                self.vx = (self.vx / spd) * self.speed
                self.vy = (self.vy / spd) * self.speed
        self.x += self.vx
        self.y += self.vy
        return []

    def draw(self, canvas):
        ca = math.cos(self.angle)
        sa = math.sin(self.angle)
        pts = [(14, 0), (-10, 8), (-6, 0), (-10, -8)]
        world = [c for px, py in pts for c in (self.x + (px*ca - py*sa), self.y + (px*sa + py*ca))]
        col = COLOR_WHITE if self.hit_flash > 0 else COLOR_RED
        canvas.create_polygon(world, fill="#2b050b", outline=col, width=2)
        canvas.create_oval(self.x - 2, self.y - 2, self.x + 2, self.y + 2, fill=COLOR_YELLOW, outline="")


class ViperScout(EnemyBase):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, 50.0, 3.2, 15.0, 220)
        self.shoot_t = random.uniform(1.0, 2.2)
        self.orb_ang = random.uniform(0, 6.28)
        self.orb_dist = random.uniform(180, 250)

    def update(self, dt: float, px: float, py: float, particle_mgr) -> list[Projectile]:
        if not self.update_base(dt): return []
        self.shoot_t -= dt
        self.orb_ang += dt * 0.9

        tx = px + math.cos(self.orb_ang) * self.orb_dist
        ty = py + math.sin(self.orb_ang) * self.orb_dist
        dx = tx - self.x
        dy = ty - self.y
        d = math.hypot(dx, dy)
        if d > 5:
            ang = math.atan2(dy, dx)
            self.vx += math.cos(ang) * 0.35
            self.vy += math.sin(ang) * 0.35
            spd = math.hypot(self.vx, self.vy)
            if spd > self.speed:
                self.vx = (self.vx / spd) * self.speed
                self.vy = (self.vy / spd) * self.speed

        self.vx *= 0.96
        self.vy *= 0.96
        self.x += self.vx
        self.y += self.vy
        self.angle = math.atan2(py - self.y, px - self.x)

        shots = []
        if self.shoot_t <= 0:
            self.shoot_t = random.uniform(1.8, 2.6)
            sound_engine.play("laser")
            shots.append(Projectile(self.x, self.y, math.cos(self.angle) * 8.5, math.sin(self.angle) * 8.5,
                                    14.0, COLOR_ORANGE, r=3.5, is_player=False))
        return shots

    def draw(self, canvas):
        ca = math.cos(self.angle)
        sa = math.sin(self.angle)
        pts = [(16, 0), (-12, 12), (-4, 4), (-12, -12)]
        world = [c for px, py in pts for c in (self.x + (px*ca - py*sa), self.y + (px*sa + py*ca))]
        col = COLOR_WHITE if self.hit_flash > 0 else COLOR_ORANGE
        canvas.create_polygon(world, fill="#2b1505", outline=col, width=2)


class CruiserBattleship(EnemyBase):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, 140.0, 1.8, 22.0, 450)
        self.fire_t = 2.0

    def update(self, dt: float, px: float, py: float, particle_mgr) -> list[Projectile]:
        if not self.update_base(dt): return []
        self.fire_t -= dt
        dx = px - self.x
        dy = py - self.y
        d = math.hypot(dx, dy)
        if d > 140:
            self.angle = math.atan2(dy, dx)
            self.vx += math.cos(self.angle) * 0.18
            self.vy += math.sin(self.angle) * 0.18
            spd = math.hypot(self.vx, self.vy)
            if spd > self.speed:
                self.vx = (self.vx / spd) * self.speed
                self.vy = (self.vy / spd) * self.speed
        else:
            self.vx *= 0.90
            self.vy *= 0.90
        self.x += self.vx
        self.y += self.vy

        shots = []
        if self.fire_t <= 0:
            self.fire_t = 2.2
            sound_engine.play("plasma")
            base = math.atan2(py - self.y, px - self.x)
            for off in (-0.26, 0.0, 0.26):
                ang = base + off
                shots.append(Projectile(self.x, self.y, math.cos(ang) * 7.0, math.sin(ang) * 7.0,
                                        18.0, COLOR_RED, r=4.5, is_player=False))
        return shots

    def draw(self, canvas):
        col = COLOR_WHITE if self.hit_flash > 0 else COLOR_MAGENTA
        pts = [c for i in range(6) for c in (self.x + math.cos(self.angle + i * math.pi / 3) * self.radius,
                                             self.y + math.sin(self.angle + i * math.pi / 3) * self.radius)]
        canvas.create_polygon(pts, fill="#1a0026", outline=col, width=2)
        canvas.create_oval(self.x - 6, self.y - 6, self.x + 6, self.y + 6, fill=COLOR_RED, outline=COLOR_WHITE)


class StealthPhantom(EnemyBase):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, 65.0, 3.8, 14.0, 350)
        self.cloak_t = 3.0
        self.is_cloaked = False

    def update(self, dt: float, px: float, py: float, particle_mgr) -> list[Projectile]:
        if not self.update_base(dt): return []
        self.cloak_t -= dt
        if self.cloak_t <= 0:
            self.is_cloaked = not self.is_cloaked
            self.cloak_t = 2.5 if self.is_cloaked else 3.5

        dx = px - self.x
        dy = py - self.y
        d = math.hypot(dx, dy)
        self.angle = math.atan2(dy, dx)
        if d > 60:
            self.vx += math.cos(self.angle) * 0.4
            self.vy += math.sin(self.angle) * 0.4
            spd = math.hypot(self.vx, self.vy)
            max_s = self.speed * (1.4 if self.is_cloaked else 1.0)
            if spd > max_s:
                self.vx = (self.vx / spd) * max_s
                self.vy = (self.vy / spd) * max_s
        self.vx *= 0.95
        self.vy *= 0.95
        self.x += self.vx
        self.y += self.vy

        shots = []
        if not self.is_cloaked and random.random() < 0.02:
            sound_engine.play("shotgun")
            for _ in range(4):
                ang = self.angle + random.uniform(-0.35, 0.35)
                shots.append(Projectile(self.x, self.y, math.cos(ang) * 8.0, math.sin(ang) * 8.0,
                                        12.0, COLOR_PURPLE, r=3.0, is_player=False))
        return shots

    def draw(self, canvas):
        if self.is_cloaked:
            canvas.create_oval(self.x - self.radius, self.y - self.radius,
                               self.x + self.radius, self.y + self.radius, outline="#442255", width=1, dash=(3, 3))
            return
        ca = math.cos(self.angle)
        sa = math.sin(self.angle)
        pts = [(16, 0), (-12, 10), (-2, 0), (-12, -10)]
        world = [c for px, py in pts for c in (self.x + (px*ca - py*sa), self.y + (px*sa + py*ca))]
        col = COLOR_WHITE if self.hit_flash > 0 else COLOR_PURPLE
        canvas.create_polygon(world, fill="#1c072b", outline=col, width=2)

# ==============================================================================
# BOSS: DREADNOUGHT LEVIATHAN
# ==============================================================================
class ShieldNode:
    def __init__(self, ang_off: float, r: float = 75.0):
        self.angle = ang_off
        self.orbit_r = r
        self.x = 0.0
        self.y = 0.0
        self.health = 130.0
        self.max_health = 130.0
        self.radius = 12.0
        self.alive = True
        self.hit_flash = 0.0

    def update(self, bx: float, by: float, dt: float, mult: float):
        self.angle += dt * 1.5 * mult
        self.x = bx + math.cos(self.angle) * self.orbit_r
        self.y = by + math.sin(self.angle) * self.orbit_r
        if self.hit_flash > 0: self.hit_flash -= dt

    def take_damage(self, amount: float, is_crit: bool, particle_mgr) -> bool:
        self.health -= amount
        self.hit_flash = 0.12
        if particle_mgr:
            particle_mgr.add_floating_text(self.x, self.y - 12, f"{int(amount)}", COLOR_CYAN, sz=11)
        if self.health <= 0:
            self.alive = False
            sound_engine.play("explosion_sm")
            if particle_mgr:
                particle_mgr.emit_shockwave(self.x, self.y, 40.0, COLOR_CYAN, spd=7.0, w=2)
            return False
        return True

    def draw(self, canvas, bx: float, by: float):
        canvas.create_line(bx, by, self.x, self.y, fill="#004466", width=1, dash=(2, 2))
        col = COLOR_WHITE if self.hit_flash > 0 else COLOR_CYAN
        canvas.create_oval(self.x - self.radius, self.y - self.radius,
                          self.x + self.radius, self.y + self.radius, fill="#031a26", outline=col, width=2)


class DreadnoughtLeviathan:
    def __init__(self, x: float, y: float, wave_num: int = 5):
        self.x = x
        self.y = y
        self.target_y = 170.0
        self.radius = 48.0
        self.name = "DREADNOUGHT LEVIATHAN"
        scale = 1.0 + (wave_num - 5) * 0.25
        self.max_health = 1000.0 * scale
        self.health = self.max_health
        self.score_val = 5000
        self.alive = True
        self.hit_flash = 0.0
        self.shield_nodes = [ShieldNode(0.0), ShieldNode(2.094), ShieldNode(4.188)]
        self.phase_2 = False
        self.attack_timer = 2.0
        self.attack_mode = 0
        self.spiral_angle = 0.0
        self.spiral_sub_t = 0.0
        self.spiral_left = 0
        self.entering = True
        sound_engine.play("boss_alarm")

    def has_active_shields(self) -> bool:
        return any(n.alive for n in self.shield_nodes)

    def take_damage(self, amount: float, is_crit: bool, particle_mgr) -> bool:
        if self.has_active_shields():
            amount *= 0.25
            if particle_mgr:
                particle_mgr.add_floating_text(self.x, self.y - 30, "DEFLECTED", COLOR_SHIELD, sz=11)
        self.health -= amount
        self.hit_flash = 0.12
        if particle_mgr:
            particle_mgr.add_floating_text(self.x, self.y - 45, f"{int(amount)}" if not is_crit else f"CRIT {int(amount)}!",
                                           COLOR_YELLOW if not is_crit else COLOR_MAGENTA, sz=14)

        if not self.phase_2 and self.health <= self.max_health * 0.45:
            self.phase_2 = True
            sound_engine.play("boss_alarm")
            if particle_mgr:
                particle_mgr.emit_shockwave(self.x, self.y, 220.0, COLOR_RED, spd=12.0, w=5)
                particle_mgr.add_floating_text(self.x, self.y - 65, "!! ENRAGE OVERCLOCK !!", COLOR_RED, sz=20)

        if self.health <= 0:
            self.alive = False
            sound_engine.play("explosion_lg")
            if particle_mgr:
                particle_mgr.emit_shockwave(self.x, self.y, 240.0, COLOR_ORANGE, spd=14.0, w=5)
                particle_mgr.emit_sparks(self.x, self.y, 50, [COLOR_RED, COLOR_YELLOW, COLOR_MAGENTA, COLOR_WHITE])
            return False
        return True

    def update(self, dt: float, px: float, py: float, particle_mgr) -> tuple[list[Projectile], list]:
        if self.hit_flash > 0: self.hit_flash -= dt
        if self.entering:
            dy = self.target_y - self.y
            self.y += dy * dt * 2.0
            if abs(dy) < 4.0: self.entering = False

        mult = 1.6 if self.phase_2 else 1.0
        self.x = (SCREEN_WIDTH / 2) + math.sin(self.spiral_angle * 0.5) * (SCREEN_WIDTH * 0.32)
        for n in self.shield_nodes:
            if n.alive: n.update(self.x, self.y, dt, mult)

        shots = []
        self.attack_timer -= dt * mult
        if self.attack_timer <= 0:
            self.attack_mode = (self.attack_mode + 1) % 3
            self.attack_timer = 2.4 if not self.phase_2 else 1.5
            if self.attack_mode == 0:
                self.spiral_left = 24 if self.phase_2 else 16
                self.spiral_sub_t = 0.0
            elif self.attack_mode == 1:
                sound_engine.play("plasma")
                base = math.atan2(py - self.y, px - self.x)
                spreads = [-0.35, -0.18, 0.0, 0.18, 0.35] if self.phase_2 else [-0.25, 0.0, 0.25]
                for spr in spreads:
                    shots.append(Projectile(self.x, self.y + 20, math.cos(base + spr) * (8.5 if self.phase_2 else 7.0),
                                            math.sin(base + spr) * (8.5 if self.phase_2 else 7.0), 22.0, COLOR_RED, r=5.0, is_player=False))
            elif self.attack_mode == 2:
                sound_engine.play("shotgun")
                spokes = 14 if self.phase_2 else 10
                for i in range(spokes):
                    ang = (i / spokes) * (2 * math.pi)
                    shots.append(Projectile(self.x, self.y, math.cos(ang) * 6.2, math.sin(ang) * 6.2, 16.0, COLOR_YELLOW, r=4.0, is_player=False))

        if self.spiral_left > 0:
            self.spiral_sub_t -= dt
            if self.spiral_sub_t <= 0:
                self.spiral_sub_t = 0.06
                self.spiral_left -= 1
                self.spiral_angle += 0.42
                for off in (0.0, math.pi):
                    ang = self.spiral_angle + off
                    shots.append(Projectile(self.x, self.y, math.cos(ang) * 7.0, math.sin(ang) * 7.0,
                                            14.0, COLOR_RED if self.phase_2 else COLOR_MAGENTA, r=3.5, is_player=False))
        return shots, []

    def draw(self, canvas):
        for n in self.shield_nodes:
            if n.alive: n.draw(canvas, self.x, self.y)

        if self.has_active_shields():
            canvas.create_oval(self.x - (self.radius + 18), self.y - (self.radius + 18),
                               self.x + (self.radius + 18), self.y + (self.radius + 18),
                               outline=COLOR_SHIELD, width=2, dash=(4, 4))

        col = COLOR_WHITE if self.hit_flash > 0 else (COLOR_RED if self.phase_2 else COLOR_MAGENTA)
        pts = [
            self.x, self.y + 45, self.x + 35, self.y + 15, self.x + 55, self.y - 20,
            self.x + 25, self.y - 38, self.x, self.y - 25, self.x - 25, self.y - 38,
            self.x - 55, self.y - 20, self.x - 35, self.y + 15
        ]
        canvas.create_polygon(pts, fill="#1c0722", outline=col, width=3)
        canvas.create_oval(self.x - 12, self.y - 6, self.x + 12, self.y + 18,
                          fill=COLOR_RED if self.phase_2 else COLOR_YELLOW, outline=COLOR_WHITE, width=2)

# ==============================================================================
# UPGRADES / ROGUE-LITE PROGRESSION
# ==============================================================================
class UpgradeItem:
    def __init__(self, item_id: str, name: str, icon: str, base: int, max_l: int, desc: str, col: str):
        self.item_id = item_id
        self.name = name
        self.icon = icon
        self.base_cost = base
        self.level = 0
        self.max_level = max_l
        self.description = desc
        self.color = col

    @property
    def cost(self) -> int:
        return int(self.base_cost * (1.6 ** self.level)) if self.level < self.max_level else 999999

    @property
    def is_maxed(self) -> bool:
        return self.level >= self.max_level


class UpgradeManager:
    def __init__(self):
        self.upgrades = [
            UpgradeItem("hull", "HULL REINFORCEMENT", "🛡️", 40, 5, "+25 Max Health & instant repair.", COLOR_GREEN),
            UpgradeItem("shield", "PLASMA SHIELD ARRAY", "⚡", 50, 5, "+20 Max Shield & faster regen.", COLOR_CYAN),
            UpgradeItem("speed", "HYPER THRUSTERS", "🚀", 45, 4, "+15% Speed & reduced dash cd.", COLOR_YELLOW),
            UpgradeItem("magnet", "QUANTUM VACUUM", "🧲", 30, 4, "+60px Scrap magnet pickup range.", COLOR_ORANGE),
            UpgradeItem("crit", "CRITICAL OVERCLOCK", "🎯", 60, 5, "+8% Crit Chance & +0.3x Mult.", COLOR_MAGENTA),
            UpgradeItem("flak_unlock", "UNLOCK: SCATTER FLAK", "💥", 90, 1, "Unlocks Weapon 3: 6-pellet flak.", COLOR_YELLOW),
            UpgradeItem("homing_unlock", "UNLOCK: HOMING PODS", "🛰️", 140, 1, "Unlocks Weapon 4: Target-seeking pods.", COLOR_GREEN),
            UpgradeItem("singularity_unlock", "UNLOCK: SINGULARITY", "🌌", 220, 1, "Unlocks Weapon 5: Gravity-vortex.", COLOR_PURPLE),
            UpgradeItem("emp_cell", "EMP SHOCKWAVE CELL", "💣", 100, 3, "+1 Max EMP charge & instant refill.", COLOR_PURPLE),
        ]

    def purchase(self, item_id: str, player, scrap: int, particle_mgr=None) -> tuple[bool, int, str]:
        item = next((u for u in self.upgrades if u.item_id == item_id), None)
        if not item or item.is_maxed:
            return False, scrap, "Upgrade unavailable or maxed!"
        if scrap < item.cost:
            return False, scrap, f"Need {item.cost - scrap} more Scrap!"

        scrap -= item.cost
        item.level += 1
        sound_engine.play("powerup")

        if item.item_id == "hull":
            player.max_health += 25
            player.health = min(player.max_health, player.health + 35)
        elif item.item_id == "shield":
            player.max_shield += 20
            player.shield = player.max_shield
            player.shield_regen_rate += 4.0
        elif item.item_id == "speed": player.speed += 0.8
        elif item.item_id == "magnet": player.magnet_range += 60.0
        elif item.item_id == "crit":
            player.crit_chance += 0.08
            player.crit_multiplier += 0.3
        elif item.item_id == "flak_unlock":
            WEAPONS_DATA["flak"].unlocked = True
            if "flak" not in player.unlocked_weapons: player.unlocked_weapons.append("flak")
        elif item.item_id == "homing_unlock":
            WEAPONS_DATA["homing"].unlocked = True
            if "homing" not in player.unlocked_weapons: player.unlocked_weapons.append("homing")
        elif item.item_id == "singularity_unlock":
            WEAPONS_DATA["singularity"].unlocked = True
            if "singularity" not in player.unlocked_weapons: player.unlocked_weapons.append("singularity")
        elif item.item_id == "emp_cell":
            player.max_emp_charges += 1
            player.emp_charges = player.max_emp_charges

        return True, scrap, f"Upgraded {item.name} to Lv {item.level}!"

# ==============================================================================
# HUD & TELEMETRY
# ==============================================================================
class HUD:
    def draw(self, canvas, player, score: int, wave: int, scrap: int, combo: int, combo_t: float, boss=None, sound_enabled: bool = True):
        bx, by = 20, 20
        bw, bh = 180, 12
        canvas.create_rectangle(bx - 8, by - 8, bx + bw + 55, by + 60, fill="#090c1a", outline="#1c2544")

        # Health
        h_ratio = max(0.0, min(1.0, player.health / player.max_health)) if player.max_health > 0 else 0
        canvas.create_rectangle(bx, by, bx + bw, by + bh, fill="#2b0d13", outline="")
        canvas.create_rectangle(bx, by, bx + (bw * h_ratio), by + bh, fill=COLOR_RED, outline="")
        canvas.create_text(bx + bw + 8, by + bh/2, text=f"HP {int(player.health)}", fill=COLOR_WHITE, font=("Consolas", 10, "bold"), anchor="w")

        # Shield
        s_ratio = max(0.0, min(1.0, player.shield / player.max_shield)) if player.max_shield > 0 else 0
        sy = by + 18
        canvas.create_rectangle(bx, sy, bx + bw, sy + bh, fill="#081a2e", outline="")
        canvas.create_rectangle(bx, sy, bx + (bw * s_ratio), sy + bh, fill=COLOR_CYAN, outline="")
        canvas.create_text(bx + bw + 8, sy + bh/2, text=f"SH {int(player.shield)}", fill=COLOR_CYAN, font=("Consolas", 10, "bold"), anchor="w")

        # Reactor
        e_ratio = max(0.0, min(1.0, player.energy / player.max_energy)) if player.max_energy > 0 else 0
        ey = by + 36
        col = COLOR_ORANGE if player.overclock_timer > 0 else COLOR_YELLOW
        canvas.create_rectangle(bx, ey, bx + bw, ey + 6, fill="#221b06", outline="")
        canvas.create_rectangle(bx, ey, bx + (bw * e_ratio), ey + 6, fill=col, outline="")

        # Top Center (Wave / Boss)
        cx = SCREEN_WIDTH / 2
        if boss and boss.alive:
            bbw = 460
            b_ratio = max(0.0, min(1.0, boss.health / boss.max_health)) if boss.max_health > 0 else 0
            b_col = COLOR_RED if boss.phase_2 else COLOR_MAGENTA
            canvas.create_rectangle(cx - bbw/2 - 4, 18, cx + bbw/2 + 4, 38, fill="#120412", outline=b_col, width=2)
            canvas.create_rectangle(cx - bbw/2, 22, cx - bbw/2 + bbw * b_ratio, 34, fill=b_col, outline="")
            canvas.create_text(cx, 10, text=f"⚠️ {boss.name} ⚠️", fill=b_col, font=("Impact", 13), anchor="center")
        else:
            canvas.create_text(cx, 24, text=f"— SECTOR WAVE {wave} —", fill=COLOR_CYAN, font=("Impact", 16), anchor="center")
            canvas.create_text(cx, 44, text="[B] TECH BAY  |  [P/ESC] PAUSE MENU", fill="#557799", font=("Consolas", 9, "bold"), anchor="center")

        # Top Right (Score & Scrap)
        rx = SCREEN_WIDTH - 20
        canvas.create_text(rx, 20, text=f"SCORE {score:07d}", fill=COLOR_WHITE, font=("Impact", 18), anchor="e")
        canvas.create_text(rx, 44, text=f"⚡ SCRAP {scrap}", fill=COLOR_YELLOW, font=("Consolas", 13, "bold"), anchor="e")

        if combo > 1:
            c_col = COLOR_ORANGE if combo < 4 else COLOR_MAGENTA
            canvas.create_text(rx, 68, text=f"COMBO x{combo}!", fill=c_col, font=("Impact", 14), anchor="e")

        # Bottom Dock (Weapons & Abilities)
        cy = SCREEN_HEIGHT - 38
        w_keys = ["pulse", "twin", "flak", "homing", "singularity"]
        slot_w = 70
        start_x = cx - (len(w_keys) * (slot_w + 8)) / 2

        for i, wk in enumerate(w_keys):
            w_def = WEAPONS_DATA[wk]
            sx = start_x + i * (slot_w + 8)
            is_act = (player.current_weapon == wk)
            is_unl = (wk in player.unlocked_weapons)
            b_col = w_def.color if is_act else ("#2a3558" if is_unl else "#141829")
            canvas.create_rectangle(sx, cy - 20, sx + slot_w, cy + 18, fill="#0e152e" if is_unl else "#060814", outline=b_col, width=2 if is_act else 1)
            canvas.create_text(sx + 5, cy - 16, text=f"[{i+1}]", fill="#445577", font=("Consolas", 8, "bold"), anchor="nw")
            canvas.create_text(sx + slot_w/2, cy + 2, text=w_def.name.split()[0] if is_unl else "LOCKED",
                               fill=COLOR_WHITE if is_act else ("#7888aa" if is_unl else "#444b66"), font=("Consolas", 9, "bold"), anchor="center")

        dash_ready = (player.dash_cooldown <= 0)
        canvas.create_text(start_x - 90, cy, text="DASH [READY]" if dash_ready else f"DASH [{player.dash_cooldown:.1f}s]",
                           fill=COLOR_CYAN if dash_ready else "#446677", font=("Consolas", 10, "bold"), anchor="e")

        emp_pips = " ".join(["[Ω]" for _ in range(player.emp_charges)])
        canvas.create_text(start_x + len(w_keys) * (slot_w + 8) + 20, cy, text=f"EMP (Q): {emp_pips}",
                           fill=COLOR_PURPLE, font=("Consolas", 10, "bold"), anchor="w")

# ==============================================================================
# INTERACTIVE BUTTON SYSTEM
# ==============================================================================
class Button:
    def __init__(self, btn_id: str, x: float, y: float, w: float, h: float,
                 text: str, callback, col: str = COLOR_CYAN, subtext: str = "", enabled: bool = True, style: str = None):
        self.btn_id = btn_id
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.text = text
        self.subtext = subtext
        self.callback = callback
        self.col = col
        self.enabled = enabled
        self.hovered = False
        self.style = style  # e.g., "p3_ribbon"

    def contains(self, mx: float, my: float) -> bool:
        if self.style == "p3_ribbon":
            # Slightly angled generous hitbox matching p3 ribbon geometry
            return (self.x - 30 <= mx <= self.x + self.w + 60) and (self.y - 4 <= my <= self.y + self.h + 4)
        return (self.x <= mx <= self.x + self.w) and (self.y <= my <= self.y + self.h)

    def draw(self, canvas):
        if self.style == "p3_ribbon":
            self._draw_p3_ribbon(canvas)
            return
        if not self.enabled:
            border = "#222a44"
            fill = "#090c18"
            txt_col = "#445566"
        elif self.hovered:
            border = COLOR_WHITE
            fill = "#1b254b"
            txt_col = COLOR_WHITE
        else:
            border = self.col
            fill = "#0e1530"
            txt_col = self.col

        canvas.create_rectangle(
            self.x, self.y, self.x + self.w, self.y + self.h,
            fill=fill, outline=border, width=2 if (self.hovered and self.enabled) else 1
        )

        cx = self.x + self.w / 2
        if self.subtext:
            canvas.create_text(
                cx, self.y + self.h * 0.35,
                text=self.text, fill=txt_col, font=("Impact", 12), anchor="center"
            )
            canvas.create_text(
                cx, self.y + self.h * 0.72,
                text=self.subtext, fill="#7799bb" if self.enabled else "#334455",
                font=("Consolas", 8), anchor="center"
            )
        else:
            canvas.create_text(
                cx, self.y + self.h / 2,
                text=self.text, fill=txt_col, font=("Impact", 12), anchor="center"
            )

    def _draw_p3_ribbon(self, canvas):
        """Render iconic Persona 3 slanted parallelogram ribbon with sliding invert."""
        offset = 26 if self.hovered else 0
        slant = 22
        bx = self.x + offset
        by = self.y
        bw = self.w
        bh = self.h

        # Parallelogram polygon points
        pts = [
            bx + slant, by,
            bx + bw + slant, by,
            bx + bw - slant, by + bh,
            bx - slant, by + bh
        ]

        if not self.enabled:
            fill_col = "#040814"
            outline_col = "#152238"
            txt_col = "#384a66"
            badge_bg = "#0d1424"
            badge_txt = "#384a66"
        elif self.hovered:
            fill_col = "#00e5ff"
            outline_col = "#ffffff"
            txt_col = "#010614"
            badge_bg = "#ffffff"
            badge_txt = "#010614"
        else:
            fill_col = "#05132d"
            outline_col = "#00a2e8"
            txt_col = "#ffffff"
            badge_bg = "#0b2552"
            badge_txt = "#00d2ff"

        # Shadow ribbon
        shadow_pts = [
            bx + slant + 4, by + 4,
            bx + bw + slant + 4, by + 4,
            bx + bw - slant + 4, by + bh + 4,
            bx - slant + 4, by + bh + 4
        ]
        canvas.create_polygon(shadow_pts, fill="#01040a", outline="")

        # Main ribbon
        canvas.create_polygon(pts, fill=fill_col, outline=outline_col, width=2 if self.hovered else 1)

        # Badge box if needed (not used currently)
        if getattr(self, "badge", None):
            badge_w = 46
            badge_pts = [
                bx + slant + 2, by + 2,
                bx + slant + badge_w, by + 2,
                bx + slant + badge_w - 7, by + bh - 2,
                bx - slant + 14, by + bh - 2
            ]
            canvas.create_polygon(badge_pts, fill=badge_bg, outline=outline_col, width=1)
            canvas.create_text(
                bx + slant + badge_w / 2 - 4, by + bh / 2,
                text=self.badge, fill=badge_txt, font=("Impact", 15, "bold"), anchor="center"
            )

        # Chevron cursor on hover
        if self.hovered:
            arrow_x = bx - slant - 16
            arrow_pts = [
                arrow_x - 4, by + bh * 0.22,
                arrow_x + 10, by + bh * 0.5,
                arrow_x - 4, by + bh * 0.78
            ]
            canvas.create_polygon(arrow_pts, fill="#00e5ff", outline="#ffffff", width=1)

        # Main text & subtext
        text_x = bx + slant + (58 if getattr(self, "badge", None) else 22)
        canvas.create_text(
            text_x, by + bh * 0.34,
            text=self.text, fill=txt_col, font=("Impact", 16), anchor="w"
        )
        if self.subtext:
            sub_col = "#003355" if self.hovered else "#5599cc"
            canvas.create_text(
                text_x, by + bh * 0.74,
                text=self.subtext, fill=sub_col, font=("Consolas", 8, "bold"), anchor="w"
            )
    def __init__(self, btn_id: str, x: float, y: float, w: float, h: float,
                 text: str, callback, col: str = COLOR_CYAN, subtext: str = "", enabled: bool = True):
        self.btn_id = btn_id
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.text = text
        self.subtext = subtext
        self.callback = callback
        self.col = col
        self.enabled = enabled
        self.hovered = False

    def contains(self, mx: float, my: float) -> bool:
        return (self.x <= mx <= self.x + self.w) and (self.y <= my <= self.y + self.h)

    def draw(self, canvas):
        if not self.enabled:
            border = "#222a44"
            fill = "#090c18"
            txt_col = "#445566"
        elif self.hovered:
            border = COLOR_WHITE
            fill = "#1b254b"
            txt_col = COLOR_WHITE
        else:
            border = self.col
            fill = "#0e1530"
            txt_col = self.col

        canvas.create_rectangle(
            self.x, self.y, self.x + self.w, self.y + self.h,
            fill=fill, outline=border, width=2 if (self.hovered and self.enabled) else 1
        )

        cx = self.x + self.w / 2
        if self.subtext:
            canvas.create_text(
                cx, self.y + self.h * 0.35,
                text=self.text, fill=txt_col, font=("Impact", 12), anchor="center"
            )
            canvas.create_text(
                cx, self.y + self.h * 0.72,
                text=self.subtext, fill="#7799bb" if self.enabled else "#334455",
                font=("Consolas", 8), anchor="center"
            )
        else:
            canvas.create_text(
                cx, self.y + self.h / 2,
                text=self.text, fill=txt_col, font=("Impact", 12), anchor="center"
            )

# ==============================================================================
# MAIN ENGINE
# ==============================================================================
    def _draw_menu_background(self):
        """Draw the Persona‑3 inspired background for the main menu.
        Includes slanted background bands, a dark‑hour lunar dial, and floating shards.
        """
        # ----- Slanted background bands -----
        band_h = SCREEN_HEIGHT // 6
        slant = 22
        colors = ["#01040a", "#001824", "#032a4b"]
        for i, col in enumerate(colors):
            y = i * band_h
            pts = [
                0 + slant, y,
                SCREEN_WIDTH + slant, y,
                SCREEN_WIDTH - slant, y + band_h,
                -slant, y + band_h
            ]
            self.canvas.create_polygon(pts, fill=col, outline="")
        # ----- Dark‑Hour lunar dial (centered) -----
        cx, cy = SCREEN_WIDTH // 2, 160
        self.canvas.create_oval(cx-80, cy-80, cx+80, cy+80,
                                fill="#071a3d", outline="#00a2e8", width=3)
        # ----- Floating moon‑light shards (reuse self.p3_shards) -----
        for s in self.p3_shards:
            s["y"] -= s["speed"]
            if s["y"] < -10:
                s["y"] = SCREEN_HEIGHT + 10
                s["x"] = random.uniform(0, SCREEN_WIDTH)
            self.canvas.create_oval(
                s["x"], s["y"],
                s["x"] + s["size"], s["y"] + s["size"],
                fill=s["color"], outline=""
            )
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("CYBER NOVA: ODYSSEY")
        self.root.geometry(f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        self.root.resizable(False, False)
        self.root.configure(bg=COLOR_BG)

        self.root.focus_force()

        self.canvas = tk.Canvas(root, width=SCREEN_WIDTH, height=SCREEN_HEIGHT, bg=COLOR_BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.state = STATE_MENU
        self.difficulty = "pilot"
        self.keys = {}
        self.mouse_x = SCREEN_WIDTH / 2
        self.mouse_y = SCREEN_HEIGHT / 2
        self.mouse_down = False

        self.active_buttons: list[Button] = []
        self.toast_message = ""
        self.toast_timer = 0.0
        self.toast_color = COLOR_YELLOW

        self.starfield = Starfield(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.particle_mgr = ParticleManager()
        self.hud = HUD()
        self.upgrade_mgr = UpgradeManager()

        self.player = None
        self.enemies = []
        self.boss = None
        self.projectiles = []
        self.pickups = []

        self.score = 0
        self.scrap = 0
        self.wave = 1
        self.kills = 0
        self.total_scrap_earned = 0
        self.combo = 0
        self.combo_timer = 0.0

        self.wave_in_progress = False
        self.wave_enemies_to_spawn = []
        self.spawn_timer = 0.0
        self.wave_clear_timer = 0.0

        self.shake_mag = 0.0
        self.shake_dx = 0.0
        self.shake_dy = 0.0

        self.selected_upg = 0
        self.upgrade_msg = ""
        self.is_new_high = False

        self._bind_events()
        self.last_time = time.perf_counter()
        self.tick()

    def show_toast(self, message: str, color: str = COLOR_YELLOW, duration: float = 2.5):
        self.toast_message = message
        self.toast_color = color
        self.toast_timer = duration

    def _bind_events(self):
        self.root.bind("<KeyPress>", self._on_key_down)
        self.root.bind("<KeyRelease>", self._on_key_up)
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<ButtonPress-1>", self._on_left_press)
        self.canvas.bind("<ButtonRelease-1>", self._on_left_release)
        self.canvas.bind("<ButtonPress-3>", self._on_right_click)
        self.canvas.bind("<MouseWheel>", self._on_wheel)

    def _on_key_down(self, event):
        self.root.focus_set()
        k = event.keysym.lower()
        self.keys[k] = True

        if self.state == STATE_MENU:
            if k in ("return", "space"): self.start_run()
        elif self.state == STATE_SAVES_MENU:
            if k in ("escape", "backspace"):
                self.state = STATE_MENU
        elif self.state == STATE_PLAYING:
            if k in ("1", "2", "3", "4", "5"):
                wlist = ["pulse", "twin", "flak", "homing", "singularity"]
                idx = int(k) - 1
                if idx < len(wlist) and wlist[idx] in self.player.unlocked_weapons:
                    self.player.current_weapon = wlist[idx]
            elif k in ("q", "f"):
                self.player.trigger_emp(self.particle_mgr, self.enemies, self.projectiles)
            elif k in ("space", "shift_l", "e"):
                self.player.trigger_dash(self.particle_mgr)
            elif k == "b":
                self.state = STATE_UPGRADES
                self.upgrade_msg = "SELECT AN UPGRADE TO INSTALL"
            elif k in ("p", "escape"):
                self.pause_game()
            elif k == "m":
                sound_engine.toggle_sound()
                self.show_toast("SFX: ON" if sound_engine.enabled else "SFX: MUTED")
        elif self.state == STATE_PAUSED:
            if k in ("p", "escape", "space", "return"):
                self.resume_game()
            elif k == "s":
                self.state = STATE_PAUSE_SAVE
            elif k == "m":
                sound_engine.toggle_sound()
                self.show_toast("SFX: ON" if sound_engine.enabled else "SFX: MUTED")
        elif self.state == STATE_PAUSE_SAVE:
            if k in ("escape", "backspace"):
                self.state = STATE_PAUSED
        elif self.state == STATE_UPGRADES:
            if k in ("b", "escape"):
                self.state = STATE_PLAYING
            elif k in ("up", "w"):
                self.selected_upg = (self.selected_upg - 1) % len(self.upgrade_mgr.upgrades)
            elif k in ("down", "s"):
                self.selected_upg = (self.selected_upg + 1) % len(self.upgrade_mgr.upgrades)
            elif k in ("return", "space", "e"):
                self._buy_selected_upgrade()
        elif self.state == STATE_CONTROLS:
            if k in ("return", "space", "escape", "b"):
                self.state = STATE_MENU
        elif self.state == STATE_GAMEOVER:
            if k in ("return", "space"):
                self.start_run()
            elif k == "escape":
                self.state = STATE_MENU

    def _on_key_up(self, event):
        self.keys[event.keysym.lower()] = False

    def _on_mouse_move(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y

        hovering_any = False
        for btn in self.active_buttons:
            is_in = btn.contains(self.mouse_x, self.mouse_y)
            btn.hovered = is_in
            if is_in and btn.enabled:
                hovering_any = True

        self.canvas.config(cursor="hand2" if hovering_any else "")

    def _on_left_press(self, event):
        self.root.focus_set()
        self.mouse_down = True

        clicked_button = False
        for btn in list(self.active_buttons):
            if btn.contains(event.x, event.y):
                if btn.enabled and btn.callback:
                    clicked_button = True
                    btn.callback()
                break

        if clicked_button:
            return

        if self.state == STATE_GAMEOVER:
            self.start_run()

    def _on_left_release(self, event):
        self.mouse_down = False

    def _on_right_click(self, event):
        if self.state == STATE_PLAYING and self.player:
            self.player.trigger_dash(self.particle_mgr)

    def _on_wheel(self, event):
        if self.state == STATE_PLAYING and self.player:
            wlist = [w for w in ["pulse", "twin", "flak", "homing", "singularity"] if w in self.player.unlocked_weapons]
            if len(wlist) > 1:
                cur = wlist.index(self.player.current_weapon)
                self.player.current_weapon = wlist[(cur + (1 if event.delta < 0 else -1)) % len(wlist)]

    def pause_game(self):
        self.state = STATE_PAUSED
        self.show_toast("GAME PAUSED", COLOR_CYAN, duration=1.5)
        self.root.focus_set()

    def resume_game(self):
        self.state = STATE_PLAYING
        self.root.focus_set()
        self.show_toast("SYSTEMS RESUMED", COLOR_GREEN, duration=1.2)

    def cycle_difficulty(self):
        keys = list(DIFFICULTIES.keys())
        idx = keys.index(self.difficulty)
        self.difficulty = keys[(idx + 1) % len(keys)]
        d = DIFFICULTIES[self.difficulty]
        self.show_toast(f"DIFFICULTY: {d['name']}", d['color'], duration=2.0)

    def add_screen_shake(self, amt: float):
        self.shake_mag = min(22.0, self.shake_mag + amt)

    def export_state(self) -> dict:
        return {
            "difficulty": self.difficulty,
            "wave": self.wave,
            "score": self.score,
            "scrap": self.scrap,
            "kills": self.kills,
            "total_scrap_earned": self.total_scrap_earned,
            "player": {
                "health": self.player.health,
                "max_health": self.player.max_health,
                "shield": self.player.shield,
                "max_shield": self.player.max_shield,
                "shield_regen_rate": self.player.shield_regen_rate,
                "speed": self.player.speed,
                "magnet_range": self.player.magnet_range,
                "crit_chance": self.player.crit_chance,
                "crit_multiplier": self.player.crit_multiplier,
                "emp_charges": self.player.emp_charges,
                "max_emp_charges": self.player.max_emp_charges,
                "current_weapon": self.player.current_weapon,
                "unlocked_weapons": list(self.player.unlocked_weapons)
            },
            "upgrades": {u.item_id: u.level for u in self.upgrade_mgr.upgrades}
        }

    def import_state(self, data: dict):
        self.difficulty = data.get("difficulty", "pilot")
        self.wave = data.get("wave", 1)
        self.score = data.get("score", 0)
        self.scrap = data.get("scrap", 0)
        self.kills = data.get("kills", 0)
        self.total_scrap_earned = data.get("total_scrap_earned", 0)
        self.combo = 0
        self.combo_timer = 0.0

        p_data = data.get("player", {})
        self.player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.75)
        self.player.health = p_data.get("health", 100)
        self.player.max_health = p_data.get("max_health", 100)
        self.player.shield = p_data.get("shield", 60)
        self.player.max_shield = p_data.get("max_shield", 60)
        self.player.shield_regen_rate = p_data.get("shield_regen_rate", 15.0)
        self.player.speed = p_data.get("speed", 5.5)
        self.player.magnet_range = p_data.get("magnet_range", 140.0)
        self.player.crit_chance = p_data.get("crit_chance", 0.10)
        self.player.crit_multiplier = p_data.get("crit_multiplier", 1.8)
        self.player.emp_charges = p_data.get("emp_charges", 2)
        self.player.max_emp_charges = p_data.get("max_emp_charges", 4)
        self.player.current_weapon = p_data.get("current_weapon", "pulse")
        self.player.unlocked_weapons = p_data.get("unlocked_weapons", ["pulse", "twin"])

        for w in self.player.unlocked_weapons:
            if w in WEAPONS_DATA: WEAPONS_DATA[w].unlocked = True

        self.upgrade_mgr = UpgradeManager()
        upg_levels = data.get("upgrades", {})
        for u in self.upgrade_mgr.upgrades:
            if u.item_id in upg_levels: u.level = upg_levels[u.item_id]

        self.enemies.clear()
        self.boss = None
        self.projectiles.clear()
        self.pickups.clear()
        self.particle_mgr.clear()

        self.state = STATE_PLAYING
        self._init_wave(self.wave)
        self.show_toast(f"RUN RESTORED: WAVE {self.wave}", COLOR_GREEN, duration=2.5)

    def save_to_slot(self, slot_id: str):
        if not self.player or self.player.health <= 0: return
        ok = save_manager.save_slot(slot_id, self.export_state())
        sm = save_manager.get_slot_metadata(slot_id)
        if ok:
            self.show_toast(f"SAVED TO {sm['name']}!", COLOR_GREEN, duration=2.5)
            sound_engine.play("pickup")
            self.state = STATE_PAUSED
        else:
            self.show_toast("SAVE FAILED TO WRITE", COLOR_RED, duration=2.5)

    def load_from_slot(self, slot_id: str):
        data = save_manager.load_slot(slot_id)
        if data: self.import_state(data)
        else: self.show_toast(f"NO DATA IN SLOT {slot_id.upper()}", COLOR_RED, duration=2.0)

    def delete_slot(self, slot_id: str):
        save_manager.delete_slot(slot_id)
        self.show_toast("SLOT CLEARED", COLOR_YELLOW, duration=1.5)

    def start_run(self):
        self.player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.75)
        self.upgrade_mgr = UpgradeManager()
        self.enemies.clear()
        self.boss = None
        self.projectiles.clear()
        self.pickups.clear()
        self.particle_mgr.clear()

        self.score = 0
        self.scrap = 0
        self.wave = 1
        self.kills = 0
        self.total_scrap_earned = 0
        self.combo = 0
        self.combo_timer = 0.0
        self.is_new_high = False

        self.state = STATE_PLAYING
        self._init_wave(self.wave)
        save_manager.save_slot("auto", self.export_state())

    def _init_wave(self, wn: int):
        self.wave_in_progress = True
        self.wave_enemies_to_spawn.clear()
        self.particle_mgr.add_floating_text(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 40, f"SECTOR WAVE {wn}", COLOR_CYAN, sz=24)
        self.starfield.trigger_warp()

        if wn % 5 == 0:
            self.boss = DreadnoughtLeviathan(SCREEN_WIDTH / 2, -60, wn)
            diff_cfg = DIFFICULTIES[self.difficulty]
            self.boss.max_health *= diff_cfg["hp_mult"]
            self.boss.health = self.boss.max_health
        else:
            self.boss = None
            drones = 6 + wn * 3
            vipers = 2 + wn * 2
            cruisers = max(0, wn - 2)
            phantoms = max(0, wn - 3)
            for _ in range(drones): self.wave_enemies_to_spawn.append(DroneKamikaze)
            for _ in range(vipers): self.wave_enemies_to_spawn.append(ViperScout)
            for _ in range(cruisers): self.wave_enemies_to_spawn.append(CruiserBattleship)
            for _ in range(phantoms): self.wave_enemies_to_spawn.append(StealthPhantom)
            random.shuffle(self.wave_enemies_to_spawn)

        self.spawn_timer = 1.0

    def _spawn_next(self):
        if not self.wave_enemies_to_spawn: return
        cls = self.wave_enemies_to_spawn.pop()
        side = random.choice(["top", "left", "right"])
        if side == "top": x, y = random.uniform(50, SCREEN_WIDTH - 50), -30
        elif side == "left": x, y = -30, random.uniform(50, SCREEN_HEIGHT * 0.6)
        else: x, y = SCREEN_WIDTH + 30, random.uniform(50, SCREEN_HEIGHT * 0.6)

        enemy = cls(x, y)
        diff_cfg = DIFFICULTIES[self.difficulty]
        enemy.health *= diff_cfg["hp_mult"]
        enemy.max_health = enemy.health
        enemy.speed *= diff_cfg["spd_mult"]
        self.enemies.append(enemy)

    def _drop_loot(self, x: float, y: float, enemy_t: str = ""):
        diff_cfg = DIFFICULTIES[self.difficulty]
        amt = random.randint(2, 4)
        if "Cruiser" in enemy_t: amt = random.randint(6, 10)
        elif "Leviathan" in enemy_t: amt = random.randint(25, 40)
        amt = max(1, int(amt * diff_cfg["scrap_mult"]))

        for _ in range(amt): self.pickups.append(Pickup(x, y, "scrap", 1))

        roll = random.random()
        if roll < 0.10: self.pickups.append(Pickup(x, y, "health", 30))
        elif roll < 0.18: self.pickups.append(Pickup(x, y, "shield", 40))
        elif roll < 0.24: self.pickups.append(Pickup(x, y, "overclock", 1))
        elif roll < 0.28: self.pickups.append(Pickup(x, y, "emp", 1))

    def _buy_selected_upgrade(self):
        item = self.upgrade_mgr.upgrades[self.selected_upg]
        ok, rem, msg = self.upgrade_mgr.purchase(item.item_id, self.player, self.scrap, self.particle_mgr)
        self.scrap = rem
        self.upgrade_msg = msg

    def update(self, dt: float):
        if self.toast_timer > 0: self.toast_timer -= dt

        vx = self.player.vx if self.player else 0.0
        vy = self.player.vy if self.player else 0.0
        self.starfield.update(vx, vy)
        self.particle_mgr.update()

        if self.shake_mag > 0:
            self.shake_dx = random.uniform(-self.shake_mag, self.shake_mag)
            self.shake_dy = random.uniform(-self.shake_mag, self.shake_mag)
            self.shake_mag = max(0.0, self.shake_mag - dt * 28.0)
        else:
            self.shake_dx, self.shake_dy = 0.0, 0.0

        if self.state != STATE_PLAYING: return

        if self.combo > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0: self.combo = 0

        self.player.handle_input(self.keys, self.mouse_x, self.mouse_y)
        self.player.update(dt, self.particle_mgr)

        if self.mouse_down or self.keys.get("space"):
            self.projectiles.extend(self.player.fire(self.particle_mgr))

        if self.wave_in_progress:
            if self.wave_enemies_to_spawn:
                self.spawn_timer -= dt
                if self.spawn_timer <= 0:
                    self.spawn_timer = max(0.35, 1.2 - (self.wave * 0.08))
                    self._spawn_next()
            elif not self.enemies and (not self.boss or not self.boss.alive):
                self.wave_in_progress = False
                self.wave_clear_timer = 3.0
                sound_engine.play("powerup")
                self.particle_mgr.add_floating_text(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20, f"WAVE {self.wave} CLEARED!", COLOR_GREEN, sz=22)
                # Auto-save to Slot 1 (Auto-Save)
                save_manager.save_slot("auto", self.export_state())
        else:
            self.wave_clear_timer -= dt
            if self.wave_clear_timer <= 0:
                self.wave += 1
                self._init_wave(self.wave)

        if self.boss and self.boss.alive:
            b_shots, mins = self.boss.update(dt, self.player.x, self.player.y, self.particle_mgr)
            self.projectiles.extend(b_shots)
            self.enemies.extend(mins)

        for e in self.enemies:
            if e.alive: self.projectiles.extend(e.update(dt, self.player.x, self.player.y, self.particle_mgr))

        for p in self.projectiles:
            if p.alive:
                if isinstance(p, HomingMissile):
                    targets = list(self.enemies) + ([self.boss] if self.boss and self.boss.alive else [])
                    p.update_homing(targets, self.particle_mgr, SCREEN_WIDTH, SCREEN_HEIGHT)
                elif isinstance(p, SingularityVortex):
                    targets = list(self.enemies) + ([self.boss] if self.boss and self.boss.alive else [])
                    p.update_vortex(targets, self.particle_mgr, SCREEN_WIDTH, SCREEN_HEIGHT)
                else:
                    p.update(SCREEN_WIDTH, SCREEN_HEIGHT)

        for pu in self.pickups:
            if pu.alive: pu.update(self.player.x, self.player.y, self.player.magnet_range)

        self._handle_collisions()

        self.enemies = [e for e in self.enemies if e.alive]
        self.projectiles = [p for p in self.projectiles if p.alive]
        self.pickups = [pu for pu in self.pickups if pu.alive]

        if self.player.health <= 0:
            self.state = STATE_GAMEOVER
            sound_engine.play("explosion_lg")
            self.add_screen_shake(20.0)
            self.is_new_high = save_manager.record_run(self.score, self.wave, self.kills, self.total_scrap_earned)

    def _handle_collisions(self):
        diff_cfg = DIFFICULTIES[self.difficulty]
        dmg_mult = diff_cfg["dmg_mult"]

        for p in self.projectiles:
            if not p.is_player or not p.alive: continue

            if self.boss and self.boss.alive:
                hit_n = False
                for node in self.boss.shield_nodes:
                    if node.alive and math.hypot(p.x - node.x, p.y - node.y) < (p.radius + node.radius):
                        node.take_damage(p.damage, False, self.particle_mgr)
                        p.piercing -= 1
                        if p.piercing <= 0: p.alive = False
                        hit_n = True
                        break
                if not hit_n and math.hypot(p.x - self.boss.x, p.y - self.boss.y) < (p.radius + self.boss.radius):
                    alive = self.boss.take_damage(p.damage, False, self.particle_mgr)
                    p.piercing -= 1
                    if p.piercing <= 0: p.alive = False
                    if not alive:
                        self.kills += 1
                        self._drop_loot(self.boss.x, self.boss.y, "Leviathan")
                        self.add_screen_shake(18.0)
                        self._reg_kill(self.boss.score_val)

            for e in self.enemies:
                if not e.alive or not p.alive: continue
                if math.hypot(p.x - e.x, p.y - e.y) < (p.radius + e.radius):
                    is_crit = random.random() < self.player.crit_chance
                    alive = e.take_damage(p.damage * (self.player.crit_multiplier if is_crit else 1.0), is_crit, self.particle_mgr)
                    p.piercing -= 1
                    if p.piercing <= 0: p.alive = False
                    if not alive:
                        self.kills += 1
                        self._drop_loot(e.x, e.y, type(e).__name__)
                        self._reg_kill(e.score_val)
                    break

        for p in self.projectiles:
            if p.is_player or not p.alive: continue
            if math.hypot(p.x - self.player.x, p.y - self.player.y) < (p.radius + self.player.radius):
                p.alive = False
                self.player.take_damage(p.damage * dmg_mult, self.particle_mgr)
                self.add_screen_shake(8.0)

        for e in self.enemies:
            if not e.alive: continue
            if math.hypot(e.x - self.player.x, e.y - self.player.y) < (e.radius + self.player.radius):
                e.take_damage(999, False, self.particle_mgr)
                self.player.take_damage(25.0 * dmg_mult, self.particle_mgr)
                self.add_screen_shake(12.0)
                break

        for pu in self.pickups:
            if not pu.alive: continue
            if math.hypot(pu.x - self.player.x, pu.y - self.player.y) < (pu.radius + self.player.radius):
                pu.alive = False
                sound_engine.play("pickup")
                if pu.pickup_type == "scrap":
                    self.scrap += pu.value
                    self.total_scrap_earned += pu.value
                    self.score += 50
                    self.particle_mgr.add_floating_text(pu.x, pu.y - 10, f"+{pu.value} CORE", COLOR_YELLOW, sz=10)
                elif pu.pickup_type == "health":
                    self.player.health = min(self.player.max_health, self.player.health + pu.value)
                    self.particle_mgr.add_floating_text(self.player.x, self.player.y - 25, "+HULL REPAIR", COLOR_GREEN, sz=14)
                elif pu.pickup_type == "shield":
                    self.player.shield = min(self.player.max_shield, self.player.shield + pu.value)
                    self.particle_mgr.add_floating_text(self.player.x, self.player.y - 25, "SHIELD BOOST", COLOR_CYAN, sz=14)
                elif pu.pickup_type == "overclock":
                    self.player.overclock_timer = 8.0
                    self.particle_mgr.add_floating_text(self.player.x, self.player.y - 30, "OVERCLOCK 8s!", COLOR_ORANGE, sz=16)
                elif pu.pickup_type == "emp":
                    self.player.emp_charges = min(self.player.max_emp_charges, self.player.emp_charges + 1)
                    self.particle_mgr.add_floating_text(self.player.x, self.player.y - 25, "+1 EMP CHARGE", COLOR_PURPLE, sz=14)

    def _reg_kill(self, base: int):
        self.combo += 1
        self.combo_timer = 3.2
        self.score += int(base * min(5.0, 1.0 + (self.combo - 1) * 0.25))

    def render(self):
        self.canvas.delete("all")
        self.active_buttons.clear()
        self.starfield.draw(self.canvas)

        if self.state == STATE_MENU:
            self._render_menu()
        elif self.state == STATE_SAVES_MENU:
            self._render_saves_menu()
        elif self.state == STATE_PLAYING:
            self._render_gameplay()
        elif self.state == STATE_UPGRADES:
            self._render_gameplay()
            self._render_upgrades_modal()
        elif self.state == STATE_PAUSED:
            self._render_gameplay()
            self._render_pause_modal()
        elif self.state == STATE_PAUSE_SAVE:
            self._render_gameplay()
            self._render_pause_save_modal()
        elif self.state == STATE_CONTROLS:
            self._render_controls_screen()
        elif self.state == STATE_GAMEOVER:
            self._render_gameplay()
            self._render_gameover_modal()

        for btn in self.active_buttons:
            btn.draw(self.canvas)

        if self.toast_timer > 0:
            cx = SCREEN_WIDTH / 2
            cy = 50
            self.canvas.create_rectangle(cx - 200, cy - 16, cx + 200, cy + 16, fill="#060b18", outline=self.toast_color, width=2)
            self.canvas.create_text(cx, cy, text=self.toast_message, fill=self.toast_color, font=("Impact", 12), anchor="center")

    def _render_gameplay(self):
        for pu in self.pickups: pu.draw(self.canvas)
        for e in self.enemies: e.draw(self.canvas)
        if self.boss and self.boss.alive: self.boss.draw(self.canvas)
        for p in self.projectiles: p.draw(self.canvas)
        if self.player and self.player.health > 0: self.player.draw(self.canvas)
        self.particle_mgr.draw(self.canvas)
        if self.player:
            self.hud.draw(self.canvas, self.player, self.score, self.wave, self.scrap, self.combo, self.combo_timer, self.boss, sound_engine.enabled)

    def _render_menu(self):
        # Draw Persona 3 inspired background (slanted bands, moon dial, floating shards)
        self._draw_menu_background()
        cx = SCREEN_WIDTH / 2
        self.canvas.create_text(cx, 88, text="CYBER NOVA", fill=COLOR_CYAN, font=("Impact", 66), anchor="center")
        self.canvas.create_text(cx, 138, text="— RETRO SYNTHWAVE SPACE ODYSSEY —", fill=COLOR_MAGENTA, font=("Consolas", 13, "bold"), anchor="center")

        hs = save_manager.profile.get("high_score", 0)
        mw = save_manager.profile.get("max_wave", 1)
        tk_kills = save_manager.profile.get("total_kills", 0)
        self.canvas.create_text(
            cx, 172,
            text=f"ALL-TIME HIGH SCORE: {hs:07d}  |  MAX SECTOR: WAVE {mw}  |  CAREER KILLS: {tk_kills}",
            fill=COLOR_YELLOW, font=("Consolas", 11, "bold"), anchor="center"
        )

        diff_info = DIFFICULTIES[self.difficulty]
        any_save = save_manager.has_any_save()

        bw = 380
        bh = 50
        start_y = 220
        spacing = 64

        self.active_buttons.append(Button(
            "new_game", cx - bw/2, start_y, bw, bh,
            "▶ NEW GAME", self.start_run, col=COLOR_CYAN,
            subtext=f"Launch fresh expedition [{diff_info['name']}]",
            style="p3_ribbon"
        ))

        save_sub = "Browse 5 save slots (1 Auto + 4 Manual)" if any_save else "5 slots available (Auto & Manual)"
        self.active_buttons.append(Button(
            "save_files", cx - bw/2, start_y + spacing, bw, bh,
            "💾 SAVE FILES (5 SLOTS)", lambda: setattr(self, 'state', STATE_SAVES_MENU),
            col=COLOR_GREEN if any_save else "#446677", subtext=save_sub,
            style="p3_ribbon"
        ))

        self.active_buttons.append(Button(
            "difficulty", cx - bw/2, start_y + spacing * 2, bw, bh,
            f"⚙️ DIFFICULTY: {diff_info['name']}", self.cycle_difficulty,
            col=diff_info['color'], subtext=diff_info['desc'][:46],
            style="p3_ribbon"
        ))

        self.active_buttons.append(Button(
            "controls", cx - bw/2, start_y + spacing * 3, bw, bh,
            "📖 CONTROLS & MANUAL", lambda: setattr(self, 'state', STATE_CONTROLS),
            col="#7788aa", subtext="View keyboard, mouse & flight specs",
            style="p3_ribbon"
        ))

        self.canvas.create_text(
            cx, SCREEN_HEIGHT - 25,
            text="[CLICK BUTTON OR PRESS ENTER/SPACE] Launch Game  |  [P/ESC] In-flight Pause Terminal",
            fill="#556688", font=("Consolas", 10), anchor="center"
        )
        cx = SCREEN_WIDTH / 2
        self.canvas.create_text(cx, 88, text="CYBER NOVA", fill=COLOR_CYAN, font=("Impact", 66), anchor="center")
        self.canvas.create_text(cx, 138, text="— RETRO SYNTHWAVE SPACE ODYSSEY —", fill=COLOR_MAGENTA, font=("Consolas", 13, "bold"), anchor="center")

        hs = save_manager.profile.get("high_score", 0)
        mw = save_manager.profile.get("max_wave", 1)
        tk_kills = save_manager.profile.get("total_kills", 0)
        self.canvas.create_text(
            cx, 172,
            text=f"ALL-TIME HIGH SCORE: {hs:07d}  |  MAX SECTOR: WAVE {mw}  |  CAREER KILLS: {tk_kills}",
            fill=COLOR_YELLOW, font=("Consolas", 11, "bold"), anchor="center"
        )

        diff_info = DIFFICULTIES[self.difficulty]
        any_save = save_manager.has_any_save()

        bw = 380
        bh = 50
        start_y = 220
        spacing = 64

        self.active_buttons.append(Button(
            "new_game", cx - bw/2, start_y, bw, bh,
            "▶ NEW GAME", self.start_run, col=COLOR_CYAN,
            subtext=f"Launch fresh expedition [{diff_info['name']}]"
        ))

        save_sub = "Browse 5 save slots (1 Auto + 4 Manual)" if any_save else "5 slots available (Auto & Manual)"
        self.active_buttons.append(Button(
            "save_files", cx - bw/2, start_y + spacing, bw, bh,
            "💾 SAVE FILES (5 SLOTS)", lambda: setattr(self, 'state', STATE_SAVES_MENU),
            col=COLOR_GREEN if any_save else "#446677", subtext=save_sub
        ))

        self.active_buttons.append(Button(
            "difficulty", cx - bw/2, start_y + spacing * 2, bw, bh,
            f"⚙️ DIFFICULTY: {diff_info['name']}", self.cycle_difficulty,
            col=diff_info['color'], subtext=diff_info['desc'][:46]
        ))

        self.active_buttons.append(Button(
            "controls", cx - bw/2, start_y + spacing * 3, bw, bh,
            "📖 CONTROLS & MANUAL", lambda: setattr(self, 'state', STATE_CONTROLS),
            col="#7788aa", subtext="View keyboard, mouse & flight specs"
        ))

        self.canvas.create_text(
            cx, SCREEN_HEIGHT - 25,
            text="[CLICK BUTTON OR PRESS ENTER/SPACE] Launch Game  |  [P/ESC] In-flight Pause Terminal",
            fill="#556688", font=("Consolas", 10), anchor="center"
        )

    def _render_saves_menu(self):
        cx = SCREEN_WIDTH / 2
        self.canvas.create_text(cx, 55, text="FLIGHT LOGS & SAVE ARCHIVES", fill=COLOR_CYAN, font=("Impact", 28), anchor="center")
        self.canvas.create_text(cx, 85, text="SELECT A SAVE FILE SLOT TO RESUME MISSION", fill=COLOR_MAGENTA, font=("Consolas", 11, "bold"), anchor="center")

        slots_meta = save_manager.get_all_slots_metadata()
        card_w = 820
        card_h = 62
        start_y = 110
        spacing = 74
        bx = cx - card_w / 2

        for i, sm in enumerate(slots_meta):
            sy = start_y + i * spacing
            slot_id = sm["id"]
            is_auto = (sm["type"] == "auto")
            tag_col = sm["color"]

            card_fill = "#0a0e22" if sm["exists"] else "#050711"
            card_border = tag_col if sm["exists"] else "#182038"
            self.canvas.create_rectangle(bx, sy, bx + card_w, sy + card_h, fill=card_fill, outline=card_border, width=1)

            self.canvas.create_text(bx + 20, sy + 20, text=sm["name"], fill=tag_col, font=("Impact", 13), anchor="w")

            if sm["exists"]:
                diff_title = DIFFICULTIES.get(sm["difficulty"], {}).get("name", sm["difficulty"].upper())
                detail_text = f"WAVE {sm['wave']}  |  SCORE: {sm['score']:07d}  |  SCRAP: {sm['scrap']}  |  {diff_title}"
                self.canvas.create_text(bx + 20, sy + 44, text=detail_text, fill=COLOR_WHITE, font=("Consolas", 10, "bold"), anchor="w")
                self.canvas.create_text(bx + 480, sy + 44, text=f"TIMESTAMP: {sm['timestamp']}", fill="#6688aa", font=("Consolas", 9), anchor="w")

                self.active_buttons.append(Button(
                    f"load_{slot_id}", bx + card_w - 170, sy + 14, 100, 36,
                    "▶ LOAD", lambda sid=slot_id: self.load_from_slot(sid),
                    col=COLOR_GREEN
                ))
                self.active_buttons.append(Button(
                    f"del_{slot_id}", bx + card_w - 60, sy + 14, 45, 36,
                    "🗑️", lambda sid=slot_id: self.delete_slot(sid),
                    col=COLOR_RED
                ))
            else:
                empty_desc = "[EMPTY AUTO-SAVE SLOT — SAVES AUTOMATICALLY AT WAVE CLEAR]" if is_auto else "[EMPTY MANUAL SAVE SLOT — CAN BE SAVED FROM PAUSE MENU]"
                self.canvas.create_text(bx + 20, sy + 44, text=empty_desc, fill="#384566", font=("Consolas", 10), anchor="w")

        self.active_buttons.append(Button(
            "back_saves", cx - 130, SCREEN_HEIGHT - 65, 260, 42,
            "◀ RETURN TO MAIN MENU", lambda: setattr(self, 'state', STATE_MENU),
            col=COLOR_CYAN
        ))

    def _render_pause_modal(self):
        self.canvas.create_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, fill="#050714", outline="")
        cx = SCREEN_WIDTH / 2
        cy = SCREEN_HEIGHT / 2

        modal_w = 520
        modal_h = 510
        bx = cx - modal_w / 2
        by = cy - modal_h / 2

        self.canvas.create_rectangle(bx, by, bx + modal_w, by + modal_h, fill="#0a0d22", outline=COLOR_CYAN, width=2)
        self.canvas.create_text(cx, by + 30, text="// TACTICAL PAUSE TERMINAL //", fill=COLOR_CYAN, font=("Impact", 22), anchor="center")

        diff_info = DIFFICULTIES[self.difficulty]
        self.canvas.create_text(
            cx, by + 60,
            text=f"SECTOR WAVE {self.wave}  |  SCORE: {self.score:07d}  |  SCRAP: {self.scrap}",
            fill=COLOR_YELLOW, font=("Consolas", 11, "bold"), anchor="center"
        )
        self.canvas.create_text(
            cx, by + 80,
            text=f"DIFFICULTY: {diff_info['name']}  |  HULL: {int(self.player.health)}/{self.player.max_health}  |  SHIELD: {int(self.player.shield)}/{self.player.max_shield}",
            fill=COLOR_WHITE, font=("Consolas", 10), anchor="center"
        )

        bw = 360
        bh = 46
        start_y = by + 115
        spacing = 58

        self.active_buttons.append(Button(
            "p_resume", cx - bw/2, start_y, bw, bh,
            "▶ RESUME MISSION", self.resume_game,
            col=COLOR_GREEN, subtext="Continue flight (Hotkey: ESC, P, SPACE)"
        ))

        self.active_buttons.append(Button(
            "p_save", cx - bw/2, start_y + spacing, bw, bh,
            "💾 SAVE GAME TO SLOT...", lambda: setattr(self, 'state', STATE_PAUSE_SAVE),
            col=COLOR_YELLOW, subtext="Choose from 4 manual save slots (Hotkey: S)"
        ))

        self.active_buttons.append(Button(
            "p_diff", cx - bw/2, start_y + spacing * 2, bw, bh,
            f"⚙️ DIFFICULTY: {diff_info['name']}", self.cycle_difficulty,
            col=diff_info['color'], subtext="Click to toggle difficulty tier"
        ))

        sfx_text = "🔊 SFX AUDIO: ON" if sound_engine.enabled else "🔇 SFX AUDIO: MUTED"
        self.active_buttons.append(Button(
            "p_audio", cx - bw/2, start_y + spacing * 3, bw, bh,
            sfx_text, lambda: (sound_engine.toggle_sound(), self.show_toast("SFX: ON" if sound_engine.enabled else "SFX: MUTED")),
            col=COLOR_CYAN, subtext="Toggle synthesizer sound effects (Hotkey: M)"
        ))

        self.active_buttons.append(Button(
            "p_quit", cx - bw/2, start_y + spacing * 4, bw, bh,
            "🚪 AUTO-SAVE & QUIT TO MENU", lambda: (save_manager.save_slot("auto", self.export_state()), setattr(self, 'state', STATE_MENU)),
            col=COLOR_RED, subtext="Saves to Slot 1 [Auto-Save] and returns to menu"
        ))

        self.canvas.create_text(
            cx, by + modal_h - 22,
            text="Press [ESC / P] to return immediately to combat",
            fill="#556688", font=("Consolas", 10), anchor="center"
        )

    def _render_pause_save_modal(self):
        self.canvas.create_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, fill="#050714", outline="")
        cx = SCREEN_WIDTH / 2
        cy = SCREEN_HEIGHT / 2

        modal_w = 600
        modal_h = 510
        bx = cx - modal_w / 2
        by = cy - modal_h / 2

        self.canvas.create_rectangle(bx, by, bx + modal_w, by + modal_h, fill="#0a0d22", outline=COLOR_YELLOW, width=2)
        self.canvas.create_text(cx, by + 30, text="// SELECT MANUAL SAVE SLOT //", fill=COLOR_YELLOW, font=("Impact", 22), anchor="center")
        self.canvas.create_text(cx, by + 56, text="CHOOSE ONE OF 4 MANUAL SLOTS TO WRITE CURRENT MISSION LOG", fill=COLOR_WHITE, font=("Consolas", 10), anchor="center")

        manual_slots = [s for s in SAVE_SLOT_DEFS if s["type"] == "manual"]
        bw = 520
        bh = 58
        start_y = by + 90
        spacing = 70

        for i, sdef in enumerate(manual_slots):
            sy = start_y + i * spacing
            sm = save_manager.get_slot_metadata(sdef["id"])
            slot_id = sdef["id"]

            if sm["exists"]:
                sub = f"Wave {sm['wave']} | Score {sm['score']:07d} | {sm['timestamp']} (OVERWRITE)"
            else:
                sub = "[EMPTY SLOT — CLICK TO SAVE]"

            self.active_buttons.append(Button(
                f"write_{slot_id}", cx - bw/2, sy, bw, bh,
                f"💾 {sm['name']}", lambda sid=slot_id: self.save_to_slot(sid),
                col=sm["color"], subtext=sub
            ))

        self.active_buttons.append(Button(
            "cancel_pause_save", cx - 120, by + modal_h - 60, 240, 42,
            "◀ CANCEL / BACK", lambda: setattr(self, 'state', STATE_PAUSED),
            col="#667799"
        ))

    def _render_controls_screen(self):
        cx = SCREEN_WIDTH / 2
        self.canvas.create_text(cx, 75, text="FLIGHT CONTROL TELEMETRY", fill=COLOR_CYAN, font=("Impact", 28), anchor="center")
        self.canvas.create_text(cx, 110, text="PILOT DIRECTIVE & SYSTEMS PROTOCOL", fill=COLOR_MAGENTA, font=("Consolas", 12, "bold"), anchor="center")

        box_w = 720
        box_h = 360
        bx = cx - box_w / 2
        by = 145

        self.canvas.create_rectangle(bx, by, bx + box_w, by + box_h, fill="#0a0f24", outline="#1c305c", width=2)
        for i, (ctrl, desc) in enumerate(CONTROLS_INFO):
            py = by + 32 + i * 36
            self.canvas.create_text(bx + 35, py, text=ctrl, fill=COLOR_YELLOW, font=("Consolas", 12, "bold"), anchor="w")
            self.canvas.create_text(bx + box_w - 35, py, text=desc, fill=COLOR_WHITE, font=("Consolas", 12), anchor="e")

        self.active_buttons.append(Button(
            "back_menu", cx - 140, by + box_h + 30, 280, 48,
            "◀ RETURN TO MAIN MENU", lambda: setattr(self, 'state', STATE_MENU),
            col=COLOR_CYAN, subtext="Press ESC or Space"
        ))

    def _render_upgrades_modal(self):
        self.canvas.create_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, fill="#050714", outline="")
        cx = SCREEN_WIDTH / 2
        cy = SCREEN_HEIGHT / 2
        mw, mh = 760, 540
        bx, by = cx - mw / 2, cy - mh / 2

        self.canvas.create_rectangle(bx, by, bx + mw, by + mh, fill="#0a0d1f", outline=COLOR_CYAN, width=2)
        self.canvas.create_text(cx, by + 28, text="⚡ TECH BAY UPGRADES ⚡", fill=COLOR_CYAN, font=("Impact", 22), anchor="center")
        self.canvas.create_text(cx, by + 52, text=f"AVAILABLE SCRAP: {self.scrap} CORES", fill=COLOR_YELLOW, font=("Consolas", 12, "bold"), anchor="center")
        self.canvas.create_text(cx, by + 76, text=self.upgrade_msg, fill=COLOR_WHITE, font=("Consolas", 11), anchor="center")

        ly = by + 100
        for i, item in enumerate(self.upgrade_mgr.upgrades):
            iy = ly + i * 42
            is_sel = (i == self.selected_upg)
            self.canvas.create_rectangle(bx + 20, iy, bx + mw - 20, iy + 36, fill="#151c38" if is_sel else "#0d1124",
                                         outline=COLOR_CYAN if is_sel else "#1c2544", width=2 if is_sel else 1)
            self.canvas.create_text(bx + 35, iy + 18, text=f"{item.icon} {item.name}", fill=item.color if is_sel else COLOR_WHITE, font=("Consolas", 11, "bold"), anchor="w")
            pips = "■ " * item.level + "□ " * (item.max_level - item.level)
            self.canvas.create_text(bx + 310, iy + 18, text=f"LV: {pips}", fill=COLOR_CYAN, font=("Consolas", 10), anchor="w")
            cost_txt = "MAXED" if item.is_maxed else f"{item.cost} SCRAP"
            self.canvas.create_text(bx + mw - 40, iy + 18, text=cost_txt, fill=COLOR_YELLOW if self.scrap >= item.cost else COLOR_RED, font=("Consolas", 11, "bold"), anchor="e")

        self.canvas.create_text(cx, by + mh - 20, text="[W/S] Select  |  [ENTER] Buy  |  [B/ESC] Return", fill="#556688", font=("Consolas", 10, "bold"), anchor="center")

    def _render_gameover_modal(self):
        self.canvas.create_rectangle(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, fill="#080308", outline="")
        cx = SCREEN_WIDTH / 2
        cy = SCREEN_HEIGHT / 2
        w = 600
        h = 440
        bx = cx - w / 2
        by = cy - h / 2

        self.canvas.create_rectangle(bx, by, bx + w, by + h, fill="#120612", outline=COLOR_RED, width=2)
        self.canvas.create_text(cx, by + 40, text="HULL DESTROYED", fill=COLOR_RED, font=("Impact", 36), anchor="center")
        
        if self.is_new_high:
            self.canvas.create_text(cx, by + 80, text="★ NEW ALL-TIME HIGH SCORE! ★", fill=COLOR_YELLOW, font=("Impact", 18), anchor="center")
        else:
            self.canvas.create_text(cx, by + 80, text="MISSION FAILED // FLIGHT TERMINATED", fill="#995566", font=("Consolas", 12), anchor="center")

        stats = [
            ("FINAL SCORE", f"{self.score:07d}"),
            ("SECTOR WAVE REACHED", f"WAVE {self.wave}"),
            ("ENEMIES ELIMINATED", f"{self.kills} CRAFT"),
            ("SCRAP HARVESTED", f"{self.total_scrap_earned} CORES"),
            ("DIFFICULTY SETTING", f"{DIFFICULTIES[self.difficulty]['name']}"),
            ("ALL-TIME HIGH SCORE", f"{save_manager.profile.get('high_score', 0):07d}")
        ]

        for i, (label, val) in enumerate(stats):
            sy = by + 120 + i * 32
            self.canvas.create_text(bx + 60, sy, text=label, fill=COLOR_WHITE, font=("Consolas", 11, "bold"), anchor="w")
            self.canvas.create_text(bx + w - 60, sy, text=val, fill=COLOR_CYAN, font=("Impact", 15), anchor="e")

        self.active_buttons.append(Button(
            "go_restart", cx - 220, by + h - 55, 200, 42,
            "▶ PLAY AGAIN", self.start_run, col=COLOR_YELLOW
        ))
        self.active_buttons.append(Button(
            "go_menu", cx + 20, by + h - 55, 200, 42,
            "🚪 MAIN MENU", lambda: setattr(self, 'state', STATE_MENU), col=COLOR_CYAN
        ))

    def tick(self):
        now = time.perf_counter()
        dt = min(0.05, now - self.last_time)
        self.last_time = now
        self.update(dt)
        self.render()
        self.root.after(FRAME_DELAY_MS, self.tick)


def main():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    root = tk.Tk()
    root.title("CYBER NOVA: ODYSSEY")
    app = Game(root)

    root.update_idletasks()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    ww = root.winfo_width()
    wh = root.winfo_height()
    root.geometry(f"{ww}x{wh}+{max(0, (sw - ww) // 2)}+{max(0, (sh - wh) // 2)}")

    root.mainloop()


if __name__ == "__main__":
    main()
