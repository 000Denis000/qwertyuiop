# world.py - World generation, tiles, resources, structures

import pygame
import random
import math
from constants import *
from items import make_item


# ─── World Resource ────────────────────────────────────────────────────────────
class WorldResource:
    """An interactable/collectible object in the world."""
    def __init__(self, x, y, rtype):
        self.x      = x  # world pixels
        self.y      = y
        self.rtype  = rtype  # "grass_blade","pebble","acorn", etc.
        self.active = True
        self.respawn_timer = 0
        data = RESOURCE_DATA[rtype]
        self.max_health = data.get("health", 1)
        self.health     = self.max_health
        self.radius     = data.get("radius", 14)
        self.respawn_time= data.get("respawn", 60)   # seconds
        self.color      = data.get("color", GREEN)
        self.color2     = data.get("color2", DARK_GREEN)
        self.req_tool   = data.get("req_tool", None)  # None=hands ok
        self.drops      = data.get("drops", [])

    def hit(self, damage, tool_type):
        if not self.active:
            return []
        if self.req_tool and tool_type != self.req_tool:
            damage = max(1, damage // 4)
        self.health -= damage
        drops = []
        if self.health <= 0:
            self.active = False
            self.respawn_timer = self.respawn_time
            for (item_id, lo, hi) in self.drops:
                count = random.randint(lo, hi)
                if count > 0:
                    drops.append(make_item(item_id, count))
        return drops

    def update(self, dt):
        if not self.active:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0:
                self.active = True
                self.health = self.max_health

    def draw(self, surface, cam_x, cam_y):
        if not self.active:
            return
        sx = self.x - cam_x
        sy = self.y - cam_y
        if not (-self.radius*2 < sx < SCREEN_WIDTH + self.radius*2 and
                -self.radius*2 < sy < SCREEN_HEIGHT + self.radius*2):
            return
        RESOURCE_DRAW[self.rtype](surface, int(sx), int(sy), self.radius, self.color, self.color2)


def _draw_grass_blade(surf, x, y, r, col, col2):
    pts = [(x-3, y+r), (x, y-r), (x+3, y+r)]
    pygame.draw.polygon(surf, col, pts)
    pygame.draw.polygon(surf, col2, pts, 1)

def _draw_circle_resource(surf, x, y, r, col, col2):
    pygame.draw.circle(surf, col, (x, y), r)
    pygame.draw.circle(surf, col2, (x, y), r, 1)

def _draw_rect_resource(surf, x, y, r, col, col2):
    rect = pygame.Rect(x-r, y-r, r*2, int(r*1.3))
    pygame.draw.rect(surf, col, rect, border_radius=3)
    pygame.draw.rect(surf, col2, rect, 1, border_radius=3)

def _draw_mushroom(surf, x, y, r, col, col2):
    # stem
    pygame.draw.rect(surf, (220,190,160), (x-4, y, 8, r))
    # cap
    pygame.draw.ellipse(surf, col, (x-r, y-r, r*2, int(r*1.2)))
    pygame.draw.ellipse(surf, col2, (x-r, y-r, r*2, int(r*1.2)), 1)

def _draw_acorn(surf, x, y, r, col, col2):
    # body
    pygame.draw.ellipse(surf, col, (x-r+4, y-r+4, r*2-8, r*2))
    # cap
    pygame.draw.ellipse(surf, col2, (x-r, y-r, r*2, r), border_radius=4)

def _draw_berry(surf, x, y, r, col, col2):
    pygame.draw.circle(surf, col, (x, y), r)
    pygame.draw.circle(surf, col2, (x-3, y-3), r//3)

def _draw_clover(surf, x, y, r, col, col2):
    for dx, dy in [(0,-1),(1,0),(0,1),(-1,0)]:
        pygame.draw.circle(surf, col, (x+dx*r//2, y+dy*r//2), r//2)
    pygame.draw.rect(surf, col2, (x-1, y, 2, r))

def _draw_stem(surf, x, y, r, col, col2):
    pygame.draw.rect(surf, col, (x-5, y-r, 10, r*2), border_radius=4)
    pygame.draw.rect(surf, col2, (x-5, y-r, 10, r*2), 1, border_radius=4)

RESOURCE_DRAW = {
    "grass_blade":  _draw_grass_blade,
    "dry_grass":    _draw_grass_blade,
    "pebble":       _draw_circle_resource,
    "quartzite":    _draw_circle_resource,
    "acorn":        _draw_acorn,
    "sprig":        _draw_rect_resource,
    "mushroom":     _draw_mushroom,
    "berry":        _draw_berry,
    "clover":       _draw_clover,
    "stem":         _draw_stem,
    "twig":         _draw_rect_resource,
    "clay":         _draw_circle_resource,
    "sap":          _draw_circle_resource,
    "dew":          _draw_circle_resource,
}

RESOURCE_DATA = {
    "grass_blade": {
        "health":2,"radius":18,"respawn":20,"color":(80,180,60),"color2":(40,120,20),
        "drops":[("plant_fiber",2,4),("grass_plank",0,1)],
    },
    "dry_grass": {
        "health":2,"radius":18,"respawn":30,"color":(180,160,60),"color2":(140,120,40),
        "drops":[("dry_grass_chunk",2,4),("plant_fiber",0,2)],
    },
    "pebble": {
        "health":3,"radius":14,"respawn":90,"color":GRAY,"color2":DARK_GRAY,
        "req_tool":"axe",
        "drops":[("pebble",2,4),("quartzite_shard",0,1)],
    },
    "quartzite": {
        "health":5,"radius":16,"respawn":120,"color":(190,190,210),"color2":(140,140,170),
        "req_tool":"axe",
        "drops":[("quartzite_shard",2,5),("pebble",0,2)],
    },
    "acorn": {
        "health":4,"radius":18,"respawn":80,"color":(160,110,50),"color2":(100,70,20),
        "drops":[("acorn_shell",1,2),("acorn_top",0,1),("acorn_meal",1,2)],
    },
    "sprig": {
        "health":2,"radius":12,"respawn":25,"color":(80,160,40),"color2":(50,110,20),
        "drops":[("sprig",2,4),("plant_fiber",1,2)],
    },
    "mushroom": {
        "health":2,"radius":20,"respawn":60,"color":(220,160,120),"color2":(180,100,60),
        "drops":[("raw_mushroom",1,2),("mushroom_spore",1,3)],
    },
    "berry": {
        "health":1,"radius":12,"respawn":40,"color":(180,30,80),"color2":(140,10,50),
        "drops":[("berry_chunk",2,4)],
    },
    "clover": {
        "health":1,"radius":16,"respawn":20,"color":(50,180,70),"color2":(30,120,40),
        "drops":[("clover_leaf",1,3)],
    },
    "stem": {
        "health":5,"radius":14,"respawn":60,"color":(80,160,50),"color2":(50,100,30),
        "req_tool":"axe",
        "drops":[("stem_piece",2,4),("plant_fiber",1,2)],
    },
    "twig": {
        "health":2,"radius":20,"respawn":50,"color":(140,100,50),"color2":(100,70,20),
        "drops":[("twig",2,4)],
    },
    "clay": {
        "health":4,"radius":16,"respawn":80,"color":(200,130,100),"color2":(160,90,60),
        "req_tool":"shovel",
        "drops":[("clay_clump",2,5)],
    },
    "sap": {
        "health":1,"radius":10,"respawn":60,"color":(255,200,50),"color2":(200,150,20),
        "drops":[("sap",1,3)],
    },
    "dew": {
        "health":1,"radius":10,"respawn":30,"color":(180,230,255),"color2":(100,180,220),
        "drops":[("dew_drop",1,2)],
    },
}


# ─── Structure ─────────────────────────────────────────────────────────────────
class Structure:
    """A placed building structure."""
    def __init__(self, tx, ty, stype):
        self.tx    = tx   # tile x
        self.ty    = ty   # tile y
        self.stype = stype
        data = STRUCTURE_DATA.get(stype, {})
        self.max_health = data.get("health", 50)
        self.health     = self.max_health
        self.solid      = data.get("solid", True)
        self.color      = data.get("color", GRAY)
        self.color2     = data.get("color2", DARK_GRAY)
        self.is_station = data.get("is_station", False)  # crafting station?
        self.station_id = data.get("station_id", None)
        self.is_storage = data.get("is_storage", False)
        self.inventory  = []  # for chests

    def hit(self, damage):
        self.health -= damage
        return self.health <= 0  # returns True if destroyed

    def draw(self, surface, cam_x, cam_y):
        rx = self.tx * TILE_SIZE - cam_x
        ry = self.ty * TILE_SIZE - cam_y
        if not (-TILE_SIZE < rx < SCREEN_WIDTH + TILE_SIZE and
                -TILE_SIZE < ry < SCREEN_HEIGHT + TILE_SIZE):
            return
        rect = pygame.Rect(rx, ry, TILE_SIZE, TILE_SIZE)
        data = STRUCTURE_DATA.get(self.stype, {})
        draw_fn = data.get("draw_fn", _draw_struct_rect)
        draw_fn(surface, rect, self.color, self.color2, self.health / self.max_health)

def _draw_struct_rect(surf, rect, col, col2, hp_ratio):
    pygame.draw.rect(surf, col, rect)
    pygame.draw.rect(surf, col2, rect, 2)
    if hp_ratio < 1.0:
        crack_col = (0,0,0,120)
        cw = int(rect.width * (1-hp_ratio))
        pygame.draw.line(surf, DARK_GRAY, rect.topleft, (rect.left+cw, rect.bottom), 2)

def _draw_struct_wall(surf, rect, col, col2, hp_ratio):
    pygame.draw.rect(surf, col, rect)
    # horizontal planks
    for i in range(1, 4):
        y = rect.top + rect.height * i // 4
        pygame.draw.line(surf, col2, (rect.left, y), (rect.right, y), 1)
    pygame.draw.rect(surf, col2, rect, 2)

def _draw_campfire(surf, rect, col, col2, hp_ratio):
    cx = rect.centerx
    cy = rect.centery
    r  = rect.width // 2 - 6
    # base logs
    pygame.draw.line(surf, BROWN, (cx-r, cy+r//2), (cx+r, cy+r//2), 6)
    pygame.draw.line(surf, BROWN, (cx-r//2, cy+r//2), (cx, cy-r//2), 5)
    pygame.draw.line(surf, BROWN, (cx+r//2, cy+r//2), (cx, cy-r//2), 5)
    # flame
    pygame.draw.polygon(surf, (255,140,0), [(cx,cy-r),(cx-r//2,cy),(cx+r//2,cy)])
    pygame.draw.polygon(surf, (255,220,0), [(cx,cy-r//2),(cx-r//3,cy),(cx+r//3,cy)])

def _draw_crafting_table(surf, rect, col, col2, hp_ratio):
    pygame.draw.rect(surf, col, rect, border_radius=4)
    # tools on top
    inner = rect.inflate(-12, -12)
    pygame.draw.rect(surf, col2, inner, border_radius=3)
    cx,cy = rect.centerx, rect.centery
    pygame.draw.line(surf, DARK_GRAY, (cx-10, cy), (cx+10, cy), 3)
    pygame.draw.line(surf, DARK_GRAY, (cx, cy-10), (cx, cy+10), 3)
    pygame.draw.rect(surf, col2, rect, 2, border_radius=4)

def _draw_chest(surf, rect, col, col2, hp_ratio):
    pygame.draw.rect(surf, col, rect, border_radius=3)
    # lid line
    mid = rect.top + rect.height // 2
    pygame.draw.line(surf, col2, (rect.left, mid), (rect.right, mid), 2)
    # lock
    pygame.draw.rect(surf, (220,180,30), (rect.centerx-4, mid-4, 8, 8), border_radius=2)
    pygame.draw.rect(surf, col2, rect, 2, border_radius=3)

def _draw_dew_collector(surf, rect, col, col2, hp_ratio):
    cx = rect.centerx; cy = rect.centery; r = rect.width//2 - 6
    pygame.draw.polygon(surf, col, [(cx,cy-r),(cx+r,cy+r),(cx-r,cy+r)])
    pygame.draw.circle(surf, LIGHT_BLUE, (cx, cy+r//2), r//3)
    pygame.draw.polygon(surf, col2, [(cx,cy-r),(cx+r,cy+r),(cx-r,cy+r)], 2)

STRUCTURE_DATA = {
    BLDG_GRASS_FLOOR: {
        "health":40,"solid":False,"color":(100,160,60),"color2":(70,120,30),
        "draw_fn":_draw_struct_rect,
    },
    BLDG_GRASS_WALL: {
        "health":60,"solid":True,"color":(90,150,55),"color2":(55,100,25),
        "draw_fn":_draw_struct_wall,
    },
    BLDG_GRASS_ROOF: {
        "health":40,"solid":False,"color":(70,130,40),"color2":(45,90,20),
        "draw_fn":_draw_struct_rect,
    },
    BLDG_GRASS_RAMP: {
        "health":40,"solid":False,"color":(100,155,55),"color2":(65,110,25),
        "draw_fn":_draw_struct_rect,
    },
    BLDG_STEM_FLOOR: {
        "health":80,"solid":False,"color":(80,145,50),"color2":(50,100,25),
        "draw_fn":_draw_struct_rect,
    },
    BLDG_STEM_WALL: {
        "health":120,"solid":True,"color":(75,140,45),"color2":(45,95,20),
        "draw_fn":_draw_struct_wall,
    },
    BLDG_CLAY_FOUND: {
        "health":200,"solid":False,"color":(190,130,100),"color2":(150,90,60),
        "draw_fn":_draw_struct_rect,
    },
    BLDG_CRAFTING_TABLE: {
        "health":80,"solid":True,"color":(160,110,60),"color2":(100,70,30),
        "is_station":True,"station_id":"basic",
        "draw_fn":_draw_crafting_table,
    },
    BLDG_CAMPFIRE: {
        "health":40,"solid":False,"color":(160,80,30),"color2":(120,50,10),
        "is_station":True,"station_id":"fire",
        "draw_fn":_draw_campfire,
    },
    BLDG_DEW_COLLECTOR: {
        "health":60,"solid":False,"color":(80,130,160),"color2":(50,90,120),
        "is_station":True,"station_id":"water",
        "draw_fn":_draw_dew_collector,
    },
    BLDG_CHEST: {
        "health":80,"solid":True,"color":(160,110,50),"color2":(110,70,20),
        "is_storage":True,
        "draw_fn":_draw_chest,
    },
    BLDG_SPINNING_WHEEL: {
        "health":60,"solid":True,"color":(180,150,100),"color2":(130,100,60),
        "is_station":True,"station_id":"spin",
        "draw_fn":_draw_crafting_table,
    },
    BLDG_ROASTING_SPIT: {
        "health":40,"solid":False,"color":(160,80,30),"color2":(100,50,10),
        "is_station":True,"station_id":"roast",
        "draw_fn":_draw_campfire,
    },
}


# ─── World ─────────────────────────────────────────────────────────────────────
class World:
    def __init__(self, seed=None):
        self.seed = seed or random.randint(0, 999999)
        random.seed(self.seed)
        self.width  = WORLD_WIDTH
        self.height = WORLD_HEIGHT
        self.tiles      = []   # 2D list [ty][tx]
        self.resources  = []   # list of WorldResource
        self.structures = {}   # (tx,ty) -> Structure
        self._generate()

    # ── Generation ──────────────────────────────────────────────────────────
    def _generate(self):
        w, h = self.width, self.height
        # Simple noise: random heights then smooth
        raw = [[random.random() for _ in range(w)] for _ in range(h)]
        smoothed = self._smooth(raw, 3)
        # Second layer for biome
        raw2 = [[random.random() for _ in range(w)] for _ in range(h)]
        biome = self._smooth(raw2, 5)

        self.tiles = []
        for ty in range(h):
            row = []
            for tx in range(w):
                v = smoothed[ty][tx]
                b = biome[ty][tx]
                # determine tile type
                if v < 0.25:
                    t = TILE_WATER
                elif v < 0.32:
                    t = TILE_MUD
                elif v < 0.38:
                    t = TILE_SAND
                elif b < 0.30:
                    t = TILE_DRY_GRASS
                elif b < 0.45:
                    t = TILE_DIRT
                elif b > 0.72:
                    t = TILE_LEAVES
                elif b > 0.62:
                    t = TILE_CLOVER
                elif b > 0.52:
                    t = TILE_STONE
                else:
                    t = TILE_GRASS
                row.append(t)
            self.tiles.append(row)

        # Ensure player spawn area (center) is grass
        cx, cy = w//2, h//2
        for ty in range(cy-4, cy+5):
            for tx in range(cx-4, cx+5):
                self.tiles[ty][tx] = TILE_GRASS

        self._spawn_resources()

    def _smooth(self, grid, passes):
        h, w = len(grid), len(grid[0])
        for _ in range(passes):
            new = [[0.0]*w for _ in range(h)]
            for y in range(h):
                for x in range(w):
                    total, count = 0.0, 0
                    for dy in (-1,0,1):
                        for dx in (-1,0,1):
                            ny, nx = y+dy, x+dx
                            if 0<=ny<h and 0<=nx<w:
                                total += grid[ny][nx]
                                count += 1
                    new[y][x] = total / count
            grid = new
        return grid

    def _spawn_resources(self):
        TILE_RESOURCES = {
            TILE_GRASS:     [("grass_blade",0.6),("sprig",0.3),("clover",0.2),("pebble",0.1)],
            TILE_DRY_GRASS: [("dry_grass",0.6),("twig",0.3),("pebble",0.15)],
            TILE_CLOVER:    [("clover",0.7),("grass_blade",0.3),("berry",0.15)],
            TILE_LEAVES:    [("mushroom",0.2),("acorn",0.3),("sprig",0.2),("sap",0.1)],
            TILE_DIRT:      [("twig",0.3),("pebble",0.3),("clay",0.2)],
            TILE_SAND:      [("pebble",0.2),("quartzite",0.15),("dew",0.1)],
            TILE_MUD:       [("clay",0.4),("stem",0.2)],
            TILE_STONE:     [("pebble",0.4),("quartzite",0.3)],
        }
        for ty in range(self.height):
            for tx in range(self.width):
                tile = self.tiles[ty][tx]
                if tile == TILE_WATER:
                    continue
                if random.random() < 0.08:  # sparse
                    options = TILE_RESOURCES.get(tile, [])
                    if not options:
                        continue
                    choices = [r for r in options if random.random() < r[1]]
                    if not choices:
                        continue
                    rtype = random.choice(choices)[0]
                    wx = tx * TILE_SIZE + random.randint(8, TILE_SIZE-8)
                    wy = ty * TILE_SIZE + random.randint(8, TILE_SIZE-8)
                    self.resources.append(WorldResource(wx, wy, rtype))

    # ── Tile helpers ────────────────────────────────────────────────────────
    def get_tile(self, tx, ty):
        if 0 <= tx < self.width and 0 <= ty < self.height:
            return self.tiles[ty][tx]
        return TILE_STONE

    def pixel_to_tile(self, px, py):
        return int(px // TILE_SIZE), int(py // TILE_SIZE)

    def is_solid_tile(self, tx, ty):
        t = self.get_tile(tx, ty)
        return t == TILE_WATER

    def is_solid_at(self, px, py, radius=PLAYER_RADIUS):
        """Check if a pixel position collides with solid tiles or walls."""
        for dx in (-radius, 0, radius):
            for dy in (-radius, 0, radius):
                tx, ty = self.pixel_to_tile(px+dx, py+dy)
                if self.is_solid_tile(tx, ty):
                    return True
                struct = self.structures.get((tx, ty))
                if struct and struct.solid:
                    return True
        return False

    # ── Structures ──────────────────────────────────────────────────────────
    def place_structure(self, tx, ty, stype):
        if (tx, ty) in self.structures:
            return False
        tile = self.get_tile(tx, ty)
        if tile == TILE_WATER:
            return False
        self.structures[(tx, ty)] = Structure(tx, ty, stype)
        return True

    def remove_structure(self, tx, ty):
        return self.structures.pop((tx, ty), None)

    def get_structure_at(self, px, py):
        tx, ty = self.pixel_to_tile(px, py)
        return self.structures.get((tx, ty))

    def get_nearby_station(self, px, py, range_px=INTERACT_RANGE):
        best = None
        best_dist = range_px
        for (tx, ty), struct in self.structures.items():
            sx = tx * TILE_SIZE + TILE_SIZE//2
            sy = ty * TILE_SIZE + TILE_SIZE//2
            dist = math.hypot(px-sx, py-sy)
            if dist < best_dist and struct.is_station:
                best_dist = dist
                best = struct
        return best

    # ── Resources ───────────────────────────────────────────────────────────
    def get_nearby_resources(self, px, py, radius):
        near = []
        for res in self.resources:
            if res.active:
                d = math.hypot(res.x - px, res.y - py)
                if d <= radius:
                    near.append((d, res))
        near.sort(key=lambda t: t[0])
        return [r for _, r in near]

    def get_closest_resource(self, px, py, radius):
        rlist = self.get_nearby_resources(px, py, radius)
        return rlist[0] if rlist else None

    # ── Update ──────────────────────────────────────────────────────────────
    def update(self, dt):
        for res in self.resources:
            res.update(dt)

    # ── Draw ────────────────────────────────────────────────────────────────
    def draw(self, surface, cam_x, cam_y):
        # visible tile range
        start_tx = max(0, int(cam_x // TILE_SIZE))
        start_ty = max(0, int(cam_y // TILE_SIZE))
        end_tx   = min(self.width,  start_tx + SCREEN_WIDTH  // TILE_SIZE + 2)
        end_ty   = min(self.height, start_ty + SCREEN_HEIGHT // TILE_SIZE + 2)

        for ty in range(start_ty, end_ty):
            for tx in range(start_tx, end_tx):
                tile = self.tiles[ty][tx]
                col  = TILE_COLORS.get(tile, GRAY)
                rx   = tx * TILE_SIZE - cam_x
                ry   = ty * TILE_SIZE - cam_y
                pygame.draw.rect(surface, col, (rx, ry, TILE_SIZE, TILE_SIZE))
                # subtle grid
                pygame.draw.rect(surface, (max(0,col[0]-15),max(0,col[1]-15),max(0,col[2]-15)),
                                 (rx, ry, TILE_SIZE, TILE_SIZE), 1)

        # Structures below entities
        for struct in self.structures.values():
            struct.draw(surface, cam_x, cam_y)

        # Resources
        for res in self.resources:
            res.draw(surface, cam_x, cam_y)

    def draw_minimap(self, surface, rect):
        """Draw a minimap of the world into rect."""
        tw = rect.width / self.width
        th = rect.height / self.height
        for ty in range(self.height):
            for tx in range(self.width):
                tile = self.tiles[ty][tx]
                col  = TILE_COLORS.get(tile, GRAY)
                pygame.draw.rect(surface, col,
                    (rect.left + tx*tw, rect.top + ty*th, max(1,tw), max(1,th)))
