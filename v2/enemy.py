# ============================================================
#  BACKYARD SURVIVAL v2  –  Enemy AI (3D)
# ============================================================
from __future__ import annotations
import math
import random
from typing import List, Dict, Optional, TYPE_CHECKING
from constants import *
from items import make, Item
from status_effects import EffectManager
from combat import apply_knockback_3d, calc_melee_damage, roll_crit, Projectile

if TYPE_CHECKING:
    from world import World
    from player import Player


# ════════════════════════════════════════════════════════════
#  AI STATE MACHINE
# ════════════════════════════════════════════════════════════
AI_IDLE    = "idle"
AI_WANDER  = "wander"
AI_AGGRO   = "aggro"
AI_ATTACK  = "attack"
AI_FLEE    = "flee"
AI_PATROL  = "patrol"
AI_STALK   = "stalk"    # slow approach, then burst


# ════════════════════════════════════════════════════════════
#  BASE ENEMY
# ════════════════════════════════════════════════════════════

class Enemy:
    _id_counter = 0

    def __init__(self, x: float, y: float, z: float):
        Enemy._id_counter += 1
        self.uid = Enemy._id_counter

        self.x, self.y, self.z = x, y, z
        self.vy = 0.0
        self.facing_angle = random.uniform(0, math.pi*2)

        # Knockback
        self.knockback_vel_x = 0.0
        self.knockback_vel_z = 0.0
        self.knockback_time  = 0.0

        # Stats — set by subclass
        self.max_health  = 30.0
        self.health      = 30.0
        self.damage      = 8
        self.defense     = 0
        self.speed       = 2.5
        self.hit_radius  = 0.5
        self.atk_range   = 0.9
        self.atk_cd      = 0.0
        self.atk_rate    = 1.5
        self.knockback   = 2.5
        self.xp_reward   = 15
        self.aggro_range = 8.0
        self.deaggro_d   = 18.0
        self.etype       = "base"
        self.active      = True
        self.element     = None

        self.effects     = EffectManager()
        self.projectiles : List[Projectile] = []

        # AI state
        self.ai_state      = AI_WANDER
        self.wander_target = (x, z)
        self.wander_timer  = random.uniform(1.0, 4.0)
        self.hurt_flash    = 0.0

        # Drops: set by subclass
        self.drops: List[tuple] = []   # [(item_id, lo, hi, chance)]

        # Ursina entity
        self.entity = None

        # Night mult (set by game loop)
        self._night_mult = 1.0

    # ── Navigation ──────────────────────────────────────────────────────
    def _move_toward(self, tx: float, tz: float, dt: float, world: "World",
                      speed_mult: float = 1.0):
        dx = tx - self.x
        dz = tz - self.z
        dist = math.hypot(dx, dz)
        if dist < 0.05:
            return
        self.facing_angle = math.atan2(dx, dz)
        spd = self.speed * speed_mult
        spd_mod = self.effects.get_stat_mod("speed")
        spd *= max(0.0, 1.0 + spd_mod)
        nx = dx / dist * spd * dt
        nz = dz / dist * spd * dt
        new_x = self.x + nx
        if world.is_walkable(new_x, self.z):
            self.x = new_x
        new_z = self.z + nz
        if world.is_walkable(self.x, new_z):
            self.z = new_z
        # Terrain Y
        self.y = world.height_at_world_xz(self.x, self.z) + 0.3

    def _pick_wander_target(self, world: "World"):
        angle = random.uniform(0, math.pi*2)
        dist  = random.uniform(2.0, 8.0)
        tx = self.x + math.sin(angle) * dist
        tz = self.z + math.cos(angle) * dist
        tx = max(1.0, min(world.size * world.scale - 1.0, tx))
        tz = max(1.0, min(world.size * world.scale - 1.0, tz))
        if world.is_walkable(tx, tz):
            self.wander_target = (tx, tz)

    def _dist_to_player(self, player: "Player") -> float:
        return math.sqrt((self.x-player.x)**2 + (self.z-player.z)**2)

    # ── AI update ────────────────────────────────────────────────────────
    def update(self, dt: float, player: "Player", world: "World"):
        if not self.active:
            return

        self.hurt_flash    = max(0.0, self.hurt_flash - dt)
        self.atk_cd        = max(0.0, self.atk_cd - dt)
        self.knockback_time= max(0.0, self.knockback_time - dt)
        self.wander_timer  = max(0.0, self.wander_timer - dt)

        # Apply knockback
        if self.knockback_time > 0:
            new_x = self.x + self.knockback_vel_x * dt
            new_z = self.z + self.knockback_vel_z * dt
            if world.is_walkable(new_x, self.z): self.x = new_x
            if world.is_walkable(self.x, new_z): self.z = new_z

        # Status effects
        eff_dmg = self.effects.update(dt, self)
        if eff_dmg > 0:
            self.health -= eff_dmg

        if self.health <= 0:
            self.active = False
            return

        dist_to_player = self._dist_to_player(player)
        self._run_ai(dt, player, world, dist_to_player)

        # Update projectiles
        for proj in self.projectiles[:]:
            proj.update(dt)
            if not proj.active:
                self.projectiles.remove(proj)
                continue
            if proj.try_hit_target(player):
                proj.apply_to(player, dist_to_player, self._night_mult)
                self.projectiles.remove(proj)

    def _run_ai(self, dt: float, player: "Player", world: "World", dist: float):
        # Aggro / deaggro
        if dist < self.aggro_range:
            self.ai_state = AI_AGGRO
        elif self.ai_state == AI_AGGRO and dist > self.deaggro_d:
            self.ai_state = AI_WANDER

        if self.ai_state == AI_AGGRO:
            self._ai_aggro(dt, player, world, dist)
        else:
            self._ai_wander(dt, world)

    def _ai_aggro(self, dt: float, player: "Player", world: "World", dist: float):
        self._move_toward(player.x, player.z, dt, world)
        if dist <= self.atk_range + player.hit_radius and self.atk_cd <= 0:
            self._do_attack(player)

    def _ai_wander(self, dt: float, world: "World"):
        if self.wander_timer <= 0:
            self._pick_wander_target(world)
            self.wander_timer = random.uniform(2.0, 5.0)
        tx, tz = self.wander_target
        dist   = math.hypot(tx - self.x, tz - self.z)
        if dist > 0.3:
            self._move_toward(tx, tz, dt, world, speed_mult=0.45)

    def _do_attack(self, player: "Player"):
        dmg = calc_melee_damage(self.damage, int(player.defense),
                                 roll_crit(0.05), self.element, self._night_mult)
        player.take_damage(dmg, self.x, self.z)
        self.atk_cd = self.atk_rate

    # ── Damage ───────────────────────────────────────────────────────────
    def take_damage(self, amount: float) -> float:
        self.health -= amount
        self.hurt_flash = 0.3
        if self.health <= 0:
            self.active = False
            self.health = 0
        self.ai_state = AI_AGGRO
        return amount

    # ── Drops ────────────────────────────────────────────────────────────
    def get_drops(self) -> List[Item]:
        result = []
        for item_id, lo, hi, chance in self.drops:
            if random.random() <= chance:
                cnt = random.randint(lo, hi)
                if cnt > 0:
                    result.append(make(item_id, cnt))
        return result


