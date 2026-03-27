# ============================================================
#  BACKYARD SURVIVAL v2  –  Items & Item Registry
# ============================================================
from constants import *


class Item:
    """A single item stack (id + count) with all stat data."""

    __slots__ = ("item_id","count","name","itype","max_stack","damage",
                 "defense","equip_slot","hunger_val","thirst_val","heal_val",
                 "speed_bonus","color","description","tool_type","ammo_id",
                 "attack_speed","knockback","equip_bonus","status_effect",
                 "effect_chance","effect_duration","element","reach","two_handed")

    def __init__(self, item_id: str, count: int = 1):
        self.item_id    = item_id
        self.count      = count
        d = ITEM_REGISTRY.get(item_id, {})
        self.name           = d.get("name",          item_id.replace("_"," ").title())
        self.itype          = d.get("itype",         ITYPE_RESOURCE)
        self.max_stack      = d.get("max_stack",     20)
        self.damage         = d.get("damage",        0)
        self.defense        = d.get("defense",       0)
        self.equip_slot     = d.get("equip_slot",    None)
        self.hunger_val     = d.get("hunger",        0)
        self.thirst_val     = d.get("thirst",        0)
        self.heal_val       = d.get("heal",          0)
        self.speed_bonus    = d.get("speed_bonus",   0.0)
        self.color          = d.get("color",         COL_SILVER)
        self.description    = d.get("desc",          "")
        self.tool_type      = d.get("tool_type",     None)
        self.ammo_id        = d.get("ammo_id",       None)
        self.attack_speed   = d.get("attack_speed",  1.0)
        self.knockback      = d.get("knockback",     1.0)
        self.equip_bonus    = d.get("equip_bonus",   {})
        self.status_effect  = d.get("status_effect", None)
        self.effect_chance  = d.get("effect_chance", 0.0)
        self.effect_duration= d.get("effect_dur",    0.0)
        self.element        = d.get("element",       None)
        self.reach          = d.get("reach",         1.0)
        self.two_handed     = d.get("two_handed",    False)

    def clone(self, count=None):
        i = Item(self.item_id, count if count is not None else self.count)
        return i

    def add(self, amount: int) -> int:
        """Add amount, return overflow."""
        space     = self.max_stack - self.count
        added     = min(space, amount)
        self.count += added
        return amount - added

    def remove(self, amount: int) -> bool:
        if self.count < amount:
            return False
        self.count -= amount
        return True

    def is_empty(self) -> bool:
        return self.count <= 0

    def __repr__(self):
        return f"<Item {self.name} x{self.count}>"


def make(item_id: str, count: int = 1) -> Item:
    return Item(item_id, count)


