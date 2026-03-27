# ============================================================
#  BACKYARD SURVIVAL v2  –  Crafting System & All Recipes
# ============================================================
from __future__ import annotations
from typing import Optional, List, Dict
from constants import *
from items import Item, make, ITEM_REGISTRY


class Recipe:
    """One crafting recipe."""

    def __init__(self, result_id: str, result_count: int,
                 ingredients: Dict[str, int],
                 station: Optional[str] = STATION_HANDS,
                 category: str = "misc",
                 description: str = ""):
        self.result_id     = result_id
        self.result_count  = result_count
        self.ingredients   = ingredients   # {item_id: count}
        self.station       = station       # required station or None
        self.category      = category
        self.description   = description

    @property
    def name(self) -> str:
        return ITEM_REGISTRY.get(self.result_id, {}).get("name", self.result_id)

    @property
    def color(self):
        return ITEM_REGISTRY.get(self.result_id, {}).get("color", COL_SILVER)

    def can_craft(self, inv, station_id: Optional[str] = None) -> bool:
        # Station check
        if self.station is not None and self.station != station_id:
            return False
        # Ingredient check
        for item_id, needed in self.ingredients.items():
            if inv.count(item_id) < needed:
                return False
        return True

    def craft(self, inv, station_id: Optional[str] = None) -> Optional[Item]:
        if not self.can_craft(inv, station_id):
            return None
        for item_id, count in self.ingredients.items():
            inv.remove(item_id, count)
        return make(self.result_id, self.result_count)

    def ingredient_status(self, inv) -> Dict[str, tuple]:
        """Returns {item_id: (have, need, satisfied)}"""
        status = {}
        for item_id, needed in self.ingredients.items():
            have = inv.count(item_id)
            status[item_id] = (have, needed, have >= needed)
        return status


