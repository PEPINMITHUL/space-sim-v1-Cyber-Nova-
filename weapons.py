"""
Weapons and Projectile Systems for CYBER NOVA.
Includes player weapons (Pulse, Twin Plasma, Flak, Homing Missiles, Singularity)
and enemy projectiles (Darts, Heavy Orbs, Boss Spiral Bullets).
"""

import math
import random
from config import (
    COLOR_CYAN, COLOR_MAGENTA, COLOR_YELLOW,
    COLOR_GREEN, COLOR_PURPLE, COLOR_RED, COLOR_WHITE, COLOR_ORANGE
)


class Projectile:
    def __init__(self, x: float, y: float, vx: float, vy: float, damage: float,
                 color: str, radius: float = 3.0, is_player: bool = True,
                 piercing: int = 1, life: int = 70):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.damage = damage
        self.color = color
        self.radius = radius
        self.is_player = is_player
        self.piercing = piercing
        self.life = life
        self.max_life = life
        self.alive = True

    def update(self, bounds_w: int, bounds_h: int):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        
        # Out of bounds or expired
        if (self.x < -40 or self.x > bounds_w + 40 or
            self.y < -40 or self.y > bounds_h + 40 or
            self.life <= 0):
            self.alive = False

    def draw(self, canvas):
        r = self.radius
        # Draw glowing head
        canvas.create_oval(
            self.x - r, self.y - r,
            self.x + r, self.y + r,
            fill=self.color, outline=COLOR_WHITE if self.is_player else ""
        )
        # Draw motion tracer line
        spd = math.hypot(self.vx, self.vy)
        if spd > 1.0:
            tail_x = self.x - (self.vx / spd) * (r * 2.5)
            tail_y = self.y - (self.vy / spd) * (r * 2.5)
            canvas.create_line(
                self.x, self.y, tail_x, tail_y,
                fill=self.color, width=max(1, int(r * 0.7))
            )


class HomingMissile(Projectile):
    def __init__(self, x: float, y: float, angle: float, speed: float, damage: float):
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        super().__init__(x, y, vx, vy, damage, COLOR_GREEN, radius=4.0, is_player=True, life=90)
        self.speed = speed
        self.angle = angle
        self.turn_rate = 0.12
        self.trail_timer = 0

    def update_homing(self, enemies: list, particle_mgr, bounds_w: int, bounds_h: int):
        # Find closest alive enemy
        closest_enemy = None
        closest_dist = float('inf')
        for e in enemies:
            if getattr(e, 'alive', False):
                dist = math.hypot(e.x - self.x, e.y - self.y)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_enemy = e

        if closest_enemy:
            target_angle = math.atan2(closest_enemy.y - self.y, closest_enemy.x - self.x)
            # Angular distance wrap
            diff = (target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi
            self.angle += max(-self.turn_rate, min(self.turn_rate, diff))
            self.vx = math.cos(self.angle) * self.speed
            self.vy = math.sin(self.angle) * self.speed

        # Emit smoke sparks behind missile
        self.trail_timer += 1
        if self.trail_timer % 2 == 0 and particle_mgr:
            tail_x = self.x - math.cos(self.angle) * 7.0
            tail_y = self.y - math.sin(self.angle) * 7.0
            particle_mgr.emit_sparks(tail_x, tail_y, 1, [COLOR_GREEN, COLOR_YELLOW, "#446644"],
                                     speed_min=0.5, speed_max=2.0, size_min=1.5, size_max=2.5, life=12)

        self.update(bounds_w, bounds_h)


class SingularityVortex(Projectile):
    def __init__(self, x: float, y: float, vx: float, vy: float, damage_per_tick: float):
        super().__init__(x, y, vx, vy, damage_per_tick, COLOR_PURPLE, radius=14.0, is_player=True, life=140)
        self.pull_radius = 160.0
        self.pulse = 0.0

    def update_vortex(self, enemies: list, particle_mgr, bounds_w: int, bounds_h: int):
        self.pulse += 0.2
        # Gravity suction effect on nearby enemies
        for e in enemies:
            if getattr(e, 'alive', False):
                dx = self.x - e.x
                dy = self.y - e.y
                dist = math.hypot(dx, dy)
                if 0 < dist < self.pull_radius:
                    force = (1.0 - (dist / self.pull_radius)) * 2.8
                    e.x += (dx / dist) * force
                    e.y += (dy / dist) * force

        if particle_mgr and random.random() < 0.35:
            particle_mgr.emit_sparks(self.x, self.y, 2, [COLOR_PURPLE, COLOR_MAGENTA, COLOR_CYAN],
                                     speed_min=1.0, speed_max=4.0, size_min=2.0, size_max=3.5, life=14)

        self.vx *= 0.96
        self.vy *= 0.96
        self.update(bounds_w, bounds_h)

    def draw(self, canvas):
        r = self.radius + math.sin(self.pulse) * 3.0
        # Outer event horizon ring
        canvas.create_oval(
            self.x - r - 6, self.y - r - 6,
            self.x + r + 6, self.y + r + 6,
            outline=COLOR_MAGENTA, width=2
        )
        # Inner black hole core
        canvas.create_oval(
            self.x - r, self.y - r,
            self.x + r, self.y + r,
            fill="#050010", outline=COLOR_PURPLE, width=3
        )


class WeaponDefinition:
    def __init__(self, name: str, key: str, cooldown: float, energy_cost: float,
                 color: str, description: str, unlocked: bool = False):
        self.name = name
        self.key = key
        self.cooldown = cooldown
        self.energy_cost = energy_cost
        self.color = color
        self.description = description
        self.unlocked = unlocked


# All available weapon types
WEAPONS_DATA = {
    "pulse": WeaponDefinition(
        name="PULSE CANNON",
        key="1",
        cooldown=0.14,
        energy_cost=3.0,
        color=COLOR_CYAN,
        description="High-velocity ionized particle needle.",
        unlocked=True
    ),
    "twin": WeaponDefinition(
        name="TWIN PLASMA",
        key="2",
        cooldown=0.22,
        energy_cost=7.0,
        color=COLOR_MAGENTA,
        description="Dual synchronized heavy plasma bolts.",
        unlocked=True
    ),
    "flak": WeaponDefinition(
        name="SCATTER FLAK",
        key="3",
        cooldown=0.44,
        energy_cost=15.0,
        color=COLOR_YELLOW,
        description="Conical spread of shrapnel pellets.",
        unlocked=False
    ),
    "homing": WeaponDefinition(
        name="HOMING PODS",
        key="4",
        cooldown=0.38,
        energy_cost=18.0,
        color=COLOR_GREEN,
        description="Smart micro-missiles with target lock.",
        unlocked=False
    ),
    "singularity": WeaponDefinition(
        name="SINGULARITY CORE",
        key="5",
        cooldown=1.20,
        energy_cost=35.0,
        color=COLOR_PURPLE,
        description="Micro-black hole tearing through targets.",
        unlocked=False
    )
}
