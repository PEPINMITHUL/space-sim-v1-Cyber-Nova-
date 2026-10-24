"""
Core Game Engine and State Machine for CYBER NOVA: ODYSSEY.
PERSONA 3 STYLIZED EDITION:
- Iconic Persona 3 angled parallelogram ribbon menus with dynamic slide & invert highlights
- Dark Hour Lunar Clock Dial, floating crystal shards, and hero ship showcase
- 5 Distinct Save Slots: Slot 1 (Auto-Save) + Slots 2-5 (Manual Saves 1-4)
- Unified "SAVE FILES" browser in Main Menu for loading/deleting any slot
- In-flight manual slot selector in Pause Menu
- Difficulty selection (Cadet, Pilot, Veteran, Cyber-Hell)
- Full mouse hover + keyboard navigation support
- 60 FPS update and rendering loop
"""

import math
import random
import time
import tkinter as tk
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FRAME_DELAY_MS,
    COLOR_BG, COLOR_CYAN, COLOR_MAGENTA, COLOR_YELLOW,
    COLOR_GREEN, COLOR_WHITE, COLOR_RED, COLOR_PURPLE,
    COLOR_ORANGE, COLOR_SHIELD, CONTROLS_INFO, DIFFICULTIES
)
from particles import Starfield, ParticleManager
from player import Player
from weapons import WEAPONS_DATA, HomingMissile, SingularityVortex
from enemies import DroneKamikaze, ViperScout, CruiserBattleship, StealthPhantom
from boss import DreadnoughtLeviathan, IrisSpecter, VoidRavager
from ships import SHIPS
import ui_theme
from pickups import Pickup
from upgrades import UpgradeManager
from hud import HUD
from sound_engine import sound_engine
from save_manager import save_manager, SAVE_SLOT_DEFS


STATE_MENU = "menu"
STATE_SHIP_SELECT = "ship_select"
STATE_SAVES_MENU = "saves_menu"
STATE_PLAYING = "playing"
STATE_UPGRADES = "upgrades"
STATE_PAUSED = "paused"
STATE_PAUSE_SAVE = "pause_save"
STATE_GAMEOVER = "gameover"
STATE_CONTROLS = "controls"


class Button:
    def __init__(self, btn_id: str, x: float, y: float, w: float, h: float,
                 text: str, callback, col: str = COLOR_CYAN, subtext: str = "",
                 enabled: bool = True, style: str = "default", badge: str = ""):
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
        self.style = style
        self.badge = badge

    def contains(self, mx: float, my: float) -> bool:
        if self.style == "p3_ribbon":
            # Slightly angled generous hitbox
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
            # Persona 3 Electric Cerulean with high contrast ink black text
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

        # Angled Badge Box (e.g. "01", "02")
        if self.badge:
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

        # Persona 3 Target Chevron Cursor on Hover
        if self.hovered:
            arrow_x = bx - slant - 16
            arrow_pts = [
                arrow_x - 4, by + bh * 0.22,
                arrow_x + 10, by + bh * 0.5,
                arrow_x - 4, by + bh * 0.78
            ]
            canvas.create_polygon(arrow_pts, fill="#00e5ff", outline="#ffffff", width=1)

        # Main Text & Subtext
        text_x = bx + slant + (58 if self.badge else 22)
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


