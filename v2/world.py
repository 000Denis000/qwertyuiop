# ============================================================
#  BACKYARD SURVIVAL v2  –  World (3D Terrain + Resources)
# ============================================================
from __future__ import annotations
import random
import math
from typing import List, Dict, Optional, Tuple
from constants import *
from items import make, Item


# ════════════════════════════════════════════════════════════
#  NOISE HELPER  (simple layered diamond-square style)
# ════════════════════════════════════════════════════════════

def _smooth_noise(size: int, scale: float, seed: int) -> list:
    """Returns size×size float grid 0..1 using layered octaves."""
    random.seed(seed)
    grid = [[0.0]*size for _ in range(size)]
    amp, freq, total_amp = 1.0, 1.0, 0.0
    for octave in range(5):
        for y in range(size):
            for x in range(size):
                nx = x / size * scale * freq
                ny = y / size * scale * freq
                # Simple gradient noise approximation
                ix, iy = int(nx), int(ny)
                fx, fy = nx - ix, ny - iy
                random.seed(seed ^ (octave*73856093) ^ (ix*19349663) ^ (iy*83492791))
                v00 = random.random()
                random.seed(seed ^ (octave*73856093) ^ ((ix+1)*19349663) ^ (iy*83492791))
                v10 = random.random()
                random.seed(seed ^ (octave*73856093) ^ (ix*19349663) ^ ((iy+1)*83492791))
                v01 = random.random()
                random.seed(seed ^ (octave*73856093) ^ ((ix+1)*19349663) ^ ((iy+1)*83492791))
                v11 = random.random()
                # Bilinear interpolation with smoothstep
                ux = fx*fx*(3-2*fx)
                uy = fy*fy*(3-2*fy)
                val = (v00*(1-ux)*(1-uy) + v10*ux*(1-uy) +
                       v01*(1-ux)*uy     + v11*ux*uy)
                grid[y][x] += val * amp
        total_amp += amp
        amp  *= 0.5
        freq *= 2.0
    # Normalize
    for y in range(size):
        for x in range(size):
            grid[y][x] /= total_amp
    return grid


# ════════════════════════════════════════════════════════════
#  WORLD RESOURCE
# ════════════════════════════════════════════════════════════

class WorldResource:
    """A harvestable resource object in 3D world."""
    _id_counter = 0

    def __init__(self, rtype: str, x: float, y: float, z: float):
        WorldResource._id_counter += 1
        self.uid     = WorldResource._id_counter
        self.rtype   = rtype
        self.x, self.y, self.z = x, y, z
        data = RESOURCE_DEFS[rtype]
        self.max_health    = data.get("health", 2)
        self.health        = float(self.max_health)
        self.respawn_time  = data.get("respawn", 30.0)
        self.respawn_timer = 0.0
        self.active        = True
        self.required_tool = data.get("req_tool", None)
        self.drops         = data.get("drops", [])
        # Ursina entity set externally
        self.entity        = None

    def hit(self, damage: float, tool_type: Optional[str]) -> List[Item]:
        if not self.active:
            return []
        # Tool penalty
        if self.required_tool and tool_type != self.required_tool:
            damage = max(1.0, damage * 0.25)
        self.health -= damage
        drops = []
        if self.health <= 0:
            self.active        = False
            self.respawn_timer = self.respawn_time
            for item_id, lo, hi in self.drops:
                cnt = random.randint(lo, hi)
                if cnt > 0:
                    drops.append(make(item_id, cnt))
        return drops

    def update(self, dt: float):
        if not self.active:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0:
                self.active = True
                self.health = float(self.max_health)
                return "respawn"
        return None


