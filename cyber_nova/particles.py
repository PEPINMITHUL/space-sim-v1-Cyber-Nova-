"""
High-Performance Particle & Visual Effects Engine for CYBER NOVA.
Includes:
- Multi-layer 3D Parallax Starfield with Warp Streak mode
- Neon Spark Particles with drag & color decay
- Shockwave Expansion Rings for blasts & EMP
- Floating Neon Combat Text & Damage Numbers
- Dash Ghost / After-Image effects
"""

import math
import random
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_CYAN, COLOR_MAGENTA, COLOR_YELLOW,
    COLOR_GREEN, COLOR_WHITE, COLOR_RED, COLOR_PURPLE, COLOR_SHIELD
)


class Star:
    def __init__(self, width: int, height: int, layer: int):
        self.width = width
        self.height = height
        self.layer = layer  # 1: Distant, 2: Mid, 3: Near
        self.x = random.uniform(0, width)
        self.y = random.uniform(0, height)
        
        if layer == 1:
            self.base_speed = random.uniform(0.3, 0.7)
            self.size = 1.0
            self.color = random.choice(["#222644", "#30355e", "#3a3f70"])
        elif layer == 2:
            self.base_speed = random.uniform(1.0, 1.8)
            self.size = 1.8
            self.color = random.choice(["#556699", "#4488bb", "#6644aa"])
        else:
            self.base_speed = random.uniform(2.5, 4.0)
            self.size = 2.5
            self.color = random.choice([COLOR_WHITE, COLOR_CYAN, "#aaddff"])

    def update(self, player_vx: float, player_vy: float, warp_factor: float = 1.0):
        # Parallax drift against player velocity + downward cosmic drift
        drift_x = -player_vx * (0.05 * self.layer)
        drift_y = (self.base_speed * warp_factor) - player_vy * (0.05 * self.layer)
        
        self.x = (self.x + drift_x) % self.width
        self.y = (self.y + drift_y) % self.height

    def draw(self, canvas, warp_factor: float = 1.0):
        if warp_factor > 1.5 and self.layer >= 2:
            # Warp streak line
            trail_len = min(40.0, self.base_speed * warp_factor * 3.0)
            canvas.create_line(
                self.x, self.y,
                self.x, self.y - trail_len,
                fill=self.color, width=self.size
            )
        else:
            r = self.size
            canvas.create_oval(
                self.x - r, self.y - r,
                self.x + r, self.y + r,
                fill=self.color, outline=""
            )


class Starfield:
    def __init__(self, width: int = SCREEN_WIDTH, height: int = SCREEN_HEIGHT, count: int = 120):
        self.width = width
        self.height = height
        self.stars = []
        self.warp_factor = 1.0
        self.target_warp = 1.0
        
        for _ in range(int(count * 0.5)):
            self.stars.append(Star(width, height, layer=1))
        for _ in range(int(count * 0.35)):
            self.stars.append(Star(width, height, layer=2))
        for _ in range(int(count * 0.15)):
            self.stars.append(Star(width, height, layer=3))

    def trigger_warp(self, duration_frames: int = 45):
        self.target_warp = 7.0

    def update(self, player_vx: float = 0.0, player_vy: float = 0.0):
        # Smooth warp dampening
        self.warp_factor += (self.target_warp - self.warp_factor) * 0.1
        if self.target_warp > 1.0:
            self.target_warp -= 0.15
            if self.target_warp < 1.0:
                self.target_warp = 1.0

        for star in self.stars:
            star.update(player_vx, player_vy, self.warp_factor)

    def draw(self, canvas):
        for star in self.stars:
            star.draw(canvas, self.warp_factor)


class SparkParticle:
    def __init__(self, x: float, y: float, vx: float, vy: float, color: str,
                 size: float = 3.0, life: int = 30, drag: float = 0.94):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.initial_size = size
        self.life = life
        self.max_life = life
        self.drag = drag
        self.alive = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= self.drag
        self.vy *= self.drag
        self.life -= 1
        self.size = self.initial_size * (self.life / self.max_life)
        if self.life <= 0 or self.size <= 0.3:
            self.alive = False

    def draw(self, canvas):
        r = self.size
        canvas.create_oval(
            self.x - r, self.y - r,
            self.x + r, self.y + r,
            fill=self.color, outline=""
        )