# ════════════════════════════════════════════════════════════
#  SPECIFIC ENEMY CLASSES
# ════════════════════════════════════════════════════════════

class WorkerAnt(Enemy):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.etype       = E_WORKER_ANT
        self.max_health  = 38.0
        self.health      = 38.0
        self.damage      = 8
        self.speed       = 3.2
        self.hit_radius  = 0.45
        self.atk_range   = 0.85
        self.atk_rate    = 1.3
        self.knockback   = 2.0
        self.xp_reward   = 12
        self.aggro_range = 8.0
        self.drops = [
            ("ant_part",    1, 3, 1.0),
            ("ant_mandible",0, 1, 0.45),
            ("ant_egg",     0, 1, 0.20),
        ]


class FireAnt(Enemy):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.etype       = E_FIRE_ANT
        self.max_health  = 55.0
        self.health      = 55.0
        self.damage      = 15
        self.speed       = 3.8
        self.hit_radius  = 0.48
        self.atk_range   = 0.9
        self.atk_rate    = 1.1
        self.knockback   = 2.5
        self.xp_reward   = 28
        self.aggro_range = 10.0
        self.element     = "fire"
        self.drops = [
            ("ant_part",      1, 3, 1.0),
            ("ant_mandible",  1, 2, 0.65),
            ("fire_ant_acid", 0, 2, 0.55),
            ("ant_head",      0, 1, 0.20),
        ]