RESOURCE_DEFS: Dict[str, dict] = {
    R_GRASS_BLADE: {
        "health":2,"respawn":18,"req_tool":None,
        "drops":[("plant_fiber",2,5),("grass_plank",0,2)],
        "scale":(0.12,0.55,0.12),"color":COL_GRASS,
    },
    R_DRY_GRASS: {
        "health":2,"respawn":25,"req_tool":None,
        "drops":[("dry_grass_chunk",2,4),("plant_fiber",0,2)],
        "scale":(0.12,0.45,0.12),"color":COL_DRY_GRASS,
    },
    R_PEBBLE: {
        "health":3,"respawn":80,"req_tool":"axe",
        "drops":[("pebble",2,4),("quartzite_shard",0,1),("smooth_pebble",0,1)],
        "scale":(0.28,0.18,0.28),"color":COL_PEBBLE,
    },
    R_QUARTZITE: {
        "health":5,"respawn":120,"req_tool":"pick",
        "drops":[("quartzite_shard",2,5),("pebble",0,2)],
        "scale":(0.25,0.30,0.25),"color":(0.75,0.78,0.92,1),
    },
    R_ACORN: {
        "health":4,"respawn":90,"req_tool":None,
        "drops":[("acorn_shell",1,2),("acorn_top",0,1),("acorn_meal",1,2)],
        "scale":(0.22,0.22,0.22),"color":COL_ACORN,
    },
    R_SPRIG: {
        "health":2,"respawn":22,"req_tool":None,
        "drops":[("sprig",2,4),("plant_fiber",1,2)],
        "scale":(0.08,0.40,0.08),"color":COL_SPRIG,
    },
    R_MUSHROOM: {
        "health":2,"respawn":55,"req_tool":None,
        "drops":[("raw_mushroom",1,2),("mushroom_spore",1,3),("mushroom_chunk",0,1)],
        "scale":(0.28,0.28,0.28),"color":COL_MUSHROOM,
    },
    R_BERRY: {
        "health":1,"respawn":38,"req_tool":None,
        "drops":[("berry_chunk",2,4)],
        "scale":(0.18,0.18,0.18),"color":COL_BERRY,
    },
    R_CLOVER: {
        "health":1,"respawn":16,"req_tool":None,
        "drops":[("clover_leaf",1,3)],
        "scale":(0.20,0.10,0.20),"color":COL_CLOVER,
    },
    R_STEM: {
        "health":5,"respawn":60,"req_tool":"axe",
        "drops":[("stem_piece",2,4),("plant_fiber",1,2),("sprig",0,1)],
        "scale":(0.10,0.90,0.10),"color":(0.32,0.60,0.20,1),
    },
    R_TWIG: {
        "health":2,"respawn":45,"req_tool":None,
        "drops":[("twig",2,4)],
        "scale":(0.25,0.08,0.08),"color":COL_BARK,
    },
    R_CLAY: {
        "health":4,"respawn":75,"req_tool":"shovel",
        "drops":[("clay_clump",2,5)],
        "scale":(0.28,0.12,0.28),"color":(0.75,0.48,0.36,1),
    },
    R_SAP: {
        "health":1,"respawn":50,"req_tool":None,
        "drops":[("sap",1,3)],
        "scale":(0.14,0.14,0.14),"color":(1.0,0.78,0.20,1),
    },
    R_DEW: {
        "health":1,"respawn":28,"req_tool":None,
        "drops":[("dew_drop",1,2)],
        "scale":(0.16,0.16,0.16),"color":(0.65,0.88,1.0,1),
    },
    R_THISTLE: {
        "health":2,"respawn":40,"req_tool":None,
        "drops":[("thistle_needle",2,4)],
        "scale":(0.10,0.50,0.10),"color":(0.78,0.78,0.30,1),
    },
    R_FLOWER: {
        "health":1,"respawn":35,"req_tool":None,
        "drops":[("flower_petal",2,4)],
        "scale":(0.22,0.26,0.22),"color":COL_PINK,
    },
    R_DANDELION: {
        "health":1,"respawn":30,"req_tool":None,
        "drops":[("dandelion_tuft",1,3),("flower_petal",0,1)],
        "scale":(0.20,0.30,0.20),"color":(1.0,0.95,0.60,1),
    },
}

