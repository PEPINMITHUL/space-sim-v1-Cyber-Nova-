"""
Loot Drops and Pickups for CYBER NOVA:
- Scrap / Energy Cores (Currency for upgrades)
- Nano-Repair Kits (Health)
- Shield Overcharger
- Overclock Matrix (Temporary Rapid-Fire buff)
- EMP Battery (Refills EMP bomb)
"""

import math
import random
from config import (
    COLOR_CYAN, COLOR_YELLOW, COLOR_GREEN,
    COLOR_RED, COLOR_PURPLE, COLOR_WHITE, COLOR_ORANGE
)


class Pickup:
    def __init__(self, x: float, y: float, pickup_type: str, value: int = 1):
        self.x = x
        self.y = y
        self.pickup_type = pickup_type
        self.value = value
        
        # Initial pop velocity
        angle = random.uniform(0, 2 * math.pi)
        pop_speed = random.uniform(1.5, 4.0)
        self.vx = math.cos(angle) * pop_speed
        self.vy = math.sin(angle) * pop_speed
        
        self.alive = True
        self.life = 700  # Stays around ~11 seconds
        self.pulse = random.uniform(0, 6.28)
        self.radius = 8.0

        if pickup_type == "scrap":
            self.color = COLOR_YELLOW
            self.radius = 5.0
        elif pickup_type == "health":
            self.color = COLOR_GREEN
            self.radius = 8.0
        elif pickup_type == "shield":
            self.color = COLOR_CYAN
            self.radius = 8.0
        elif pickup_type == "overclock":
            self.color = COLOR_ORANGE
            self.radius = 9.0
        elif pickup_type == "emp":
            self.color = COLOR_PURPLE
            self.radius = 9.0
        else:
            self.color = COLOR_WHITE

    def update(self, player_x: float, player_y: float, magnet_range: float):
        self.pulse += 0.12
        self.life -= 1
        if self.life <= 0:
            self.alive = False
            return

        # Natural friction
        self.vx *= 0.94
        self.vy *= 0.94
        self.x += self.vx
        self.y += self.vy

        # Magnetism towards player
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.hypot(dx, dy)
        if dist < magnet_range and dist > 0.1:
            pull_accel = (1.0 - (dist / magnet_range)) * 14.0 + 3.0
            self.x += (dx / dist) * pull_accel
            self.y += (dy / dist) * pull_accel

    def draw(self, canvas):
        r = self.radius + math.sin(self.pulse) * 1.5
        
        # Flashing when close to despawning
        if self.life < 100 and (self.life // 8) % 2 == 0:
            return

        if self.pickup_type == "scrap":
            # Diamond shape for scrap
            points = [
                self.x, self.y - r,
                self.x + r, self.y,
                self.x, self.y + r,
                self.x - r, self.y
            ]
            canvas.create_polygon(points, fill=self.color, outline=COLOR_WHITE, width=1)
        elif self.pickup_type == "health":
            # Cross icon for health
            canvas.create_oval(self.x - r, self.y - r, self.x + r, self.y + r, fill="#003311", outline=self.color, width=2)
            arm = r * 0.6
            w = 2
            canvas.create_line(self.x - arm, self.y, self.x + arm, self.y, fill=self.color, width=w)
            canvas.create_line(self.x, self.y - arm, self.x, self.y + arm, fill=self.color, width=w)
        elif self.pickup_type == "shield":
            # Shield ring
            canvas.create_oval(self.x - r, self.y - r, self.x + r, self.y + r, fill="#001833", outline=self.color, width=2)
            canvas.create_oval(self.x - r*0.5, self.y - r*0.5, self.x + r*0.5, self.y + r*0.5, fill=COLOR_CYAN, outline="")
        elif self.pickup_type == "overclock":
            # Lightning bolt star
            canvas.create_oval(self.x - r, self.y - r, self.x + r, self.y + r, fill="#331800", outline=self.color, width=2)
            canvas.create_text(self.x, self.y, text="⚡", fill=COLOR_ORANGE, font=("Arial", int(r * 1.2), "bold"))
        elif self.pickup_type == "emp":
            # EMP orb
            canvas.create_oval(self.x - r, self.y - r, self.x + r, self.y + r, fill="#220033", outline=self.color, width=2)
            canvas.create_text(self.x, self.y, text="Ω", fill=COLOR_PURPLE, font=("Consolas", int(r * 1.2), "bold"))
