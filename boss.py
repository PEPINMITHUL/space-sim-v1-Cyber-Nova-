"""
Colossal Flagship Boss Encounter: DREADNOUGHT LEVIATHAN.
Features:
- Multi-phase combat state machine
- Orbiting Shield Node Drones (provide defensive energy barrier)
- Radial bullet-hell spiral patterns, targeted hyper-cannons, drone spawners
- Phase 2 Enrage protocol with Klaxon Siren and red neon surge
- Multi-stage screen-shaking explosion sequence
"""

import math
import random
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_RED, COLOR_MAGENTA, COLOR_CYAN,
    COLOR_YELLOW, COLOR_WHITE, COLOR_SHIELD, COLOR_PURPLE, COLOR_ORANGE
)
from weapons import Projectile
from sound_engine import sound_engine


class ShieldNode:
    """Orbiting defensive drone providing damage resistance to the Boss."""
    def __init__(self, angle_offset: float, orbit_radius: float = 75.0):
        self.angle = angle_offset
        self.orbit_radius = orbit_radius
        self.x = 0.0
        self.y = 0.0
        self.health = 130.0
        self.max_health = 130.0
        self.radius = 12.0
        self.alive = True
        self.hit_flash = 0.0

    def update(self, boss_x: float, boss_y: float, dt: float, speed_mult: float = 1.0):
        self.angle += dt * 1.5 * speed_mult
        self.x = boss_x + math.cos(self.angle) * self.orbit_radius
        self.y = boss_y + math.sin(self.angle) * self.orbit_radius
        if self.hit_flash > 0:
            self.hit_flash -= dt

    def take_damage(self, amount: float, is_crit: bool, particle_mgr) -> bool:
        self.health -= amount
        self.hit_flash = 0.12
        if particle_mgr:
            txt = f"{int(amount)}" if not is_crit else f"CRIT {int(amount)}!"
            particle_mgr.add_floating_text(self.x, self.y - 12, txt, COLOR_CYAN, size=11)
            particle_mgr.emit_sparks(self.x, self.y, 4, [COLOR_CYAN, COLOR_WHITE], speed_min=2.0, speed_max=4.5)
        if self.health <= 0:
            self.alive = False
            sound_engine.play("explosion_sm")
            if particle_mgr:
                particle_mgr.emit_shockwave(self.x, self.y, 40.0, COLOR_CYAN, speed=7.0, width=2)
                particle_mgr.emit_sparks(self.x, self.y, 14, [COLOR_CYAN, COLOR_SHIELD, COLOR_WHITE], speed_min=2.0, speed_max=5.5)
            return False
        return True

    def draw(self, canvas, boss_x: float, boss_y: float):
        # Energy link line to boss
        canvas.create_line(boss_x, boss_y, self.x, self.y, fill="#004466", width=1, dash=(2, 2))
        col = COLOR_WHITE if self.hit_flash > 0 else COLOR_CYAN
        canvas.create_oval(self.x - self.radius, self.y - self.radius,
                          self.x + self.radius, self.y + self.radius,
                          fill="#031a26", outline=col, width=2)
        # Inner shield diode
        canvas.create_oval(self.x - 4, self.y - 4, self.x + 4, self.y + 4, fill=COLOR_SHIELD, outline="")