class Game:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("CYBER NOVA: ODYSSEY // PERSONA 3 EDITION")
        self.root.geometry(f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        self.root.resizable(False, False)
        self.root.configure(bg=COLOR_BG)

        self.root.focus_force()

        self.canvas = tk.Canvas(
            root, width=SCREEN_WIDTH, height=SCREEN_HEIGHT,
            bg=COLOR_BG, highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Game State & Persona 3 Menu variables
        self.state = STATE_SHIP_SELECT  # start with ship selection
        self.difficulty = "pilot"
        self.keys = {}
        self.mouse_x = SCREEN_WIDTH / 2
        self.mouse_y = SCREEN_HEIGHT / 2
        self.mouse_down = False
        self.menu_selected_idx = 0
        self.menu_tick = 0.0

        # Persona 3 floating moonlight shards
        self.p3_shards = []
        for _ in range(20):
            self.p3_shards.append({
                'x': random.uniform(0, SCREEN_WIDTH),
                'y': random.uniform(0, SCREEN_HEIGHT),
                'size': random.uniform(6, 18),
                'speed': random.uniform(0.35, 1.1),
                'rot': random.uniform(0, 6.28),
                'rot_spd': random.uniform(-0.02, 0.02),
                'color': random.choice(["#071a3d", "#0c2c66", "#0088cc", "#1e5b99", "#00e5ff"]) 
            })

        # Interactive Buttons & Toast
        self.active_buttons: list[Button] = []
        self.toast_message = ""
        self.toast_timer = 0.0
        self.toast_color = COLOR_YELLOW

        # Core Systems
        self.starfield = Starfield(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.particle_mgr = ParticleManager()
        self.hud = HUD()
        self.upgrade_mgr = UpgradeManager()

        # Run Attributes
        self.player = None
        self.enemies = []
        self.boss = None
        self.projectiles = []
        self.pickups = []

        self.score = 0
        self.scrap = 0
        self.wave = 1
        self.kills = 0
        # Selected ship identifier (persisted later)
        self.selected_ship_id: str | None = self._load_selected_ship()
        self.total_scrap_earned = 0
        self.combo = 0
        self.combo_timer = 0.0

        # Spawning & Wave flow
        self.wave_in_progress = False
        self.wave_enemies_to_spawn = []
        self.spawn_timer = 0.0
        self.wave_clear_timer = 0.0

        # Screen Shake
        self.shake_magnitude = 0.0
        self.shake_dx = 0.0
        self.shake_dy = 0.0

        # Tech Bay UI tracking
        self.selected_upgrade_idx = 0
        self.upgrade_message = ""
        self.is_new_high_score = False

        self._bind_events()
        self.last_time = time.perf_counter()
        self.tick()

    # Persistence helpers for ship selection
    def _ship_save_path(self) -> str:
        """Return the absolute path to the ship selection JSON file."""
        import os
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "ship_selection.json")

    def _load_selected_ship(self) -> str | None:
        """Load persisted ship id if it exists."""
        import json, os
        path = self._ship_save_path()
        if os.path.isfile(path):
            try:
                data = json.load(open(path, "r"))
                return data.get("ship_id")
            except Exception:
                return None
        return None

    def _save_selected_ship(self, ship_id: str) -> None:
        """Persist the chosen ship id to disk."""
        import json
        path = self._ship_save_path()
        json.dump({"ship_id": ship_id}, open(path, "w"))

    def _choose_ship(self, ship_id: str) -> None:
        """Callback when a ship button is pressed."""
        self.selected_ship_id = ship_id
        self._save_selected_ship(ship_id)
        # Transition to main menu after selection
        self.state = STATE_MENU
        self.menu_selected_idx = 0
        self.active_buttons.clear()
        self.show_toast(f"Ship '{SHIPS[ship_id].name}' selected!", COLOR_GREEN, duration=2.0)

    def _render_ship_select(self) -> None:
        """Render the ship selection screen using Persona‑3 ribbon UI."""
        # Background
        ui_theme.draw_menu_background(self.canvas)
        # Title
        self.canvas.create_text(
            SCREEN_WIDTH // 2, 60,
            text="SELECT YOUR SHIP",
            fill=COLOR_CYAN,
            font=("Impact", 32), anchor="center"
        )
        self.canvas.create_text(
            SCREEN_WIDTH // 2, 95,
            text="CHOOSE A CHASSIS BEFORE LAUNCHING",
            fill="#5599cc",
            font=("Consolas", 10, "bold"), anchor="center"
        )
        # Create a button for each ship
        btn_w, btn_h = 520, 68
        start_y = 130
        gap = 86
        for idx, (sid, ship) in enumerate(SHIPS.items()):
            x = SCREEN_WIDTH // 2 - btn_w // 2
            y = start_y + idx * gap
            # Truncate subtext to fit within ribbon
            sub = f"{ship.perk_desc} | {ship.con_desc}"
            if len(sub) > 52:
                sub = sub[:49] + "..."
            btn = Button(
                btn_id=sid,
                x=x,
                y=y,
                w=btn_w,
                h=btn_h,
                text=f"{ship.name} — {ship.perk_name} / {ship.con_name}",
                callback=lambda s=sid: self._choose_ship(s),
                col=COLOR_CYAN,
                style="p3_ribbon",
                subtext=sub,
                badge=str(idx+1).zfill(2)
            )
            self.active_buttons.append(btn)

        # Bottom hint strip
        self.canvas.create_text(
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30,
            text="[CLICK] SELECT SHIP  |  PERKS & DRAWBACKS MODIFY YOUR PILOT STATS",
            fill="#55aadd", font=("Consolas", 10, "bold"), anchor="center"
        )

    # Existing methods continue below ...
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("CYBER NOVA: ODYSSEY // PERSONA 3 EDITION")
        self.root.geometry(f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        self.root.resizable(False, False)
        self.root.configure(bg=COLOR_BG)

        self.root.focus_force()

        self.canvas = tk.Canvas(
            root, width=SCREEN_WIDTH, height=SCREEN_HEIGHT,
            bg=COLOR_BG, highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        # Game State & Persona 3 Menu variables
        self.state = STATE_SHIP_SELECT
        self.difficulty = "pilot"
        self.keys = {}
        self.mouse_x = SCREEN_WIDTH / 2
        self.mouse_y = SCREEN_HEIGHT / 2
        self.mouse_down = False
        self.menu_selected_idx = 0
        self.menu_tick = 0.0

        # Persona 3 floating moonlight shards
        self.p3_shards = []
        for _ in range(20):
            self.p3_shards.append({
                'x': random.uniform(0, SCREEN_WIDTH),
                'y': random.uniform(0, SCREEN_HEIGHT),
                'size': random.uniform(6, 18),
                'speed': random.uniform(0.35, 1.1),
                'rot': random.uniform(0, 6.28),
                'rot_spd': random.uniform(-0.02, 0.02),
                'color': random.choice(["#071a3d", "#0c2c66", "#0088cc", "#1e5b99", "#00e5ff"])
            })

        # Interactive Buttons & Toast
        self.active_buttons: list[Button] = []
        self.toast_message = ""
        self.toast_timer = 0.0
        self.toast_color = COLOR_YELLOW

        # Core Systems
        self.starfield = Starfield(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.particle_mgr = ParticleManager()
        self.hud = HUD()
        self.upgrade_mgr = UpgradeManager()

        # Run Attributes
        self.player = None
        self.enemies = []
        self.boss = None
        self.projectiles = []
        self.pickups = []
        
        self.score = 0
        self.scrap = 0
        self.wave = 1
        self.kills = 0
        # Selected ship identifier (persisted later)
        self.selected_ship_id: str | None = None
        self.total_scrap_earned = 0
        self.combo = 0
        self.combo_timer = 0.0

        # Spawning & Wave flow
        self.wave_in_progress = False
        self.wave_enemies_to_spawn = []
        self.spawn_timer = 0.0
        self.wave_clear_timer = 0.0

        # Screen Shake
        self.shake_magnitude = 0.0
        self.shake_dx = 0.0
        self.shake_dy = 0.0

        # Tech Bay UI tracking
        self.selected_upgrade_idx = 0
        self.upgrade_message = ""
        self.is_new_high_score = False

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
        self.canvas.bind("<ButtonPress-1>", self._on_left_click_press)
        self.canvas.bind("<ButtonRelease-1>", self._on_left_click_release)
        self.canvas.bind("<ButtonPress-3>", self._on_right_click)
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)

    def _on_key_down(self, event):
        self.root.focus_set()
        k = event.keysym.lower()
        self.keys[k] = True

        if self.state == STATE_SHIP_SELECT:
            self._render_ship_select()
        elif self.state == STATE_MENU:
            self._render_persona3_menu()
            # Persona 3 Menu Keyboard Navigation
            if k in ("w", "up"):
                self.menu_selected_idx = (self.menu_selected_idx - 1) % 4
                sound_engine.play("laser")
            elif k in ("s", "down"):
                self.menu_selected_idx = (self.menu_selected_idx + 1) % 4
                sound_engine.play("laser")
            elif k in ("return", "space"):
                # Execute selected menu button
                if self.active_buttons and 0 <= self.menu_selected_idx < len(self.active_buttons):
                    self.active_buttons[self.menu_selected_idx].callback()
        elif self.state == STATE_SAVES_MENU:
            if k in ("escape", "backspace"):
                self.state = STATE_SHIP_SELECT
        elif self.state == STATE_PLAYING:
            if k in ("1", "2", "3", "4", "5"):
                weapons = ["pulse", "twin", "flak", "homing", "singularity"]
                idx = int(k) - 1
                if idx < len(weapons):
                    w_name = weapons[idx]
                    if w_name in self.player.unlocked_weapons:
                        self.player.current_weapon = w_name
            elif k in ("q", "f"):
                self.player.trigger_emp(self.particle_mgr, self.enemies, self.projectiles)
            elif k in ("space", "shift_l", "e"):
                self.player.trigger_dash(self.particle_mgr)
            elif k == "b":
                self.state = STATE_UPGRADES
                self.upgrade_message = "SELECT AN UPGRADE TO INSTALL"
            elif k in ("p", "escape"):
                self.pause_game()
            elif k == "m":
                sound_engine.toggle_sound()
                self.show_toast("SFX: ON" if sound_engine.enabled else "SFX: MUTED")
        elif self.state == STATE_PAUSED:
            if k in ("p", "escape", "space", "return"):
                self.resume_game()
            elif k == "m":
                sound_engine.toggle_sound()
                self.show_toast("SFX: ON" if sound_engine.enabled else "SFX: MUTED")
            elif k == "s":
                self.state = STATE_PAUSE_SAVE
        elif self.state == STATE_PAUSE_SAVE:
            if k in ("escape", "backspace"):
                self.state = STATE_PAUSED
        elif self.state == STATE_UPGRADES:
            if k in ("b", "escape"):
                self.state = STATE_PLAYING
            elif k in ("up", "w"):
                self.selected_upgrade_idx = (self.selected_upgrade_idx - 1) % len(self.upgrade_mgr.upgrades)
            elif k in ("down", "s"):
                self.selected_upgrade_idx = (self.selected_upgrade_idx + 1) % len(self.upgrade_mgr.upgrades)
            elif k in ("return", "space", "e"):
                self._buy_selected_upgrade()
        elif self.state == STATE_CONTROLS:
            if k in ("return", "space", "escape", "b"):
                self.state = STATE_SHIP_SELECT
        elif self.state == STATE_GAMEOVER:
            if k in ("return", "space"):
                self.start_new_run()
            elif k == "escape":
                self.state = STATE_SHIP_SELECT

    def _on_key_up(self, event):
        self.keys[event.keysym.lower()] = False

    def _on_mouse_move(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y

        hovering_any = False
        for i, btn in enumerate(self.active_buttons):
            is_in = btn.contains(self.mouse_x, self.mouse_y)
            btn.hovered = is_in
            if is_in and btn.enabled:
                hovering_any = True
                if self.state == STATE_MENU:
                    self.menu_selected_idx = i
                elif self.state == STATE_SHIP_SELECT:
                    # No index handling needed for ship select hover
                    pass

        self.canvas.config(cursor="hand2" if hovering_any else "")

    def _on_left_click_press(self, event):
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
            self.start_new_run()

    def _on_left_click_release(self, event):
        self.mouse_down = False

    def _on_right_click(self, event):
        if self.state == STATE_PLAYING and self.player:
            self.player.trigger_dash(self.particle_mgr)

    def _on_mouse_wheel(self, event):
        if self.state == STATE_PLAYING and self.player:
            weapons = [w for w in ["pulse", "twin", "flak", "homing", "singularity"] if w in self.player.unlocked_weapons]
            if len(weapons) > 1:
                cur_idx = weapons.index(self.player.current_weapon)
                delta = 1 if event.delta < 0 else -1
                new_idx = (cur_idx + delta) % len(weapons)
                self.player.current_weapon = weapons[new_idx]

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
        diff_info = DIFFICULTIES[self.difficulty]
        self.show_toast(f"DIFFICULTY: {diff_info['name']}", diff_info['color'], duration=2.0)

    def add_screen_shake(self, amount: float):
        self.shake_magnitude = min(22.0, self.shake_magnitude + amount)

    def export_state(self) -> dict:
        upgrades_data = {u.item_id: u.level for u in self.upgrade_mgr.upgrades}
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
            "upgrades": upgrades_data
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
            if w in WEAPONS_DATA:
                WEAPONS_DATA[w].unlocked = True

        self.upgrade_mgr = UpgradeManager()
        upg_levels = data.get("upgrades", {})
        for u in self.upgrade_mgr.upgrades:
            if u.item_id in upg_levels:
                u.level = upg_levels[u.item_id]

        self.enemies.clear()
        self.boss = None
        self.projectiles.clear()
        self.pickups.clear()
        self.particle_mgr.clear()

        self.state = STATE_PLAYING
        self._init_wave(self.wave)
        self.show_toast(f"RUN RESTORED: WAVE {self.wave}", COLOR_GREEN, duration=2.5)

    def save_to_slot(self, slot_id: str):
        if not self.player or self.player.health <= 0:
            return
        state_data = self.export_state()
        success = save_manager.save_slot(slot_id, state_data)
        slot_meta = save_manager.get_slot_metadata(slot_id)
        if success:
            self.show_toast(f"SAVED TO {slot_meta['name']}!", COLOR_GREEN, duration=2.5)
            sound_engine.play("pickup")
            self.state = STATE_PAUSED
        else:
            self.show_toast("SAVE FAILED TO WRITE", COLOR_RED, duration=2.5)

    def load_from_slot(self, slot_id: str):
        data = save_manager.load_slot(slot_id)
        if data:
            self.import_state(data)
        else:
            self.show_toast(f"NO DATA IN SLOT {slot_id.upper()}", COLOR_RED, duration=2.0)

    def delete_slot(self, slot_id: str):
        save_manager.delete_slot(slot_id)
        self.show_toast("SLOT CLEARED", COLOR_YELLOW, duration=1.5)

    def start_new_run(self):
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
        # Selected ship identifier (persisted later)
        self.selected_ship_id: str | None = None
        self.total_scrap_earned = 0
        self.combo = 0
        self.combo_timer = 0.0
        self.is_new_high_score = False

        self.state = STATE_PLAYING
        self._init_wave(self.wave)
        save_manager.save_slot("auto", self.export_state())

    def _init_wave(self, wave_num: int):
        self.wave_in_progress = True
        self.wave_enemies_to_spawn.clear()
        self.particle_mgr.add_floating_text(
            SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 40,
            f"SECTOR WAVE {wave_num}", COLOR_CYAN, size=24
        )
        self.starfield.trigger_warp()

        if wave_num % 5 == 0:
            # Choose boss based on wave progression
            if wave_num < 10:
                # Early boss – flagship
                self.boss = DreadnoughtLeviathan(SCREEN_WIDTH / 2, -60, wave_num)
            elif wave_num < 15:
                # Mid‑game boss
                self.boss = IrisSpecter(SCREEN_WIDTH / 2, -60, wave_num)
            else:
                # Late‑game boss
                self.boss = VoidRavager(SCREEN_WIDTH / 2, -60, wave_num)
            diff_cfg = DIFFICULTIES[self.difficulty]
            self.boss.max_health *= diff_cfg["hp_mult"]
            self.boss.health = self.boss.max_health
            self.particle_mgr.add_floating_text(
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                "⚠️ BOSS APPEARED ⚠️", COLOR_RED, size=18
            )
            self.boss = DreadnoughtLeviathan(SCREEN_WIDTH / 2, -60, wave_num)
            diff_cfg = DIFFICULTIES[self.difficulty]
            self.boss.max_health *= diff_cfg["hp_mult"]
            self.boss.health = self.boss.max_health
            self.particle_mgr.add_floating_text(
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                "⚠️ TITAN SIGNATURE DETECTED ⚠️", COLOR_RED, size=18
            )
        else:
            self.boss = None
            drone_count = 6 + wave_num * 3
            viper_count = 2 + wave_num * 2
            cruiser_count = max(0, wave_num - 2)
            phantom_count = max(0, wave_num - 3)

            for _ in range(drone_count): self.wave_enemies_to_spawn.append(DroneKamikaze)
            for _ in range(viper_count): self.wave_enemies_to_spawn.append(ViperScout)
            for _ in range(cruiser_count): self.wave_enemies_to_spawn.append(CruiserBattleship)
            for _ in range(phantom_count): self.wave_enemies_to_spawn.append(StealthPhantom)

            random.shuffle(self.wave_enemies_to_spawn)

        self.spawn_timer = 1.0

    def _spawn_next_enemy(self):
        if not self.wave_enemies_to_spawn:
            return

        cls = self.wave_enemies_to_spawn.pop()
        side = random.choice(["top", "left", "right"])
        if side == "top":
            x = random.uniform(50, SCREEN_WIDTH - 50)
            y = -30
        elif side == "left":
            x = -30
            y = random.uniform(50, SCREEN_HEIGHT * 0.6)
        else:
            x = SCREEN_WIDTH + 30
            y = random.uniform(50, SCREEN_HEIGHT * 0.6)

        enemy = cls(x, y)
        diff_cfg = DIFFICULTIES[self.difficulty]
        enemy.health *= diff_cfg["hp_mult"]
        enemy.max_health = enemy.health
        enemy.speed *= diff_cfg["spd_mult"]
        self.enemies.append(enemy)

    def _drop_loot(self, x: float, y: float, enemy_type: str = ""):
        diff_cfg = DIFFICULTIES[self.difficulty]
        base_scrap = random.randint(2, 4)
        if "Cruiser" in enemy_type:
            base_scrap = random.randint(6, 10)
        elif "Leviathan" in enemy_type:
            base_scrap = random.randint(25, 40)

        scrap_amount = max(1, int(base_scrap * diff_cfg["scrap_mult"]))
        for _ in range(scrap_amount):
            self.pickups.append(Pickup(x, y, "scrap", value=1))

        roll = random.random()
        if roll < 0.10:
            self.pickups.append(Pickup(x, y, "health", value=30))
        elif roll < 0.18:
            self.pickups.append(Pickup(x, y, "shield", value=40))
        elif roll < 0.24:
            self.pickups.append(Pickup(x, y, "overclock", value=1))
        elif roll < 0.28:
            self.pickups.append(Pickup(x, y, "emp", value=1))

    def _buy_selected_upgrade(self):
        item = self.upgrade_mgr.upgrades[self.selected_upgrade_idx]
        success, remaining_scrap, msg = self.upgrade_mgr.purchase(
            item.item_id, self.player, self.scrap, self.particle_mgr
        )
        self.scrap = remaining_scrap
        self.upgrade_message = msg

    def update(self, dt: float):
        if self.toast_timer > 0:
            self.toast_timer -= dt

        self.menu_tick += dt

        # Update floating Persona 3 moonlight shards
        for shard in self.p3_shards:
            shard['y'] -= shard['speed']
            shard['rot'] += shard['rot_spd']
            if shard['y'] < -30:
                shard['y'] = SCREEN_HEIGHT + 20
                shard['x'] = random.uniform(0, SCREEN_WIDTH)

        # Starfield & Particle Updates
        vx = self.player.vx if self.player else 0.0
        vy = self.player.vy if self.player else 0.0
        self.starfield.update(vx, vy)
        self.particle_mgr.update()

        if self.shake_magnitude > 0:
            self.shake_dx = random.uniform(-self.shake_magnitude, self.shake_magnitude)
            self.shake_dy = random.uniform(-self.shake_magnitude, self.shake_magnitude)
            self.shake_magnitude = max(0.0, self.shake_magnitude - dt * 28.0)
        else:
            self.shake_dx = 0.0
            self.shake_dy = 0.0

        if self.state != STATE_PLAYING:
            return

        if self.combo > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo = 0

        self.player.handle_input(self.keys, self.mouse_x, self.mouse_y)
        self.player.update(dt, self.particle_mgr)

        if self.mouse_down or self.keys.get("space"):
            new_shots = self.player.fire(self.particle_mgr)
            self.projectiles.extend(new_shots)

        if self.wave_in_progress:
            if self.wave_enemies_to_spawn:
                self.spawn_timer -= dt
                if self.spawn_timer <= 0:
                    self.spawn_timer = max(0.35, 1.2 - (self.wave * 0.08))
                    self._spawn_next_enemy()
            elif not self.enemies and (not self.boss or not self.boss.alive):
                self.wave_in_progress = False
                self.wave_clear_timer = 3.0
                sound_engine.play("powerup")
                self.particle_mgr.add_floating_text(
                    SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20,
                    f"WAVE {self.wave} CLEARED!", COLOR_GREEN, size=22
                )
                self.particle_mgr.add_floating_text(
                    SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 15,
                    "PRESS [B] TO ACCESS TECH BAY", COLOR_YELLOW, size=14
                )
                save_manager.save_slot("auto", self.export_state())
        else:
            self.wave_clear_timer -= dt
            if self.wave_clear_timer <= 0:
                self.wave += 1
                self._init_wave(self.wave)

        if self.boss and self.boss.alive:
            boss_shots, minions = self.boss.update(dt, self.player.x, self.player.y, self.particle_mgr)
            self.projectiles.extend(boss_shots)
            self.enemies.extend(minions)

        for enemy in self.enemies:
            if enemy.alive:
                e_shots = enemy.update(dt, self.player.x, self.player.y, self.particle_mgr)
                self.projectiles.extend(e_shots)

        for p in self.projectiles:
            if p.alive:
                if isinstance(p, HomingMissile):
                    targets = list(self.enemies)
                    if self.boss and self.boss.alive:
                        targets.append(self.boss)
                    p.update_homing(targets, self.particle_mgr, SCREEN_WIDTH, SCREEN_HEIGHT)
                elif isinstance(p, SingularityVortex):
                    targets = list(self.enemies)
                    if self.boss and self.boss.alive:
                        targets.append(self.boss)
                    p.update_vortex(targets, self.particle_mgr, SCREEN_WIDTH, SCREEN_HEIGHT)
                else:
                    p.update(SCREEN_WIDTH, SCREEN_HEIGHT)

        for pu in self.pickups:
            if pu.alive:
                pu.update(self.player.x, self.player.y, self.player.magnet_range)

        self._handle_collisions()

        self.enemies = [e for e in self.enemies if e.alive]
        self.projectiles = [p for p in self.projectiles if p.alive]
        self.pickups = [pu for pu in self.pickups if pu.alive]

        if self.player.health <= 0:
            self._handle_game_over()

    def _handle_collisions(self):
        diff_cfg = DIFFICULTIES[self.difficulty]
        dmg_mult = diff_cfg["dmg_mult"]

        for p in self.projectiles:
            if not p.is_player or not p.alive:
                continue

            if self.boss and self.boss.alive:
                hit_node = False
                for node in self.boss.shield_nodes:
                    if node.alive and math.hypot(p.x - node.x, p.y - node.y) < (p.radius + node.radius):
                        node.take_damage(p.damage, False, self.particle_mgr)
                        p.piercing -= 1
                        if p.piercing <= 0:
                            p.alive = False
                        hit_node = True
                        break
                
                if not hit_node and math.hypot(p.x - self.boss.x, p.y - self.boss.y) < (p.radius + self.boss.radius):
                    boss_alive = self.boss.take_damage(p.damage, False, self.particle_mgr)
                    p.piercing -= 1
                    if p.piercing <= 0:
                        p.alive = False
                    if not boss_alive:
                        self.kills += 1
                        self._drop_loot(self.boss.x, self.boss.y, "Leviathan")
                        self.add_screen_shake(18.0)
                        self._register_kill(self.boss.score_val)

            for enemy in self.enemies:
                if not enemy.alive or not p.alive:
                    continue
                dist = math.hypot(p.x - enemy.x, p.y - enemy.y)
                if dist < (p.radius + enemy.radius):
                    is_crit = random.random() < self.player.crit_chance
                    dmg = p.damage * (self.player.crit_multiplier if is_crit else 1.0)
                    is_alive = enemy.take_damage(dmg, is_crit, self.particle_mgr)
                    
                    p.piercing -= 1
                    if p.piercing <= 0:
                        p.alive = False

                    if not is_alive:
                        self.kills += 1
                        self._drop_loot(enemy.x, enemy.y, type(enemy).__name__)
                        self._register_kill(enemy.score_val)
                    break

        for p in self.projectiles:
            if p.is_player or not p.alive:
                continue
            dist = math.hypot(p.x - self.player.x, p.y - self.player.y)
            if dist < (p.radius + self.player.radius):
                p.alive = False
                incoming_dmg = p.damage * dmg_mult
                alive = self.player.take_damage(incoming_dmg, self.particle_mgr)
                self.add_screen_shake(8.0)
                if not alive:
                    break

        for enemy in self.enemies:
            if not enemy.alive:
                continue
            dist = math.hypot(enemy.x - self.player.x, enemy.y - self.player.y)
            if dist < (enemy.radius + self.player.radius):
                ram_dmg = (28.0 if isinstance(enemy, DroneKamikaze) else 18.0) * dmg_mult
                enemy.take_damage(999, False, self.particle_mgr)
                self.player.take_damage(ram_dmg, self.particle_mgr)
                self.add_screen_shake(12.0)
                break

        for pu in self.pickups:
            if not pu.alive:
                continue
            dist = math.hypot(pu.x - self.player.x, pu.y - self.player.y)
            if dist < (pu.radius + self.player.radius):
                pu.alive = False
                sound_engine.play("pickup")
                if pu.pickup_type == "scrap":
                    self.scrap += pu.value
                    self.total_scrap_earned += pu.value
                    self.score += 50
                    self.particle_mgr.add_floating_text(pu.x, pu.y - 10, f"+{pu.value} CORE", COLOR_YELLOW, size=10)
                elif pu.pickup_type == "health":
                    healed = min(pu.value, self.player.max_health - self.player.health)
                    self.player.health += healed
                    self.particle_mgr.add_floating_text(self.player.x, self.player.y - 25, f"+{int(healed)} HULL", COLOR_GREEN, size=14)
                elif pu.pickup_type == "shield":
                    self.player.shield = min(self.player.max_shield, self.player.shield + pu.value)
                    self.particle_mgr.add_floating_text(self.player.x, self.player.y - 25, "SHIELD BOOST!", COLOR_CYAN, size=14)
                elif pu.pickup_type == "overclock":
                    self.player.overclock_timer = 8.0
                    self.particle_mgr.add_floating_text(self.player.x, self.player.y - 30, "OVERCLOCK 8s!", COLOR_ORANGE, size=16)
                elif pu.pickup_type == "emp":
                    self.player.emp_charges = min(self.player.max_emp_charges, self.player.emp_charges + 1)
                    self.particle_mgr.add_floating_text(self.player.x, self.player.y - 25, "+1 EMP CHARGE", COLOR_PURPLE, size=14)

    def _register_kill(self, base_score: int):
        self.combo += 1
        self.combo_timer = 3.2
        mult = min(5.0, 1.0 + (self.combo - 1) * 0.25)
        added_score = int(base_score * mult)
        self.score += added_score

    def _handle_game_over(self):
        self.state = STATE_GAMEOVER
        sound_engine.play("explosion_lg")
        self.add_screen_shake(20.0)
        self.is_new_high_score = save_manager.record_run(
            self.score, self.wave, self.kills, self.total_scrap_earned
        )

    def render(self):
        self.canvas.delete("all")
        self.active_buttons.clear()

        # Background Stars
        self.starfield.draw(self.canvas)

        if self.state == STATE_SHIP_SELECT:
            self._render_ship_select()
        elif self.state == STATE_MENU:
            self._render_persona3_menu()
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

        # Render Active Buttons
        for btn in self.active_buttons:
            btn.draw(self.canvas)

        # Floating Toast Banner
        if self.toast_timer > 0:
            self._render_toast()

    def _render_toast(self):
        cx = SCREEN_WIDTH / 2
        cy = 50
        self.canvas.create_rectangle(
            cx - 200, cy - 16, cx + 200, cy + 16,
            fill="#060b18", outline=self.toast_color, width=2
        )
        self.canvas.create_text(
            cx, cy, text=self.toast_message,
            fill=self.toast_color, font=("Impact", 12), anchor="center"
        )

    def _render_gameplay(self):
        for pu in self.pickups: pu.draw(self.canvas)
        for e in self.enemies: e.draw(self.canvas)
        if self.boss and self.boss.alive: self.boss.draw(self.canvas)
        for p in self.projectiles: p.draw(self.canvas)
        if self.player and self.player.health > 0: self.player.draw(self.canvas)
        self.particle_mgr.draw(self.canvas)

        if self.player:
            self.hud.draw(
                self.canvas, self.player, self.score, self.wave,
                self.scrap, self.combo, self.combo_timer,
                self.boss, sound_engine.enabled
            )

    def _render_persona3_menu(self):
        """Draw authentic, high-impact Persona 3 aesthetic main menu."""
        # 1. Persona 3 Midnight Blue Angled Cut Background
        # Giant diagonal geometric split bars cutting across screen at -18 degrees
        band_pts_1 = [-100, -50, SCREEN_WIDTH + 200, 260, SCREEN_WIDTH + 200, 520, -100, 210]
        self.canvas.create_polygon(band_pts_1, fill="#040e24", outline="")

        band_pts_2 = [-100, 220, SCREEN_WIDTH + 200, 530, SCREEN_WIDTH + 200, 680, -100, 370]
        self.canvas.create_polygon(band_pts_2, fill="#071b40", outline="")

        # Persona 3 Accent Cerulean Speed Slashes
        slash_pts_1 = [-50, 480, SCREEN_WIDTH + 150, 720, SCREEN_WIDTH + 150, 730, -50, 490]
        self.canvas.create_polygon(slash_pts_1, fill="#0088cc", outline="")

        slash_pts_2 = [180, -30, 220, -30, 60, SCREEN_HEIGHT + 30, 20, SCREEN_HEIGHT + 30]
        self.canvas.create_polygon(slash_pts_2, fill="#051536", outline="")

        # 2. Draw Floating Moonlight Crystal Shards
        for s in self.p3_shards:
            sx, sy, sz, rot = s['x'], s['y'], s['size'], s['rot']
            cos_r, sin_r = math.cos(rot), math.sin(rot)
            # Diamond/Crystal Shard
            local_pts = [(0, -sz), (sz * 0.5, 0), (0, sz), (-sz * 0.5, 0)]
            world_pts = []
            for lx, ly in local_pts:
                world_pts.extend([sx + (lx * cos_r - ly * sin_r), sy + (lx * sin_r + ly * cos_r)])
            self.canvas.create_polygon(world_pts, fill=s['color'], outline="#00e5ff" if sz > 14 else "")

        # 3. Center-Right Hero Showcase & Dark Hour Lunar Clock Dial
        hx = 770
        hy = 360
        dial_r = 175

        # Concentric Lunar Ring (Persona 3 Clock motif)
        self.canvas.create_oval(hx - dial_r, hy - dial_r, hx + dial_r, hy + dial_r, outline="#08295c", width=3)
        self.canvas.create_oval(hx - dial_r + 14, hy - dial_r + 14, hx + dial_r - 14, hy + dial_r - 14, outline="#004488", width=1, dash=(3, 3))
        self.canvas.create_oval(hx - dial_r + 28, hy - dial_r + 28, hx + dial_r - 28, hy + dial_r - 28, outline="#00a2e8", width=1)

        # Rotating Radial Clock Tick Marks
        tick_rot = self.menu_tick * 0.18
        for i in range(24):
            ang = tick_rot + i * (math.pi / 12)
            inner_r = dial_r - (16 if i % 2 == 0 else 8)
            outer_r = dial_r
            tx1 = hx + math.cos(ang) * inner_r
            ty1 = hy + math.sin(ang) * inner_r
            tx2 = hx + math.cos(ang) * outer_r
            ty2 = hy + math.sin(ang) * outer_r
            self.canvas.create_line(tx1, ty1, tx2, ty2, fill="#00e5ff" if i % 6 == 0 else "#0055aa", width=2 if i % 6 == 0 else 1)

        # Persona 3 Stylized Radiant Halo behind ship
        halo_r = 90
        halo_pulse = math.sin(self.menu_tick * 2.5) * 6
        self.canvas.create_oval(
            hx - halo_r - halo_pulse, hy - halo_r - halo_pulse,
            hx + halo_r + halo_pulse, hy + halo_r + halo_pulse,
            outline="#00e5ff", width=2
        )

        # Hero Fighter Silhouette (High Contrast P3 Stylized Spacecraft)
        ship_ang = -0.28
        sca, ssa = math.cos(ship_ang), math.sin(ship_ang)
        hero_scale = 3.6
        # Nose, right wing, engine, notch, engine, left wing
        ship_base_pts = [
            (32 * hero_scale, 0),
            (-16 * hero_scale, 22 * hero_scale),
            (-8 * hero_scale, 9 * hero_scale),
            (-14 * hero_scale, 0),
            (-8 * hero_scale, -9 * hero_scale),
            (-16 * hero_scale, -22 * hero_scale),
        ]
        
        # Shadow Layer
        shadow_ship = []
        for px, py in ship_base_pts:
            wx = hx + 12 + (px * sca - py * ssa)
            wy = hy + 12 + (px * ssa + py * sca)
            shadow_ship.extend([wx, wy])
        self.canvas.create_polygon(shadow_ship, fill="#01040a", outline="")

        # Main Chassis Silhouette
        main_ship = []
        for px, py in ship_base_pts:
            wx = hx + (px * sca - py * ssa)
            wy = hy + (px * ssa + py * sca)
            main_ship.extend([wx, wy])
        self.canvas.create_polygon(main_ship, fill="#06183a", outline="#00e5ff", width=3)

        # Cockpit Core Glow
        cockpit_x = hx + (6 * hero_scale * sca)
        cockpit_y = hy + (6 * hero_scale * ssa)
        self.canvas.create_oval(cockpit_x - 6, cockpit_y - 6, cockpit_x + 6, cockpit_y + 6, fill="#ffffff", outline="#00e5ff", width=2)

        # Unit Telemetry Badge beneath Hero
        badge_box = [hx - 160, hy + 145, hx + 170, hy + 145, hx + 150, hy + 185, hx - 180, hy + 185]
        self.canvas.create_polygon(badge_box, fill="#05132d", outline="#0088cc", width=1)
        self.canvas.create_text(
            hx - 10, hy + 158,
            text="PROTAGONIST CHASSIS // TYPE-03 NOVA ARROWHEAD",
            fill="#00e5ff", font=("Impact", 11), anchor="center"
        )
        self.canvas.create_text(
            hx - 10, hy + 174,
            text="EVOKER LINK: SYNCHRONIZED  |  DARK HOUR STATUS: NOMINAL",
            fill="#88bbdd", font=("Consolas", 8, "bold"), anchor="center"
        )

        # 4. Top-Left Logo Block (P3 Slanted Cutout Stencil Style)
        # Giant Slanted Header Block
        logo_bg = [30, 35, 480, 35, 455, 128, 5, 128]
        self.canvas.create_polygon(logo_bg, fill="#030b1c", outline="#00e5ff", width=2)

        # Persona 3 Slanted Drop Shadow
        self.canvas.create_text(76, 76, text="CYBER NOVA", fill="#002b4d", font=("Impact", 48, "italic"), anchor="w")
        self.canvas.create_text(74, 74, text="CYBER NOVA", fill="#00e5ff", font=("Impact", 48, "italic"), anchor="w")
        self.canvas.create_text(72, 72, text="CYBER NOVA", fill="#ffffff", font=("Impact", 48, "italic"), anchor="w")

        # Subtitle Ribbon
        sub_ribbon = [60, 134, 460, 134, 442, 160, 42, 160]
        self.canvas.create_polygon(sub_ribbon, fill="#00e5ff", outline="")
        self.canvas.create_text(
            250, 147,
            text="ODYSSEY // REVOLUTIONARY SYSTEM 3.0",
            fill="#020817", font=("Impact", 12), anchor="center"
        )

        # 5. Top-Right "DARK HOUR / MOON PHASE" Telemetry Widget
        top_r_w = 420
        top_r_h = 75
        trx = SCREEN_WIDTH - top_r_w - 30
        try_y = 35
        m_widget_pts = [trx + 22, try_y, trx + top_r_w + 22, try_y, trx + top_r_w - 22, try_y + top_r_h, trx - 22, try_y + top_r_h]
        self.canvas.create_polygon(m_widget_pts, fill="#030b1c", outline="#00a2e8", width=1)

        # Moon Phase Icon & Readout
        self.canvas.create_text(
            trx + 35, try_y + 24,
            text="● FULL MOON // 100% LUNAR PHASE",
            fill="#00e5ff", font=("Impact", 13), anchor="w"
        )
        self.canvas.create_text(
            trx + 35, try_y + 44,
            text="DARK HOUR : ACTIVE // SECTOR 00-TA",
            fill="#ffffff", font=("Consolas", 10, "bold"), anchor="w"
        )

        hs = save_manager.profile.get("high_score", 0)
        mw = save_manager.profile.get("max_wave", 1)
        self.canvas.create_text(
            trx + 35, try_y + 60,
            text=f"HI-SCORE: {hs:07d}  |  MAX SECTOR: WAVE {mw}",
            fill=COLOR_YELLOW, font=("Consolas", 9, "bold"), anchor="w"
        )

        # 6. Left Side: The Iconic Persona 3 Ribbon Menu
        menu_start_x = 75
        menu_start_y = 220
        ribbon_w = 420
        ribbon_h = 62
        spacing = 76

        diff_info = DIFFICULTIES[self.difficulty]
        any_save = save_manager.has_any_save()

        # 01. NEW GAME
        b1 = Button(
            "new_game", menu_start_x, menu_start_y, ribbon_w, ribbon_h,
            "NEW GAME", self.start_new_run, col=COLOR_CYAN,
            subtext=f"LAUNCH EXPEDITION // {diff_info['name']}",
            style="p3_ribbon", badge="01"
        )
        if self.menu_selected_idx == 0:
            b1.hovered = True
        self.active_buttons.append(b1)

        # 02. SAVE FILES
        save_sub = "ARCHIVES (5 SLOTS AVAILABLE)" if any_save else "5 ARCHIVE SLOTS READY"
        b2 = Button(
            "save_files", menu_start_x, menu_start_y + spacing, ribbon_w, ribbon_h,
            "SAVE FILES", lambda: setattr(self, 'state', STATE_SAVES_MENU),
            col=COLOR_GREEN if any_save else "#446677", subtext=save_sub,
            style="p3_ribbon", badge="02"
        )
        if self.menu_selected_idx == 1:
            b2.hovered = True
        self.active_buttons.append(b2)

        # 03. DIFFICULTY
        b3 = Button(
            "difficulty", menu_start_x, menu_start_y + spacing * 2, ribbon_w, ribbon_h,
            f"DIFFICULTY : {diff_info['name'].split()[0]}", self.cycle_difficulty,
            col=diff_info['color'], subtext=diff_info['desc'][:42],
            style="p3_ribbon", badge="03"
        )
        if self.menu_selected_idx == 2:
            b3.hovered = True
        self.active_buttons.append(b3)

        # 04. PROTOCOL / CONTROLS
        b4 = Button(
            "controls", menu_start_x, menu_start_y + spacing * 3, ribbon_w, ribbon_h,
            "PROTOCOL MANUAL", lambda: setattr(self, 'state', STATE_CONTROLS),
            col="#7788aa", subtext="FLIGHT TELEMETRY & WEAPON CONTROL",
            style="p3_ribbon", badge="04"
        )
        if self.menu_selected_idx == 3:
            b4.hovered = True
        self.active_buttons.append(b4)

        # 7. Persona 3 Bottom Strip Navigation Guide
        bottom_strip = [-50, SCREEN_HEIGHT - 38, SCREEN_WIDTH + 50, SCREEN_HEIGHT - 38, SCREEN_WIDTH + 50, SCREEN_HEIGHT, -50, SCREEN_HEIGHT]
        self.canvas.create_polygon(bottom_strip, fill="#030a1c", outline="#0088cc", width=1)
        self.canvas.create_text(
            SCREEN_WIDTH / 2, SCREEN_HEIGHT - 19,
            text="[W / S / ARROWS] SELECT MENU  |  [ENTER / SPACE / CLICK] CONFIRM  |  [P / ESC] IN-FLIGHT PAUSE",
            fill="#55aadd", font=("Consolas", 10, "bold"), anchor="center"
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
        self.canvas.create_text(cx, by + 76, text=self.upgrade_message, fill=COLOR_WHITE, font=("Consolas", 11), anchor="center")

        ly = by + 100
        for i, item in enumerate(self.upgrade_mgr.upgrades):
            iy = ly + i * 42
            is_sel = (i == self.selected_upgrade_idx)
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
        
        if self.is_new_high_score:
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
            "▶ PLAY AGAIN", self.start_new_run, col=COLOR_YELLOW
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
