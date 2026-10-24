"""
Enemy Ships and AI Behaviors for CYBER NOVA:
- DroneKamikaze: Rapid swarmer tracking player
- ViperScout: Agile strafer shooting energy darts
- CruiserBattleship: Heavy tank firing spread volleys
- StealthPhantom: Teleports/cloaks for ambush attacks
"""

import math
import random
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_RED, COLOR_ORANGE, COLOR_YELLOW,
    COLOR_WHITE, COLOR_PURPLE, COLOR_MAGENTA, COLOR_CYAN
)
from weapons import Projectile
from sound_engine import sound_engine


class EnemyBase:
    def __init__(self, x: float, y: float, health: float, speed: float, radius: float, score_val: int):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.angle = 0.0
        self.health = health
        self.max_health = health
        self.speed = speed
        self.radius = radius
        self.score_val = score_val
        self.alive = True
        self.stun_timer = 0.0
        self.hit_flash = 0.0

    def take_damage(self, amount: float, is_crit: bool, particle_mgr) -> bool:
        """Apply damage and floating combat text."""
        self.health -= amount
        self.hit_flash = 0.12

        if particle_mgr:
            txt = f"{int(amount)}" if not is_crit else f"CRIT {int(amount)}!"
            col = COLOR_YELLOW if not is_crit else COLOR_MAGENTA
            particle_mgr.add_floating_text(self.x, self.y - 12, txt, col, size=11 if not is_crit else 14)
            particle_mgr.emit_sparks(self.x, self.y, 4, [COLOR_WHITE, COLOR_RED, COLOR_ORANGE], speed_min=2.0, speed_max=5.0)

        if self.health <= 0:
            self.alive = False
            sound_engine.play("explosion_sm")
            if particle_mgr:
                particle_mgr.emit_sparks(self.x, self.y, 16, [COLOR_RED, COLOR_ORANGE, COLOR_YELLOW, COLOR_WHITE],
                                         speed_min=2.5, speed_max=6.5, size_min=2.0, size_max=4.5)
                particle_mgr.emit_shockwave(self.x, self.y, 35.0, COLOR_ORANGE, speed=7.0, width=2)
            return False
        return True

    def update_base(self, dt: float):
        if self.hit_flash > 0:
            self.hit_flash -= dt
        if self.stun_timer > 0:
            self.stun_timer -= dt
            self.vx *= 0.88
            self.vy *= 0.88
            self.x += self.vx
            self.y += self.vy
            return False  # Stunned, skip action
        return True


class DroneKamikaze(EnemyBase):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, health=22.0, speed=4.2, radius=12.0, score_val=100)
        self.pulse = random.uniform(0, 6.28)

    def update(self, dt: float, player_x: float, player_y: float, particle_mgr) -> list[Projectile]:
        if not self.update_base(dt):
            return []

        self.pulse += dt * 8.0
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.angle = math.atan2(dy, dx)
            self.vx += math.cos(self.angle) * 0.4
            self.vy += math.sin(self.angle) * 0.4
            # Cap speed
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
        # Sharp red needle
        pts = [
            (14, 0),
            (-10, 8),
            (-6, 0),
            (-10, -8)
        ]
        world_pts = []
        for px, py in pts:
            wx = self.x + (px * ca - py * sa)
            wy = self.y + (px * sa + py * ca)
            world_pts.extend([wx, wy])

        col = COLOR_WHITE if self.hit_flash > 0 else COLOR_RED
        canvas.create_polygon(world_pts, fill="#2b050b", outline=col, width=2)
        # Pulsing eye
        canvas.create_oval(self.x - 2, self.y - 2, self.x + 2, self.y + 2, fill=COLOR_YELLOW, outline="")


class ViperScout(EnemyBase):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, health=50.0, speed=3.2, radius=15.0, score_val=220)
        self.shoot_timer = random.uniform(1.0, 2.2)
        self.orbit_angle = random.uniform(0, 6.28)
        self.orbit_dist = random.uniform(180, 250)

    def update(self, dt: float, player_x: float, player_y: float, particle_mgr) -> list[Projectile]:
        if not self.update_base(dt):
            return []

        self.shoot_timer -= dt
        self.orbit_angle += dt * 0.9

        # Target point orbiting player
        target_x = player_x + math.cos(self.orbit_angle) * self.orbit_dist
        target_y = player_y + math.sin(self.orbit_angle) * self.orbit_dist

        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)
        if dist > 5:
            move_ang = math.atan2(dy, dx)
            self.vx += math.cos(move_ang) * 0.35
            self.vy += math.sin(move_ang) * 0.35
            spd = math.hypot(self.vx, self.vy)
            if spd > self.speed:
                self.vx = (self.vx / spd) * self.speed
                self.vy = (self.vy / spd) * self.speed

        self.vx *= 0.96
        self.vy *= 0.96
        self.x += self.vx
        self.y += self.vy

        # Aim towards player
        self.angle = math.atan2(player_y - self.y, player_x - self.x)

        projectiles = []
        if self.shoot_timer <= 0:
            self.shoot_timer = random.uniform(1.8, 2.6)
            sound_engine.play("laser")
            b_spd = 8.5
            b_vx = math.cos(self.angle) * b_spd
            b_vy = math.sin(self.angle) * b_spd
            projectiles.append(Projectile(self.x, self.y, b_vx, b_vy, damage=14.0, color=COLOR_ORANGE, radius=3.5, is_player=False))
            if particle_mgr:
                particle_mgr.emit_sparks(self.x, self.y, 3, [COLOR_ORANGE, COLOR_YELLOW], speed_min=2.0, speed_max=4.0)

        return projectiles

    def draw(self, canvas):
        ca = math.cos(self.angle)
        sa = math.sin(self.angle)
        pts = [
            (16, 0),
            (-12, 12),
            (-4, 4),
            (-12, -12)
        ]
        world_pts = []
        for px, py in pts:
            wx = self.x + (px * ca - py * sa)
            wy = self.y + (px * sa + py * ca)
            world_pts.extend([wx, wy])

        col = COLOR_WHITE if self.hit_flash > 0 else COLOR_ORANGE
        canvas.create_polygon(world_pts, fill="#2b1505", outline=col, width=2)


