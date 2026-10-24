"""
Ship definitions for Cyber Nova.
Each ship provides a unique perk (bonus) and a con (drawback).
The Ship dataclass is used by the Game engine to modify the Player stats.
"""

from dataclasses import dataclass
from typing import Callable, Dict

# Perk/Con are simple descriptors. In a full implementation they could be callables.
# For now we store a short text and a function that mutates the Player.

@dataclass
class Ship:
    id: str
    name: str
    sprite: str  # path to a small PNG for the ship selector (optional, not used now)
    perk_name: str
    perk_desc: str
    con_name: str
    con_desc: str
    # Functions that will be called on player init to apply the modifiers.
    apply_perk: Callable[["Player"], None]
    apply_con: Callable[["Player"], None]

# Helper functions that modify player attributes.
def _speed_bonus(player, factor: float = 1.2):
    player.speed *= factor

def _shield_bonus(player, amount: float = 20):
    player.max_shield += amount
    player.shield += amount

def _dash_cooldown_reduction(player, factor: float = 0.7):
    player.dash_cooldown *= factor

def _emp_extra_charge(player, extra: int = 1):
    player.max_emp_charges += extra
    player.emp_charges = player.max_emp_charges

def _overclock_increase(player, extra: float = 5.0):
    # Overclock timer bonus when power‑up is active.
    player.overclock_timer += extra

# Ship catalogue
SHIPS: Dict[str, Ship] = {
    "falcon": Ship(
        id="falcon",
        name="Falcon",
        sprite="",
        perk_name="Speed Burst",
        perk_desc="+20% movement speed.",
        con_name="Fragile",
        con_desc="-10% shield capacity.",
        apply_perk=lambda p: _speed_bonus(p, 1.2),
        apply_con=lambda p: _shield_bonus(p, -10),
    ),
    "marauder": Ship(
        id="marauder",
        name="Marauder",
        sprite="",
        perk_name="Heavy Shield",
        perk_desc="+30 shield capacity.",
        con_name="Slow Dash",
        con_desc="dash cooldown 30% longer.",
        apply_perk=lambda p: _shield_bonus(p, 30),
        apply_con=lambda p: _dash_cooldown_reduction(p, 1.3),
    ),
    "spectre": Ship(
        id="spectre",
        name="Spectre",
        sprite="",
        perk_name="Stealth EMP",
        perk_desc="EMP also grants temporary invisibility.",
        con_name="Weak Firepower",
        con_desc="-15% weapon damage.",
        apply_perk=lambda p: _emp_extra_charge(p, 1),
        apply_con=lambda p: setattr(p, "crit_multiplier", p.crit_multiplier * 0.85),
    ),
    "titan": Ship(
        id="titan",
        name="Titan",
        sprite="",
        perk_name="Extra EMP",
        perk_desc="+2 EMP charges.",
        con_name="Heavy",
        con_desc="-10% movement speed.",
        apply_perk=lambda p: _emp_extra_charge(p, 2),
        apply_con=lambda p: _speed_bonus(p, 0.9),
    ),
}
