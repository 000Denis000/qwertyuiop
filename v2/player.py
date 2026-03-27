# ============================================================
#  BACKYARD SURVIVAL v2  –  Player (3D Entity)
# ============================================================
from __future__ import annotations
import math
import random
from typing import List, Optional, TYPE_CHECKING
from constants import *
from inventory import PlayerInventory
from items import make, Item
from status_effects import EffectManager
from combat import SwingAttack, apply_knockback_3d

if TYPE_CHECKING:
    from world import World
    from enemy import Enemy


class Player:
    """
    Pure-logic player (no Ursina imports).
    The GameRenderer creates and manages the Ursina entity separately.
    """

    def __init__(self, world: "World"):
        self.world = world

        # ── Position & movement ─────────────────────────────────────────
        cx, cy, cz = world.world_center()
        self.x  = cx
        self.y  = cy + 0.8    # stand on terrain
        self.z  = cz
        self.vy = 0.0         # vertical velocity for jumping
        self.on_ground    = True
        self.facing_angle = 0.0   # radians in XZ, -Z is forward
        self.pitch        = 0.0   # camera pitch degrees
        self.yaw          = 0.0   # camera yaw degrees

        # Knockback
        self.knockback_vel_x = 0.0
        self.knockback_vel_z = 0.0
        self.knockback_time  = 0.0

        # ── Vital stats ──────────────────────────────────────────────────
        self.max_health  = PLAYER_MAX_HEALTH
        self.max_stamina = PLAYER_MAX_STAMINA
        self.max_hunger  = PLAYER_MAX_HUNGER
        self.max_thirst  = PLAYER_MAX_THIRST
        self.health      = float(self.max_health)
        self.stamina     = float(self.max_stamina)
        self.hunger      = float(self.max_hunger)
        self.thirst      = float(self.max_thirst)

        # ── XP / Level ───────────────────────────────────────────────────
        self.xp         = 0
        self.level      = 1
        self.xp_to_next = 100
        self.level_ups  = []   # queued level-up messages

        # ── Combat state ─────────────────────────────────────────────────
        self.atk_cooldown  = 0.0
        self.invincible    = 0.0
        self.is_blocking   = False
        self.is_sprinting  = False
        self.is_dead       = False
        self.hit_radius    = 0.55

        # ── Status effects ───────────────────────────────────────────────
        self.effects      = EffectManager()
        self.defense      = 0   # recalculated each frame from equipment

        # ── Inventory ────────────────────────────────────────────────────
        self.inv = PlayerInventory()
        self._give_start_items()

        # ── Stats tracking ───────────────────────────────────────────────
        self.enemies_killed = 0
        self.items_crafted  = 0
        self.structures_built = 0
        self.total_damage_dealt = 0
        self.total_damage_taken = 0
        self.distance_travelled = 0.0
        self._last_x = self.x
        self._last_z = self.z

        # ── Interaction memory ───────────────────────────────────────────
        self.nearby_station = None   # updated by game loop
        self.recent_drops: List[tuple] = []   # [(item_name, count, timer)]

    # ── Starting items ───────────────────────────────────────────────────
    def _give_start_items(self):
        for item_id, count in [
            ("plant_fiber", 6), ("pebble", 4), ("sprig", 4),
            ("raw_mushroom", 2), ("berry_chunk", 3), ("twig", 3),
        ]:
            self.inv.add(make(item_id, count))

    # ── Movement ─────────────────────────────────────────────────────────
    def move(self, move_x: float, move_z: float, dt: float,
             sprint: bool = False):
        if self.is_dead:
            return

        # Stamina check for sprint
        if sprint and self.stamina > 5:
            self.is_sprinting = True
            self.stamina = max(0, self.stamina - SPRINT_STAMINA_COST * dt)
        else:
            self.is_sprinting = False

        speed_mult = PLAYER_SPRINT_MULT if self.is_sprinting else 1.0
        # Equipment speed bonus
        speed_bonus = self.inv.speed_bonus
        # Effect speed mod
        speed_mod = self.effects.get_stat_mod("speed")
        base_speed = PLAYER_MOVE_SPEED * (1.0 + speed_bonus) * (1.0 + speed_mod)
        speed = base_speed * speed_mult

        # Rotate movement by yaw
        yaw_rad = math.radians(self.yaw)
        fw_x = math.sin(yaw_rad)
        fw_z = math.cos(yaw_rad)
        right_x = math.cos(yaw_rad)
        right_z = -math.sin(yaw_rad)

        dx = (move_x * right_x + move_z * fw_x) * speed * dt
        dz = (move_x * right_z + move_z * fw_z) * speed * dt

        # Separate axis collision
        new_x = self.x + dx
        if self.world.is_walkable(new_x, self.z):
            self.x = new_x
        new_z = self.z + dz
        if self.world.is_walkable(self.x, new_z):
            self.z = new_z

        # Clamp to world
        margin = 0.5
        max_w  = self.world.size * self.world.scale - margin
        self.x = max(margin, min(max_w, self.x))
        self.z = max(margin, min(max_w, self.z))

        # Terrain-follow Y
        ground_y = self.world.height_at_world_xz(self.x, self.z)
        self.y = ground_y + 0.55

        # Track facing
        if abs(dx) > 0.001 or abs(dz) > 0.001:
            self.facing_angle = math.atan2(dx, dz)

        # Distance stat
        d = math.hypot(self.x - self._last_x, self.z - self._last_z)
        self.distance_travelled += d
        self._last_x, self._last_z = self.x, self.z

    def apply_knockback(self, dt: float):
        if self.knockback_time > 0:
            self.knockback_time -= dt
            new_x = self.x + self.knockback_vel_x * dt
            new_z = self.z + self.knockback_vel_z * dt
            if self.world.is_walkable(new_x, self.z):
                self.x = new_x
            if self.world.is_walkable(self.x, new_z):
                self.z = new_z

    def jump(self):
        if self.on_ground and self.stamina > 10:
            self.vy = PLAYER_JUMP_POWER
            self.on_ground = False
            self.stamina -= 10

    # ── Combat ───────────────────────────────────────────────────────────
    def get_weapon(self):
        return self.inv.weapon

    def can_attack(self) -> bool:
        return (not self.is_dead and self.atk_cooldown <= 0 and
                self.stamina > 3)

    def attack(self, enemies: list) -> List[tuple]:
        """Perform melee swing. Returns list of (enemy, damage, is_crit)."""
        if not self.can_attack():
            return []

        weapon = self.get_weapon()
        if weapon:
            base_dmg     = weapon.damage
            atk_spd_mult = weapon.attack_speed
            kb_force     = weapon.knockback * KNOCKBACK_BASE
            reach        = weapon.reach * PLAYER_ATTACK_RANGE
        else:
            base_dmg     = BASE_DAMAGE
            atk_spd_mult = 1.0
            kb_force     = KNOCKBACK_BASE
            reach        = PLAYER_ATTACK_RANGE

        # Damage bonuses from effects
        dmg_bonus = self.effects.get_stat_mod("damage")
        # Equipment bonus
        dmg_bonus += self.inv.equipment.total_bonus("attack_speed")
        final_dmg = int(base_dmg * (1.0 + dmg_bonus))

        night_t   = getattr(self, "_night_mult", 1.0)
        swing     = SwingAttack(
            attacker   = self,
            damage     = final_dmg,
            arc_rad    = math.radians(80),
            reach      = reach,
            knockback  = kb_force,
            weapon_item= weapon,
            night_mult = 1.0,  # player doesn't get night penalty
        )
        results = swing.resolve(enemies)

        cooldown = PLAYER_ATK_COOLDOWN / max(0.1, atk_spd_mult)
        self.atk_cooldown = cooldown
        self.stamina      = max(0, self.stamina - 8)

        for enemy, dmg, is_crit in results:
            self.total_damage_dealt += dmg
            if not enemy.active:
                self.enemies_killed += 1
                self.gain_xp(enemy.xp_reward)

        return results

    def harvest(self, resources: list) -> List[Item]:
        """Swing at closest resource, return drops."""
        if self.atk_cooldown > 0 or self.is_dead:
            return []
        weapon    = self.get_weapon()
        tool_type = weapon.tool_type if weapon else None
        damage    = (weapon.damage if weapon else BASE_DAMAGE)
        reach     = (weapon.reach * PLAYER_ATTACK_RANGE if weapon else PLAYER_ATTACK_RANGE)
        cooldown  = (PLAYER_ATK_COOLDOWN / weapon.attack_speed if weapon else PLAYER_ATK_COOLDOWN)

        drops = []
        for res in resources:
            d = math.hypot(res.x - self.x, res.z - self.z)
            if d <= reach and res.active:
                new_drops = res.hit(damage, tool_type)
                drops.extend(new_drops)
                if new_drops:
                    break   # one resource per swing

        self.atk_cooldown = cooldown
        self.stamina      = max(0, self.stamina - 5)
        return drops

    def collect(self, resources: list) -> List[Item]:
        """Press E to collect the nearest resource."""
        if self.is_dead:
            return []
        drops = []
        for res in resources:
            d = math.hypot(res.x - self.x, res.z - self.z)
            if d <= PLAYER_COLLECT_RANGE and res.active:
                new_drops = res.hit(999, None)
                drops.extend(new_drops)
                break
        return drops

    def take_damage(self, amount: float,
                    source_x: float = None, source_z: float = None) -> float:
        if self.invincible > 0 or self.is_dead:
            return 0.0

        defense = (self.inv.defense + self.effects.get_stat_mod("defense"))
        if self.is_blocking:
            defense += 25

        reduced = max(1.0, amount - defense * 0.35)
        self.health -= reduced
        self.invincible = PLAYER_INVINCIBLE_T
        self.total_damage_taken += reduced

        # Knockback away from source
        if source_x is not None and source_z is not None:
            dx = self.x - source_x
            dz = self.z - source_z
            apply_knockback_3d(self, dx, dz, 4.0)

        if self.health <= 0:
            self.health  = 0
            self.is_dead = True

        return reduced

    def eat(self, item: Item) -> bool:
        if item.itype != ITYPE_FOOD:
            return False
        self.hunger = min(self.max_hunger, self.hunger + item.hunger_val)
        self.thirst = min(self.max_thirst, self.thirst + item.thirst_val)
        self.health = min(self.max_health, self.health + item.heal_val)
        if item.status_effect and random.random() < item.effect_chance:
            self.effects.apply(item.status_effect, item.effect_duration)
        return True

    # ── XP / Level ───────────────────────────────────────────────────────
    def gain_xp(self, amount: int):
        self.xp += amount
        while self.xp >= self.xp_to_next:
            self.xp       -= self.xp_to_next
            self.level    += 1
            self.xp_to_next = int(self.xp_to_next * 1.45)
            self.max_health  += 12
            self.max_stamina += 6
            self.health      = self.max_health
            self.stamina     = self.max_stamina
            self.level_ups.append(f"Level {self.level}! Max health +12")

    def pop_level_ups(self) -> List[str]:
        msgs = self.level_ups[:]
        self.level_ups.clear()
        return msgs

    # ── Update ───────────────────────────────────────────────────────────
    def update(self, dt: float):
        if self.is_dead:
            return

        # Cooldowns
        self.atk_cooldown = max(0.0, self.atk_cooldown - dt)
        self.invincible   = max(0.0, self.invincible   - dt)

        # Knockback
        self.apply_knockback(dt)

        # Stamina regen
        if not self.is_sprinting and not self.is_blocking:
            regen = STAMINA_REGEN * dt
            self.stamina = min(self.max_stamina, self.stamina + regen)

        if self.is_blocking:
            self.stamina = max(0, self.stamina - BLOCK_STAMINA_COST * dt)
            if self.stamina <= 0:
                self.is_blocking = False

        # Hunger / thirst drain
        self.hunger = max(0.0, self.hunger - HUNGER_DRAIN * dt)
        self.thirst = max(0.0, self.thirst - THIRST_DRAIN * dt)

        # Starvation / dehydration
        if self.hunger <= 0 or self.thirst <= 0:
            self.health -= 2.5 * dt

        # Health regen when well-fed
        if self.hunger > HEALTH_REGEN_THRESH and self.thirst > HEALTH_REGEN_THRESH:
            self.health = min(self.max_health,
                              self.health + HEALTH_REGEN_RATE * dt)

        # Status effect tick damage
        effect_dmg = self.effects.update(dt, self)
        if effect_dmg > 0:
            self.health -= effect_dmg

        # Recalculate defense cache
        self.defense = self.inv.defense + self.effects.get_stat_mod("defense")

        if self.health <= 0:
            self.health  = 0.0
            self.is_dead = True

    # ── Respawn ──────────────────────────────────────────────────────────
    def respawn(self):
        cx, cy, cz = self.world.world_center()
        self.x, self.z = cx + random.uniform(-3, 3), cz + random.uniform(-3, 3)
        self.y = self.world.height_at_world_xz(self.x, self.z) + 0.55
        self.health      = self.max_health
        self.stamina     = self.max_stamina
        self.hunger      = 60.0
        self.thirst      = 60.0
        self.is_dead     = False
        self.invincible  = 2.0
        self.effects.clear()
        self.knockback_time = 0

    # ── Serialization ────────────────────────────────────────────────────
    def serialize(self) -> dict:
        return {
            "x": self.x, "y": self.y, "z": self.z,
            "yaw": self.yaw, "pitch": self.pitch,
            "health": self.health, "stamina": self.stamina,
            "hunger": self.hunger, "thirst": self.thirst,
            "xp": self.xp, "level": self.level,
            "xp_to_next": self.xp_to_next,
            "max_health": self.max_health,
            "max_stamina": self.max_stamina,
            "inventory": self.inv.serialize(),
            "enemies_killed": self.enemies_killed,
            "items_crafted": self.items_crafted,
        }

    def deserialize(self, data: dict):
        self.x = data.get("x", self.x)
        self.y = data.get("y", self.y)
        self.z = data.get("z", self.z)
        self.yaw         = data.get("yaw", 0)
        self.pitch       = data.get("pitch", 0)
        self.health      = data.get("health", self.max_health)
        self.stamina     = data.get("stamina", self.max_stamina)
        self.hunger      = data.get("hunger", self.max_hunger)
        self.thirst      = data.get("thirst", self.max_thirst)
        self.xp          = data.get("xp", 0)
        self.level       = data.get("level", 1)
        self.xp_to_next  = data.get("xp_to_next", 100)
        self.max_health  = data.get("max_health", PLAYER_MAX_HEALTH)
        self.max_stamina = data.get("max_stamina", PLAYER_MAX_STAMINA)
        self.enemies_killed = data.get("enemies_killed", 0)
        self.items_crafted  = data.get("items_crafted", 0)
        if "inventory" in data:
            self.inv.deserialize(data["inventory"])