# ============================================================
#  ITEM REGISTRY
# ============================================================
# Keys: name, itype, max_stack, damage, defense, equip_slot,
#       hunger, thirst, heal, speed_bonus, color, desc,
#       tool_type, ammo_id, attack_speed, knockback,
#       equip_bonus={stat:val}, status_effect, effect_chance,
#       effect_dur, element, reach, two_handed
# ============================================================
ITEM_REGISTRY: dict = {

    # ═══════════════════════════════════════════════════════
    #  RAW RESOURCES
    # ═══════════════════════════════════════════════════════
    "plant_fiber": {
        "name":"Plant Fiber","itype":ITYPE_RESOURCE,
        "color":COL_FIBER,"max_stack":50,
        "desc":"Fibrous strands torn from grass blades.",
    },
    "grass_plank": {
        "name":"Grass Plank","itype":ITYPE_RESOURCE,
        "color":(0.45,0.65,0.22,1),"max_stack":40,
        "desc":"Dried and pressed grass blade.",
    },
    "dry_grass_chunk": {
        "name":"Dry Grass Chunk","itype":ITYPE_RESOURCE,
        "color":COL_DRY_GRASS,"max_stack":40,
        "desc":"Brittle dry grass. Good tinder.",
    },
    "pebble": {
        "name":"Pebble","itype":ITYPE_RESOURCE,
        "color":COL_PEBBLE,"max_stack":30,
        "desc":"A small smooth stone.",
    },
    "quartzite_shard": {
        "name":"Quartzite Shard","itype":ITYPE_RESOURCE,
        "color":(0.75,0.78,0.92,1),"max_stack":20,
        "desc":"Razor-sharp crystal fragment.",
    },
    "sprig": {
        "name":"Sprig","itype":ITYPE_RESOURCE,
        "color":COL_SPRIG,"max_stack":30,
        "desc":"A slim plant sprig.",
    },
    "twig": {
        "name":"Twig","itype":ITYPE_RESOURCE,
        "color":COL_BARK,"max_stack":30,
        "desc":"Short dry twig.",
    },
    "acorn_shell": {
        "name":"Acorn Shell","itype":ITYPE_RESOURCE,
        "color":COL_ACORN,"max_stack":20,
        "desc":"Hard acorn husk.",
    },
    "acorn_top": {
        "name":"Acorn Top","itype":ITYPE_RESOURCE,
        "color":(0.40,0.28,0.10,1),"max_stack":20,
        "desc":"Scaly acorn cap.",
    },
    "acorn_meal": {
        "name":"Acorn Meal","itype":ITYPE_RESOURCE,
        "color":COL_TAN,"max_stack":20,
        "desc":"Ground acorn — nutritious base ingredient.",
    },
    "raw_mushroom": {
        "name":"Raw Mushroom","itype":ITYPE_FOOD,
        "color":COL_MUSHROOM,"max_stack":10,
        "hunger":10,"heal":-3,
        "desc":"Edible raw but causes mild nausea.",
    },
    "mushroom_chunk": {
        "name":"Mushroom Chunk","itype":ITYPE_RESOURCE,
        "color":COL_PEACH,"max_stack":20,
        "desc":"Dried mushroom chunk.",
    },
    "mushroom_spore": {
        "name":"Mushroom Spore","itype":ITYPE_RESOURCE,
        "color":(0.82,0.55,0.78,1),"max_stack":30,
        "desc":"Fine mushroom spore dust.",
    },
    "berry_chunk": {
        "name":"Berry Chunk","itype":ITYPE_FOOD,
        "color":COL_BERRY,"max_stack":20,
        "hunger":14,"thirst":18,
        "desc":"Sweet and juicy backyard berry.",
    },
    "clover_leaf": {
        "name":"Clover Leaf","itype":ITYPE_RESOURCE,
        "color":COL_CLOVER,"max_stack":30,
        "desc":"Lucky clover fragment.",
    },
    "stem_piece": {
        "name":"Stem Piece","itype":ITYPE_RESOURCE,
        "color":(0.32,0.60,0.20,1),"max_stack":30,
        "desc":"Hollow plant stem section.",
    },
    "sap": {
        "name":"Sap","itype":ITYPE_RESOURCE,
        "color":(1.0,0.78,0.20,1),"max_stack":20,
        "desc":"Sticky tree resin.",
    },
    "clay_clump": {
        "name":"Clay Clump","itype":ITYPE_RESOURCE,
        "color":(0.75,0.48,0.36,1),"max_stack":30,
        "desc":"Dense moist clay from muddy soil.",
    },
    "silk_rope": {
        "name":"Silk Rope","itype":ITYPE_RESOURCE,
        "color":(0.90,0.88,0.80,1),"max_stack":20,
        "desc":"Braided spider-silk cordage. Strong and light.",
    },
    "dew_drop": {
        "name":"Dew Drop","itype":ITYPE_RESOURCE,
        "color":(0.65,0.88,1.0,1),"max_stack":10,
        "desc":"Crystal-clear water droplet.",
    },
    "thistle_needle": {
        "name":"Thistle Needle","itype":ITYPE_RESOURCE,
        "color":(0.78,0.78,0.30,1),"max_stack":30,
        "desc":"Barbed thistle spike — natural arrowhead.",
    },
    "feather": {
        "name":"Feather","itype":ITYPE_RESOURCE,
        "color":COL_WHITE,"max_stack":30,
        "desc":"Light bird feather for fletching.",
    },
    "flower_petal": {
        "name":"Flower Petal","itype":ITYPE_RESOURCE,
        "color":(1.0,0.70,0.80,1),"max_stack":20,
        "desc":"Fragrant petal with minor magical properties.",
    },
    "dandelion_tuft": {
        "name":"Dandelion Tuft","itype":ITYPE_RESOURCE,
        "color":(1.0,0.95,0.60,1),"max_stack":20,
        "desc":"Fluffy seed head. Used for padding armor.",
    },
    "mint_chunk": {
        "name":"Mint Chunk","itype":ITYPE_RESOURCE,
        "color":(0.35,0.90,0.62,1),"max_stack":20,
        "desc":"Crystallized mint shard. Icy cold.",
    },
    "woven_fiber": {
        "name":"Woven Fiber","itype":ITYPE_RESOURCE,
        "color":(0.50,0.72,0.28,1),"max_stack":30,
        "desc":"Tightly spun plant fiber thread.",
    },
    "hardened_clay": {
        "name":"Hardened Clay","itype":ITYPE_RESOURCE,
        "color":(0.65,0.38,0.28,1),"max_stack":20,
        "desc":"Kiln-baked clay brick.",
    },
    "resin_glob": {
        "name":"Resin Glob","itype":ITYPE_RESOURCE,
        "color":(0.95,0.70,0.15,1),"max_stack":20,
        "desc":"Hardened amber resin. Excellent adhesive.",
    },
    "smooth_pebble": {
        "name":"Smooth Pebble","itype":ITYPE_RESOURCE,
        "color":(0.60,0.62,0.66,1),"max_stack":20,
        "desc":"A perfectly round river pebble.",
    },

    # ═══════════════════════════════════════════════════════
    #  CREATURE DROPS
    # ═══════════════════════════════════════════════════════
    "ant_part": {
        "name":"Ant Part","itype":ITYPE_RESOURCE,
        "color":COL_ANT,"max_stack":20,
        "desc":"Chitin segment from an ant exoskeleton.",
    },
    "ant_mandible": {
        "name":"Ant Mandible","itype":ITYPE_RESOURCE,
        "color":(0.50,0.25,0.08,1),"max_stack":20,
        "desc":"Serrated ant jaw — natural cutting tool.",
    },
    "ant_head": {
        "name":"Ant Head","itype":ITYPE_RESOURCE,
        "color":(0.68,0.38,0.14,1),"max_stack":10,
        "desc":"Whole ant head. Excellent for helmets.",
    },
    "fire_ant_acid": {
        "name":"Fire Ant Acid","itype":ITYPE_RESOURCE,
        "color":COL_ORANGE,"max_stack":10,
        "desc":"Formic acid sac. Volatile and corrosive.",
    },
    "soldier_ant_part": {
        "name":"Soldier Ant Part","itype":ITYPE_RESOURCE,
        "color":(0.70,0.32,0.10,1),"max_stack":15,
        "desc":"Thick soldier-ant chitin plating.",
    },
    "spider_silk": {
        "name":"Spider Silk","itype":ITYPE_RESOURCE,
        "color":(0.88,0.88,0.84,1),"max_stack":20,
        "desc":"Incredibly strong spider thread.",
    },
    "spider_fang": {
        "name":"Spider Fang","itype":ITYPE_RESOURCE,
        "color":(0.78,0.70,0.12,1),"max_stack":10,
        "desc":"Hollow venom fang.",
    },
    "spider_part": {
        "name":"Spider Part","itype":ITYPE_RESOURCE,
        "color":COL_SPIDER,"max_stack":20,
        "desc":"Spider exoskeleton fragment.",
    },
    "spider_venom_gland": {
        "name":"Venom Gland","itype":ITYPE_RESOURCE,
        "color":(0.58,0.28,0.75,1),"max_stack":10,
        "desc":"Intact venom gland. Handle with care.",
    },
    "wolf_spider_eye": {
        "name":"Wolf Spider Eye","itype":ITYPE_RESOURCE,
        "color":(0.85,0.60,0.10,1),"max_stack":10,
        "desc":"Large reflective wolf spider eye.",
    },
    "ladybug_shell": {
        "name":"Ladybug Shell","itype":ITYPE_RESOURCE,
        "color":COL_LADYBUG,"max_stack":10,
        "desc":"Spotted elytra — very hard shell.",
    },
    "stinkbug_gas_sac": {
        "name":"Stink Gas Sac","itype":ITYPE_RESOURCE,
        "color":(0.45,0.75,0.20,1),"max_stack":10,
        "desc":"Pressurised defensive gas bladder.",
    },
    "weevil_snout": {
        "name":"Weevil Snout","itype":ITYPE_RESOURCE,
        "color":(0.32,0.24,0.14,1),"max_stack":10,
        "desc":"Hardened weevil rostrum.",
    },
    "bombardier_gland": {
        "name":"Bombardier Gland","itype":ITYPE_RESOURCE,
        "color":COL_ORANGE,"max_stack":10,
        "desc":"Reactive explosive gland — don't squeeze.",
    },
    "gnat_fuzz": {
        "name":"Gnat Fuzz","itype":ITYPE_RESOURCE,
        "color":(0.72,0.68,0.60,1),"max_stack":20,
        "desc":"Fine downy fuzz from a gnat.",
    },
    "mosquito_beak": {
        "name":"Mosquito Beak","itype":ITYPE_RESOURCE,
        "color":(0.45,0.42,0.36,1),"max_stack":20,
        "desc":"Long hollow needle-like proboscis.",
    },
    "cricket_leg": {
        "name":"Cricket Leg","itype":ITYPE_RESOURCE,
        "color":(0.40,0.35,0.20,1),"max_stack":20,
        "desc":"Powerful jumping leg with spines.",
    },
    "aphid_honeydew": {
        "name":"Aphid Honeydew","itype":ITYPE_FOOD,
        "color":(1.00,0.92,0.38,1),"max_stack":10,
        "thirst":38,"hunger":8,"heal":6,
        "desc":"Sweet aphid secretion.",
    },

    # ═══════════════════════════════════════════════════════
    #  PROCESSED / CRAFTED MATERIALS
    # ═══════════════════════════════════════════════════════
    "ant_chitin": {
        "name":"Ant Chitin","itype":ITYPE_RESOURCE,
        "color":(0.75,0.42,0.18,1),"max_stack":20,
        "desc":"Purified ant chitin plate.",
    },
    "woven_silk": {
        "name":"Woven Silk","itype":ITYPE_RESOURCE,
        "color":(0.92,0.90,0.84,1),"max_stack":20,
        "desc":"Densely woven spider silk fabric.",
    },
    "pebblet_axe_head": {
        "name":"Axe Head","itype":ITYPE_RESOURCE,
        "color":COL_PEBBLE,"max_stack":5,
        "desc":"Knapped pebble axe head.",
    },

    # ═══════════════════════════════════════════════════════
    #  TOOLS
    # ═══════════════════════════════════════════════════════
    "pebblet_axe": {
        "name":"Pebblet Axe","itype":ITYPE_TOOL,
        "color":COL_PEBBLE,"max_stack":1,"damage":9,
        "tool_type":"axe","attack_speed":0.85,"knockback":1.2,
        "equip_slot":ESLOT_WEAPON,
        "desc":"Knapped pebble axe. Chops grass and stems.",
    },
    "pebblet_hammer": {
        "name":"Pebblet Hammer","itype":ITYPE_TOOL,
        "color":COL_PEBBLE,"max_stack":1,"damage":7,
        "tool_type":"hammer","attack_speed":0.70,"knockback":1.0,
        "equip_slot":ESLOT_WEAPON,
        "desc":"Required for construction.",
    },
    "acorn_shovel": {
        "name":"Acorn Shovel","itype":ITYPE_TOOL,
        "color":COL_ACORN,"max_stack":1,"damage":5,
        "tool_type":"shovel","attack_speed":0.90,"knockback":0.8,
        "equip_slot":ESLOT_WEAPON,
        "desc":"Dig up clay and sand.",
    },
    "quartzite_pick": {
        "name":"Quartzite Pick","itype":ITYPE_TOOL,
        "color":(0.75,0.78,0.92,1),"max_stack":1,"damage":11,
        "tool_type":"pick","attack_speed":0.80,"knockback":1.1,
        "equip_slot":ESLOT_WEAPON,
        "desc":"Mines stone, pebbles, and quartzite.",
    },
    "ant_mandible_axe": {
        "name":"Mandible Axe","itype":ITYPE_TOOL,
        "color":COL_ANT,"max_stack":1,"damage":14,
        "tool_type":"axe","attack_speed":1.10,"knockback":1.3,
        "equip_slot":ESLOT_WEAPON,
        "desc":"Dual-blade ant mandible axe. Harvests fast.",
    },
    "mosquito_needle": {
        "name":"Mosquito Needle","itype":ITYPE_TOOL,
        "color":(0.45,0.42,0.36,1),"max_stack":1,"damage":8,
        "tool_type":"needle","attack_speed":1.50,"knockback":0.6,
        "equip_slot":ESLOT_WEAPON,
        "desc":"Hollow needle. Can inject substances.",
    },

    # ═══════════════════════════════════════════════════════
    #  WEAPONS
    # ═══════════════════════════════════════════════════════
    "pebblet_dagger": {
        "name":"Pebblet Dagger","itype":ITYPE_WEAPON,
        "color":COL_PEBBLE,"max_stack":1,"damage":13,
        "attack_speed":1.40,"knockback":0.9,"equip_slot":ESLOT_WEAPON,
        "desc":"Fast jabbing stone dagger.",
    },
    "sprig_bow": {
        "name":"Sprig Bow","itype":ITYPE_WEAPON,
        "color":COL_SPRIG,"max_stack":1,"damage":15,
        "attack_speed":0.55,"knockback":0.6,"equip_slot":ESLOT_WEAPON,
        "tool_type":"bow","ammo_id":"thistle_arrow","two_handed":True,
        "desc":"Flexible sprig bow. Requires Thistle Arrows.",
    },
    "thistle_arrow": {
        "name":"Thistle Arrow","itype":ITYPE_AMMO,
        "color":(0.78,0.78,0.30,1),"max_stack":40,
        "damage":14,"desc":"Feathered thistle arrow.",
    },
    "quartzite_arrow": {
        "name":"Quartzite Arrow","itype":ITYPE_AMMO,
        "color":(0.75,0.78,0.92,1),"max_stack":40,
        "damage":20,"desc":"Crystal-tipped arrow. Pierces armor.",
    },
    "acid_arrow": {
        "name":"Acid Arrow","itype":ITYPE_AMMO,
        "color":COL_ORANGE,"max_stack":30,"damage":12,
        "status_effect":SE_BURN,"effect_chance":0.60,"effect_dur":4.0,
        "desc":"Fire ant acid-coated arrow. Burns on hit.",
    },
    "bone_spear": {
        "name":"Bone Spear","itype":ITYPE_WEAPON,
        "color":(0.88,0.82,0.72,1),"max_stack":1,"damage":17,
        "attack_speed":0.88,"knockback":1.6,"equip_slot":ESLOT_WEAPON,
        "reach":1.4,"two_handed":True,
        "desc":"Long-reach spear. Excellent vs charging enemies.",
    },
    "ant_club": {
        "name":"Ant Club","itype":ITYPE_WEAPON,
        "color":COL_ANT,"max_stack":1,"damage":22,
        "attack_speed":0.72,"knockback":2.5,"equip_slot":ESLOT_WEAPON,
        "desc":"Brutal bludgeon made from ant mandibles.",
    },
    "spider_fang_dagger": {
        "name":"Spider Fang Dagger","itype":ITYPE_WEAPON,
        "color":(0.78,0.70,0.12,1),"max_stack":1,"damage":19,
        "attack_speed":1.15,"knockback":0.9,"equip_slot":ESLOT_WEAPON,
        "status_effect":SE_POISON,"effect_chance":0.35,"effect_dur":5.0,
        "element":"poison",
        "desc":"Venom-coated fang blade. Chance to poison.",
    },
    "mint_mace": {
        "name":"Mint Mace","itype":ITYPE_WEAPON,
        "color":(0.35,0.90,0.62,1),"max_stack":1,"damage":27,
        "attack_speed":0.58,"knockback":3.0,"equip_slot":ESLOT_WEAPON,
        "status_effect":SE_SLOW,"effect_chance":0.50,"effect_dur":3.0,
        "element":"ice",
        "desc":"Heavy mace of crystallized mint. Slows targets.",
    },
    "ladybug_shield": {
        "name":"Ladybug Shield","itype":ITYPE_WEAPON,
        "color":COL_LADYBUG,"max_stack":1,"damage":5,"defense":22,
        "attack_speed":0.50,"knockback":1.8,"equip_slot":ESLOT_OFFHAND,
        "desc":"Durable spotted shield. Great blocking stats.",
    },
    "bombardier_launcher": {
        "name":"Acid Launcher","itype":ITYPE_WEAPON,
        "color":COL_ORANGE,"max_stack":1,"damage":25,
        "attack_speed":0.40,"knockback":0.4,"equip_slot":ESLOT_WEAPON,
        "tool_type":"launcher","ammo_id":None,"two_handed":True,
        "element":"fire","status_effect":SE_BURN,"effect_chance":0.80,"effect_dur":3.0,
        "desc":"Repurposed bombardier gland launcher. AoE burn.",
    },
    "stink_sack_bomb": {
        "name":"Stink Bomb","itype":ITYPE_WEAPON,
        "color":(0.45,0.75,0.20,1),"max_stack":5,"damage":18,
        "attack_speed":0.70,"knockback":0.5,"equip_slot":ESLOT_WEAPON,
        "element":"poison","status_effect":SE_STINK,"effect_chance":1.0,"effect_dur":6.0,
        "desc":"Thrown stink bomb. AoE stink cloud.",
    },
    "cricket_crossbow": {
        "name":"Cricket Crossbow","itype":ITYPE_WEAPON,
        "color":(0.40,0.35,0.20,1),"max_stack":1,"damage":28,
        "attack_speed":0.38,"knockback":1.0,"equip_slot":ESLOT_WEAPON,
        "tool_type":"crossbow","ammo_id":"quartzite_arrow","two_handed":True,
        "desc":"Powerful crossbow built from cricket legs.",
    },
    "ant_queen_club": {
        "name":"Queen's Mandible","itype":ITYPE_WEAPON,
        "color":(0.85,0.60,0.10,1),"max_stack":1,"damage":35,
        "attack_speed":0.65,"knockback":4.0,"equip_slot":ESLOT_WEAPON,
        "desc":"Legendary weapon. Heavy with enormous knockback.",
    },

    # ═══════════════════════════════════════════════════════
    #  ARMOR – ACORN SET  (Tier 1, balanced)
    # ═══════════════════════════════════════════════════════
    "acorn_helmet": {
        "name":"Acorn Helmet","itype":ITYPE_ARMOR,
        "color":COL_ACORN,"max_stack":1,"defense":8,
        "equip_slot":ESLOT_HEAD,
        "desc":"Hard acorn-shell cap. Starter head protection.",
    },
    "acorn_chestplate": {
        "name":"Acorn Chestplate","itype":ITYPE_ARMOR,
        "color":COL_ACORN,"max_stack":1,"defense":12,
        "equip_slot":ESLOT_CHEST,
        "desc":"Layered acorn-shell torso armor.",
    },
    "acorn_greaves": {
        "name":"Acorn Greaves","itype":ITYPE_ARMOR,
        "color":COL_ACORN,"max_stack":1,"defense":8,
        "equip_slot":ESLOT_LEGS,
        "desc":"Solid acorn-shell leg guards.",
    },
    "acorn_boots": {
        "name":"Acorn Boots","itype":ITYPE_ARMOR,
        "color":(0.50,0.34,0.12,1),"max_stack":1,"defense":5,
        "equip_slot":ESLOT_FEET,
        "desc":"Acorn-cap boots.",
    },

    # ═══════════════════════════════════════════════════════
    #  ARMOR – ANT SET  (Tier 2, light/fast)
    # ═══════════════════════════════════════════════════════
    "ant_helmet": {
        "name":"Ant Helmet","itype":ITYPE_ARMOR,
        "color":COL_ANT,"max_stack":1,"defense":12,
        "equip_slot":ESLOT_HEAD,
        "equip_bonus":{"attack_speed":0.05},
        "desc":"Ant-head helmet. Minor attack speed bonus.",
    },
    "ant_chestplate": {
        "name":"Ant Chestplate","itype":ITYPE_ARMOR,
        "color":COL_ANT,"max_stack":1,"defense":16,
        "equip_slot":ESLOT_CHEST,
        "desc":"Layered ant-chitin chest armor.",
    },
    "ant_greaves": {
        "name":"Ant Greaves","itype":ITYPE_ARMOR,
        "color":COL_ANT,"max_stack":1,"defense":10,
        "equip_slot":ESLOT_LEGS,
        "speed_bonus":0.10,
        "desc":"Ant-chitin leg armor. +10% move speed.",
    },
    "ant_boots": {
        "name":"Ant Boots","itype":ITYPE_ARMOR,
        "color":(0.55,0.28,0.08,1),"max_stack":1,"defense":7,
        "equip_slot":ESLOT_FEET,"speed_bonus":0.08,
        "desc":"Ant-leg boots. +8% move speed.",
    },

    # ═══════════════════════════════════════════════════════
    #  ARMOR – SPIDER SET  (Tier 2, ranged/stealth)
    # ═══════════════════════════════════════════════════════
    "spider_helmet": {
        "name":"Spider Helmet","itype":ITYPE_ARMOR,
        "color":COL_SPIDER,"max_stack":1,"defense":10,
        "equip_slot":ESLOT_HEAD,
        "equip_bonus":{"ranged_damage":0.10},
        "desc":"Silk-lined spider helmet. +10% ranged damage.",
    },
    "spider_chestplate": {
        "name":"Spider Chestplate","itype":ITYPE_ARMOR,
        "color":COL_SPIDER,"max_stack":1,"defense":18,
        "equip_slot":ESLOT_CHEST,
        "desc":"Dense woven spider-silk chest armor.",
    },
    "spider_greaves": {
        "name":"Spider Greaves","itype":ITYPE_ARMOR,
        "color":COL_SPIDER,"max_stack":1,"defense":12,
        "equip_slot":ESLOT_LEGS,
        "desc":"Spider-silk wrapped leg armor.",
    },
    "spider_boots": {
        "name":"Spider Boots","itype":ITYPE_ARMOR,
        "color":(0.12,0.10,0.16,1),"max_stack":1,"defense":8,
        "equip_slot":ESLOT_FEET,
        "desc":"Spider boots. Silent movement.",
    },

    # ═══════════════════════════════════════════════════════
    #  ARMOR – LADYBUG SET  (Tier 3, tank)
    # ═══════════════════════════════════════════════════════
    "ladybug_helmet": {
        "name":"Ladybug Helmet","itype":ITYPE_ARMOR,
        "color":COL_LADYBUG,"max_stack":1,"defense":20,
        "equip_slot":ESLOT_HEAD,
        "desc":"Spotted elytra helmet. Very high protection.",
    },
    "ladybug_chestplate": {
        "name":"Ladybug Chestplate","itype":ITYPE_ARMOR,
        "color":COL_LADYBUG,"max_stack":1,"defense":28,
        "equip_slot":ESLOT_CHEST,
        "desc":"Hardest chest armor. Significantly reduces mobility.",
    },
    "ladybug_greaves": {
        "name":"Ladybug Greaves","itype":ITYPE_ARMOR,
        "color":COL_LADYBUG,"max_stack":1,"defense":18,
        "equip_slot":ESLOT_LEGS,
        "desc":"Thick elytra leg guards.",
    },

    # ═══════════════════════════════════════════════════════
    #  ARMOR – SPIDER/SILK LIGHT SET  (Tier 2, mage)
    # ═══════════════════════════════════════════════════════
    "woven_silk_robes": {
        "name":"Silk Robes","itype":ITYPE_ARMOR,
        "color":(0.88,0.82,0.74,1),"max_stack":1,"defense":8,
        "equip_slot":ESLOT_CHEST,
        "equip_bonus":{"status_chance":0.15},
        "desc":"Lightweight silk robes. +15% status effect chance.",
    },
    "woven_silk_hood": {
        "name":"Silk Hood","itype":ITYPE_ARMOR,
        "color":(0.88,0.82,0.74,1),"max_stack":1,"defense":6,
        "equip_slot":ESLOT_HEAD,
        "desc":"Silk hood. Quiet and comfortable.",
    },

    # ═══════════════════════════════════════════════════════
    #  FOOD
    # ═══════════════════════════════════════════════════════
    "roasted_mushroom": {
        "name":"Roasted Mushroom","itype":ITYPE_FOOD,
        "color":(0.78,0.52,0.28,1),"max_stack":10,
        "hunger":38,"thirst":-5,"heal":12,
        "desc":"Cooked over fire. Very filling.",
    },
    "mushroom_tea": {
        "name":"Mushroom Tea","itype":ITYPE_FOOD,
        "color":(0.68,0.45,0.82,1),"max_stack":5,
        "hunger":5,"thirst":65,"heal":18,
        "status_effect":SE_REGEN,"effect_dur":20.0,"effect_chance":1.0,
        "desc":"Warm herbal tea. Hydrating + health regen.",
    },
    "acorn_soup": {
        "name":"Acorn Soup","itype":ITYPE_FOOD,
        "color":(0.78,0.62,0.32,1),"max_stack":5,
        "hunger":52,"thirst":32,"heal":22,
        "desc":"Hearty broth. Best early-game meal.",
    },
    "clover_salad": {
        "name":"Clover Salad","itype":ITYPE_FOOD,
        "color":(0.22,0.78,0.35,1),"max_stack":10,
        "hunger":22,"thirst":14,
        "desc":"Fresh clover leaves. Light snack.",
    },
    "weevil_jerky": {
        "name":"Weevil Jerky","itype":ITYPE_FOOD,
        "color":(0.62,0.40,0.20,1),"max_stack":10,
        "hunger":42,"heal":8,
        "desc":"Dried weevil meat. Tough but filling.",
    },
    "ant_egg_omelette": {
        "name":"Ant Egg Omelette","itype":ITYPE_FOOD,
        "color":(0.95,0.95,0.75,1),"max_stack":5,
        "hunger":30,"heal":15,"thirst":5,
        "desc":"Fluffy egg omelette. Cooked over fire.",
    },
    "honeydew_smoothie": {
        "name":"Honeydew Smoothie","itype":ITYPE_FOOD,
        "color":(1.00,0.90,0.35,1),"max_stack":5,
        "thirst":55,"hunger":12,"heal":10,
        "status_effect":SE_BOOST_SPD,"effect_dur":30.0,"effect_chance":1.0,
        "desc":"Aphid honeydew drink. Grants speed boost.",
    },
    "flower_petal_salve": {
        "name":"Flower Salve","itype":ITYPE_FOOD,
        "color":COL_PINK,"max_stack":5,
        "heal":35,
        "desc":"Medicinal petal paste. Heal only — no nutrition.",
    },
    "mushroom_power_shake": {
        "name":"Power Shake","itype":ITYPE_FOOD,
        "color":(0.55,0.22,0.72,1),"max_stack":3,
        "hunger":20,"thirst":20,"heal":20,
        "status_effect":SE_BOOST_ATK,"effect_dur":60.0,"effect_chance":1.0,
        "desc":"Mushroom + silk extract. Boosts attack for 60s.",
    },
    "acorn_bread": {
        "name":"Acorn Bread","itype":ITYPE_FOOD,
        "color":COL_TAN,"max_stack":8,
        "hunger":35,"heal":5,
        "desc":"Dense acorn bread. Good trail food.",
    },
    "berry_jam": {
        "name":"Berry Jam","itype":ITYPE_FOOD,
        "color":(0.80,0.15,0.40,1),"max_stack":8,
        "hunger":18,"thirst":22,"heal":8,
        "desc":"Sweet cooked berry reduction.",
    },
    "ant_egg": {
        "name":"Ant Egg","itype":ITYPE_FOOD,
        "color":(0.95,0.95,0.82,1),"max_stack":10,
        "hunger":18,"heal":4,
        "desc":"Raw ant egg. Edible but bland.",
    },
}


def get_data(item_id: str) -> dict:
    return ITEM_REGISTRY.get(item_id, {})
