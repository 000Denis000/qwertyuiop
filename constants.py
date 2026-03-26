# constants.py - Game-wide constants

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TILE_SIZE = 64
FPS = 60
WORLD_WIDTH = 120   # tiles
WORLD_HEIGHT = 120  # tiles
GAME_TITLE = "Backyard Survival"

# ─── Colors ───────────────────────────────────────────────────────────────────
BLACK        = (0,   0,   0)
WHITE        = (255, 255, 255)
GREEN        = (34,  139, 34)
DARK_GREEN   = (0,   80,  0)
LIGHT_GREEN  = (144, 238, 144)
BROWN        = (139, 90,  43)
DARK_BROWN   = (80,  50,  20)
GRAY         = (130, 130, 130)
DARK_GRAY    = (60,  60,  60)
LIGHT_GRAY   = (200, 200, 200)
RED          = (220, 50,  50)
DARK_RED     = (140, 0,   0)
ORANGE       = (255, 140, 0)
YELLOW       = (255, 215, 0)
BLUE         = (30,  100, 220)
LIGHT_BLUE   = (135, 206, 235)
CYAN         = (0,   200, 220)
PURPLE       = (130, 40,  180)
PINK         = (255, 105, 180)
TAN          = (210, 180, 140)
SAND         = (240, 200, 120)
LIME         = (80,  220, 60)
TEAL         = (0,   150, 130)
MAROON       = (120, 20,  20)
OLIVE        = (100, 120, 20)
PEACH        = (255, 200, 150)
CREAM        = (255, 253, 208)

# UI-specific
UI_BG        = (20,  20,  25,  210)
UI_BORDER    = (80,  80,  90)
UI_HIGHLIGHT = (80,  120, 200)
UI_SLOT_BG   = (40,  40,  50)
UI_SLOT_SEL  = (100, 140, 220)
HEALTH_COL   = (220, 60,  60)
STAMINA_COL  = (60,  160, 220)
HUNGER_COL   = (220, 160, 30)
THIRST_COL   = (30,  160, 220)
XP_COL       = (170, 80,  230)
DAY_SKY      = (135, 206, 250)
NIGHT_SKY    = (10,  10,  40)

# ─── Game States ───────────────────────────────────────────────────────────────
STATE_PLAYING   = "playing"
STATE_INVENTORY = "inventory"
STATE_CRAFTING  = "crafting"
STATE_BUILDING  = "building"
STATE_PAUSED    = "paused"
STATE_DEAD      = "dead"
STATE_MAIN_MENU = "main_menu"

# ─── Tile Types ────────────────────────────────────────────────────────────────
TILE_GRASS      = 0
TILE_DIRT       = 1
TILE_WATER      = 2
TILE_STONE      = 3
TILE_SAND       = 4
TILE_MUD        = 5
TILE_LEAVES     = 6
TILE_CLOVER     = 7
TILE_DRY_GRASS  = 8

TILE_COLORS = {
    TILE_GRASS:     (55,  130, 50),
    TILE_DIRT:      (140, 100, 60),
    TILE_WATER:     (40,  100, 200),
    TILE_STONE:     (110, 110, 115),
    TILE_SAND:      (220, 195, 130),
    TILE_MUD:       (90,  70,  40),
    TILE_LEAVES:    (60,  110, 40),
    TILE_CLOVER:    (40,  160, 70),
    TILE_DRY_GRASS: (170, 145, 60),
}

# ─── Player ────────────────────────────────────────────────────────────────────
PLAYER_MAX_HEALTH   = 100
PLAYER_MAX_STAMINA  = 100
PLAYER_MAX_HUNGER   = 100
PLAYER_MAX_THIRST   = 100
PLAYER_SPEED        = 190      # px/s walking
PLAYER_SPRINT_MULT  = 1.65
PLAYER_RADIUS       = 18
PLAYER_ATTACK_RANGE = 72
PLAYER_ATK_COOLDOWN = 0.5      # seconds
PLAYER_COLLECT_RANGE= 70
INTERACT_RANGE      = 80
HUNGER_DRAIN_RATE   = 0.8      # per second
THIRST_DRAIN_RATE   = 1.1
SPRINT_STAMINA_COST = 25       # per second
STAMINA_REGEN       = 12       # per second
BLOCK_STAMINA_COST  = 15       # per second

# ─── Enemy ─────────────────────────────────────────────────────────────────────
ENEMY_ANT          = "ant"
ENEMY_FIRE_ANT     = "fire_ant"
ENEMY_SPIDER       = "spider"
ENEMY_LADYBUG      = "ladybug"
ENEMY_STINKBUG     = "stinkbug"
ENEMY_BOMBARDIER   = "bombardier"
ENEMY_WEEVIL       = "weevil"
ENEMY_APHID        = "aphid"

# ─── Items (type tags) ─────────────────────────────────────────────────────────
ITYPE_RESOURCE  = "resource"
ITYPE_TOOL      = "tool"
ITYPE_WEAPON    = "weapon"
ITYPE_ARMOR     = "armor"
ITYPE_FOOD      = "food"
ITYPE_BUILDING  = "building_mat"
ITYPE_AMMO      = "ammo"
ITYPE_STATION   = "station"

# ─── Slots ────────────────────────────────────────────────────────────────────
SLOT_HEAD    = "head"
SLOT_CHEST   = "chest"
SLOT_LEGS    = "legs"
SLOT_WEAPON  = "weapon"
SLOT_OFFHAND = "offhand"

# ─── Building types ────────────────────────────────────────────────────────────
BLDG_GRASS_FLOOR    = "grass_floor"
BLDG_GRASS_WALL     = "grass_wall"
BLDG_GRASS_ROOF     = "grass_roof"
BLDG_GRASS_RAMP     = "grass_ramp"
BLDG_STEM_FLOOR     = "stem_floor"
BLDG_STEM_WALL      = "stem_wall"
BLDG_CLAY_FOUND     = "clay_foundation"
BLDG_CRAFTING_TABLE = "crafting_table"
BLDG_CAMPFIRE       = "campfire"
BLDG_DEW_COLLECTOR  = "dew_collector"
BLDG_CHEST          = "chest"
BLDG_SPINNING_WHEEL = "spinning_wheel"
BLDG_ROASTING_SPIT  = "roasting_spit"

# ─── Day/Night ────────────────────────────────────────────────────────────────
DAY_LENGTH = 480   # seconds per full day
