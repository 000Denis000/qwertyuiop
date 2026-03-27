# ============================================================
#  BACKYARD SURVIVAL v2  –  3D World Renderer (Ursina)
# ============================================================
from __future__ import annotations
import math
import random
from typing import Dict, List, Optional, TYPE_CHECKING
from ursina import (
    Entity, DirectionalLight, AmbientLight, PointLight,
    color, Vec3, Vec4, destroy, scene, invoke,
    Mesh, MeshCollider
)
from ursina.shaders import basic_lighting_shader
from constants import *
from world import (World, WorldResource, Structure,
                   RESOURCE_DEFS, STRUCTURE_DEFS, TILE_COLORS)
from enemy import Enemy

if TYPE_CHECKING:
    from player import Player


def _col(c: tuple):
    return color.rgba(*[int(v*255) for v in c])


# ═══════════════════════════════════════════════════════════
#  TERRAIN
# ═══════════════════════════════════════════════════════════

class TerrainRenderer:
    """Renders the world as a grid of cubes/flat tiles."""

    CHUNK = 16   # tiles per chunk (for batching)

    def __init__(self, world: World):
        self.world      = world
        self._chunks    = []   # list of chunk entities
        self._water_ent = None
        self._build()

    def _build(self):
        w = self.world
        # Build terrain chunks
        chunk = self.CHUNK
        for cz in range(0, w.size, chunk):
            for cx in range(0, w.size, chunk):
                self._build_chunk(cx, cz,
                                   min(cx+chunk, w.size),
                                   min(cz+chunk, w.size))
        # Single flat water plane
        water_y = TERRAIN_HEIGHT * WATER_LEVEL - 0.05
        water_w = w.size * TILE_WORLD_SCALE
        self._water_ent = Entity(
            model  = "plane",
            scale  = (water_w, 1, water_w),
            position = (water_w/2, water_y, water_w/2),
            color  = _col(COL_WATER),
            double_sided=True,
        )
        self._chunks.append(self._water_ent)

    def _build_chunk(self, x0, z0, x1, z1):
        w = self.world
        verts, tris, colors_v = [], [], []
        vi = 0
        for tz in range(z0, z1):
            for tx in range(x0, x1):
                tile = w.tiles[tz][tx]
                h    = w.heights[tz][tx]
                col_t= TILE_COLORS.get(tile, COL_GRASS)
                s    = TILE_WORLD_SCALE
                x    = tx * s
                z_   = tz * s
                # Four corners (y varies slightly based on neighbors)
                h00 = w.heights[max(0,tz-1)][max(0,tx-1)] if tz>0 and tx>0 else h
                h10 = w.heights[max(0,tz-1)][min(w.size-1,tx)] if tz>0 else h
                h01 = w.heights[min(w.size-1,tz)][max(0,tx-1)] if tx>0 else h
                h11 = h
                verts += [
                    (x,     h00, z_),      # 0 back-left
                    (x+s,   h10, z_),      # 1 back-right
                    (x,     h01, z_+s),    # 2 front-left
                    (x+s,   h11, z_+s),    # 3 front-right
                ]
                tris += [(vi,vi+2,vi+1),(vi+1,vi+2,vi+3)]
                c = tuple(int(v*255) for v in col_t[:3])
                # Slight shading variation
                shade = 0.92 + random.uniform(0, 0.08)
                c2 = tuple(min(255, int(v*shade)) for v in c)
                colors_v += [c2, c2, c2, c2]
                vi += 4

        if not verts:
            return
        mesh = Mesh(vertices=verts, triangles=tris,
                    colors=colors_v, mode="triangle")
        ent  = Entity(model=mesh, double_sided=True)
        self._chunks.append(ent)

    def destroy(self):
        for e in self._chunks:
            destroy(e)
        self._chunks.clear()


# ═══════════════════════════════════════════════════════════
#  RESOURCE RENDERER
# ═══════════════════════════════════════════════════════════

def _build_resource_entity(res: WorldResource) -> Entity:
    rdata  = RESOURCE_DEFS[res.rtype]
    sc     = rdata.get("scale", (0.2, 0.4, 0.2))
    col_t  = rdata.get("color", COL_GRASS)
    # Choose shape based on type
    if res.rtype in (R_GRASS_BLADE, R_DRY_GRASS, R_SPRIG, R_STEM, R_THISTLE):
        model = "cube"
        # Tall thin blade
    elif res.rtype in (R_PEBBLE, R_QUARTZITE, R_CLAY, R_SAP, R_DEW):
        model = "sphere"
    elif res.rtype in (R_MUSHROOM,):
        model = "sphere"
    elif res.rtype in (R_ACORN, R_BERRY):
        model = "sphere"
    else:
        model = "cube"

    ent = Entity(
        model    = model,
        scale    = sc,
        position = Vec3(res.x, res.y + sc[1]/2, res.z),
        color    = _col(col_t),
        double_sided = True,
    )
    # Slight random Y rotation for variety
    ent.rotation_y = random.uniform(0, 360)
    return ent


