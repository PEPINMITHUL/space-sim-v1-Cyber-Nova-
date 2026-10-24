"""
UI Theme utilities for Cyber Nova – Persona‑3 style.
Provides:
* draw_menu_background(canvas) – slanted bands, lunar dial, floating shards.
* draw_ribbon_button(canvas, btn) – renders a Button in the p3 ribbon style.
* helper constants for geometry and colors.
"""

import random
from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    COLOR_BG,
    COLOR_CYAN,
    COLOR_ORANGE,
    COLOR_PURPLE,
    COLOR_RED,
    COLOR_GREEN,
    COLOR_BLUE,
    COLOR_WHITE,
    COLOR_YELLOW,
)

# Pre‑generated shard data used for the background effect
# Each shard is a dict with x, y, size, speed, color.
# Generated once at import time to avoid recomputation each frame.
_P3_SHARDS: list[dict] = []
for _ in range(30):
    _P3_SHARDS.append({
        "x": random.uniform(0, SCREEN_WIDTH),
        "y": random.uniform(0, SCREEN_HEIGHT),
        "size": random.uniform(2, 6),
        "speed": random.uniform(0.2, 0.8),
        "color": random.choice([COLOR_CYAN, COLOR_ORANGE, COLOR_PURPLE, COLOR_RED]),
    })


def _draw_slanted_bands(canvas):
    """Draw three slanted background bands – the classic Persona‑3 backdrop."""
    band_h = SCREEN_HEIGHT // 6
    slant = 22
    colors = ["#01040a", "#001824", "#032a4b"]
    for i, col in enumerate(colors):
        y = i * band_h
        pts = [
            0 + slant, y,
            SCREEN_WIDTH + slant, y,
            SCREEN_WIDTH - slant, y + band_h,
            -slant, y + band_h,
        ]
        canvas.create_polygon(pts, fill=col, outline="")


def _draw_lunar_dial(canvas):
    """Draw a dark‑hour moon in the centre top of the screen."""
    cx, cy = SCREEN_WIDTH // 2, 160
    canvas.create_oval(
        cx - 80, cy - 80, cx + 80, cy + 80,
        fill="#071a3d", outline="#00a2e8", width=3,
    )


def _draw_floating_shards(canvas):
    """Animate the pre‑generated shards – tiny luminous particles."""
    for s in _P3_SHARDS:
        s["y"] -= s["speed"]
        if s["y"] < -10:
            s["y"] = SCREEN_HEIGHT + 10
            s["x"] = random.uniform(0, SCREEN_WIDTH)
        canvas.create_oval(
            s["x"], s["y"], s["x"] + s["size"], s["y"] + s["size"],
            fill=s["color"], outline="",
        )


def draw_menu_background(canvas):
    """Public helper – call from Game._draw_menu_background()."""
    _draw_slanted_bands(canvas)
    _draw_lunar_dial(canvas)
    _draw_floating_shards(canvas)


def draw_ribbon_button(canvas, btn):
    """Render a Button instance using the Persona‑3 ribbon style.
    The Button class already stores geometry and state (hovered, enabled, badge).
    This function mirrors the logic formerly embedded in Button.draw()."""
    # Geometry shortcuts
    bx, by, bw, bh = btn.x, btn.y, btn.w, btn.h
    offset = 26 if btn.hovered else 0
    slant = 22
    bx += offset
    # Polygon points for the ribbon
    pts = [
        bx + slant, by,
        bx + bw + slant, by,
        bx + bw - slant, by + bh,
        bx - slant, by + bh,
    ]
    # Determine colours based on state
    if not btn.enabled:
        fill_col = "#040814"
        outline_col = "#152238"
        txt_col = "#384a66"
        badge_bg = "#0d1424"
        badge_txt = "#384a66"
    elif btn.hovered:
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
    # Shadow for depth
    shadow = [
        bx + slant + 4, by + 4,
        bx + bw + slant + 4, by + 4,
        bx + bw - slant + 4, by + bh + 4,
        bx - slant + 4, by + bh + 4,
    ]
    canvas.create_polygon(shadow, fill="#01040a", outline="")
    # Main ribbon
    canvas.create_polygon(pts, fill=fill_col, outline=outline_col, width=2 if btn.hovered else 1)
    # Badge, if present
    if getattr(btn, "badge", None):
        badge_w = 46
        badge_pts = [
            bx + slant + 2, by + 2,
            bx + slant + badge_w, by + 2,
            bx + slant + badge_w - 7, by + bh - 2,
            bx - slant + 14, by + bh - 2,
        ]
        canvas.create_polygon(badge_pts, fill=badge_bg, outline=outline_col, width=1)
        canvas.create_text(
            bx + slant + badge_w / 2 - 4, by + bh / 2,
            text=btn.badge, fill=badge_txt,
            font=("Impact", 15, "bold"), anchor="center",
        )
    # Chevron cursor on hover
    if btn.hovered:
        arrow_x = bx - slant - 16
        arrow_pts = [
            arrow_x - 4, by + bh * 0.22,
            arrow_x + 10, by + bh * 0.5,
            arrow_x - 4, by + bh * 0.78,
        ]
        canvas.create_polygon(arrow_pts, fill="#00e5ff", outline="#ffffff", width=1)
    # Main text & optional subtext
    text_x = bx + slant + (58 if getattr(btn, "badge", None) else 22)
    canvas.create_text(
        text_x, by + bh * 0.34,
        text=btn.text, fill=txt_col, font=("Impact", 16), anchor="w",
    )
    if btn.subtext:
        sub_col = "#003355" if btn.hovered else "#5599cc"
        canvas.create_text(
            text_x, by + bh * 0.74,
            text=btn.subtext, fill=sub_col,
            font=("Consolas", 8, "bold"), anchor="w",
        )