TILE_RESOURCE_TABLE: Dict[int, List[Tuple[str, float]]] = {
    TILE_GRASS:     [(R_GRASS_BLADE,0.55),(R_SPRIG,0.25),(R_CLOVER,0.18),(R_PEBBLE,0.10),
                     (R_FLOWER,0.08),(R_DEW,0.06)],
    TILE_DRY_GRASS: [(R_DRY_GRASS,0.55),(R_TWIG,0.28),(R_PEBBLE,0.14),(R_THISTLE,0.12)],
    TILE_CLOVER:    [(R_CLOVER,0.65),(R_GRASS_BLADE,0.25),(R_BERRY,0.14),(R_FLOWER,0.10)],
    TILE_LEAVES:    [(R_MUSHROOM,0.22),(R_ACORN,0.28),(R_SPRIG,0.18),(R_SAP,0.12),
                     (R_TWIG,0.20),(R_CLOVER,0.08)],
    TILE_DIRT:      [(R_TWIG,0.28),(R_PEBBLE,0.28),(R_CLAY,0.20),(R_SPRIG,0.10)],
    TILE_SAND:      [(R_PEBBLE,0.22),(R_QUARTZITE,0.14),(R_DEW,0.10)],
    TILE_MUD:       [(R_CLAY,0.42),(R_STEM,0.18),(R_DEW,0.14)],
    TILE_STONE:     [(R_PEBBLE,0.38),(R_QUARTZITE,0.28),(R_TWIG,0.08)],
    TILE_GRAVEL:    [(R_PEBBLE,0.50),(R_QUARTZITE,0.22),(R_SAP,0.06)],
}


# ════════════════════════════════════════════════════════════
#  STRUCTURE
# ════════════════════════════════════════════════════════════

class Structure:
    """A placed building structure."""
    _id_counter = 0

    def __init__(self, btype: str, tx: int, ty: int):
        Structure._id_counter += 1
        self.uid    = Structure._id_counter
        self.btype  = btype
        self.tx, self.ty = tx, ty
        data = STRUCTURE_DEFS.get(btype, {})
        self.max_health  = data.get("health", 60)
        self.health      = float(self.max_health)
        self.solid       = data.get("solid", True)
        self.is_station  = data.get("is_station", False)
        self.station_id  = data.get("station_id", None)
        self.is_storage  = data.get("is_storage", False)
        self.color       = data.get("color", COL_BARK)
        self.scale       = data.get("scale", (1.0, 1.0, 1.0))
        self.name        = data.get("name", btype.replace("_"," ").title())
        self.inventory   = []   # for chests
        # Ursina entity
        self.entity      = None

    def hit(self, damage: float) -> bool:
        self.health -= damage
        return self.health <= 0

    def world_pos(self) -> Tuple[float, float, float]:
        x = (self.tx + 0.5) * TILE_WORLD_SCALE
        z = (self.ty + 0.5) * TILE_WORLD_SCALE
        return x, 0.5, z


