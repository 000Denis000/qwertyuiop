# items.py - All item definitions

from constants import *
import pygame

class Item:
    """Represents a stack of one item type in the inventory."""
    def __init__(self, item_id, count=1):
        self.item_id = item_id
        self.count   = count
        data = ITEM_DATA.get(item_id, {})
        self.name        = data.get("name", item_id)
        self.itype       = data.get("itype", ITYPE_RESOURCE)
        self.max_stack   = data.get("max_stack", 20)
        self.damage      = data.get("damage", 0)
        self.defense     = data.get("defense", 0)
        self.equip_slot  = data.get("equip_slot", None)
        self.hunger_val  = data.get("hunger", 0)
        self.thirst_val  = data.get("thirst", 0)
        self.heal_val    = data.get("heal", 0)
        self.speed_bonus = data.get("speed_bonus", 0)
        self.color       = data.get("color", GRAY)
        self.description = data.get("desc", "")
        self.tool_type   = data.get("tool_type", None)  # "axe","hammer","bow"
        self.ammo_id     = data.get("ammo_id", None)
        self.attack_speed= data.get("attack_speed", 1.0)  # multiplier
        self.knockback   = data.get("knockback", 100)

    def split(self, amount):
        """Remove `amount` from this stack, return a new Item with that count."""
        amount = min(amount, self.count)
        self.count -= amount
        return Item(self.item_id, amount)

    def __repr__(self):
        return f"<Item {self.name} x{self.count}>"

    def draw_icon(self, surface, rect, selected=False):
        """Draw item icon inside rect."""
        bg_col = UI_SLOT_SEL if selected else UI_SLOT_BG
        pygame.draw.rect(surface, bg_col, rect, border_radius=4)
        pygame.draw.rect(surface, UI_BORDER, rect, 1, border_radius=4)
        cx = rect.centerx
        cy = rect.centery
        r  = min(rect.width, rect.height) // 2 - 6
        data = ITEM_DATA.get(self.item_id, {})
        shape = data.get("shape", "circle")
        col   = data.get("color", GRAY)
        if shape == "circle":
            pygame.draw.circle(surface, col, (cx, cy), r)
        elif shape == "rect":
            pygame.draw.rect(surface, col, (cx-r, cy-r, r*2, r*2))
        elif shape == "diamond":
            pts = [(cx, cy-r), (cx+r, cy), (cx, cy+r), (cx-r, cy)]
            pygame.draw.polygon(surface, col, pts)
        elif shape == "triangle":
            pts = [(cx, cy-r), (cx+r, cy+r), (cx-r, cy+r)]
            pygame.draw.polygon(surface, col, pts)
        elif shape == "arrow":
            pts = [(cx, cy-r), (cx+r//2, cy+r//2), (cx, cy), (cx-r//2, cy+r//2)]
            pygame.draw.polygon(surface, col, pts)
        elif shape == "cross":
            t = max(3, r//3)
            pygame.draw.rect(surface, col, (cx-t, cy-r, t*2, r*2))
            pygame.draw.rect(surface, col, (cx-r, cy-t, r*2, t*2))
        elif shape == "star":
            import math
            pts = []
            for i in range(10):
                angle = math.radians(i * 36 - 90)
                rad = r if i % 2 == 0 else r // 2
                pts.append((cx + rad*math.cos(angle), cy + rad*math.sin(angle)))
            pygame.draw.polygon(surface, col, pts)


# ─── Item Definitions ─────────────────────────────────────────────────────────
# id: {name, itype, shape, color, max_stack, damage, defense, equip_slot,
#      hunger, thirst, heal, speed_bonus, tool_type, ammo_id, attack_speed,
#      knockback, desc}
ITEM_DATA = {
    # ── Resources ────────────────────────────────────────────────────────────
    "plant_fiber": {
        "name":"Plant Fiber","itype":ITYPE_RESOURCE,"shape":"cross",
        "color":LIME,"max_stack":50,"desc":"Basic fiber stripped from grass blades.",
    },
    "grass_plank": {
        "name":"Grass Plank","itype":ITYPE_RESOURCE,"shape":"rect",
        "color":(120,170,60),"max_stack":40,"desc":"Dried and pressed grass.",
    },
    "dry_grass_chunk": {
        "name":"Dry Grass Chunk","itype":ITYPE_RESOURCE,"shape":"rect",
        "color":(180,155,60),"max_stack":40,"desc":"Dry grass clump, good for fire.",
    },
    "pebble": {
        "name":"Pebble","itype":ITYPE_RESOURCE,"shape":"circle",
        "color":GRAY,"max_stack":30,"desc":"Smooth stone pebble.",
    },
    "quartzite_shard": {
        "name":"Quartzite Shard","itype":ITYPE_RESOURCE,"shape":"diamond",
        "color":(200,200,220),"max_stack":20,"desc":"Sharp crystal shard.",
    },
    "sprig": {
        "name":"Sprig","itype":ITYPE_RESOURCE,"shape":"cross",
        "color":(80,160,40),"max_stack":30,"desc":"Thin plant sprig.",
    },
    "acorn_shell": {
        "name":"Acorn Shell","itype":ITYPE_RESOURCE,"shape":"circle",
        "color":BROWN,"max_stack":20,"desc":"Half of an acorn shell.",
    },
    "acorn_top": {
        "name":"Acorn Top","itype":ITYPE_RESOURCE,"shape":"circle",
        "color":(100,70,30),"max_stack":20,"desc":"The cap of an acorn.",
    },
    "acorn_meal": {
        "name":"Acorn Meal","itype":ITYPE_RESOURCE,"shape":"circle",
        "color":TAN,"max_stack":20,"desc":"Coarsely ground acorn.",
    },
    "mushroom_chunk": {
        "name":"Mushroom Chunk","itype":ITYPE_RESOURCE,"shape":"circle",
        "color":PEACH,"max_stack":20,"desc":"Raw mushroom chunk.",
    },
    "mushroom_spore": {
        "name":"Mushroom Spore","itype":ITYPE_RESOURCE,"shape":"star",
        "color":(220,160,200),"max_stack":30,"desc":"Tiny mushroom spore.",
    },
    "clover_leaf": {
        "name":"Clover Leaf","itype":ITYPE_RESOURCE,"shape":"star",
        "color":(50,180,70),"max_stack":30,"desc":"Four-leaf clover fragment.",
    },
    "stem_piece": {
        "name":"Stem Piece","itype":ITYPE_RESOURCE,"shape":"rect",
        "color":(90,150,50),"max_stack":30,"desc":"Section of plant stem.",
    },
    "sap": {
        "name":"Sap","itype":ITYPE_RESOURCE,"shape":"circle",
        "color":(255,200,50),"max_stack":20,"desc":"Sticky tree sap.",
    },
    "clay_clump": {
        "name":"Clay Clump","itype":ITYPE_RESOURCE,"shape":"circle",
        "color":(200,130,100),"max_stack":30,"desc":"Moist clay from the soil.",
    },
    "silk_rope": {
        "name":"Silk Rope","itype":ITYPE_RESOURCE,"shape":"cross",
        "color":(230,220,200),"max_stack":20,"desc":"Braided spider silk.",
    },
    "dew_drop": {
        "name":"Dew Drop","itype":ITYPE_RESOURCE,"shape":"circle",
        "color":LIGHT_BLUE,"max_stack":10,"desc":"Pure water droplet.",
    },
    "twig": {
        "name":"Twig","itype":ITYPE_RESOURCE,"shape":"rect",
        "color":(120,85,40),"max_stack":30,"desc":"Small dry twig.",
    },
    "thistle_needle": {
        "name":"Thistle Needle","itype":ITYPE_RESOURCE,"shape":"triangle",
        "color":(200,200,80),"max_stack":30,"desc":"Sharp thistle spike.",
    },
    "feather": {
        "name":"Feather","itype":ITYPE_RESOURCE,"shape":"arrow",
        "color":WHITE,"max_stack":30,"desc":"Light bird feather.",
    },

    # ── Creature Drops ───────────────────────────────────────────────────────
    "ant_part": {
        "name":"Ant Part","itype":ITYPE_RESOURCE,"shape":"circle",
        "color":(160,80,30),"max_stack":20,"desc":"Ant body segment.",
    },
    "ant_mandible": {
        "name":"Ant Mandible","itype":ITYPE_RESOURCE,"shape":"diamond",
        "color":(120,60,20),"max_stack":20,"desc":"Sharp ant jaw.",
    },
    "ant_head": {
        "name":"Ant Head","itype":ITYPE_RESOURCE,"shape":"circle",
        "color":(180,90,30),"max_stack":10,"desc":"Ant head, useful for crafting.",
    },
    "spider_silk": {
        "name":"Spider Silk","itype":ITYPE_RESOURCE,"shape":"cross",
        "color":(220,220,220),"max_stack":20,"desc":"Strong spider silk thread.",
    },
    "spider_fang": {
        "name":"Spider Fang","itype":ITYPE_RESOURCE,"shape":"diamond",
        "color":(200,180,30),"max_stack":10,"desc":"Venom-coated spider fang.",
    },
    "spider_part": {
        "name":"Spider Part","itype":ITYPE_RESOURCE,"shape":"circle",
        "color":(50,50,60),"max_stack":20,"desc":"Spider body segment.",
    },
    "ladybug_shell": {
        "name":"Ladybug Shell","itype":ITYPE_RESOURCE,"shape":"circle",
        "color":(220,40,40),"max_stack":10,"desc":"Tough spotted shell.",
    },
    "stinkbug_gas": {
        "name":"Stink Gas Sac","itype":ITYPE_RESOURCE,"shape":"circle",
        "color":(120,180,40),"max_stack":10,"desc":"Pressurized stink sac.",
    },
    "weevil_nose": {
        "name":"Weevil Snout","itype":ITYPE_RESOURCE,"shape":"diamond",
        "color":(80,60,40),"max_stack":10,"desc":"Tough weevil rostrum.",
    },
    "bombardier_gland": {
        "name":"Bombardier Gland","itype":ITYPE_RESOURCE,"shape":"circle",
        "color":(220,120,0),"max_stack":10,"desc":"Explosive gland.",
    },

    # ── Tools ────────────────────────────────────────────────────────────────
    "pebblet_axe": {
        "name":"Pebblet Axe","itype":ITYPE_TOOL,"shape":"triangle",
        "color":GRAY,"max_stack":1,"damage":8,"tool_type":"axe",
        "attack_speed":0.85,"knockback":80,"desc":"Basic axe for chopping grass and stems.",
    },
    "pebblet_hammer": {
        "name":"Pebblet Hammer","itype":ITYPE_TOOL,"shape":"rect",
        "color":GRAY,"max_stack":1,"damage":6,"tool_type":"hammer",
        "attack_speed":0.7,"knockback":60,"desc":"Used for construction.",
    },
    "acorn_shovel": {
        "name":"Acorn Shovel","itype":ITYPE_TOOL,"shape":"triangle",
        "color":BROWN,"max_stack":1,"damage":5,"tool_type":"shovel",
        "attack_speed":0.9,"knockback":50,"desc":"Dig up clay and mud.",
    },

    # ── Weapons ──────────────────────────────────────────────────────────────
    "pebblet_dagger": {
        "name":"Pebblet Dagger","itype":ITYPE_WEAPON,"shape":"diamond",
        "color":(180,180,200),"max_stack":1,"damage":12,
        "equip_slot":SLOT_WEAPON,"attack_speed":1.3,"knockback":60,
        "desc":"Fast stabbing weapon made from pebbles.",
    },
    "sprig_bow": {
        "name":"Sprig Bow","itype":ITYPE_WEAPON,"shape":"arrow",
        "color":(90,140,50),"max_stack":1,"damage":14,
        "equip_slot":SLOT_WEAPON,"attack_speed":0.6,"knockback":40,
        "tool_type":"bow","ammo_id":"thistle_arrow",
        "desc":"Ranged bow made from sprigs.",
    },
    "thistle_arrow": {
        "name":"Thistle Arrow","itype":ITYPE_AMMO,"shape":"arrow",
        "color":(220,220,80),"max_stack":40,"desc":"Arrows for the sprig bow.",
    },
    "ant_club": {
        "name":"Ant Club","itype":ITYPE_WEAPON,"shape":"rect",
        "color":(160,80,30),"max_stack":1,"damage":20,
        "equip_slot":SLOT_WEAPON,"attack_speed":0.75,"knockback":160,
        "desc":"Heavy club made from ant mandibles. High knockback.",
    },
    "spider_fang_dagger": {
        "name":"Spider Fang Dagger","itype":ITYPE_WEAPON,"shape":"diamond",
        "color":(200,180,30),"max_stack":1,"damage":18,
        "equip_slot":SLOT_WEAPON,"attack_speed":1.1,"knockback":70,
        "desc":"Fast venom-coated fang dagger.",
    },
    "mint_mace": {
        "name":"Mint Mace","itype":ITYPE_WEAPON,"shape":"cross",
        "color":(100,220,160),"max_stack":1,"damage":25,
        "equip_slot":SLOT_WEAPON,"attack_speed":0.6,"knockback":200,
        "desc":"Heavy mace of crystallized mint. Devastating knockback.",
    },
    "ladybug_shield": {
        "name":"Ladybug Shield","itype":ITYPE_WEAPON,"shape":"circle",
        "color":(220,40,40),"max_stack":1,"damage":4,"defense":20,
        "equip_slot":SLOT_OFFHAND,"attack_speed":0.5,"knockback":120,
        "desc":"Durable shield crafted from ladybug shell.",
    },
    "bone_spear": {
        "name":"Bone Spear","itype":ITYPE_WEAPON,"shape":"arrow",
        "color":(230,220,190),"max_stack":1,"damage":16,
        "equip_slot":SLOT_WEAPON,"attack_speed":0.9,"knockback":120,
        "desc":"Long reach spear. Good against charging enemies.",
    },

    # ── Armor ────────────────────────────────────────────────────────────────
    "acorn_helmet": {
        "name":"Acorn Helmet","itype":ITYPE_ARMOR,"shape":"circle",
        "color":(140,100,40),"max_stack":1,"defense":8,
        "equip_slot":SLOT_HEAD,"desc":"Tough acorn shell helmet.",
    },
    "acorn_chestplate": {
        "name":"Acorn Chestplate","itype":ITYPE_ARMOR,"shape":"rect",
        "color":(140,100,40),"max_stack":1,"defense":12,
        "equip_slot":SLOT_CHEST,"desc":"Acorn shell body armor.",
    },
    "acorn_greaves": {
        "name":"Acorn Greaves","itype":ITYPE_ARMOR,"shape":"rect",
        "color":(140,100,40),"max_stack":1,"defense":8,
        "equip_slot":SLOT_LEGS,"desc":"Acorn leg guards.",
    },
    "ant_helmet": {
        "name":"Ant Helmet","itype":ITYPE_ARMOR,"shape":"circle",
        "color":(180,90,30),"max_stack":1,"defense":12,
        "equip_slot":SLOT_HEAD,"desc":"Ant head armor. Lightweight.",
    },
    "ant_chestplate": {
        "name":"Ant Chestplate","itype":ITYPE_ARMOR,"shape":"rect",
        "color":(160,80,30),"max_stack":1,"defense":16,
        "equip_slot":SLOT_CHEST,"desc":"Ant exoskeleton chest armor.",
    },
    "ant_greaves": {
        "name":"Ant Greaves","itype":ITYPE_ARMOR,"shape":"rect",
        "color":(160,80,30),"max_stack":1,"defense":10,
        "equip_slot":SLOT_LEGS,"speed_bonus":0.1,
        "desc":"Ant leg armor. Increases movement speed.",
    },
    "spider_helmet": {
        "name":"Spider Helmet","itype":ITYPE_ARMOR,"shape":"circle",
        "color":(50,50,70),"max_stack":1,"defense":10,
        "equip_slot":SLOT_HEAD,"desc":"Spider silk helmet.",
    },
    "spider_chestplate": {
        "name":"Spider Chestplate","itype":ITYPE_ARMOR,"shape":"rect",
        "color":(50,50,70),"max_stack":1,"defense":18,
        "equip_slot":SLOT_CHEST,"desc":"Dense spider silk chest armor.",
    },
    "ladybug_chestplate": {
        "name":"Ladybug Chestplate","itype":ITYPE_ARMOR,"shape":"rect",
        "color":(220,40,40),"max_stack":1,"defense":24,
        "equip_slot":SLOT_CHEST,"desc":"Hardest chest armor available. Very heavy.",
    },

    # ── Food ─────────────────────────────────────────────────────────────────
    "roasted_mushroom": {
        "name":"Roasted Mushroom","itype":ITYPE_FOOD,"shape":"circle",
        "color":(200,140,80),"max_stack":10,"hunger":35,"thirst":-5,"heal":10,
        "desc":"Cooked mushroom. Very filling.",
    },
    "berry_chunk": {
        "name":"Berry Chunk","itype":ITYPE_FOOD,"shape":"circle",
        "color":(180,30,80),"max_stack":20,"hunger":15,"thirst":20,
        "desc":"Juicy and sweet. Good for thirst.",
    },
    "acorn_soup": {
        "name":"Acorn Soup","itype":ITYPE_FOOD,"shape":"circle",
        "color":(200,160,80),"max_stack":5,"hunger":50,"thirst":30,"heal":20,
        "desc":"Nutritious acorn soup. Restores a lot.",
    },
    "mushroom_tea": {
        "name":"Mushroom Tea","itype":ITYPE_FOOD,"shape":"circle",
        "color":(180,120,200),"max_stack":5,"hunger":5,"thirst":60,"heal":15,
        "desc":"Herbal tea. Excellent hydration.",
    },
    "ant_egg": {
        "name":"Ant Egg","itype":ITYPE_FOOD,"shape":"circle",
        "color":(240,240,200),"max_stack":10,"hunger":20,"heal":5,
        "desc":"Protein-rich ant egg.",
    },
    "weevil_jerky": {
        "name":"Weevil Jerky","itype":ITYPE_FOOD,"shape":"rect",
        "color":(160,100,50),"max_stack":10,"hunger":40,"heal":5,
        "desc":"Dried weevil meat. Tough but filling.",
    },
    "aphid_honeydew": {
        "name":"Aphid Honeydew","itype":ITYPE_FOOD,"shape":"circle",
        "color":(255,235,100),"max_stack":10,"thirst":40,"hunger":10,"heal":8,
        "desc":"Sweet aphid secretion.",
    },
    "clover_salad": {
        "name":"Clover Salad","itype":ITYPE_FOOD,"shape":"star",
        "color":(60,200,80),"max_stack":10,"hunger":25,"thirst":15,
        "desc":"Fresh clover leaves.",
    },
    "raw_mushroom": {
        "name":"Raw Mushroom","itype":ITYPE_FOOD,"shape":"circle",
        "color":PEACH,"max_stack":10,"hunger":12,"heal":-5,
        "desc":"Raw mushroom. Eat cooked for full benefit.",
    },
}

def make_item(item_id, count=1):
    """Helper factory to create an Item."""
    return Item(item_id, count)