class IrisSpecter:
    """Mid‑game boss – uses homing missiles and sweeping lasers."""
    def __init__(self, x: float, y: float, wave_num: int = 10):
        self.x = x
        self.y = y
        self.target_y = 140.0
        self.radius = 42.0
        self.max_health = 1400.0
        self.health = self.max_health
        self.score_val = 7500
        self.alive = True
        self.hit_flash = 0.0
        self.phase_2 = False
        self.attack_timer = 3.0
        self.attack_mode = 0  # 0: Homing missiles, 1: Laser sweep, 2: Burst
        self.entering = True
        sound_engine.play("boss_alarm")

    def take_damage(self, amount: float, is_crit: bool, particle_mgr) -> bool:
        self.health -= amount
        self.hit_flash = 0.12
        if particle_mgr:
            txt = f"{int(amount)}" if not is_crit else f"CRIT {int(amount)}!"
            col = COLOR_YELLOW if not is_crit else COLOR_MAGENTA
            particle_mgr.add_floating_text(self.x, self.y - 45, txt, col, size=13 if not is_crit else 17)
        if not self.phase_2 and self.health <= self.max_health * 0.5:
            self.phase_2 = True
            sound_engine.play("boss_alarm")
            if particle_mgr:
                particle_mgr.emit_shockwave(self.x, self.y, 200.0, COLOR_RED, speed=12.0, width=5)
        if self.health <= 0:
            self.alive = False
            sound_engine.play("explosion_lg")
        return self.alive

    def update(self, dt: float, player_x: float, player_y: float, particle_mgr) -> tuple[list[Projectile], list]:
        if self.hit_flash > 0:
            self.hit_flash -= dt
        # entrance
        if self.entering:
            dy = self.target_y - self.y
            self.y += dy * dt * 2.0
            if abs(dy) < 4.0:
                self.entering = False
        # Simple horizontal sway
        self.x = SCREEN_WIDTH / 2 + math.sin(dt * 0.8) * 80
        self.attack_timer -= dt
        projectiles = []
        if self.attack_timer <= 0:
            self.attack_mode = (self.attack_mode + 1) % 3
            self.attack_timer = 2.5 if not self.phase_2 else 1.6
            if self.attack_mode == 0:
                # fire 3 homing missiles
                for _ in range(3):
                    projectile = Projectile(self.x, self.y, 0, 0, damage=20, color=COLOR_PURPLE, radius=6, is_player=False, homing=True, target_x=player_x, target_y=player_y)
                    projectiles.append(projectile)
                if particle_mgr:
                    particle_mgr.emit_shockwave(self.x, self.y, 40, COLOR_PURPLE, speed=6, width=2)
            elif self.attack_mode == 1:
                # sweeping laser (wide line of projectiles)
                for i in range(-2, 3):
                    ang = math.radians(i * 5)
                    vx = math.cos(ang) * 9.0
                    vy = math.sin(ang) * 9.0
                    projectiles.append(Projectile(self.x, self.y, vx, vy, damage=18, color=COLOR_RED, radius=5, is_player=False))
                if particle_mgr:
                    particle_mgr.emit_shockwave(self.x, self.y, 50, COLOR_RED, speed=8, width=3)
            else:
                # radial burst of fast projectiles
                spokes = 12 if not self.phase_2 else 18
                speed = 7.5 if not self.phase_2 else 9.5
                for i in range(spokes):
                    ang = (i / spokes) * 2 * math.pi
                    vx = math.cos(ang) * speed
                    vy = math.sin(ang) * speed
                    projectiles.append(Projectile(self.x, self.y, vx, vy, damage=15, color=COLOR_ORANGE, radius=4, is_player=False))
                if particle_mgr:
                    particle_mgr.emit_shockwave(self.x, self.y, 45, COLOR_ORANGE, speed=7, width=2)
        return projectiles, []