# ════════════════════════════════════════════════════════════
#  RECIPE DATABASE
# ════════════════════════════════════════════════════════════
ALL_RECIPES: List[Recipe] = [

    # ─── MATERIALS (hands) ──────────────────────────────────
    Recipe("grass_plank",     4,  {"plant_fiber": 6},
           STATION_HANDS, "materials",
           "Press fibrous grass into flat planks."),
    Recipe("silk_rope",       1,  {"spider_silk": 3},
           STATION_HANDS, "materials",
           "Braid spider silk into rope."),
    Recipe("acorn_meal",      1,  {"acorn_shell": 2},
           STATION_HANDS, "materials",
           "Grind acorn shell into coarse meal."),
    Recipe("woven_fiber",     2,  {"plant_fiber": 4, "sprig": 1},
           STATION_HANDS, "materials",
           "Tightly spin fiber into thread."),
    Recipe("woven_silk",      1,  {"spider_silk": 4},
           STATION_SPIN, "materials",
           "Weave silk on the spinning wheel."),
    Recipe("ant_chitin",      1,  {"ant_part": 3, "sap": 1},
           STATION_BASIC, "materials",
           "Harden ant parts with sap."),
    Recipe("hardened_clay",   2,  {"clay_clump": 3},
           STATION_FIRE, "materials",
           "Fire clay in a campfire."),
    Recipe("resin_glob",      1,  {"sap": 3},
           STATION_FIRE, "materials",
           "Reduce sap into hard resin."),
    Recipe("stem_piece",      2,  {"plant_fiber": 3, "sprig": 1},
           STATION_HANDS, "materials",
           "Bundle fiber around a sprig."),
    Recipe("pebblet_axe_head",1,  {"pebble": 2, "quartzite_shard": 1},
           STATION_HANDS, "materials",
           "Knap pebbles into an axe head."),

    # ─── TOOLS (hands / basic) ──────────────────────────────
    Recipe("pebblet_axe",     1,  {"pebble": 3, "sprig": 2},
           STATION_HANDS, "tools",
           "Basic pebble axe. Chops grass and stems."),
    Recipe("pebblet_hammer",  1,  {"pebble": 4, "sprig": 2},
           STATION_HANDS, "tools",
           "Required to build structures."),
    Recipe("acorn_shovel",    1,  {"acorn_shell": 2, "twig": 2},
           STATION_HANDS, "tools",
           "Digs up clay and sand."),
    Recipe("quartzite_pick",  1,  {"quartzite_shard": 3, "twig": 2, "silk_rope": 1},
           STATION_BASIC, "tools",
           "Mines hard stone resources."),
    Recipe("ant_mandible_axe",1,  {"ant_mandible": 3, "sprig": 2, "silk_rope": 1},
           STATION_BASIC, "tools",
           "Fast dual-blade harvesting tool."),
    Recipe("mosquito_needle", 1,  {"mosquito_beak": 2, "twig": 1, "silk_rope": 1},
           STATION_BASIC, "tools",
           "Hollow needle. Can inject liquids."),

    # ─── WEAPONS (hands / basic / bench) ────────────────────
    Recipe("pebblet_dagger",  1,  {"pebble": 2, "sprig": 1},
           STATION_HANDS, "weapons",
           "Quick stone dagger."),
    Recipe("sprig_bow",       1,  {"sprig": 3, "plant_fiber": 2, "silk_rope": 1},
           STATION_HANDS, "weapons",
           "Ranged bow using Thistle Arrows."),
    Recipe("thistle_arrow",   8,  {"thistle_needle": 2, "plant_fiber": 2},
           STATION_HANDS, "weapons",
           "Basic arrows for the Sprig Bow."),
    Recipe("quartzite_arrow", 6,  {"quartzite_shard": 2, "plant_fiber": 1, "feather": 1},
           STATION_BASIC, "weapons",
           "Armor-piercing crystal-tipped arrows."),
    Recipe("acid_arrow",      6,  {"thistle_needle": 2, "fire_ant_acid": 1, "plant_fiber": 1},
           STATION_BASIC, "weapons",
           "Acid-coated arrows that burn targets."),
    Recipe("bone_spear",      1,  {"twig": 3, "quartzite_shard": 2, "silk_rope": 1},
           STATION_BASIC, "weapons",
           "Long-reach two-handed spear."),
    Recipe("ant_club",        1,  {"ant_part": 3, "ant_mandible": 2, "sprig": 2},
           STATION_BASIC, "weapons",
           "Heavy bludgeon with massive knockback."),
    Recipe("spider_fang_dagger",1,{"spider_fang": 2, "silk_rope": 1, "sap": 1},
           STATION_BASIC, "weapons",
           "Venom blade with poison chance."),
    Recipe("mint_mace",       1,  {"mint_chunk": 6, "ant_mandible": 2, "silk_rope": 2},
           STATION_BENCH, "weapons",
           "Icy mace. Slows targets on hit."),
    Recipe("ladybug_shield",  1,  {"ladybug_shell": 2, "ant_part": 2, "silk_rope": 1},
           STATION_BASIC, "weapons",
           "High-defense shield for blocking."),
    Recipe("bombardier_launcher",1,{"bombardier_gland": 2, "twig": 3, "silk_rope": 2},
           STATION_BENCH, "weapons",
           "AoE fire weapon. Burns enemies."),
    Recipe("stink_sack_bomb", 3,  {"stinkbug_gas_sac": 1, "plant_fiber": 1},
           STATION_BASIC, "weapons",
           "Thrown stink bomb. AoE poison cloud."),
    Recipe("cricket_crossbow",1,  {"cricket_leg": 4, "twig": 3, "silk_rope": 3},
           STATION_BENCH, "weapons",
           "Powerful ranged crossbow."),
    Recipe("ant_queen_club",  1,  {"ant_part": 8, "ant_mandible": 5, "soldier_ant_part": 3, "silk_rope": 3},
           STATION_BENCH, "weapons",
           "Legendary end-game weapon."),

    # ─── ARMOR – Acorn Set (hands/basic) ────────────────────
    Recipe("acorn_helmet",    1,  {"acorn_shell": 2, "plant_fiber": 2},
           STATION_BASIC, "armor",
           "Starter head armor."),
    Recipe("acorn_chestplate",1,  {"acorn_shell": 4, "plant_fiber": 3},
           STATION_BASIC, "armor",
           "Acorn shell torso armor."),
    Recipe("acorn_greaves",   1,  {"acorn_shell": 2, "plant_fiber": 2, "sprig": 2},
           STATION_BASIC, "armor",
           "Acorn shell leg guards."),
    Recipe("acorn_boots",     1,  {"acorn_shell": 1, "plant_fiber": 2},
           STATION_BASIC, "armor",
           "Acorn shell boots."),

    # ─── ARMOR – Ant Set (basic) ─────────────────────────────
    Recipe("ant_helmet",      1,  {"ant_head": 1, "ant_part": 2, "silk_rope": 1},
           STATION_BASIC, "armor",
           "Ant head helmet, light and quick."),
    Recipe("ant_chestplate",  1,  {"ant_part": 4, "ant_mandible": 2, "silk_rope": 2},
           STATION_BASIC, "armor",
           "Layered ant chitin chest armor."),
    Recipe("ant_greaves",     1,  {"ant_part": 2, "ant_mandible": 1, "silk_rope": 1},
           STATION_BASIC, "armor",
           "+10% move speed."),
    Recipe("ant_boots",       1,  {"ant_part": 1, "silk_rope": 1},
           STATION_BASIC, "armor",
           "+8% move speed."),

    # ─── ARMOR – Spider Set (bench/basic) ────────────────────
    Recipe("spider_helmet",   1,  {"spider_silk": 4, "spider_part": 2},
           STATION_BASIC, "armor",
           "+10% ranged damage."),
    Recipe("spider_chestplate",1, {"spider_silk": 6, "spider_part": 3, "spider_fang": 1},
           STATION_BASIC, "armor",
           "Dense silk weave armor."),
    Recipe("spider_greaves",  1,  {"spider_silk": 4, "spider_part": 2},
           STATION_BASIC, "armor",
           "Silent silk leg wraps."),
    Recipe("spider_boots",    1,  {"spider_silk": 3, "spider_part": 1},
           STATION_BASIC, "armor",
           "Silent silk boots."),
    Recipe("woven_silk_robes",1,  {"woven_silk": 4, "spider_part": 2, "flower_petal": 3},
           STATION_SPIN, "armor",
           "+15% status effect chance."),
    Recipe("woven_silk_hood", 1,  {"woven_silk": 2, "spider_part": 1},
           STATION_SPIN, "armor",
           "Lightweight silk hood."),

    # ─── ARMOR – Ladybug Set (bench) ─────────────────────────
    Recipe("ladybug_helmet",  1,  {"ladybug_shell": 2, "ant_part": 2, "silk_rope": 2},
           STATION_BENCH, "armor",
           "Heaviest helmet — maximum defense."),
    Recipe("ladybug_chestplate",1, {"ladybug_shell": 3, "ant_part": 4, "silk_rope": 2},
           STATION_BENCH, "armor",
           "Highest defense armor in game."),
    Recipe("ladybug_greaves", 1,  {"ladybug_shell": 2, "ant_part": 2, "silk_rope": 1},
           STATION_BENCH, "armor",
           "Heavy spotted leg guards."),

    # ─── FOOD (hands / fire / roast) ────────────────────────
    Recipe("clover_salad",    1,  {"clover_leaf": 3},
           STATION_HANDS, "food",
           "Simple clover snack."),
    Recipe("acorn_bread",     2,  {"acorn_meal": 3, "dew_drop": 1},
           STATION_FIRE, "food",
           "Hearty acorn bread. Good travel food."),
    Recipe("roasted_mushroom",1,  {"raw_mushroom": 1},
           STATION_FIRE, "food",
           "Cook mushroom over fire. Much more nutritious."),
    Recipe("mushroom_tea",    1,  {"raw_mushroom": 1, "dew_drop": 2},
           STATION_FIRE, "food",
           "Hydrating herbal tea + health regen."),
    Recipe("acorn_soup",      1,  {"acorn_meal": 2, "dew_drop": 2, "plant_fiber": 1},
           STATION_FIRE, "food",
           "Best early hunger/thirst restore."),
    Recipe("weevil_jerky",    1,  {"ant_part": 2},
           STATION_ROAST, "food",
           "Dried bug meat. High hunger restore."),
    Recipe("ant_egg_omelette",1,  {"ant_egg": 2, "plant_fiber": 1},
           STATION_FIRE, "food",
           "Protein-rich egg omelette."),
    Recipe("berry_jam",       1,  {"berry_chunk": 4},
           STATION_FIRE, "food",
           "Cooked berry reduction. Sweet jam."),
    Recipe("honeydew_smoothie",1, {"aphid_honeydew": 2, "berry_chunk": 1, "dew_drop": 1},
           STATION_HANDS, "food",
           "+Speed bonus for 30 seconds."),
    Recipe("flower_petal_salve",1,{"flower_petal": 3, "sap": 1},
           STATION_HANDS, "food",
           "Pure healing salve. No nutrition."),
    Recipe("mushroom_power_shake",1,{"raw_mushroom": 2, "spider_venom_gland": 1, "dew_drop": 1},
           STATION_BENCH, "food",
           "Attack boost for 60 seconds."),
    Recipe("acorn_bread",     2,  {"acorn_meal": 3, "dew_drop": 1},
           STATION_FIRE, "food",
           "Trail bread. Great hunger per slot."),
]

