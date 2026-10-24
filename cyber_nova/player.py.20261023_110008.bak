"""
Player Spacecraft Controller, Vector Physics, and Abilities.
Includes:
- Inertial vector movement with thruster exhaust
- Dynamic mouse rotation & aim
- Quantum Blink Dash (Invulnerable dodge)
- EMP Shockwave super ability
- Shield auto-regeneration & Hull management
- Energy & Overheat regulation
"""

import math
import random
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_CYAN, COLOR_MAGENTA, COLOR_YELLOW,
    COLOR_WHITE, COLOR_RED, COLOR_SHIELD, COLOR_PURPLE, COLOR_ORANGE,
    PLAYER_DEFAULT_SPEED, PLAYER_FRICTION, PLAYER_MAX_HEALTH,
    PLAYER_MAX_SHIELD, PLAYER_SHIELD_REGEN_RATE, PLAYER_SHIELD_REGEN_DELAY,
    PLAYER_DASH_SPEED, PLAYER_DASH_COOLDOWN
)
from weapons import Projectile, HomingMissile, SingularityVortex, WEAPONS_DATA
from sound_engine import sound_engine


class Player:
    def __init__(self, x: float, y: float, ship: "Ship" = None):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.angle = -math.pi / 2  # Facing upwards
        self.radius = 16.0

        # Upgradable Stats
        self.max_health = PLAYER_MAX_HEALTH
        self.health = PLAYER_MAX_HEALTH
        self.max_shield = PLAYER_MAX_SHIELD
        self.shield = PLAYER_MAX_SHIELD
        self.shield_regen_rate = PLAYER_SHIELD_REGEN_RATE
        self.speed = PLAYER_DEFAULT_SPEED
        self.magnet_range = 140.0
        self.crit_chance = 0.10
        self.crit_multiplier = 1.8

        # Energy & Cooldowns
        self.max_energy = 100.0
        self.energy = 100.0
        self.energy_regen = 32.0  # per second
        self.fire_cooldown = 0.0
        self.shield_delay_timer = 0.0
        self.invulnerable_timer = 0.0

        # Dash Ability
        self.dash_cooldown = 0.0
        self.is_dashing = False
        self.dash_timer = 0.0
        self.dash_dir_x = 0.0
        self.dash_dir_y = 0.0

        # EMP Shockwave
        self.emp_charges = 2
        self.max_emp_charges = 4

        # Overclock Powerup
        self.overclock_timer = 0.0

        # Weaponry
        self.current_weapon = "pulse"
        self.unlocked_weapons = ["pulse", "twin"]

        # Thruster particle timer
        self.thrusting = False
        self.shield_flash_alpha = 0.0

        # Ship handling
        self.ship = ship
        if self.ship is not None:
            # Apply perk first, then con (con may counteract perk)
            try:
                self.ship.apply_perk(self)
            except Exception:
                pass
            try:
                self.ship.apply_con(self)
            except Exception:
                pass
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.angle = -math.pi / 2  # Facing upwards
        self.radius = 16.0
        
        # Upgradable Stats
        self.max_health = PLAYER_MAX_HEALTH
        self.health = PLAYER_MAX_HEALTH
        self.max_shield = PLAYER_MAX_SHIELD
        self.shield = PLAYER_MAX_SHIELD
        self.shield_regen_rate = PLAYER_SHIELD_REGEN_RATE
        self.speed = PLAYER_DEFAULT_SPEED
        self.magnet_range = 140.0
        self.crit_chance = 0.10
        self.crit_multiplier = 1.8
        
        # Energy & Cooldowns
        self.max_energy = 100.0
        self.energy = 100.0
        self.energy_regen = 32.0  # per second
        self.fire_cooldown = 0.0
        self.shield_delay_timer = 0.0
        self.invulnerable_timer = 0.0
        
        # Dash Ability
        self.dash_cooldown = 0.0
        self.is_dashing = False
        self.dash_timer = 0.0
        self.dash_dir_x = 0.0
        self.dash_dir_y = 0.0
        
        # EMP Shockwave
        self.emp_charges = 2
        self.max_emp_charges = 4
        
        # Overclock Powerup
        self.overclock_timer = 0.0
        
        # Weaponry
        self.current_weapon = "pulse"
        self.unlocked_weapons = ["pulse", "twin"]
        
        # Thruster particle timer
        self.thrusting = False
        self.shield_flash_alpha = 0.0

    def get_points(self) -> list[tuple[float, float]]:
        """Calculate geometric polygon points of the fighter jet oriented along self.angle."""
        ca = math.cos(self.angle)
        sa = math.sin(self.angle)
        
        # Nose, right wing tip, right thruster, center tail notch, left thruster, left wing tip
        pts = [
            (22, 0),       # Nose
            (-14, 15),     # Right wing
            (-8, 6),       # Right engine
            (-12, 0),      # Tail notch
            (-8, -6),      # Left engine
            (-14, -15),    # Left wing
        ]
        
        world_pts = []
        for px, py in pts:
            wx = self.x + (px * ca - py * sa)
            wy = self.y + (px * sa + py * ca)
            world_pts.append((wx, wy))
        return world_pts

    def handle_input(self, keys: dict, mouse_x: float, mouse_y: float):
        """Update velocities and angle based on player keyboard and mouse input."""
        # Aim towards mouse cursor
        dx = mouse_x - self.x
        dy = mouse_y - self.y
        if math.hypot(dx, dy) > 8:
            self.angle = math.atan2(dy, dx)

        if self.is_dashing:
            return  # Velocity locked during dash

        accel_x = 0.0
        accel_y = 0.0
        accel_mag = 1.1

        if keys.get("w") or keys.get("up"):
            accel_y -= accel_mag
        if keys.get("s") or keys.get("down"):
            accel_y += accel_mag
        if keys.get("a") or keys.get("left"):
            accel_x -= accel_mag
        if keys.get("d") or keys.get("right"):
            accel_x += accel_mag

        self.thrusting = (accel_x != 0.0 or accel_y != 0.0)

        if self.thrusting:
            # Normalize diagonal acceleration
            norm = math.hypot(accel_x, accel_y)
            if norm > 0:
                accel_x = (accel_x / norm) * accel_mag
                accel_y = (accel_y / norm) * accel_mag

            self.vx += accel_x
            self.vy += accel_y
            
            # Cap max speed
            current_speed = math.hypot(self.vx, self.vy)
            if current_speed > self.speed:
                factor = self.speed / current_speed
                self.vx *= factor
                self.vy *= factor

    def trigger_dash(self, particle_mgr) -> bool:
        """Trigger Quantum Blink Dash if off cooldown."""
        if self.dash_cooldown > 0 or self.is_dashing:
            return False

        # Dash in movement direction or facing direction
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
        
        # Audio & shockwave
        sound_engine.play("dash")
        if particle_mgr:
            particle_mgr.emit_shockwave(self.x, self.y, 45.0, COLOR_CYAN, speed=10.0, width=2)
            particle_mgr.emit_sparks(self.x, self.y, 14, [COLOR_CYAN, COLOR_WHITE, COLOR_SHIELD], speed_min=3.0, speed_max=7.0)

        return True

    def trigger_emp(self, particle_mgr, enemies: list, projectiles: list) -> bool:
        """Activate EMP super bomb: clears enemy projectiles, damages & stuns all enemies."""
        if self.emp_charges <= 0:
            return False

        self.emp_charges -= 1
        sound_engine.play("emp")
        
        if particle_mgr:
            particle_mgr.emit_shockwave(self.x, self.y, 500.0, COLOR_PURPLE, speed=16.0, width=6)
            particle_mgr.emit_shockwave(self.x, self.y, 350.0, COLOR_CYAN, speed=12.0, width=4)
            particle_mgr.add_floating_text(self.x, self.y - 30, "EMP DETONATION!", COLOR_PURPLE, size=18)

        # Clear all enemy projectiles
        for p in projectiles:
            if not p.is_player and p.alive:
                p.alive = False
                if particle_mgr:
                    particle_mgr.emit_sparks(p.x, p.y, 4, [COLOR_CYAN, COLOR_WHITE], speed_min=2.0, speed_max=4.0)

        # Stun and blast all active enemies
        for e in enemies:
            if getattr(e, 'alive', False):
                e.take_damage(80, is_crit=True, particle_mgr=particle_mgr)
                if hasattr(e, 'stun_timer'):
                    e.stun_timer = 3.5  # 3.5 seconds stun!

        return True

    def fire(self, particle_mgr) -> list[Projectile]:
        """Fire the active weapon."""
        if self.fire_cooldown > 0:
            return []

        w_def = WEAPONS_DATA.get(self.current_weapon)
        if not w_def:
            return []

        cost = 0.0 if self.overclock_timer > 0 else w_def.energy_cost
        if self.energy < cost:
            return []

        self.energy -= cost
        # Overclock cuts cooldown in half
        cd = w_def.cooldown * (0.5 if self.overclock_timer > 0 else 1.0)
        self.fire_cooldown = cd

        spawned = []
        ca = math.cos(self.angle)
        sa = math.sin(self.angle)
        nose_x = self.x + ca * 22
        nose_y = self.y + sa * 22

        is_crit = random.random() < self.crit_chance
        mult = self.crit_multiplier if is_crit else 1.0

        if self.current_weapon == "pulse":
            sound_engine.play("laser")
            dmg = 24.0 * mult
            spd = 18.0
            vx = ca * spd + self.vx * 0.2
            vy = sa * spd + self.vy * 0.2
            col = COLOR_YELLOW if is_crit else COLOR_CYAN
            spawned.append(Projectile(nose_x, nose_y, vx, vy, dmg, col, radius=3.5, is_player=True))
            if particle_mgr:
                particle_mgr.emit_directional_sparks(nose_x, nose_y, 3, self.angle, 0.3, 4.0, [col, COLOR_WHITE])

        elif self.current_weapon == "twin":
            sound_engine.play("plasma")
            dmg = 20.0 * mult
            spd = 16.0
            # Left & right wing offsets
            offsets = [(-sa * 10, ca * 10), (sa * 10, -ca * 10)]
            col = COLOR_WHITE if is_crit else COLOR_MAGENTA
            for ox, oy in offsets:
                bx = self.x + ca * 14 + ox
                by = self.y + sa * 14 + oy
                vx = ca * spd + self.vx * 0.2
                vy = sa * spd + self.vy * 0.2
                spawned.append(Projectile(bx, by, vx, vy, dmg, col, radius=4.0, is_player=True))
                if particle_mgr:
                    particle_mgr.emit_directional_sparks(bx, by, 2, self.angle, 0.2, 3.5, [col, COLOR_MAGENTA])

        elif self.current_weapon == "flak":
            sound_engine.play("shotgun")
            dmg = 14.0 * mult
            pellet_count = 6
            spd = 15.0
            col = COLOR_WHITE if is_crit else COLOR_YELLOW
            for _ in range(pellet_count):
                spread_angle = self.angle + random.uniform(-0.28, 0.28)
                p_spd = spd * random.uniform(0.85, 1.15)
                vx = math.cos(spread_angle) * p_spd + self.vx * 0.2
                vy = math.sin(spread_angle) * p_spd + self.vy * 0.2
                spawned.append(Projectile(nose_x, nose_y, vx, vy, dmg, col, radius=2.5, is_player=True, life=45))
            if particle_mgr:
                particle_mgr.emit_directional_sparks(nose_x, nose_y, 8, self.angle, 0.5, 6.0, [COLOR_YELLOW, COLOR_ORANGE])

        elif self.current_weapon == "homing":
            sound_engine.play("missile")
            dmg = 38.0 * mult
            spd = 11.0
            for side in (-0.35, 0.35):
                angle = self.angle + side
                spawned.append(HomingMissile(nose_x, nose_y, angle, spd, dmg))

        elif self.current_weapon == "singularity":
            sound_engine.play("emp")
            dmg = 15.0 * mult
            spd = 5.5
            vx = ca * spd
            vy = sa * spd
            spawned.append(SingularityVortex(nose_x, nose_y, vx, vy, dmg))

        return spawned

    def take_damage(self, amount: float, particle_mgr) -> bool:
        """Apply damage first to shield, then to hull. Returns True if alive, False if destroyed."""
        if self.invulnerable_timer > 0:
            return True

        self.shield_delay_timer = PLAYER_SHIELD_REGEN_DELAY
        self.invulnerable_timer = 0.45  # Grace period flash
        self.shield_flash_alpha = 1.0

        if self.shield > 0:
            sound_engine.play("shield_hit")
            if self.shield >= amount:
                self.shield -= amount
                if particle_mgr:
                    particle_mgr.emit_shockwave(self.x, self.y, 35.0, COLOR_SHIELD, speed=6.0, width=2)
            else:
                remaining = amount - self.shield
                self.shield = 0.0
                self.health -= remaining
                sound_engine.play("explosion_sm")
                if particle_mgr:
                    particle_mgr.emit_shockwave(self.x, self.y, 45.0, COLOR_RED, speed=8.0, width=3)
                    particle_mgr.add_floating_text(self.x, self.y - 20, "SHIELD BROKEN!", COLOR_RED, size=14)
        else:
            sound_engine.play("explosion_sm")
            self.health -= amount
            if particle_mgr:
                particle_mgr.emit_sparks(self.x, self.y, 16, [COLOR_RED, COLOR_YELLOW, COLOR_WHITE], speed_min=2.0, speed_max=6.0)

        if self.health <= 0:
            self.health = 0.0
            return False
        return True

    def update(self, dt: float, particle_mgr):
        """Update cooldowns, regenerative systems, and motion."""
        # Timers
        if self.fire_cooldown > 0:
            self.fire_cooldown -= dt
        if self.dash_cooldown > 0:
            self.dash_cooldown -= dt
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= dt
        if self.overclock_timer > 0:
            self.overclock_timer -= dt
        if self.shield_flash_alpha > 0:
            self.shield_flash_alpha = max(0.0, self.shield_flash_alpha - dt * 2.5)

        # Dash movement execution
        if self.is_dashing:
            self.dash_timer -= dt
            self.vx = self.dash_dir_x * PLAYER_DASH_SPEED
            self.vy = self.dash_dir_y * PLAYER_DASH_SPEED
            
            # Emit ghost afterimage
            if particle_mgr and random.random() < 0.6:
                particle_mgr.add_ghost(self.get_points(), COLOR_CYAN)

            if self.dash_timer <= 0:
                self.is_dashing = False
                self.vx *= 0.35
                self.vy *= 0.35

        # Normal friction
        if not self.is_dashing:
            self.vx *= PLAYER_FRICTION
            self.vy *= PLAYER_FRICTION

        # Apply position
        self.x += self.vx
        self.y += self.vy

        # Screen boundaries clamping
        margin = self.radius + 6
        self.x = max(margin, min(SCREEN_WIDTH - margin, self.x))
        self.y = max(margin, min(SCREEN_HEIGHT - margin, self.y))

        # Energy Regeneration
        regen = self.energy_regen * (2.0 if self.overclock_timer > 0 else 1.0)
        self.energy = min(self.max_energy, self.energy + regen * dt)

        # Shield Auto-Regeneration
        if self.shield_delay_timer > 0:
            self.shield_delay_timer -= dt
        else:
            if self.shield < self.max_shield:
                prev_shield = self.shield
                self.shield = min(self.max_shield, self.shield + self.shield_regen_rate * dt)
                if prev_shield < self.max_shield and self.shield >= self.max_shield and particle_mgr:
                    particle_mgr.add_floating_text(self.x, self.y - 25, "SHIELD FULL", COLOR_SHIELD, size=12)

        # Thruster particle trail
        if (self.thrusting or self.is_dashing) and particle_mgr:
            ca = math.cos(self.angle)
            sa = math.sin(self.angle)
            tail_x = self.x - ca * 12
            tail_y = self.y - sa * 12
            colors = [COLOR_CYAN, COLOR_MAGENTA, COLOR_WHITE] if not self.is_dashing else [COLOR_CYAN, COLOR_SHIELD]
            particle_mgr.emit_directional_sparks(
                tail_x, tail_y, 2, self.angle + math.pi, 0.4, 4.5, colors, size=2.5
            )

    def draw(self, canvas):
        # Flicker if invulnerable
        if self.invulnerable_timer > 0 and int(self.invulnerable_timer * 20) % 2 == 0:
            return

        points = self.get_points()
        flat_pts = []
        for px, py in points:
            flat_pts.extend([px, py])

        # Outer ship outline & interior
        hull_col = COLOR_CYAN if self.overclock_timer <= 0 else COLOR_ORANGE
        canvas.create_polygon(
            flat_pts,
            fill="#091428",
            outline=hull_col,
            width=2
        )

        # Cockpit glowing core
        ca = math.cos(self.angle)
        sa = math.sin(self.angle)
        core_x = self.x + ca * 2
        core_y = self.y + sa * 2
        canvas.create_oval(
            core_x - 3, core_y - 3,
            core_x + 3, core_y + 3,
            fill=COLOR_WHITE, outline=COLOR_MAGENTA, width=1
        )

        # Shield energy ring
        if self.shield > 0 and (self.shield_flash_alpha > 0 or self.shield < self.max_shield * 0.4):
            r = self.radius + 6.0
            canvas.create_oval(
                self.x - r, self.y - r,
                self.x + r, self.y + r,
                outline=COLOR_SHIELD, width=2
            )
