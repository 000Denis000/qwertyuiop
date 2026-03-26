# building.py - Building system: blueprint preview, placement, demolition

import pygame
import math
from constants import *
from items import make_item


# Cost (ingredients) for each building type
BUILDING_COSTS = {
    BLDG_GRASS_FLOOR:    {"plant_fiber": 4},
    BLDG_GRASS_WALL:     {"plant_fiber": 4, "grass_plank": 2},
    BLDG_GRASS_ROOF:     {"plant_fiber": 6},
    BLDG_GRASS_RAMP:     {"plant_fiber": 6, "sprig": 1},
    BLDG_STEM_FLOOR:     {"stem_piece": 3},
    BLDG_STEM_WALL:      {"stem_piece": 4},
    BLDG_CLAY_FOUND:     {"clay_clump": 4},
    BLDG_CRAFTING_TABLE: {"grass_plank": 8, "pebble": 4},
    BLDG_CAMPFIRE:       {"twig": 4, "dry_grass_chunk": 2},
    BLDG_DEW_COLLECTOR:  {"plant_fiber": 4, "pebble": 2, "stem_piece": 2},
    BLDG_CHEST:          {"sprig": 8, "pebble": 4},
    BLDG_SPINNING_WHEEL: {"twig": 6, "pebble": 4, "plant_fiber": 4},
    BLDG_ROASTING_SPIT:  {"twig": 4, "plant_fiber": 2},
}

# Category groupings for building menu
BUILDING_CATEGORIES = {
    "Floors":    [BLDG_GRASS_FLOOR, BLDG_STEM_FLOOR, BLDG_CLAY_FOUND],
    "Walls":     [BLDG_GRASS_WALL,  BLDG_STEM_WALL],
    "Roofs":     [BLDG_GRASS_ROOF,  BLDG_GRASS_RAMP],
    "Stations":  [BLDG_CRAFTING_TABLE, BLDG_CAMPFIRE, BLDG_ROASTING_SPIT,
                  BLDG_DEW_COLLECTOR, BLDG_SPINNING_WHEEL],
    "Storage":   [BLDG_CHEST],
}

BUILD_CATEGORY_NAMES = list(BUILDING_CATEGORIES.keys())

BUILDING_NAMES = {
    BLDG_GRASS_FLOOR:    "Grass Floor",
    BLDG_GRASS_WALL:     "Grass Wall",
    BLDG_GRASS_ROOF:     "Grass Roof",
    BLDG_GRASS_RAMP:     "Grass Ramp",
    BLDG_STEM_FLOOR:     "Stem Floor",
    BLDG_STEM_WALL:      "Stem Wall",
    BLDG_CLAY_FOUND:     "Clay Foundation",
    BLDG_CRAFTING_TABLE: "Crafting Table",
    BLDG_CAMPFIRE:       "Campfire",
    BLDG_DEW_COLLECTOR:  "Dew Collector",
    BLDG_CHEST:          "Storage Chest",
    BLDG_SPINNING_WHEEL: "Spinning Wheel",
    BLDG_ROASTING_SPIT:  "Roasting Spit",
}

BUILDING_COLORS = {
    BLDG_GRASS_FLOOR:    (100, 160, 60),
    BLDG_GRASS_WALL:     (90,  150, 55),
    BLDG_GRASS_ROOF:     (70,  130, 40),
    BLDG_GRASS_RAMP:     (100, 155, 55),
    BLDG_STEM_FLOOR:     (80,  145, 50),
    BLDG_STEM_WALL:      (75,  140, 45),
    BLDG_CLAY_FOUND:     (190, 130, 100),
    BLDG_CRAFTING_TABLE: (160, 110, 60),
    BLDG_CAMPFIRE:       (220, 100, 30),
    BLDG_DEW_COLLECTOR:  (80,  130, 200),
    BLDG_CHEST:          (160, 110, 50),
    BLDG_SPINNING_WHEEL: (180, 150, 100),
    BLDG_ROASTING_SPIT:  (180, 80,  30),
}