class ResourceRenderer:
    def __init__(self, world: World):
        self.world    = world
        self._entities: Dict[int, Entity] = {}
        self._build_all()

    def _build_all(self):
        for uid, res in self.world.resources.items():
            if res.active:
                ent = _build_resource_entity(res)
                self._entities[uid] = ent
                res.entity = ent

    def update(self, events: list):
        """Handle respawn events from world.update()."""
        for res, event in events:
            if event == "respawn":
                if res.uid not in self._entities or \
                   not self._entities[res.uid].enabled:
                    ent = _build_resource_entity(res)
                    self._entities[res.uid] = ent
                    res.entity = ent

    def on_harvest(self, res: WorldResource):
        if not res.active and res.uid in self._entities:
            ent = self._entities[res.uid]
            ent.enabled = False

    def destroy(self):
        for ent in self._entities.values():
            destroy(ent)
        self._entities.clear()


# ═══════════════════════════════════════════════════════════
#  STRUCTURE RENDERER
# ═══════════════════════════════════════════════════════════

def _build_structure_entity(struct: Structure) -> Entity:
    data   = STRUCTURE_DEFS.get(struct.btype, {})
    sc     = data.get("scale", (1.0, 1.0, 1.0))
    col_t  = data.get("color", COL_BARK)
    px, py, pz = struct.world_pos()
    ent = Entity(
        model    = "cube",
        scale    = (sc[0] * TILE_WORLD_SCALE,
                    sc[1],
                    sc[2] * TILE_WORLD_SCALE),
        position = Vec3(px, py + sc[1]/2, pz),
        color    = _col(col_t),
        double_sided = True,
    )
    return ent


class StructureRenderer:
    def __init__(self, world: World):
        self.world    = world
        self._entities: Dict[tuple, Entity] = {}

    def add(self, struct: Structure):
        if (struct.tx, struct.ty) not in self._entities:
            ent = _build_structure_entity(struct)
            self._entities[(struct.tx, struct.ty)] = ent
            struct.entity = ent

    def remove(self, tx: int, ty: int):
        key = (tx, ty)
        if key in self._entities:
            destroy(self._entities.pop(key))

    def update_health(self, struct: Structure):
        ent = self._entities.get((struct.tx, struct.ty))
        if ent:
            ratio = struct.health / struct.max_health
            r, g, b, a = struct.color
            ent.color = color.rgba(int(r*255), int(g*255*ratio),
                                    int(b*255*ratio), 255)

    def destroy(self):
        for ent in self._entities.values():
            destroy(ent)
        self._entities.clear()


# ═══════════════════════════════════════════════════════════
#  ENEMY RENDERER
# ═══════════════════════════════════════════════════════════

ENEMY_VISUAL = {
    E_WORKER_ANT:  {"body_col":COL_ANT,     "body_scale":(0.30,0.18,0.45), "head_scale":(0.20,0.15,0.20)},
    E_FIRE_ANT:    {"body_col":COL_FIRE,     "body_scale":(0.32,0.20,0.48), "head_scale":(0.22,0.16,0.22)},
    E_SOLDIER_ANT: {"body_col":(0.70,0.32,0.10,1), "body_scale":(0.38,0.24,0.55), "head_scale":(0.26,0.20,0.26)},
    E_SPIDER:      {"body_col":COL_SPIDER,   "body_scale":(0.42,0.22,0.55), "head_scale":(0.28,0.18,0.28)},
    E_WOLF_SPIDER: {"body_col":(0.28,0.20,0.35,1), "body_scale":(0.48,0.26,0.58), "head_scale":(0.32,0.22,0.32)},
    E_LADYBUG:     {"body_col":COL_LADYBUG,  "body_scale":(0.60,0.32,0.80), "head_scale":(0.28,0.22,0.28)},
    E_STINKBUG:    {"body_col":COL_STINKBUG, "body_scale":(0.52,0.28,0.65), "head_scale":(0.24,0.18,0.24)},
    E_BOMBARDIER:  {"body_col":(0.35,0.28,0.12,1), "body_scale":(0.46,0.24,0.56), "head_scale":(0.22,0.18,0.22)},
    E_WEEVIL:      {"body_col":COL_BROWN,    "body_scale":(0.38,0.22,0.50), "head_scale":(0.20,0.16,0.30)},
    E_APHID:       {"body_col":(0.65,0.80,0.30,1), "body_scale":(0.25,0.14,0.30), "head_scale":(0.16,0.12,0.16)},
    E_GNAT:        {"body_col":(0.55,0.52,0.45,1), "body_scale":(0.18,0.10,0.24), "head_scale":(0.14,0.10,0.14)},
    E_MOSQUITO:    {"body_col":(0.42,0.40,0.30,1), "body_scale":(0.20,0.10,0.28), "head_scale":(0.12,0.10,0.16)},
    E_CRICKET:     {"body_col":(0.45,0.38,0.22,1), "body_scale":(0.50,0.26,0.62), "head_scale":(0.26,0.20,0.26)},
}