class CruiserBattleship(EnemyBase):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, health=140.0, speed=1.8, radius=22.0, score_val=450)
        self.fire_timer = 2.0

    def update(self, dt: float, player_x: float, player_y: float, particle_mgr) -> list[Projectile]:
        if not self.update_base(dt):
            return []

        self.fire_timer -= dt

        # Slowly advance towards player
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.hypot(dx, dy)
        if dist > 140:
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

        projectiles = []
        if self.fire_timer <= 0:
            self.fire_timer = 2.2
            sound_engine.play("plasma")
            # 3-way spread volley
            base_ang = math.atan2(player_y - self.y, player_x - self.x)
            for offset in (-0.26, 0.0, 0.26):
                ang = base_ang + offset
                b_spd = 7.0
                vx = math.cos(ang) * b_spd
                vy = math.sin(ang) * b_spd
                projectiles.append(Projectile(self.x, self.y, vx, vy, damage=18.0, color=COLOR_RED, radius=4.5, is_player=False))
            if particle_mgr:
                particle_mgr.emit_shockwave(self.x, self.y, 25.0, COLOR_RED, speed=5.0, width=2)

        return projectiles

    def draw(self, canvas):
        col = COLOR_WHITE if self.hit_flash > 0 else COLOR_MAGENTA
        # Heavy Hexagonal Hull
        pts = []
        for i in range(6):
            ang = self.angle + i * (math.pi / 3)
            pts.extend([self.x + math.cos(ang) * self.radius, self.y + math.sin(ang) * self.radius])
        canvas.create_polygon(pts, fill="#1a0026", outline=col, width=2)

        # Core reactor
        canvas.create_oval(self.x - 6, self.y - 6, self.x + 6, self.y + 6, fill=COLOR_RED, outline=COLOR_WHITE)


class StealthPhantom(EnemyBase):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, health=65.0, speed=3.8, radius=14.0, score_val=350)
        self.cloak_timer = 3.0
        self.is_cloaked = False
        self.teleport_cooldown = 4.5

    def update(self, dt: float, player_x: float, player_y: float, particle_mgr) -> list[Projectile]:
        if not self.update_base(dt):
            return []

        self.cloak_timer -= dt
        if self.cloak_timer <= 0:
            self.is_cloaked = not self.is_cloaked
            self.cloak_timer = 2.5 if self.is_cloaked else 3.5
            if particle_mgr:
                particle_mgr.emit_shockwave(self.x, self.y, 30.0, COLOR_PURPLE, speed=6.0, width=2)

        # If cloaked, move swiftly to flank player's rear
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.hypot(dx, dy)
        self.angle = math.atan2(dy, dx)

        if dist > 60:
            self.vx += math.cos(self.angle) * 0.4
            self.vy += math.sin(self.angle) * 0.4
            spd = math.hypot(self.vx, self.vy)
            max_spd = self.speed * (1.4 if self.is_cloaked else 1.0)
            if spd > max_spd:
                self.vx = (self.vx / spd) * max_spd
                self.vy = (self.vy / spd) * max_spd

        self.vx *= 0.95
        self.vy *= 0.95
        self.x += self.vx
        self.y += self.vy

        projectiles = []
        # Decloak ambush burst
        if not self.is_cloaked and random.random() < 0.02:
            sound_engine.play("shotgun")
            for _ in range(4):
                spread = self.angle + random.uniform(-0.35, 0.35)
                vx = math.cos(spread) * 8.0
                vy = math.sin(spread) * 8.0
                projectiles.append(Projectile(self.x, self.y, vx, vy, damage=12.0, color=COLOR_PURPLE, radius=3.0, is_player=False))
            if particle_mgr:
                particle_mgr.emit_sparks(self.x, self.y, 6, [COLOR_PURPLE, COLOR_WHITE], speed_min=2.0, speed_max=5.0)

        return projectiles

    def draw(self, canvas):
        if self.is_cloaked:
            # Faint ghost silhouette
            canvas.create_oval(
                self.x - self.radius, self.y - self.radius,
                self.x + self.radius, self.y + self.radius,
                outline="#442255", width=1, dash=(3, 3)
            )
            return

        col = COLOR_WHITE if self.hit_flash > 0 else COLOR_PURPLE
        ca = math.cos(self.angle)
        sa = math.sin(self.angle)
        pts = [
            (16, 0),
            (-12, 10),
            (-2, 0),
            (-12, -10)
        ]
        world_pts = []
        for px, py in pts:
            wx = self.x + (px * ca - py * sa)
            wy = self.y + (px * sa + py * ca)
            world_pts.extend([wx, wy])

        canvas.create_polygon(world_pts, fill="#1c072b", outline=col, width=2)