STRUCTURE_DEFS: Dict[str, dict] = {
    B_GRASS_FLOOR:    {"health":50,"solid":False,"color":COL_GRASS,
                       "scale":(1.0,0.12,1.0),"name":"Grass Floor"},
    B_GRASS_WALL:     {"health":70,"solid":True,"color":(0.36,0.60,0.22,1),
                       "scale":(1.0,1.2,0.12),"name":"Grass Wall"},
    B_GRASS_RAMP:     {"health":50,"solid":False,"color":COL_GRASS,
                       "scale":(1.0,0.6,1.0),"name":"Grass Ramp"},
    B_STEM_FLOOR:     {"health":100,"solid":False,"color":(0.32,0.58,0.20,1),
                       "scale":(1.0,0.14,1.0),"name":"Stem Floor"},
    B_STEM_WALL:      {"health":150,"solid":True,"color":(0.28,0.52,0.16,1),
                       "scale":(1.0,1.2,0.14),"name":"Stem Wall"},
    B_CLAY_FOUNDATION:{"health":250,"solid":False,"color":(0.75,0.48,0.36,1),
                       "scale":(1.0,0.20,1.0),"name":"Clay Foundation"},
    B_WOVEN_FLOOR:    {"health":80,"solid":False,"color":(0.50,0.70,0.28,1),
                       "scale":(1.0,0.12,1.0),"name":"Woven Floor"},
    B_CRAFTING_TABLE: {"health":100,"solid":True,"is_station":True,
                       "station_id":STATION_BASIC,
                       "color":COL_BARK,"scale":(0.9,0.6,0.9),"name":"Crafting Table"},
    B_WORKBENCH:      {"health":120,"solid":True,"is_station":True,
                       "station_id":STATION_BENCH,
                       "color":(0.60,0.42,0.20,1),"scale":(0.9,0.65,0.9),"name":"Workbench"},
    B_CAMPFIRE:       {"health":50,"solid":False,"is_station":True,
                       "station_id":STATION_FIRE,
                       "color":COL_FIRE,"scale":(0.65,0.4,0.65),"name":"Campfire"},
    B_ROASTING_SPIT:  {"health":50,"solid":False,"is_station":True,
                       "station_id":STATION_ROAST,
                       "color":COL_BARK,"scale":(0.8,0.5,0.3),"name":"Roasting Spit"},
    B_DEW_COLLECTOR:  {"health":70,"solid":False,"is_station":True,
                       "station_id":STATION_WATER,
                       "color":COL_THIRST,"scale":(0.7,0.7,0.7),"name":"Dew Collector"},
    B_SPINNING_WHEEL: {"health":80,"solid":True,"is_station":True,
                       "station_id":STATION_SPIN,
                       "color":(0.70,0.55,0.35,1),"scale":(0.8,0.75,0.8),"name":"Spinning Wheel"},
    B_CHEST:          {"health":100,"solid":True,"is_storage":True,
                       "color":(0.62,0.42,0.20,1),"scale":(0.75,0.60,0.75),"name":"Chest"},
}

BUILDING_COSTS: Dict[str, Dict[str, int]] = {
    B_GRASS_FLOOR:    {"plant_fiber":4},
    B_GRASS_WALL:     {"plant_fiber":4,"grass_plank":2},
    B_GRASS_RAMP:     {"plant_fiber":6,"sprig":1},
    B_STEM_FLOOR:     {"stem_piece":3},
    B_STEM_WALL:      {"stem_piece":4},
    B_CLAY_FOUNDATION:{"clay_clump":4},
    B_WOVEN_FLOOR:    {"woven_fiber":4},
    B_CRAFTING_TABLE: {"grass_plank":8,"pebble":4},
    B_WORKBENCH:      {"grass_plank":12,"pebble":6,"twig":4},
    B_CAMPFIRE:       {"twig":4,"dry_grass_chunk":2},
    B_ROASTING_SPIT:  {"twig":4,"plant_fiber":2},
    B_DEW_COLLECTOR:  {"plant_fiber":4,"pebble":2,"stem_piece":2},
    B_SPINNING_WHEEL: {"twig":6,"pebble":4,"plant_fiber":4},
    B_CHEST:          {"sprig":8,"pebble":4},
}

BUILDING_CATEGORY_MAP: Dict[str, List[str]] = {
    "Floors":   [B_GRASS_FLOOR, B_STEM_FLOOR, B_CLAY_FOUNDATION, B_WOVEN_FLOOR],
    "Walls":    [B_GRASS_WALL,  B_STEM_WALL],
    "Ramps":    [B_GRASS_RAMP],
    "Stations": [B_CRAFTING_TABLE, B_WORKBENCH, B_CAMPFIRE,
                 B_ROASTING_SPIT, B_DEW_COLLECTOR, B_SPINNING_WHEEL],
    "Storage":  [B_CHEST],
}