class VoidRavager:
    """Late‑game boss – massive area attacks and shield drones."""
    def __init__(self, x: float, y: float, wave_num: int = 15):
        self.x = x
        self.y = y
        self.target_y = 120.0
        self.radius = 55.0
        self.max_health = 2000.0
        self.health = self.max_health
        self.score_val = 12000
        self.alive = True
        self.hit_flash = 0.0
        self.phase_2 = False
        # Shield drones similar to DreadnoughtLeviathan but stronger
        self.shield_nodes = [ShieldNode(0.0, orbit_radius=90.0), ShieldNode(2.094, orbit_radius=90.0), ShieldNode(4.188, orbit_radius=90.0)]
        self.attack_timer = 2.2
        self.attack_mode = 0
        self.entering = True
        sound_engine.play("boss_alarm")

    def take_damage(self, amount: float, is_crit: bool, particle_mgr) -> bool:
        # Damage reduction while any shield alive
        if any(node.alive for node in self.shield_nodes):
            amount *= 0.2
        self.health -= amount
        self.hit_flash = 0.12
        if particle_mgr:
            txt = f"{int(amount)}" if not is_crit else f"CRIT {int(amount)}!"
            col = COLOR_YELLOW if not is_crit else COLOR_MAGENTA
            particle_mgr.add_floating_text(self.x, self.y - 45, txt, col, size=13 if not is_crit else 17)
        if not self.phase_2 and self.health <= self.max_health * 0.4:
            self.phase_2 = True
            sound_engine.play("boss_alarm")
            if particle_mgr:
                particle_mgr.emit_shockwave(self.x, self.y, 250.0, COLOR_RED, speed=14, width=6)
        if self.health <= 0:
            self.alive = False
            sound_engine.play("explosion_lg")
        return self.alive

    def update(self, dt: float, player_x: float, player_y: float, particle_mgr) -> tuple[list[Projectile], list]:
        if self.hit_flash > 0:
            self.hit_flash -= dt
        if self.entering:
            dy = self.target_y - self.y
            self.y += dy * dt * 2.5
            if abs(dy) < 3.0:
                self.entering = False
        # sway
        self.x = SCREEN_WIDTH / 2 + math.sin(dt * 0.6) * 100
        # update shields
        for node in self.shield_nodes:
            if node.alive:
                node.update(self.x, self.y, dt, speed_mult=1.2)
        self.attack_timer -= dt
        projectiles = []
        if self.attack_timer <= 0:
            self.attack_mode = (self.attack_mode + 1) % 3
            self.attack_timer = 3.0 if not self.phase_2 else 1.8
            if self.attack_mode == 0:
                # massive ring burst
                spokes = 20 if not self.phase_2 else 30
                speed = 6.0 if not self.phase_2 else 8.0
                for i in range(spokes):
                    ang = (i / spokes) * 2 * math.pi
                    vx = math.cos(ang) * speed
                    vy = math.sin(ang) * speed
                    projectiles.append(Projectile(self.x, self.y, vx, vy, damage=22, color=COLOR_RED, radius=5, is_player=False))
                if particle_mgr:
                    particle_mgr.emit_shockwave(self.x, self.y, 70, COLOR_RED, speed=9, width=4)
            elif self.attack_mode == 1:
                # charge laser beam (single wide projectile)
                vx = 0
                vy = 10.5 if not self.phase_2 else 13.5
                projectiles.append(Projectile(self.x, self.y, vx, vy, damage=30, color=COLOR_ORANGE, radius=7, is_player=False))
                if particle_mgr:
                    particle_mgr.emit_shockwave(self.x, self.y, 55, COLOR_ORANGE, speed=8, width=3)
            else:
                # spawn two smaller shield drones that act as minions
                spawned_minions = []
                for _ in range(2):
                    d = ShieldNode(random.uniform(0, 2*math.pi), orbit_radius=50.0)
                    d.health = 70
                    d.max_health = 70
                    # treat as a simple enemy with its own update (reuse ShieldNode update later)
                    # For now we just add to spawned list as a placeholder object
                    spawned = type('MiniDrone', (), {
                        '__init__': lambda self: None,
                        'update': lambda self, dt, player_x, player_y, pm: [],
                        'draw': lambda self, canvas: None,
                        'alive': True,
                        'x': self.x,
                        'y': self.y,
                        'radius': 15,
                        'health': d.health,
                        'max_health': d.max_health,
                        'take_damage': lambda self, dmg, crit, pm: setattr(self, 'alive', False) or True,
                    })()
                    projectiles.append(spawned)
                if particle_mgr:
                    particle_mgr.emit_shockwave(self.x, self.y, 60, COLOR_PURPLE, speed=7, width=2)
        return projectiles, []

# End of boss definitions