class SoldierAnt(Enemy):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.etype       = E_SOLDIER_ANT
        self.max_health  = 75.0
        self.health      = 75.0
        self.damage      = 18
        self.defense     = 8
        self.speed       = 2.8
        self.hit_radius  = 0.58
        self.atk_range   = 1.0
        self.atk_rate    = 1.5
        self.knockback   = 3.5
        self.xp_reward   = 35
        self.aggro_range = 7.0
        self.drops = [
            ("soldier_ant_part", 1, 3, 1.0),
            ("ant_mandible",     1, 2, 0.75),
            ("ant_head",         0, 1, 0.30),
            ("ant_part",         1, 2, 1.0),
        ]


class OrbWeaverSpider(Enemy):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.etype       = E_SPIDER
        self.max_health  = 65.0
        self.health      = 65.0
        self.damage      = 20
        self.speed       = 4.5
        self.hit_radius  = 0.55
        self.atk_range   = 1.0
        self.atk_rate    = 1.6
        self.knockback   = 2.0
        self.xp_reward   = 45
        self.aggro_range = 12.0
        self.element     = "poison"
        self._web_cd     = 0.0
        self.drops = [
            ("spider_silk",      1, 4, 1.0),
            ("spider_fang",      0, 2, 0.55),
            ("spider_part",      1, 3, 1.0),
            ("spider_venom_gland",0, 1, 0.25),
        ]

    def _do_attack(self, player: "Player"):
        super()._do_attack(player)
        # Poison on hit
        if random.random() < 0.30:
            player.effects.apply(SE_POISON, 5.0)

    def _run_ai(self, dt, player, world, dist):
        super()._run_ai(dt, player, world, dist)
        self._web_cd = max(0, self._web_cd - dt)


class WolfSpider(Enemy):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.etype       = E_WOLF_SPIDER
        self.max_health  = 90.0
        self.health      = 90.0
        self.damage      = 25
        self.defense     = 5
        self.speed       = 5.5   # fast!
        self.hit_radius  = 0.60
        self.atk_range   = 1.1
        self.atk_rate    = 1.2
        self.knockback   = 3.0
        self.xp_reward   = 60
        self.aggro_range = 6.0   # ambush range
        self.deaggro_d   = 25.0
        self._pounce_cd  = 0.0
        self.drops = [
            ("spider_silk",      1, 5, 1.0),
            ("spider_fang",      1, 2, 0.70),
            ("spider_part",      1, 3, 1.0),
            ("wolf_spider_eye",  0, 1, 0.40),
            ("spider_venom_gland",0, 1, 0.30),
        ]

    def _run_ai(self, dt, player, world, dist):
        super()._run_ai(dt, player, world, dist)
        # Pounce when at medium distance
        self._pounce_cd = max(0, self._pounce_cd - dt)
        if (self.ai_state == AI_AGGRO and 2.0 < dist < 5.0
                and self._pounce_cd <= 0):
            # Lunge
            apply_knockback_3d(self,
                                player.x - self.x, player.z - self.z,
                                12.0, 0.4)
            self._pounce_cd = 4.0


