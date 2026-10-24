"""
Heads-Up Display (HUD) and In-Game Cyberpunk Interface for CYBER NOVA.
Includes:
- Health, Shield, and Energy reactor gauges
- Wave tracker, Score counter, and Combo Multiplier bar
- Weapon selector dock with cooldown & unlock indicators
- EMP charges & Dash meter
- Boss health display with phase indicator
- Floating notifications & Sound/Mute indicator
"""

import math
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_CYAN, COLOR_MAGENTA, COLOR_YELLOW,
    COLOR_GREEN, COLOR_WHITE, COLOR_RED, COLOR_SHIELD,
    COLOR_PURPLE, COLOR_ORANGE, COLOR_UI_BG, COLOR_UI_BORDER
)
from weapons import WEAPONS_DATA


class HUD:
    def __init__(self):
        pass

    def draw(self, canvas, player, score: int, wave: int, scrap: int,
             combo: int, combo_timer: float, boss=None, sound_enabled: bool = True):
        # 1. Top Left: Health & Shield Gauges
        self._draw_gauges(canvas, player)

        # 2. Top Center: Wave & Boss Bar (if active)
        if boss and boss.alive:
            self._draw_boss_bar(canvas, boss)
        else:
            self._draw_wave_banner(canvas, wave)

        # 3. Top Right: Score, High Score & Scrap Wallet
        self._draw_score_panel(canvas, score, scrap, combo, combo_timer)

        # 4. Bottom Center: Weapon Arsenal Dock & Ability Meters
        self._draw_bottom_dock(canvas, player)

        # 5. Top Right Corner: Sound Status
        sound_text = "🔊 SFX ON [M]" if sound_enabled else "🔇 SFX OFF [M]"
        canvas.create_text(
            SCREEN_WIDTH - 20, SCREEN_HEIGHT - 20,
            text=sound_text, fill="#556677",
            font=("Consolas", 10), anchor="e"
        )

    def _draw_gauges(self, canvas, player):
        start_x = 20
        start_y = 20
        bar_w = 180
        bar_h = 12

        # Panel background
        canvas.create_rectangle(
            start_x - 8, start_y - 8,
            start_x + bar_w + 55, start_y + 60,
            fill="#090c1a", outline="#1c2544", width=1
        )

        # Hull Health Bar
        health_ratio = max(0.0, min(1.0, player.health / player.max_health)) if player.max_health > 0 else 0
        canvas.create_rectangle(start_x, start_y, start_x + bar_w, start_y + bar_h, fill="#2b0d13", outline="")
        canvas.create_rectangle(start_x, start_y, start_x + (bar_w * health_ratio), start_y + bar_h, fill=COLOR_RED, outline="")
        canvas.create_rectangle(start_x, start_y, start_x + bar_w, start_y + bar_h, outline="#ff4466", width=1)
        canvas.create_text(start_x + bar_w + 8, start_y + bar_h / 2, text=f"HP {int(player.health)}", fill=COLOR_WHITE, font=("Consolas", 10, "bold"), anchor="w")

        # Plasma Shield Bar
        shield_ratio = max(0.0, min(1.0, player.shield / player.max_shield)) if player.max_shield > 0 else 0
        s_y = start_y + 18
        canvas.create_rectangle(start_x, s_y, start_x + bar_w, s_y + bar_h, fill="#081a2e", outline="")
        canvas.create_rectangle(start_x, s_y, start_x + (bar_w * shield_ratio), s_y + bar_h, fill=COLOR_CYAN, outline="")
        canvas.create_rectangle(start_x, s_y, start_x + bar_w, s_y + bar_h, outline=COLOR_SHIELD, width=1)
        canvas.create_text(start_x + bar_w + 8, s_y + bar_h / 2, text=f"SH {int(player.shield)}", fill=COLOR_CYAN, font=("Consolas", 10, "bold"), anchor="w")

        # Energy / Reactor Bar
        energy_ratio = max(0.0, min(1.0, player.energy / player.max_energy)) if player.max_energy > 0 else 0
        e_y = start_y + 36
        e_col = COLOR_ORANGE if player.overclock_timer > 0 else COLOR_YELLOW
        canvas.create_rectangle(start_x, e_y, start_x + bar_w, e_y + 6, fill="#221b06", outline="")
        canvas.create_rectangle(start_x, e_y, start_x + (bar_w * energy_ratio), e_y + 6, fill=e_col, outline="")
        lbl = "OVERCLOCK!" if player.overclock_timer > 0 else "REACTOR"
        canvas.create_text(start_x + bar_w + 8, e_y + 3, text=lbl, fill=e_col, font=("Consolas", 8, "bold"), anchor="w")

    def _draw_wave_banner(self, canvas, wave: int):
        cx = SCREEN_WIDTH / 2
        canvas.create_text(
            cx, 24,
            text=f"— SECTOR WAVE {wave} —",
            fill=COLOR_CYAN, font=("Impact", 16), anchor="center"
        )
        canvas.create_text(
            cx, 44,
            text="[B] TECH BAY UPGRADES",
            fill="#557799", font=("Consolas", 9, "bold"), anchor="center"
        )

    def _draw_boss_bar(self, canvas, boss):
        cx = SCREEN_WIDTH / 2
        bar_w = 460
        bar_h = 16
        bx = cx - (bar_w / 2)
        by = 22

        # Outer casing
        canvas.create_rectangle(bx - 4, by - 4, bx + bar_w + 4, by + bar_h + 4, fill="#120412", outline=COLOR_MAGENTA, width=2)
        
        ratio = max(0.0, min(1.0, boss.health / boss.max_health)) if boss.max_health > 0 else 0
        col = COLOR_RED if boss.phase_2 else COLOR_MAGENTA
        canvas.create_rectangle(bx, by, bx + (bar_w * ratio), by + bar_h, fill=col, outline="")

        # Title
        title = f"⚠️ {boss.name} ⚠️" if not boss.phase_2 else f"🔥 {boss.name} [ENRAGED] 🔥"
        canvas.create_text(cx, by - 12, text=title, fill=col, font=("Impact", 13), anchor="center")

        # Shield indicator
        if boss.has_active_shields():
            active_count = sum(1 for n in boss.shield_nodes if n.alive)
            canvas.create_text(cx, by + bar_h + 10, text=f"DEFENSIVE NODES ACTIVE: {active_count}/3", fill=COLOR_CYAN, font=("Consolas", 9, "bold"), anchor="center")

    def _draw_score_panel(self, canvas, score: int, scrap: int, combo: int, combo_timer: float):
        rx = SCREEN_WIDTH - 20
        ry = 20

        # Score
        canvas.create_text(
            rx, ry,
            text=f"SCORE {score:07d}",
            fill=COLOR_WHITE, font=("Impact", 18), anchor="e"
        )

        # Scrap currency
        canvas.create_text(
            rx, ry + 24,
            text=f"⚡ SCRAP {scrap}",
            fill=COLOR_YELLOW, font=("Consolas", 13, "bold"), anchor="e"
        )

        # Combo Multiplier
        if combo > 1:
            combo_col = COLOR_ORANGE if combo < 4 else COLOR_MAGENTA
            canvas.create_text(
                rx, ry + 48,
                text=f"COMBO x{combo}!",
                fill=combo_col, font=("Impact", 14), anchor="e"
            )
            # Combo meter bar
            meter_w = 90
            meter_ratio = max(0.0, min(1.0, combo_timer / 3.0))
            canvas.create_rectangle(rx - meter_w, ry + 62, rx, ry + 66, fill="#221100", outline="")
            canvas.create_rectangle(rx - (meter_w * meter_ratio), ry + 62, rx, ry + 66, fill=combo_col, outline="")

    def _draw_bottom_dock(self, canvas, player):
        cx = SCREEN_WIDTH / 2
        cy = SCREEN_HEIGHT - 38

        # Arsenal Slots (1 to 5)
        weapon_keys = ["pulse", "twin", "flak", "homing", "singularity"]
        slot_w = 70
        spacing = 8
        total_w = len(weapon_keys) * slot_w + (len(weapon_keys) - 1) * spacing
        start_x = cx - total_w / 2

        for i, w_key in enumerate(weapon_keys):
            w_def = WEAPONS_DATA[w_key]
            sx = start_x + i * (slot_w + spacing)
            sy = cy - 20
            
            is_active = (player.current_weapon == w_key)
            is_unlocked = (w_key in player.unlocked_weapons)

            # Slot border & fill
            border_col = w_def.color if is_active else ("#2a3558" if is_unlocked else "#141829")
            fill_col = "#0e152e" if is_unlocked else "#060814"
            w_width = 2 if is_active else 1

            canvas.create_rectangle(
                sx, sy, sx + slot_w, sy + 38,
                fill=fill_col, outline=border_col, width=w_width
            )

            # Slot number & weapon name
            name_short = w_def.name.split()[0] if is_unlocked else "LOCKED"
            text_col = COLOR_WHITE if is_active else ("#7888aa" if is_unlocked else "#444b66")
            canvas.create_text(sx + 5, sy + 4, text=f"[{i+1}]", fill="#445577", font=("Consolas", 8, "bold"), anchor="nw")
            canvas.create_text(sx + slot_w / 2, sy + 22, text=name_short, fill=text_col, font=("Consolas", 9, "bold"), anchor="center")

        # Left of dock: Dash Meter
        dash_x = start_x - 90
        dash_ready = (player.dash_cooldown <= 0)
        dash_col = COLOR_CYAN if dash_ready else "#446677"
        dash_txt = "DASH [READY]" if dash_ready else f"DASH [{player.dash_cooldown:.1f}s]"
        canvas.create_text(dash_x, cy, text=dash_txt, fill=dash_col, font=("Consolas", 10, "bold"), anchor="e")

        # Right of dock: EMP charges
        emp_x = start_x + total_w + 20
        emp_pips = " ".join(["[Ω]" for _ in range(player.emp_charges)]) + " ".join(["[ ]" for _ in range(player.max_emp_charges - player.emp_charges)])
        canvas.create_text(emp_x, cy, text=f"EMP (Q): {emp_pips}", fill=COLOR_PURPLE, font=("Consolas", 10, "bold"), anchor="w")