class DreadnoughtLeviathan:
    def __init__(self, x: float, y: float, wave_num: int = 5):
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = 170.0
        self.radius = 48.0
        self.name = "DREADNOUGHT LEVIATHAN"
        
        # Scaling with wave loops
        scale = 1.0 + (wave_num - 5) * 0.25
        self.max_health = 1000.0 * scale
        self.health = self.max_health
        self.score_val = 5000
        self.alive = True
        self.hit_flash = 0.0
        
        # Shield nodes
        self.shield_nodes = [
            ShieldNode(0.0),
            ShieldNode(2.094),  # 120 deg
            ShieldNode(4.188)   # 240 deg
        ]
        
        # Attack Timers & State Machine
        self.phase_2 = False
        self.attack_timer = 2.0
        self.attack_mode = 0  # 0: Spiral, 1: Targeted Cannon, 2: Shock Burst
        self.spiral_angle = 0.0
        self.spiral_sub_timer = 0.0
        self.spiral_shots_left = 0
        
        # Boss Entrance
        self.entering = True
        sound_engine.play("boss_alarm")

    def has_active_shields(self) -> bool:
        return any(node.alive for node in self.shield_nodes)

    def take_damage(self, amount: float, is_crit: bool, particle_mgr) -> bool:
        # If shields are alive, boss takes 75% reduced damage!
        if self.has_active_shields():
            amount *= 0.25
            if particle_mgr:
                particle_mgr.add_floating_text(self.x, self.y - 30, "DEFLECTED (SHIELDS UP)", COLOR_SHIELD, size=11)
                particle_mgr.emit_shockwave(self.x, self.y, self.radius + 15, COLOR_SHIELD, speed=5.0, width=1)
        
        self.health -= amount
        self.hit_flash = 0.12

        if particle_mgr:
            txt = f"{int(amount)}" if not is_crit else f"CRIT {int(amount)}!"
            col = COLOR_YELLOW if not is_crit else COLOR_MAGENTA
            particle_mgr.add_floating_text(self.x, self.y - 45, txt, col, size=13 if not is_crit else 17)

        # Trigger Phase 2 Enrage
        if not self.phase_2 and self.health <= self.max_health * 0.45:
            self.phase_2 = True
            sound_engine.play("boss_alarm")
            if particle_mgr:
                particle_mgr.emit_shockwave(self.x, self.y, 220.0, COLOR_RED, speed=12.0, width=5)
                particle_mgr.add_floating_text(self.x, self.y - 65, "!! ENRAGE OVERCLOCK !!", COLOR_RED, size=20)

        if self.health <= 0:
            self.alive = False
            sound_engine.play("explosion_lg")
            if particle_mgr:
                # Spectacular multi-blast
                for _ in range(3):
                    particle_mgr.emit_shockwave(self.x, self.y, 160.0, COLOR_MAGENTA, speed=9.0, width=4)
                    particle_mgr.emit_shockwave(self.x, self.y, 240.0, COLOR_ORANGE, speed=14.0, width=5)
                particle_mgr.emit_sparks(self.x, self.y, 50, [COLOR_RED, COLOR_YELLOW, COLOR_MAGENTA, COLOR_WHITE],
                                         speed_min=3.0, speed_max=10.0, size_min=3.0, size_max=7.0, life=45)
            return False
        return True

    def update(self, dt: float, player_x: float, player_y: float, particle_mgr) -> tuple[list[Projectile], list]:
        """Returns tuple of (new_projectiles, new_spawned_minions)."""
        if self.hit_flash > 0:
            self.hit_flash -= dt

        # Smooth entrance movement
        if self.entering:
            dy = self.target_y - self.y
            self.y += dy * dt * 2.0
            if abs(dy) < 4.0:
                self.entering = False

        # Sway horizontally
        speed_mult = 1.6 if self.phase_2 else 1.0
        self.x = (SCREEN_WIDTH / 2) + math.sin(self.spiral_angle * 0.5) * (SCREEN_WIDTH * 0.32)

        # Update orbiting shield nodes
        for node in self.shield_nodes:
            if node.alive:
                node.update(self.x, self.y, dt, speed_mult)

        projectiles = []
        spawned_minions = []

        # Attack State Machine
        self.attack_timer -= dt * speed_mult
        if self.attack_timer <= 0:
            self.attack_mode = (self.attack_mode + 1) % 3
            self.attack_timer = 2.4 if not self.phase_2 else 1.5

            if self.attack_mode == 0:
                # Start Spiral Nova
                self.spiral_shots_left = 24 if self.phase_2 else 16
                self.spiral_sub_timer = 0.0

            elif self.attack_mode == 1:
                # Targeted Cannon Salvo
                sound_engine.play("plasma")
                base_angle = math.atan2(player_y - self.y, player_x - self.x)
                spreads = [-0.35, -0.18, 0.0, 0.18, 0.35] if self.phase_2 else [-0.25, 0.0, 0.25]
                for spr in spreads:
                    ang = base_angle + spr
                    spd = 8.5 if self.phase_2 else 7.0
                    vx = math.cos(ang) * spd
                    vy = math.sin(ang) * spd
                    projectiles.append(Projectile(self.x, self.y + 20, vx, vy, damage=22.0, color=COLOR_RED, radius=5.0, is_player=False))
                if particle_mgr:
                    particle_mgr.emit_shockwave(self.x, self.y + 20, 45.0, COLOR_RED, speed=7.0, width=3)

            elif self.attack_mode == 2:
                # Radial Ring Shock Burst
                sound_engine.play("shotgun")
                spoke_count = 14 if self.phase_2 else 10
                for i in range(spoke_count):
                    ang = (i / spoke_count) * (2 * math.pi)
                    spd = 6.2
                    vx = math.cos(ang) * spd
                    vy = math.sin(ang) * spd
                    projectiles.append(Projectile(self.x, self.y, vx, vy, damage=16.0, color=COLOR_YELLOW, radius=4.0, is_player=False))

        # Spiral sub-firing ticks
        if self.spiral_shots_left > 0:
            self.spiral_sub_timer -= dt
            if self.spiral_sub_timer <= 0:
                self.spiral_sub_timer = 0.06
                self.spiral_shots_left -= 1
                self.spiral_angle += 0.42
                
                # Double spiral arms
                for arm_offset in (0.0, math.pi):
                    ang = self.spiral_angle + arm_offset
                    spd = 7.0
                    vx = math.cos(ang) * spd
                    vy = math.sin(ang) * spd
                    col = COLOR_MAGENTA if not self.phase_2 else COLOR_RED
                    projectiles.append(Projectile(self.x, self.y, vx, vy, damage=14.0, color=col, radius=3.5, is_player=False))

        return projectiles, []

    def draw(self, canvas):
        # Draw active shield nodes
        for node in self.shield_nodes:
            if node.alive:
                node.draw(canvas, self.x, self.y)

        # Draw protective energy barrier ring if shields active
        if self.has_active_shields():
            canvas.create_oval(
                self.x - (self.radius + 18), self.y - (self.radius + 18),
                self.x + (self.radius + 18), self.y + (self.radius + 18),
                outline=COLOR_SHIELD, width=2, dash=(4, 4)
            )

        col = COLOR_WHITE if self.hit_flash > 0 else (COLOR_RED if self.phase_2 else COLOR_MAGENTA)
        
        # Heavy Battlecruiser Frame
        # Central diamond + left/right wings
        ca = math.cos(math.pi / 2)  # Facing downward
        sa = math.sin(math.pi / 2)

        pts = [
            (self.x, self.y + 45),         # Main Prow / Cannon
            (self.x + 35, self.y + 15),    # Right flank
            (self.x + 55, self.y - 20),    # Right wing tip
            (self.x + 25, self.y - 38),    # Right engine
            (self.x, self.y - 25),         # Central aft
            (self.x - 25, self.y - 38),    # Left engine
            (self.x - 55, self.y - 20),    # Left wing tip
            (self.x - 35, self.y + 15),    # Left flank
        ]
        flat_pts = []
        for px, py in pts:
            flat_pts.extend([px, py])

        canvas.create_polygon(flat_pts, fill="#1c0722", outline=col, width=3)

        # Glowing Hypercore
        core_col = COLOR_RED if self.phase_2 else COLOR_YELLOW
        canvas.create_oval(
            self.x - 12, self.y - 6,
            self.x + 12, self.y + 18,
            fill=core_col, outline=COLOR_WHITE, width=2
        )