class LadyBug(Enemy):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.etype       = E_LADYBUG
        self.max_health  = 140.0
        self.health      = 140.0
        self.damage      = 12
        self.defense     = 15
        self.speed       = 1.8
        self.hit_radius  = 0.75
        self.atk_range   = 1.2
        self.atk_rate    = 2.2
        self.knockback   = 4.0
        self.xp_reward   = 55
        self.aggro_range = 0.0   # passive — only aggro when hit
        self.drops = [
            ("ladybug_shell", 1, 2, 1.0),
        ]
        self._is_passive = True

    def take_damage(self, amount: float) -> float:
        self._is_passive = False
        self.aggro_range = 999.0   # will now chase
        return super().take_damage(amount)


class StinkBug(Enemy):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.etype       = E_STINKBUG
        self.max_health  = 80.0
        self.health      = 80.0
        self.damage      = 12
        self.defense     = 4
        self.speed       = 2.2
        self.hit_radius  = 0.60
        self.atk_range   = 0.9
        self.atk_rate    = 2.5
        self.knockback   = 2.0
        self.xp_reward   = 32
        self.aggro_range = 9.0
        self._gas_cd     = 0.0
        self.drops = [
            ("stinkbug_gas_sac", 1, 2, 1.0),
            ("ant_part",         0, 1, 0.30),
        ]

    def _run_ai(self, dt, player, world, dist):
        super()._run_ai(dt, player, world, dist)
        self._gas_cd = max(0, self._gas_cd - dt)
        # Gas cloud AoE when close
        if self.ai_state == AI_AGGRO and dist < 2.5 and self._gas_cd <= 0:
            player.take_damage(7.0, self.x, self.z)
            player.effects.apply(SE_STINK, 5.0)
            self._gas_cd = 3.5


class BombardierBeetle(Enemy):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.etype       = E_BOMBARDIER
        self.max_health  = 60.0
        self.health      = 60.0
        self.damage      = 7    # weak melee
        self.speed       = 2.8
        self.hit_radius  = 0.52
        self.atk_range   = 0.9
        self.atk_rate    = 3.0
        self.knockback   = 1.5
        self.xp_reward   = 38
        self.aggro_range = 14.0
        self._shoot_cd   = 0.0
        self._preferred  = 6.0  # preferred combat range
        self.element     = "fire"
        self.drops = [
            ("bombardier_gland", 1, 2, 1.0),
            ("ant_part",         0, 1, 0.30),
        ]

    def _run_ai(self, dt, player, world, dist):
        self.atk_cd    = max(0, self.atk_cd - dt)
        self._shoot_cd = max(0, self._shoot_cd - dt)
        self.wander_timer = max(0, self.wander_timer - dt)
        self.hurt_flash   = max(0, self.hurt_flash - dt)

        if dist < self.aggro_range:
            self.ai_state = AI_AGGRO

        if self.ai_state != AI_AGGRO:
            self._ai_wander(dt, world)
            return

        if dist > self.deaggro_d:
            self.ai_state = AI_WANDER
            return

        # Keep preferred distance
        if dist < self._preferred - 1.0:
            # Back away
            dx = self.x - player.x
            dz = self.z - player.z
            self._move_toward(self.x + dx, self.z + dz, dt, world)
        elif dist > self._preferred + 1.0:
            self._move_toward(player.x, player.z, dt, world)

        # Shoot
        if self._shoot_cd <= 0 and dist < self._preferred + 3.0:
            dy = (player.y + 0.5) - self.y
            dx = player.x - self.x
            dz = player.z - self.z
            self.projectiles.append(Projectile(
                owner=self, x=self.x, y=self.y+0.3, z=self.z,
                dir_x=dx, dir_y=dy, dir_z=dz,
                speed=8.0, damage=22,
                color=COL_FIRE, hits_player=True,
                element="fire",
                status_effect=SE_BURN, effect_chance=0.70, effect_dur=3.0,
            ))
            self._shoot_cd = 2.2