_DEFAULT_VIS = {"body_col":COL_RED, "body_scale":(0.30,0.20,0.40),
                "head_scale":(0.20,0.16,0.20)}


class EnemyRenderer:
    def __init__(self):
        self._entities: Dict[int, dict] = {}  # uid -> {"body":e, "head":e, "hp_bg":e, "hp_fill":e}

    def add(self, enemy: Enemy):
        vis = ENEMY_VISUAL.get(enemy.etype, _DEFAULT_VIS)
        body_c = _col(vis["body_col"])
        bs     = vis["body_scale"]
        hs     = vis["head_scale"]

        body = Entity(model="cube",
                       scale=bs,
                       position=Vec3(enemy.x, enemy.y + bs[1]/2, enemy.z),
                       color=body_c)
        head = Entity(model="sphere",
                       scale=hs,
                       position=Vec3(enemy.x,
                                     enemy.y + bs[1] + hs[1]*0.4,
                                     enemy.z + bs[2]*0.3),
                       color=body_c)
        # Health bar (world-space billboard approximation)
        hp_bg = Entity(model="quad",
                        scale=(0.55, 0.06),
                        position=Vec3(enemy.x, enemy.y + bs[1]*1.6, enemy.z),
                        color=color.rgba(30,30,30,200),
                        billboard=True, always_on_top=True)
        hp_fill = Entity(model="quad",
                          scale=(0.55, 0.05),
                          position=Vec3(enemy.x - 0.275,
                                        enemy.y + bs[1]*1.6,
                                        enemy.z),
                          color=color.red,
                          billboard=True, always_on_top=True,
                          origin=(-0.5, 0))

        self._entities[enemy.uid] = {
            "body": body, "head": head,
            "hp_bg": hp_bg, "hp_fill": hp_fill,
        }
        enemy.entity = body

    def update_enemy(self, enemy: Enemy):
        ents = self._entities.get(enemy.uid)
        if not ents:
            return
        vis = ENEMY_VISUAL.get(enemy.etype, _DEFAULT_VIS)
        bs  = vis["body_scale"]
        hs  = vis["head_scale"]

        if not enemy.active:
            for e in ents.values():
                e.enabled = False
            return

        ents["body"].position = Vec3(enemy.x, enemy.y + bs[1]/2, enemy.z)
        ents["body"].rotation_y = -math.degrees(enemy.facing_angle)
        # Flash on hurt
        if enemy.hurt_flash > 0:
            ents["body"].color = color.white
            ents["head"].color = color.white
        else:
            ents["body"].color = _col(vis["body_col"])
            ents["head"].color = _col(vis["body_col"])

        ents["head"].position = Vec3(
            enemy.x,
            enemy.y + bs[1] + hs[1]*0.4,
            enemy.z + bs[2]*0.3
        )

        # HP bar
        ratio = max(0, enemy.health / enemy.max_health)
        ents["hp_bg"].position  = Vec3(enemy.x, enemy.y + bs[1]*1.7, enemy.z)
        ents["hp_fill"].position= Vec3(enemy.x - 0.275,
                                        enemy.y + bs[1]*1.7, enemy.z)
        ents["hp_fill"].scale_x = 0.55 * ratio
        ents["hp_bg"].enabled   = (ratio < 1.0)
        ents["hp_fill"].enabled = (ratio < 1.0)

    def remove(self, uid: int):
        ents = self._entities.pop(uid, None)
        if ents:
            for e in ents.values():
                destroy(e)

    def destroy_all(self):
        for ents in self._entities.values():
            for e in ents.values():
                destroy(e)
        self._entities.clear()


# ═══════════════════════════════════════════════════════════
#  PLAYER RENDERER
# ═══════════════════════════════════════════════════════════