# ════════════════════════════════════════════════════════════
#  WORLD
# ════════════════════════════════════════════════════════════

class World:
    def __init__(self, seed: int = None):
        self.seed       = seed or random.randint(1, 999999)
        self.size       = WORLD_SIZE
        self.scale      = TILE_WORLD_SCALE
        # 2-D tile type grid [z][x]
        self.tiles      : List[List[int]]           = []
        # Height map [z][x]  0.0 .. TERRAIN_HEIGHT
        self.heights    : List[List[float]]         = []
        # Resources: uid -> WorldResource
        self.resources  : Dict[int, WorldResource]  = {}
        # Structures: (tx,ty) -> Structure
        self.structures : Dict[tuple, Structure]    = {}
        self._generate()

    # ── Generation ──────────────────────────────────────────────────────
    def _generate(self):
        size = self.size
        # Height map
        h_grid = _smooth_noise(size, 4.0, self.seed)
        # Biome map (different seed)
        b_grid = _smooth_noise(size, 2.5, self.seed ^ 0xDEAD)
        # Moisture map
        m_grid = _smooth_noise(size, 3.0, self.seed ^ 0xBEEF)

        self.heights = [[h_grid[z][x] * TERRAIN_HEIGHT for x in range(size)]
                        for z in range(size)]
        self.tiles = [[TILE_GRASS]*size for _ in range(size)]

        water_h = TERRAIN_HEIGHT * WATER_LEVEL

        for z in range(size):
            for x in range(size):
                h = self.heights[z][x]
                b = b_grid[z][x]
                m = m_grid[z][x]
                if h < water_h:
                    t = TILE_WATER
                elif h < water_h * 1.3:
                    t = TILE_MUD if m > 0.5 else TILE_SAND
                elif h < water_h * 1.8 and m > 0.55:
                    t = TILE_MUD
                elif b < 0.28:
                    t = TILE_DRY_GRASS
                elif b < 0.42:
                    t = TILE_DIRT
                elif b > 0.72:
                    t = TILE_LEAVES
                elif b > 0.62:
                    t = TILE_CLOVER
                elif b > 0.52:
                    t = TILE_STONE if h > TERRAIN_HEIGHT*0.6 else TILE_GRAVEL
                else:
                    t = TILE_GRASS
                self.tiles[z][x] = t

        # Clear spawn area
        cx = cy = size // 2
        for dz in range(-5, 6):
            for dx in range(-5, 6):
                tz, tx = cy+dz, cx+dx
                if 0 <= tz < size and 0 <= tx < size:
                    self.tiles[tz][tx] = TILE_GRASS
                    self.heights[tz][tx] = max(water_h * 1.5,
                                               self.heights[tz][tx])

        self._spawn_resources()

    def _spawn_resources(self):
        size = self.size
        for z in range(size):
            for x in range(size):
                tile = self.tiles[z][x]
                if tile == TILE_WATER:
                    continue
                if random.random() > RESOURCE_DENSITY:
                    continue
                options = TILE_RESOURCE_TABLE.get(tile, [])
                if not options:
                    continue
                rtype = None
                for rt, prob in options:
                    if random.random() < prob:
                        rtype = rt
                        break
                if rtype is None:
                    continue
                wx = (x + random.uniform(0.1, 0.9)) * self.scale
                wy = self.height_at_world(wx, 0)
                wz = (z + random.uniform(0.1, 0.9)) * self.scale
                res = WorldResource(rtype, wx, wy, wz)
                self.resources[res.uid] = res

    # ── Height / Tile helpers ────────────────────────────────────────────
    def height_at_tile(self, tx: int, tz: int) -> float:
        if 0 <= tz < self.size and 0 <= tx < self.size:
            return self.heights[tz][tx]
        return 0.0

    def height_at_world(self, wx: float, wz_ignored) -> float:
        tx = int(wx / self.scale)
        tz = int(wz_ignored / self.scale) if wz_ignored else 0
        # Better: use wx, wz
        return self.height_at_tile(tx, tz)

    def height_at_world_xz(self, wx: float, wz: float) -> float:
        tx = int(wx / self.scale)
        tz = int(wz / self.scale)
        return self.height_at_tile(tx, tz)

    def tile_at_world(self, wx: float, wz: float) -> int:
        tx = int(wx / self.scale)
        tz = int(wz / self.scale)
        if 0 <= tz < self.size and 0 <= tx < self.size:
            return self.tiles[tz][tx]
        return TILE_STONE

    def tile_at(self, tx: int, tz: int) -> int:
        if 0 <= tz < self.size and 0 <= tx < self.size:
            return self.tiles[tz][tx]
        return TILE_STONE

    def is_walkable(self, wx: float, wz: float) -> bool:
        tile = self.tile_at_world(wx, wz)
        if tile == TILE_WATER:
            return False
        tx = int(wx / self.scale)
        tz = int(wz / self.scale)
        struct = self.structures.get((tx, tz))
        if struct and struct.solid:
            return False
        return True

    def world_center(self) -> Tuple[float, float, float]:
        cx = (self.size // 2 + 0.5) * self.scale
        cz = (self.size // 2 + 0.5) * self.scale
        cy = self.height_at_world_xz(cx, cz)
        return cx, cy, cz

    # ── Resource helpers ─────────────────────────────────────────────────
    def resources_near(self, wx: float, wz: float,
                        radius: float) -> List[WorldResource]:
        result = []
        for res in self.resources.values():
            if res.active:
                d = math.hypot(res.x - wx, res.z - wz)
                if d <= radius:
                    result.append(res)
        result.sort(key=lambda r: math.hypot(r.x-wx, r.z-wz))
        return result

    # ── Structure helpers ─────────────────────────────────────────────────
    def place_structure(self, tx: int, tz: int, btype: str) -> Optional[Structure]:
        if (tx, tz) in self.structures:
            return None
        tile = self.tile_at(tx, tz)
        if tile == TILE_WATER:
            return None
        s = Structure(btype, tx, tz)
        self.structures[(tx, tz)] = s
        return s

    def remove_structure(self, tx: int, tz: int) -> Optional[Structure]:
        return self.structures.pop((tx, tz), None)

    def structure_at_world(self, wx: float, wz: float) -> Optional[Structure]:
        tx = int(wx / self.scale)
        tz = int(wz / self.scale)
        return self.structures.get((tx, tz))

    def nearest_station(self, wx: float, wz: float,
                         max_dist: float = PLAYER_COLLECT_RANGE * 2) -> Optional[Structure]:
        best, best_d = None, max_dist
        for s in self.structures.values():
            sx = (s.tx + 0.5) * self.scale
            sz = (s.ty + 0.5) * self.scale
            d  = math.hypot(sx - wx, sz - wz)
            if d < best_d and s.is_station:
                best, best_d = s, d
        return best

    # ── Update ──────────────────────────────────────────────────────────
    def update(self, dt: float) -> List[Tuple[WorldResource, str]]:
        """Returns list of (resource, event) where event is 'respawn'."""
        events = []
        for res in list(self.resources.values()):
            ev = res.update(dt)
            if ev:
                events.append((res, ev))
        return events

    # ── Serialization ────────────────────────────────────────────────────
    def serialize(self) -> dict:
        return {
            "seed": self.seed,
            "structures": {
                f"{k[0]},{k[1]}": {"btype": v.btype, "health": v.health}
                for k, v in self.structures.items()
            },
        }

    def deserialize(self, data: dict):
        for key, val in data.get("structures", {}).items():
            tx, tz = map(int, key.split(","))
            self.place_structure(tx, tz, val["btype"])
            s = self.structures.get((tx, tz))
            if s:
                s.health = val.get("health", s.max_health)