class Weevil(Enemy):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.etype       = E_WEEVIL
        self.max_health  = 45.0
        self.health      = 45.0
        self.damage      = 10
        self.speed       = 2.6
        self.hit_radius  = 0.48
        self.atk_range   = 0.85
        self.atk_rate    = 1.4
        self.knockback   = 2.0
        self.xp_reward   = 20
        self.aggro_range = 7.0
        self.drops = [
            ("weevil_snout", 0, 1, 0.45),
            ("ant_part",     1, 2, 1.0),
        ]


class Aphid(Enemy):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.etype       = E_APHID
        self.max_health  = 18.0
        self.health      = 18.0
        self.damage      = 3
        self.speed       = 1.5
        self.hit_radius  = 0.35
        self.atk_range   = 0.6
        self.atk_rate    = 2.0
        self.knockback   = 0.8
        self.xp_reward   = 5
        self.aggro_range = 0.0   # fully passive
        self.drops = [
            ("aphid_honeydew", 1, 3, 1.0),
        ]

    def _run_ai(self, dt, player, world, dist):
        # Flee if hit
        if self.health < self.max_health:
            dx = self.x - player.x
            dz = self.z - player.z
            self._move_toward(self.x + dx*3, self.z + dz*3, dt, world, 0.8)
        else:
            self._ai_wander(dt, world)


class Gnat(Enemy):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.etype       = E_GNAT
        self.max_health  = 12.0
        self.health      = 12.0
        self.damage      = 4
        self.speed       = 4.0
        self.hit_radius  = 0.30
        self.atk_range   = 0.6
        self.atk_rate    = 1.0
        self.knockback   = 0.5
        self.xp_reward   = 4
        self.aggro_range = 5.0
        self.drops = [
            ("gnat_fuzz",  1, 2, 1.0),
            ("plant_fiber",0, 1, 0.30),
        ]

    def _run_ai(self, dt, player, world, dist):
        # Swarm behavior: moves in circles around player
        if dist < self.aggro_range:
            self.ai_state = AI_AGGRO
        if self.ai_state == AI_AGGRO:
            angle = math.atan2(self.z - player.z, self.x - player.x)
            angle += 0.5 * dt
            target_x = player.x + math.cos(angle) * 1.2
            target_z = player.z + math.sin(angle) * 1.2
            self._move_toward(target_x, target_z, dt, world)
            if dist <= self.atk_range and self.atk_cd <= 0:
                self._do_attack(player)
        else:
            self._ai_wander(dt, world)


class Mosquito(Enemy):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.etype       = E_MOSQUITO
        self.max_health  = 22.0
        self.health      = 22.0
        self.damage      = 6
        self.speed       = 4.5
        self.hit_radius  = 0.32
        self.atk_range   = 0.7
        self.atk_rate    = 1.2
        self.knockback   = 0.8
        self.xp_reward   = 8
        self.aggro_range = 10.0
        self.element     = "poison"
        self.drops = [
            ("mosquito_beak",  1, 2, 1.0),
            ("dew_drop",       0, 1, 0.25),
        ]

    def _do_attack(self, player):
        super()._do_attack(player)
        if random.random() < 0.50:
            player.effects.apply(SE_BLEED, 4.0)


class Cricket(Enemy):
    def __init__(self, x, y, z):
        super().__init__(x, y, z)
        self.etype       = E_CRICKET
        self.max_health  = 85.0
        self.health      = 85.0
        self.damage      = 16
        self.defense     = 3
        self.speed       = 3.8
        self.hit_radius  = 0.60
        self.atk_range   = 1.0
        self.atk_rate    = 1.5
        self.knockback   = 3.5
        self.xp_reward   = 40
        self.aggro_range = 7.0
        self._jump_cd    = 0.0
        self.drops = [
            ("cricket_leg",  2, 4, 1.0),
            ("ant_part",     0, 1, 0.40),
        ]

    def _run_ai(self, dt, player, world, dist):
        super()._run_ai(dt, player, world, dist)
        self._jump_cd = max(0, self._jump_cd - dt)
        # Jumping attack — leap at player from medium distance
        if (self.ai_state == AI_AGGRO and 2.5 < dist < 6.0
                and self._jump_cd <= 0):
            apply_knockback_3d(self,
                                player.x - self.x, player.z - self.z,
                                14.0, 0.5)
            self._jump_cd = 3.0


