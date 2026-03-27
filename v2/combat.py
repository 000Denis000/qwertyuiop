# ============================================================
#  BACKYARD SURVIVAL v2  –  Combat System
# ============================================================
from __future__ import annotations
import math
import random
from typing import List, Optional, TYPE_CHECKING
from constants import *
from items import Item
from status_effects import EffectManager, make_effect

if TYPE_CHECKING:
    from enemy import Enemy
    from player import Player


# ════════════════════════════════════════════════════════════
#  DAMAGE CALCULATION
# ════════════════════════════════════════════════════════════

def calc_melee_damage(attacker_damage: int, target_defense: int,
                      is_crit: bool, weapon_element: str = None,
                      night_mult: float = 1.0) -> int:
    base = max(1, attacker_damage - target_defense // 3)
    if is_crit:
        base = int(base * 1.75)
    base = int(base * night_mult)
    # Slight randomness ±15%
    base = int(base * random.uniform(0.85, 1.15))
    return max(1, base)


def calc_ranged_damage(base_damage: int, target_defense: int,
                       distance: float, max_range: float = 15.0,
                       is_crit: bool = False) -> int:
    # Falloff after 60% of max range
    falloff_start = max_range * 0.60
    if distance > falloff_start:
        falloff = 1.0 - 0.40 * ((distance - falloff_start) / (max_range - falloff_start))
        base_damage = int(base_damage * max(0.6, falloff))
    dmg = max(1, base_damage - target_defense // 4)
    if is_crit:
        dmg = int(dmg * 1.75)
    return max(1, int(dmg * random.uniform(0.88, 1.12)))


def roll_crit(base_chance: float, crit_bonus: float = 0.0) -> bool:
    return random.random() < (base_chance + crit_bonus)


def apply_knockback_3d(target, dir_x: float, dir_z: float,
                        force: float, dt_safe: float = 0.15):
    """Push target in XZ plane."""
    dist = math.hypot(dir_x, dir_z)
    if dist < 0.001:
        return
    nx = dir_x / dist
    nz = dir_z / dist
    target.knockback_vel_x = nx * force
    target.knockback_vel_z = nz * force
    target.knockback_time  = dt_safe


# ════════════════════════════════════════════════════════════
#  PROJECTILE
# ════════════════════════════════════════════════════════════

class Projectile:
    """A flying projectile in 3D world space."""

    def __init__(self, owner, x: float, y: float, z: float,
                 dir_x: float, dir_y: float, dir_z: float,
                 speed: float, damage: int, radius: float = 0.18,
                 lifetime: float = 3.5, color=None,
                 hits_player: bool = False,
                 element: str = None,
                 status_effect: str = None,
                 effect_chance: float = 0.0,
                 effect_dur: float = 3.0):
        self.owner          = owner
        self.x, self.y, self.z = x, y, z
        # Normalize direction
        mag = math.sqrt(dir_x**2 + dir_y**2 + dir_z**2)
        if mag < 0.001:
            mag = 1
        self.vx = dir_x / mag * speed
        self.vy = dir_y / mag * speed
        self.vz = dir_z / mag * speed
        self.damage         = damage
        self.radius         = radius
        self.lifetime       = lifetime
        self.age            = 0.0
        self.active         = True
        self.color          = color or COL_YELLOW
        self.hits_player    = hits_player
        self.element        = element
        self.status_effect  = status_effect
        self.effect_chance  = effect_chance
        self.effect_dur     = effect_dur
        self._gravity       = 2.2   # slight arc
        # Ursina entity (set externally)
        self.entity         = None

    def update(self, dt: float):
        if not self.active:
            return
        self.age     += dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.active = False
            return
        # Apply gravity arc
        self.vy -= self._gravity * dt
        self.x  += self.vx * dt
        self.y  += self.vy * dt
        self.z  += self.vz * dt
        # Hit ground
        if self.y < 0.0:
            self.active = False

    def try_hit_target(self, target) -> bool:
        """Returns True if hit target."""
        if not self.active:
            return False
        tx, ty, tz = target.x, target.y, target.z
        dist = math.sqrt((self.x-tx)**2 + (self.y-ty)**2 + (self.z-tz)**2)
        hit_radius = self.radius + getattr(target, "hit_radius", 0.5)
        if dist <= hit_radius:
            self.active = False
            return True
        return False

    def apply_to(self, target, distance: float = 0.0, night_mult: float = 1.0):
        """Deal damage and apply effects."""
        is_crit = roll_crit(CRIT_CHANCE)
        dmg     = calc_ranged_damage(self.damage, getattr(target, "defense", 0),
                                      distance, is_crit=is_crit)
        dmg = int(dmg * night_mult)
        took = target.take_damage(dmg)
        # Status effect
        if self.status_effect and random.random() < self.effect_chance:
            if hasattr(target, "effects"):
                target.effects.apply(self.status_effect, self.effect_dur)
        return dmg


# ════════════════════════════════════════════════════════════
#  SWING ATTACK (melee arc)
# ════════════════════════════════════════════════════════════

class SwingAttack:
    """One melee swing — an arc in front of the attacker."""

    def __init__(self, attacker, damage: int, arc_rad: float,
                 reach: float, knockback: float,
                 weapon_item: Item = None,
                 night_mult: float = 1.0):
        self.attacker     = attacker
        self.damage       = damage
        self.arc_rad      = arc_rad      # radians half-angle
        self.reach        = reach
        self.knockback    = knockback
        self.weapon_item  = weapon_item
        self.night_mult   = night_mult
        self.element      = weapon_item.element if weapon_item else None
        self.status_eff   = weapon_item.status_effect if weapon_item else None
        self.eff_chance   = weapon_item.effect_chance if weapon_item else 0.0
        self.eff_dur      = weapon_item.effect_duration if weapon_item else 0.0

    def resolve(self, targets: list) -> List[tuple]:
        """Returns [(target, damage_dealt), ...]"""
        results = []
        ax, az = self.attacker.x, self.attacker.z
        # Attacker's facing in XZ plane
        facing = getattr(self.attacker, "facing_angle", 0.0)

        for target in targets:
            if target is self.attacker:
                continue
            if not getattr(target, "active", True):
                continue
            tx, tz = target.x, target.z
            dx, dz = tx - ax, tz - az
            dist   = math.hypot(dx, dz)
            hit_r  = getattr(target, "hit_radius", 0.5)
            if dist > self.reach + hit_r:
                continue
            # Angle check
            if dist > 0.01:
                angle_to = math.atan2(dz, dx)
                diff = abs(math.atan2(
                    math.sin(angle_to - facing),
                    math.cos(angle_to - facing)
                ))
                if diff > self.arc_rad:
                    continue

            is_crit = roll_crit(CRIT_CHANCE)
            def_val = getattr(target, "defense", 0)
            dmg     = calc_melee_damage(self.damage, def_val, is_crit,
                                         self.element, self.night_mult)
            if dmg <= 0:
                continue

            # Knockback
            if dist > 0.001:
                apply_knockback_3d(target, dx, dz, self.knockback)

            target.take_damage(dmg)

            # Status effect
            if self.status_eff and random.random() < self.eff_chance:
                if hasattr(target, "effects"):
                    target.effects.apply(self.status_eff, self.eff_dur)

            results.append((target, dmg, is_crit))
        return results
