# crafting.py - Crafting recipes and system

from constants import *
from items import make_item, ITEM_DATA


class Recipe:
    def __init__(self, result_id, result_count, ingredients, station=None, category="misc"):
        """
        station: None (hands), "basic" (crafting table), "fire" (campfire/spit),
                 "spin" (spinning wheel), "roast" (roasting spit), "water" (dew collector)
        """
        self.result_id    = result_id
        self.result_count = result_count
        self.ingredients  = ingredients  # {item_id: count}
        self.station      = station
        self.category     = category     # "tools","weapons","armor","food","building","materials"

    @property
    def name(self):
        return ITEM_DATA.get(self.result_id, {}).get("name", self.result_id)

    @property
    def color(self):
        return ITEM_DATA.get(self.result_id, {}).get("color", (128,128,128))

    def can_craft(self, player, available_station=None):
        for item_id, count in self.ingredients.items():
            if player.count_item(item_id) < count:
                return False
        if self.station and self.station != available_station:
            return False
        return True

    def craft(self, player, available_station=None):
        if not self.can_craft(player, available_station):
            return None
        for item_id, count in self.ingredients.items():
            player.remove_item(item_id, count)
        return make_item(self.result_id, self.result_count)


# ─── All Recipes ──────────────────────────────────────────────────────────────
# Hands = no station needed
# "basic" = crafting table
# "fire"  = campfire or roasting spit
# "roast" = roasting spit specifically
# "spin"  = spinning wheel

ALL_RECIPES = [
    # ── Materials (hands) ─────────────────────────────────────────────────
    Recipe("silk_rope",   1, {"spider_silk": 3},                  None,    "materials"),
    Recipe("grass_plank", 4, {"plant_fiber": 6},                  None,    "materials"),
    Recipe("acorn_meal",  1, {"acorn_shell": 2},                  None,    "materials"),

    # ── Tools (hands/basic) ───────────────────────────────────────────────
    Recipe("pebblet_axe",     1, {"pebble": 3, "sprig": 2},       None,    "tools"),
    Recipe("pebblet_hammer",  1, {"pebble": 4, "sprig": 2},       None,    "tools"),
    Recipe("acorn_shovel",    1, {"acorn_shell": 2, "twig": 2},   None,    "tools"),

    # ── Weapons (hands/basic) ─────────────────────────────────────────────
    Recipe("pebblet_dagger",  1, {"pebble": 2, "sprig": 1},       None,    "weapons"),
    Recipe("sprig_bow",       1, {"sprig": 3, "plant_fiber": 2},  None,    "weapons"),
    Recipe("thistle_arrow",   5, {"thistle_needle": 1, "plant_fiber": 1}, None, "weapons"),
    Recipe("bone_spear",      1, {"twig": 3, "quartzite_shard": 2}, "basic", "weapons"),
    Recipe("ant_club",        1, {"ant_part": 3, "sprig": 2},     "basic", "weapons"),
    Recipe("spider_fang_dagger", 1, {"spider_fang": 2, "silk_rope": 1}, "basic", "weapons"),
    Recipe("mint_mace",       1, {"quartzite_shard": 6, "ant_mandible": 2, "silk_rope": 2}, "basic", "weapons"),
    Recipe("ladybug_shield",  1, {"ladybug_shell": 2, "ant_part": 2, "silk_rope": 1}, "basic", "weapons"),

    # ── Armor (basic station) ─────────────────────────────────────────────
    Recipe("acorn_helmet",     1, {"acorn_shell": 2, "plant_fiber": 2},  "basic", "armor"),
    Recipe("acorn_chestplate", 1, {"acorn_shell": 4, "plant_fiber": 3},  "basic", "armor"),
    Recipe("acorn_greaves",    1, {"acorn_shell": 2, "plant_fiber": 2, "sprig": 2}, "basic", "armor"),
    Recipe("ant_helmet",       1, {"ant_head": 1, "ant_part": 2},        "basic", "armor"),
    Recipe("ant_chestplate",   1, {"ant_part": 4, "ant_mandible": 2},    "basic", "armor"),
    Recipe("ant_greaves",      1, {"ant_part": 2, "ant_mandible": 1, "silk_rope": 1}, "basic", "armor"),
    Recipe("spider_helmet",    1, {"spider_silk": 4, "spider_part": 2},  "basic", "armor"),
    Recipe("spider_chestplate",1, {"spider_silk": 6, "spider_part": 3, "spider_fang": 1}, "basic", "armor"),
    Recipe("ladybug_chestplate",1,{"ladybug_shell": 3, "ant_part": 4, "silk_rope": 2}, "basic", "armor"),

    # ── Food (fire/roast) ─────────────────────────────────────────────────
    Recipe("roasted_mushroom", 1, {"raw_mushroom": 1},            "fire",  "food"),
    Recipe("weevil_jerky",     1, {"ant_part": 2},                "roast", "food"),  # using ant parts as generic meat
    Recipe("mushroom_tea",     1, {"raw_mushroom": 1, "dew_drop": 1}, "fire", "food"),
    Recipe("acorn_soup",       1, {"acorn_meal": 2, "dew_drop": 2}, "fire", "food"),
    Recipe("clover_salad",     1, {"clover_leaf": 3},             None,    "food"),
    Recipe("aphid_honeydew",   2, {"aphid_honeydew": 1},          None,    "food"),  # stack consolidate

    # ── Building materials (hands) ────────────────────────────────────────
    Recipe("stem_piece",       2, {"plant_fiber": 3, "sprig": 1}, None,    "building"),

    # ── Stations (hands) ──────────────────────────────────────────────────
    # These create placeable items that represent building stations
]

# Categorized recipe lookup
RECIPES_BY_CATEGORY = {}
for rec in ALL_RECIPES:
    RECIPES_BY_CATEGORY.setdefault(rec.category, []).append(rec)

CATEGORIES = ["tools", "weapons", "armor", "food", "materials", "building"]


class CraftingSystem:
    def __init__(self):
        self.selected_category = 0
        self.selected_recipe   = 0
        self.scroll_offset     = 0
        self.result_popup      = None   # (item, timer)
        self.available_station = None   # station type the player is near

    def set_station(self, station_id):
        self.available_station = station_id

    def get_category_name(self):
        return CATEGORIES[self.selected_category] if CATEGORIES else "misc"

    def get_visible_recipes(self, player):
        cat = CATEGORIES[self.selected_category]
        recipes = RECIPES_BY_CATEGORY.get(cat, [])
        return recipes

    def craft_selected(self, player):
        recipes = self.get_visible_recipes(player)
        if not recipes or self.selected_recipe >= len(recipes):
            return None
        recipe = recipes[self.selected_recipe]
        result = recipe.craft(player, self.available_station)
        if result:
            leftover = player.add_item(result)
            self.result_popup = (result, 2.0)
            player.gain_xp(10)
        return result

    def update(self, dt):
        if self.result_popup:
            item, timer = self.result_popup
            timer -= dt
            if timer <= 0:
                self.result_popup = None
            else:
                self.result_popup = (item, timer)

    def next_category(self):
        self.selected_category = (self.selected_category + 1) % len(CATEGORIES)
        self.selected_recipe   = 0
        self.scroll_offset     = 0

    def prev_category(self):
        self.selected_category = (self.selected_category - 1) % len(CATEGORIES)
        self.selected_recipe   = 0
        self.scroll_offset     = 0
