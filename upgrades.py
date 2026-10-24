"""
Rogue-lite Tech Bay Upgrade System for CYBER NOVA.
Allows players to spend collected Scrap Cores on permanent run upgrades
and unlock devastating prototype arsenal weapons.
"""

from config import (
    COLOR_CYAN, COLOR_MAGENTA, COLOR_YELLOW,
    COLOR_GREEN, COLOR_WHITE, COLOR_ORANGE, COLOR_PURPLE
)
from weapons import WEAPONS_DATA
from sound_engine import sound_engine


class UpgradeItem:
    def __init__(self, item_id: str, name: str, icon: str, base_cost: int,
                 max_level: int, description: str, color: str = COLOR_CYAN):
        self.item_id = item_id
        self.name = name
        self.icon = icon
        self.base_cost = base_cost
        self.level = 0
        self.max_level = max_level
        self.description = description
        self.color = color

    @property
    def cost(self) -> int:
        if self.level >= self.max_level:
            return 999999
        return int(self.base_cost * (1.6 ** self.level))

    @property
    def is_maxed(self) -> bool:
        return self.level >= self.max_level


class UpgradeManager:
    def __init__(self):
        self.upgrades = [
            UpgradeItem(
                "hull", "HULL REINFORCEMENT", "🛡️", base_cost=40, max_level=5,
                description="+25 Max Health & instant repair.", color=COLOR_GREEN
            ),
            UpgradeItem(
                "shield", "PLASMA SHIELD ARRAY", "⚡", base_cost=50, max_level=5,
                description="+20 Max Shield & faster regen rate.", color=COLOR_CYAN
            ),
            UpgradeItem(
                "speed", "HYPER THRUSTERS", "🚀", base_cost=45, max_level=4,
                description="+15% Speed & reduced dash cooldown.", color=COLOR_YELLOW
            ),
            UpgradeItem(
                "magnet", "QUANTUM VACUUM", "🧲", base_cost=30, max_level=4,
                description="+60px Scrap magnet collection radius.", color=COLOR_ORANGE
            ),
            UpgradeItem(
                "crit", "CRITICAL OVERCLOCK", "🎯", base_cost=60, max_level=5,
                description="+8% Critical Strike chance & higher burst.", color=COLOR_MAGENTA
            ),
            UpgradeItem(
                "flak_unlock", "UNLOCK: SCATTER FLAK", "💥", base_cost=90, max_level=1,
                description="Unlocks Weapon 3: 6-pellet high spread flak.", color=COLOR_YELLOW
            ),
            UpgradeItem(
                "homing_unlock", "UNLOCK: HOMING PODS", "🛰️", base_cost=140, max_level=1,
                description="Unlocks Weapon 4: Target-seeking micro-missiles.", color=COLOR_GREEN
            ),
            UpgradeItem(
                "singularity_unlock", "UNLOCK: SINGULARITY CORE", "🌌", base_cost=220, max_level=1,
                description="Unlocks Weapon 5: Gravity-vortex black hole.", color=COLOR_PURPLE
            ),
            UpgradeItem(
                "emp_cell", "EMP SHOCKWAVE CELL", "💣", base_cost=100, max_level=3,
                description="+1 Max EMP super charge & instant refill.", color=COLOR_PURPLE
            ),
        ]

    def get_item(self, item_id: str) -> UpgradeItem | None:
        for u in self.upgrades:
            if u.item_id == item_id:
                return u
        return None

    def purchase(self, item_id: str, player, scrap_wallet: int, particle_mgr=None) -> tuple[bool, int, str]:
        """Attempt to buy an upgrade. Returns (success, remaining_scrap, message)."""
        item = self.get_item(item_id)
        if not item:
            return False, scrap_wallet, "Invalid upgrade item."

        if item.is_maxed:
            return False, scrap_wallet, "Upgrade already maxed!"

        cost = item.cost
        if scrap_wallet < cost:
            return False, scrap_wallet, f"Need {cost - scrap_wallet} more Scrap!"

        # Deduct cost and level up
        scrap_wallet -= cost
        item.level += 1
        sound_engine.play("powerup")

        # Apply specific attribute bonuses
        if item.item_id == "hull":
            player.max_health += 25
            player.health = min(player.max_health, player.health + 35)
        elif item.item_id == "shield":
            player.max_shield += 20
            player.shield = player.max_shield
            player.shield_regen_rate += 4.0
        elif item.item_id == "speed":
            player.speed += 0.8
        elif item.item_id == "magnet":
            player.magnet_range += 60.0
        elif item.item_id == "crit":
            player.crit_chance += 0.08
            player.crit_multiplier += 0.3
        elif item.item_id == "flak_unlock":
            WEAPONS_DATA["flak"].unlocked = True
            if "flak" not in player.unlocked_weapons:
                player.unlocked_weapons.append("flak")
        elif item.item_id == "homing_unlock":
            WEAPONS_DATA["homing"].unlocked = True
            if "homing" not in player.unlocked_weapons:
                player.unlocked_weapons.append("homing")
        elif item.item_id == "singularity_unlock":
            WEAPONS_DATA["singularity"].unlocked = True
            if "singularity" not in player.unlocked_weapons:
                player.unlocked_weapons.append("singularity")
        elif item.item_id == "emp_cell":
            player.max_emp_charges += 1
            player.emp_charges = player.max_emp_charges

        if particle_mgr:
            particle_mgr.add_floating_text(player.x, player.y - 30, f"{item.name} UPGRADED!", item.color, size=14)

        return True, scrap_wallet, f"Upgraded {item.name} to Lv {item.level}!"