class ShockwaveRing:
    def __init__(self, x: float, y: float, max_radius: float, color: str,
                 speed: float = 8.0, initial_width: int = 3):
        self.x = x
        self.y = y
        self.current_radius = 4.0
        self.max_radius = max_radius
        self.speed = speed
        self.color = color
        self.initial_width = initial_width
        self.alive = True

    def update(self):
        self.current_radius += self.speed
        if self.current_radius >= self.max_radius:
            self.alive = False

    def draw(self, canvas):
        progress = self.current_radius / self.max_radius
        line_w = max(1, int(self.initial_width * (1.0 - progress * 0.7)))
        r = self.current_radius
        canvas.create_oval(
            self.x - r, self.y - r,
            self.x + r, self.y + r,
            outline=self.color, width=line_w
        )


class FloatingText:
    def __init__(self, x: float, y: float, text: str, color: str,
                 size: int = 12, life: int = 40, vy: float = -1.5):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.size = size
        self.life = life
        self.max_life = life
        self.vy = vy
        self.alive = True

    def update(self):
        self.y += self.vy
        self.vy *= 0.95
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self, canvas):
        font = ("Impact" if "CRIT" in self.text or "BOSS" in self.text else "Consolas", self.size, "bold")
        canvas.create_text(
            self.x, self.y,
            text=self.text, fill=self.color,
            font=font, anchor="center"
        )


class DashGhost:
    def __init__(self, points: list[tuple[float, float]], color: str, life: int = 12):
        self.points = points
        self.color = color
        self.life = life
        self.max_life = life
        self.alive = True

    def update(self):
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self, canvas):
        if len(self.points) >= 3:
            flat_pts = []
            for px, py in self.points:
                flat_pts.extend([px, py])
            canvas.create_polygon(
                flat_pts, outline=self.color, fill="", width=1
            )


class ParticleManager:
    def __init__(self):
        self.particles: list[SparkParticle] = []
        self.shockwaves: list[ShockwaveRing] = []
        self.floating_texts: list[FloatingText] = []
        self.ghosts: list[DashGhost] = []

    def emit_sparks(self, x: float, y: float, count: int, colors: list[str],
                    speed_min: float = 2.0, speed_max: float = 7.0,
                    size_min: float = 2.0, size_max: float = 4.5, life: int = 25):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            spd = random.uniform(speed_min, speed_max)
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            col = random.choice(colors)
            sz = random.uniform(size_min, size_max)
            lf = random.randint(int(life * 0.7), int(life * 1.3))
            self.particles.append(SparkParticle(x, y, vx, vy, col, size=sz, life=lf))

    def emit_directional_sparks(self, x: float, y: float, count: int, base_angle: float,
                                spread: float, speed: float, colors: list[str], size: float = 3.0):
        for _ in range(count):
            angle = base_angle + random.uniform(-spread, spread)
            spd = speed * random.uniform(0.7, 1.3)
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            col = random.choice(colors)
            self.particles.append(SparkParticle(x, y, vx, vy, col, size=size, life=15, drag=0.88))

    def emit_shockwave(self, x: float, y: float, max_radius: float, color: str, speed: float = 9.0, width: int = 3):
        self.shockwaves.append(ShockwaveRing(x, y, max_radius, color, speed=speed, initial_width=width))

    def add_floating_text(self, x: float, y: float, text: str, color: str = COLOR_YELLOW, size: int = 12):
        self.floating_texts.append(FloatingText(x, y, text, color, size=size))

    def add_ghost(self, points: list[tuple[float, float]], color: str = COLOR_CYAN):
        self.ghosts.append(DashGhost(points, color))

    def update(self):
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive]

        for s in self.shockwaves:
            s.update()
        self.shockwaves = [s for s in self.shockwaves if s.alive]

        for t in self.floating_texts:
            t.update()
        self.floating_texts = [t for t in self.floating_texts if t.alive]

        for g in self.ghosts:
            g.update()
        self.ghosts = [g for g in self.ghosts if g.alive]

    def draw(self, canvas):
        for g in self.ghosts:
            g.draw(canvas)
        for s in self.shockwaves:
            s.draw(canvas)
        for p in self.particles:
            p.draw(canvas)
        for t in self.floating_texts:
            t.draw(canvas)

    def clear(self):
        self.particles.clear()
        self.shockwaves.clear()
        self.floating_texts.clear()
        self.ghosts.clear()