# ════════════════════════════════════════════════════════════
#  ENEMY CLASS TABLE
# ════════════════════════════════════════════════════════════
ENEMY_CLASS_MAP = {
    E_WORKER_ANT:  WorkerAnt,
    E_FIRE_ANT:    FireAnt,
    E_SOLDIER_ANT: SoldierAnt,
    E_SPIDER:      OrbWeaverSpider,
    E_WOLF_SPIDER: WolfSpider,
    E_LADYBUG:     LadyBug,
    E_STINKBUG:    StinkBug,
    E_BOMBARDIER:  BombardierBeetle,
    E_WEEVIL:      Weevil,
    E_APHID:       Aphid,
    E_GNAT:        Gnat,
    E_MOSQUITO:    Mosquito,
    E_CRICKET:     Cricket,
}

# Biome -> list of (etype, weight)
BIOME_SPAWN_TABLE: Dict[int, List[tuple]] = {
    TILE_GRASS:     [(E_WORKER_ANT,4),(E_APHID,3),(E_LADYBUG,1),(E_GNAT,3),(E_MOSQUITO,2)],
    TILE_DRY_GRASS: [(E_WORKER_ANT,3),(E_FIRE_ANT,2),(E_WEEVIL,3),(E_CRICKET,2)],
    TILE_DIRT:      [(E_WORKER_ANT,3),(E_WEEVIL,3),(E_FIRE_ANT,1),(E_CRICKET,1)],
    TILE_LEAVES:    [(E_SPIDER,3),(E_WOLF_SPIDER,1),(E_LADYBUG,1),(E_STINKBUG,2),(E_APHID,2)],
    TILE_STONE:     [(E_BOMBARDIER,2),(E_STINKBUG,2),(E_WEEVIL,2),(E_SOLDIER_ANT,1)],
    TILE_CLOVER:    [(E_APHID,4),(E_LADYBUG,2),(E_WORKER_ANT,2),(E_GNAT,3)],
    TILE_MUD:       [(E_STINKBUG,2),(E_APHID,2),(E_MOSQUITO,3)],
    TILE_SAND:      [(E_WORKER_ANT,2),(E_WEEVIL,2),(E_APHID,2),(E_GNAT,2)],
    TILE_GRAVEL:    [(E_BOMBARDIER,2),(E_SOLDIER_ANT,1),(E_WEEVIL,2),(E_CRICKET,1)],
}


def _weighted_choice(table: List[tuple]) -> str:
    total  = sum(w for _, w in table)
    r      = random.uniform(0, total)
    cum    = 0.0
    for etype, w in table:
        cum += w
        if r <= cum:
            return etype
    return table[-1][0]


def spawn_enemies(world: "World", count: int = 80) -> List[Enemy]:
    enemies = []
    attempts = 0
    cx = world.size // 2
    cz = world.size // 2
    while len(enemies) < count and attempts < count * 15:
        attempts += 1
        tx = random.randint(3, world.size - 4)
        tz = random.randint(3, world.size - 4)
        if abs(tx-cx) < 10 and abs(tz-cz) < 10:
            continue
        tile = world.tile_at(tx, tz)
        if tile == TILE_WATER:
            continue
        table = BIOME_SPAWN_TABLE.get(tile, [(E_WORKER_ANT, 1)])
        etype  = _weighted_choice(table)
        EClass = ENEMY_CLASS_MAP.get(etype, WorkerAnt)
        wx = (tx + random.uniform(0.2, 0.8)) * world.scale
        wz = (tz + random.uniform(0.2, 0.8)) * world.scale
        wy = world.height_at_world_xz(wx, wz) + 0.3
        enemies.append(EClass(wx, wy, wz))
    return enemies