class BuildingSystem:
    def __init__(self, world):
        self.world           = world
        self.active          = False
        self.selected_cat    = 0
        self.selected_index  = 0
        self.blueprint_tx    = 0
        self.blueprint_ty    = 0
        self.can_place       = False
        self.demolish_mode   = False

    @property
    def selected_type(self):
        cat_name = BUILD_CATEGORY_NAMES[self.selected_cat]
        items = BUILDING_CATEGORIES[cat_name]
        if self.selected_index < len(items):
            return items[self.selected_index]
        return None

    @property
    def current_category(self):
        return BUILD_CATEGORY_NAMES[self.selected_cat]

    @property
    def current_items(self):
        return BUILDING_CATEGORIES[self.current_category]

    def next_category(self):
        self.selected_cat   = (self.selected_cat + 1) % len(BUILD_CATEGORY_NAMES)
        self.selected_index = 0

    def prev_category(self):
        self.selected_cat   = (self.selected_cat - 1) % len(BUILD_CATEGORY_NAMES)
        self.selected_index = 0

    def next_item(self):
        items = self.current_items
        self.selected_index = (self.selected_index + 1) % len(items)

    def prev_item(self):
        items = self.current_items
        self.selected_index = (self.selected_index - 1) % len(items)

    def update_blueprint(self, mouse_world_x, mouse_world_y, player):
        """Snap blueprint to tile grid, check if placeable."""
        self.blueprint_tx = int(mouse_world_x // TILE_SIZE)
        self.blueprint_ty = int(mouse_world_y // TILE_SIZE)

        stype = self.selected_type
        if stype is None:
            self.can_place = False
            return

        # Check tile is not water
        tile = self.world.get_tile(self.blueprint_tx, self.blueprint_ty)
        if tile == TILE_WATER:
            self.can_place = False
            return

        # Check not already occupied
        if (self.blueprint_tx, self.blueprint_ty) in self.world.structures:
            self.can_place = False
            return

        # Check player can afford it
        self.can_place = self.can_afford(player, stype)

    def can_afford(self, player, stype):
        cost = BUILDING_COSTS.get(stype, {})
        for item_id, count in cost.items():
            if player.count_item(item_id) < count:
                return False
        return True

    def place(self, player):
        stype = self.selected_type
        if stype is None or not self.can_place:
            return False
        cost = BUILDING_COSTS.get(stype, {})
        for item_id, count in cost.items():
            player.remove_item(item_id, count)
        success = self.world.place_structure(self.blueprint_tx, self.blueprint_ty, stype)
        if success:
            player.gain_xp(5)
        return success

    def demolish(self, tx, ty, player):
        """Remove a structure and refund some materials."""
        struct = self.world.structures.get((tx, ty))
        if not struct:
            return False
        stype = struct.stype
        cost = BUILDING_COSTS.get(stype, {})
        # Refund 50% of materials
        for item_id, count in cost.items():
            refund = max(1, count // 2)
            player.add_item(make_item(item_id, refund))
        self.world.remove_structure(tx, ty)
        return True

    def draw_blueprint(self, surface, cam_x, cam_y):
        if not self.active or self.selected_type is None:
            return
        rx = self.blueprint_tx * TILE_SIZE - cam_x
        ry = self.blueprint_ty * TILE_SIZE - cam_y
        col = BUILDING_COLORS.get(self.selected_type, (128, 128, 128))
        if self.can_place:
            alpha_col = (col[0], col[1], col[2])
            border_col = (50, 220, 50)
        else:
            alpha_col = (220, 50, 50)
            border_col = (220, 50, 50)

        # Semi-transparent fill
        bp_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        bp_surf.fill((*alpha_col, 120))
        surface.blit(bp_surf, (rx, ry))
        pygame.draw.rect(surface, border_col, (rx, ry, TILE_SIZE, TILE_SIZE), 3)

        # Cost display
        cost = BUILDING_COSTS.get(self.selected_type, {})
        from items import ITEM_DATA
        font = pygame.font.SysFont("monospace", 12)
        for i, (item_id, count) in enumerate(cost.items()):
            name = ITEM_DATA.get(item_id, {}).get("name", item_id)
            text = f"{name}: {count}"
            col2 = (50, 220, 50) if True else (220, 50, 50)
            surf = font.render(text, True, col2)
            surface.blit(surf, (rx, ry + TILE_SIZE + 5 + i * 14))

    def draw_menu(self, surface):
        """Draw the building selection sidebar."""
        if not self.active:
            return
        font_lg = pygame.font.SysFont("monospace", 15, bold=True)
        font_sm = pygame.font.SysFont("monospace", 13)
        panel_w = 200
        panel_x = SCREEN_WIDTH - panel_w - 10
        panel_y = 80

        # Panel background
        panel_surf = pygame.Surface((panel_w, 420), pygame.SRCALPHA)
        panel_surf.fill((20, 20, 25, 210))
        surface.blit(panel_surf, (panel_x, panel_y))
        pygame.draw.rect(surface, UI_BORDER, (panel_x, panel_y, panel_w, 420), 2, border_radius=6)

        # Category tabs
        tab_h = 28
        for i, cat in enumerate(BUILD_CATEGORY_NAMES):
            tx = panel_x + i * (panel_w // len(BUILD_CATEGORY_NAMES))
            ty_pos = panel_y - tab_h
            tw = panel_w // len(BUILD_CATEGORY_NAMES)
            col = UI_HIGHLIGHT if i == self.selected_cat else UI_SLOT_BG
            pygame.draw.rect(surface, col, (tx, ty_pos, tw, tab_h), border_radius=4)
            pygame.draw.rect(surface, UI_BORDER, (tx, ty_pos, tw, tab_h), 1, border_radius=4)
            label = font_sm.render(cat[:6], True, WHITE)
            surface.blit(label, (tx + 4, ty_pos + 6))

        # Items in category
        items = self.current_items
        for i, stype in enumerate(items):
            iy = panel_y + 10 + i * 54
            is_sel = (i == self.selected_index)
            slot_rect = pygame.Rect(panel_x + 8, iy, panel_w - 16, 48)
            slot_col = UI_SLOT_SEL if is_sel else UI_SLOT_BG
            pygame.draw.rect(surface, slot_col, slot_rect, border_radius=4)
            pygame.draw.rect(surface, UI_BORDER, slot_rect, 1, border_radius=4)

            # Color swatch
            bcolor = BUILDING_COLORS.get(stype, GRAY)
            pygame.draw.rect(surface, bcolor, (panel_x+12, iy+8, 32, 32), border_radius=3)

            # Name
            name = BUILDING_NAMES.get(stype, stype)
            name_surf = font_sm.render(name, True, WHITE)
            surface.blit(name_surf, (panel_x + 50, iy + 6))

            # Cost summary
            cost = BUILDING_COSTS.get(stype, {})
            cost_str = " ".join(f"{c}" for c in cost.values())
            cost_surf = font_sm.render(cost_str[:20], True, LIGHT_GRAY)
            surface.blit(cost_surf, (panel_x + 50, iy + 24))

        # Mode indicator
        mode_str = "[DEMOLISH]" if self.demolish_mode else "[PLACE]"
        mode_col = RED if self.demolish_mode else LIME
        mode_surf = font_lg.render(mode_str, True, mode_col)
        surface.blit(mode_surf, (panel_x + 10, panel_y + 390))