class PlayerRenderer:
    """Visual representation of the player in 3D."""

    def __init__(self):
        skin   = _col(COL_TAN)
        shirt  = _col(COL_BLUE)
        pants  = _col(COL_DARK_BLUE)

        self.body  = Entity(model="cube", scale=(0.40,0.50,0.22),
                             color=shirt)
        self.head  = Entity(model="sphere", scale=(0.28,0.28,0.28),
                             color=skin)
        self.arm_r = Entity(model="cube", scale=(0.12,0.38,0.12),
                             color=skin)
        self.arm_l = Entity(model="cube", scale=(0.12,0.38,0.12),
                             color=skin)
        self.leg_r = Entity(model="cube", scale=(0.14,0.36,0.14),
                             color=pants)
        self.leg_l = Entity(model="cube", scale=(0.14,0.36,0.14),
                             color=pants)
        # Weapon ghost (shown in hand)
        self.weapon_ent = Entity(model="cube", scale=(0.06,0.30,0.06),
                                  color=_col(COL_PEBBLE), enabled=False)
        self._parts = [self.body, self.head, self.arm_r, self.arm_l,
                        self.leg_r, self.leg_l, self.weapon_ent]
        self._swing_angle = 0.0
        self._swing_dir   = 1

    def update(self, player, dt: float):
        x, y, z = player.x, player.y, player.z
        yaw_deg = -math.degrees(player.facing_angle)

        self.body.position  = Vec3(x, y + 0.32, z)
        self.body.rotation_y= yaw_deg
        self.head.position  = Vec3(x, y + 0.72, z)
        self.head.rotation_y= yaw_deg

        # Arm swing when moving
        if player.is_sprinting or abs(player.knockback_vel_x) > 0.1:
            self._swing_angle += self._swing_dir * 180 * dt
            if abs(self._swing_angle) > 35:
                self._swing_dir *= -1

        arm_offset = 0.26
        ar = math.radians(yaw_deg + 90)
        al = math.radians(yaw_deg - 90)
        self.arm_r.position = Vec3(
            x + math.cos(ar)*arm_offset,
            y + 0.40, z + math.sin(ar)*arm_offset)
        self.arm_r.rotation_x = self._swing_angle
        self.arm_l.position = Vec3(
            x + math.cos(al)*arm_offset,
            y + 0.40, z + math.sin(al)*arm_offset)
        self.arm_l.rotation_x = -self._swing_angle

        leg_offset = 0.10
        fa = math.radians(yaw_deg)
        self.leg_r.position = Vec3(
            x + math.cos(ar)*leg_offset,
            y + 0.06, z + math.sin(ar)*leg_offset)
        self.leg_l.position = Vec3(
            x + math.cos(al)*leg_offset,
            y + 0.06, z + math.sin(al)*leg_offset)

        # Weapon in right hand
        weapon = player.inv.weapon
        if weapon:
            wr = math.radians(yaw_deg + 90)
            wx = x + math.cos(wr)*0.38
            wz = z + math.sin(wr)*0.38
            self.weapon_ent.position  = Vec3(wx, y+0.38, wz)
            self.weapon_ent.rotation_y= yaw_deg
            self.weapon_ent.color     = _col(weapon.color)
            self.weapon_ent.enabled   = True
        else:
            self.weapon_ent.enabled = False

        # Hurt flash
        if player.invincible > 0 and int(player.invincible * 12) % 2 == 0:
            for p_ in self._parts:
                p_.color = color.white
        # else: colors stay normal (set above)

    def destroy(self):
        for p_ in self._parts:
            destroy(p_)


# ═══════════════════════════════════════════════════════════
#  LIGHTING
# ═══════════════════════════════════════════════════════════

class WorldLighting:
    def __init__(self):
        self.sun       = DirectionalLight(shadows=True)
        self.sun.look_at(Vec3(-1, -1.5, -1))
        self.sun.color = _col(COL_CREAM)

        self.ambient   = AmbientLight()
        self.ambient.color = color.rgba(120, 130, 160, 255)

    def update(self, day_t: float):
        """day_t: 0..1, 0.5=noon."""
        if 0.25 < day_t < 0.75:
            # Daytime
            brightness = math.sin((day_t - 0.25) / 0.5 * math.pi)
            sun_r = int(255 * (0.80 + 0.20*brightness))
            sun_g = int(255 * (0.75 + 0.25*brightness))
            sun_b = int(255 * (0.55 + 0.35*brightness))
            self.sun.color = color.rgba(sun_r, sun_g, sun_b, 255)
            self.sun.enabled = True
            amb = int(120 + 80*brightness)
            self.ambient.color = color.rgba(amb, amb+10, amb+20, 255)
        else:
            # Night
            self.sun.enabled = False
            amb = 35
            self.ambient.color = color.rgba(amb, amb, amb+20, 255)

    def destroy(self):
        destroy(self.sun)
        destroy(self.ambient)