# ── Lookup structures ──────────────────────────────────────
RECIPES_BY_CATEGORY: Dict[str, List[Recipe]] = {}
for _rec in ALL_RECIPES:
    RECIPES_BY_CATEGORY.setdefault(_rec.category, []).append(_rec)

RECIPE_CATEGORIES = ["tools", "weapons", "armor", "food", "materials"]


# ════════════════════════════════════════════════════════════
#  CRAFTING SYSTEM
# ════════════════════════════════════════════════════════════
class CraftingSystem:
    def __init__(self):
        self.selected_cat    = 0
        self.selected_index  = 0
        self.scroll_offset   = 0
        self.active_station  = None   # station id or None
        self.result_popup    = None   # (item, timer) or None

    # ── State ─────────────────────────────────────────────────────────────
    def open_at_station(self, station_id: Optional[str]):
        self.active_station = station_id
        self.selected_index = 0
        self.scroll_offset  = 0

    def current_category(self) -> str:
        return RECIPE_CATEGORIES[self.selected_cat % len(RECIPE_CATEGORIES)]

    def visible_recipes(self, inv) -> List[Recipe]:
        return RECIPES_BY_CATEGORY.get(self.current_category(), [])

    def selected_recipe(self, inv) -> Optional[Recipe]:
        recipes = self.visible_recipes(inv)
        if not recipes or self.selected_index >= len(recipes):
            return None
        return recipes[self.selected_index]

    # ── Navigation ────────────────────────────────────────────────────────
    def next_cat(self):
        self.selected_cat = (self.selected_cat + 1) % len(RECIPE_CATEGORIES)
        self.selected_index = 0
        self.scroll_offset  = 0

    def prev_cat(self):
        self.selected_cat = (self.selected_cat - 1) % len(RECIPE_CATEGORIES)
        self.selected_index = 0
        self.scroll_offset  = 0

    def next_recipe(self, inv):
        recipes = self.visible_recipes(inv)
        if not recipes:
            return
        self.selected_index = min(len(recipes)-1, self.selected_index + 1)
        if self.selected_index >= self.scroll_offset + 9:
            self.scroll_offset += 1

    def prev_recipe(self, inv):
        self.selected_index = max(0, self.selected_index - 1)
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index

    # ── Craft ─────────────────────────────────────────────────────────────
    def craft(self, inv) -> Optional[Item]:
        rec = self.selected_recipe(inv)
        if rec is None:
            return None
        result = rec.craft(inv, self.active_station)
        if result:
            leftover = inv.add(result)
            self.result_popup = (result, 2.5)
        return result

    # ── Update ────────────────────────────────────────────────────────────
    def update(self, dt: float):
        if self.result_popup:
            item, t = self.result_popup
            t -= dt
            self.result_popup = (item, t) if t > 0 else None
