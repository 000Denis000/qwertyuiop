# ============================================================
#  BACKYARD SURVIVAL v2  –  Constants & Configuration
# ============================================================

# ── Window ──────────────────────────────────────────────────
WINDOW_TITLE   = "Backyard Survival"
WINDOW_WIDTH   = 1280
WINDOW_HEIGHT  = 720
TARGET_FPS     = 60

# ── World ───────────────────────────────────────────────────
WORLD_SIZE        = 80       # tiles per side
TILE_WORLD_SCALE  = 2.0      # 1 tile = 2 world units
WORLD_SCALE       = WORLD_SIZE * TILE_WORLD_SCALE
TERRAIN_HEIGHT    = 3.5      # max terrain height variation
WATER_LEVEL       = 0.18     # fraction of terrain height for water
RESOURCE_DENSITY  = 0.07     # probability a tile spawns a resource

# ── Player ──────────────────────────────────────────────────
PLAYER_MOVE_SPEED     = 5.0
PLAYER_SPRINT_MULT    = 1.75
PLAYER_JUMP_POWER     = 5.0
PLAYER_MAX_HEALTH     = 100.0
PLAYER_MAX_STAMINA    = 100.0
PLAYER_MAX_HUNGER     = 100.0
PLAYER_MAX_THIRST     = 100.0
PLAYER_ATTACK_RANGE   = 2.2
PLAYER_COLLECT_RANGE  = 2.5
PLAYER_ATK_COOLDOWN   = 0.45   # seconds between swings
PLAYER_INVINCIBLE_T   = 0.6    # seconds of iframes after hit
HUNGER_DRAIN          = 0.06   # per second
THIRST_DRAIN          = 0.09   # per second
STAMINA_REGEN         = 18.0   # per second
SPRINT_STAMINA_COST   = 20.0   # per second
BLOCK_STAMINA_COST    = 14.0   # per second
HEALTH_REGEN_RATE     = 1.0    # per second when well-fed
HEALTH_REGEN_THRESH   = 55.0   # hunger/thirst must be above this

# ── Camera ──────────────────────────────────────────────────
CAM_DISTANCE      = 10.0
CAM_HEIGHT        = 6.0
CAM_SENSITIVITY   = 60.0    # degrees per second
CAM_MIN_PITCH     = -20.0
CAM_MAX_PITCH     = 60.0
CAM_LERP          = 6.0

# ── Combat ──────────────────────────────────────────────────
BASE_DAMAGE       = 5
KNOCKBACK_BASE    = 3.0
CRIT_CHANCE       = 0.08    # 8% base crit

# ── Day / Night ─────────────────────────────────────────────
DAY_LENGTH        = 480.0   # seconds per full cycle
DAWN_START        = 0.20    # fraction of day
DUSK_START        = 0.70
NIGHT_ENEMY_MULT  = 1.4     # damage multiplier at night

# ── Inventory ───────────────────────────────────────────────
INV_ROWS          = 6
INV_COLS          = 5
HOTBAR_SLOTS      = 5
CHEST_SLOTS       = 20

# ── Item type tags ──────────────────────────────────────────
ITYPE_RESOURCE  = "resource"
ITYPE_TOOL      = "tool"
ITYPE_WEAPON    = "weapon"
ITYPE_ARMOR     = "armor"
ITYPE_FOOD      = "food"
ITYPE_AMMO      = "ammo"
ITYPE_MISC      = "misc"

# ── Equipment slots ─────────────────────────────────────────
ESLOT_HEAD      = "head"
ESLOT_CHEST     = "chest"
ESLOT_LEGS      = "legs"
ESLOT_FEET      = "feet"
ESLOT_WEAPON    = "weapon"
ESLOT_OFFHAND   = "offhand"
ALL_EQUIP_SLOTS = [ESLOT_HEAD, ESLOT_CHEST, ESLOT_LEGS, ESLOT_FEET,
                   ESLOT_WEAPON, ESLOT_OFFHAND]

# ── Building types ──────────────────────────────────────────
B_GRASS_FLOOR    = "grass_floor"
B_GRASS_WALL     = "grass_wall"
B_GRASS_RAMP     = "grass_ramp"
B_STEM_FLOOR     = "stem_floor"
B_STEM_WALL      = "stem_wall"
B_CLAY_FOUNDATION= "clay_foundation"
B_WOVEN_FLOOR    = "woven_floor"
B_CRAFTING_TABLE = "crafting_table"
B_CAMPFIRE       = "campfire"
B_ROASTING_SPIT  = "roasting_spit"
B_DEW_COLLECTOR  = "dew_collector"
B_CHEST          = "chest"
B_SPINNING_WHEEL = "spinning_wheel"
B_WORKBENCH      = "workbench"

# Crafting station IDs
STATION_HANDS    = None
STATION_BASIC    = "basic"
STATION_FIRE     = "fire"
STATION_ROAST    = "roast"
STATION_SPIN     = "spin"
STATION_BENCH    = "bench"
STATION_WATER    = "water"

# ── Tile types ──────────────────────────────────────────────
TILE_GRASS       = 0
TILE_DIRT        = 1
TILE_WATER       = 2
TILE_STONE       = 3
TILE_SAND        = 4
TILE_MUD         = 5
TILE_LEAVES      = 6
TILE_CLOVER      = 7
TILE_DRY_GRASS   = 8
TILE_GRAVEL      = 9

# ── Colors (Ursina Vec4 tuples converted at runtime) ────────
COL_GRASS       = (0.35, 0.58, 0.22, 1)
COL_DARK_GRASS  = (0.20, 0.40, 0.12, 1)
COL_DIRT        = (0.55, 0.38, 0.20, 1)
COL_WATER       = (0.15, 0.42, 0.75, 1)
COL_STONE       = (0.50, 0.50, 0.52, 1)
COL_SAND        = (0.85, 0.78, 0.52, 1)
COL_MUD         = (0.40, 0.28, 0.14, 1)
COL_LEAVES      = (0.25, 0.50, 0.15, 1)
COL_CLOVER      = (0.20, 0.65, 0.28, 1)
COL_DRY_GRASS   = (0.70, 0.60, 0.24, 1)
COL_GRAVEL      = (0.55, 0.53, 0.50, 1)
COL_BARK        = (0.45, 0.30, 0.12, 1)
COL_PEBBLE      = (0.55, 0.55, 0.58, 1)
COL_FIBER       = (0.45, 0.70, 0.25, 1)
COL_MUSHROOM    = (0.80, 0.55, 0.38, 1)
COL_BERRY       = (0.75, 0.12, 0.30, 1)
COL_ACORN       = (0.60, 0.40, 0.16, 1)
COL_SPRIG       = (0.30, 0.65, 0.18, 1)
COL_ANT         = (0.65, 0.35, 0.12, 1)
COL_SPIDER      = (0.18, 0.14, 0.22, 1)
COL_LADYBUG     = (0.82, 0.15, 0.15, 1)
COL_STINKBUG    = (0.35, 0.55, 0.20, 1)
COL_FIRE        = (1.00, 0.55, 0.05, 1)
COL_ICE         = (0.55, 0.85, 1.00, 1)
COL_POISON      = (0.40, 0.80, 0.30, 1)
COL_GOLD        = (1.00, 0.84, 0.00, 1)
COL_WHITE       = (1.00, 1.00, 1.00, 1)
COL_BLACK       = (0.00, 0.00, 0.00, 1)
COL_RED         = (0.86, 0.20, 0.20, 1)
COL_LIME        = (0.20, 0.90, 0.25, 1)
COL_CYAN        = (0.10, 0.80, 0.85, 1)
COL_PURPLE      = (0.55, 0.15, 0.75, 1)
COL_ORANGE      = (1.00, 0.55, 0.10, 1)
COL_YELLOW      = (1.00, 0.85, 0.10, 1)
COL_BLUE        = (0.15, 0.45, 0.90, 1)
COL_PINK        = (1.00, 0.45, 0.70, 1)
COL_TEAL        = (0.10, 0.65, 0.55, 1)
COL_BROWN       = (0.55, 0.35, 0.15, 1)
COL_TAN         = (0.82, 0.70, 0.50, 1)
COL_SILVER      = (0.75, 0.75, 0.78, 1)
COL_PEACH       = (1.00, 0.78, 0.60, 1)
COL_CREAM       = (1.00, 0.98, 0.82, 1)
COL_DARK_RED    = (0.55, 0.05, 0.05, 1)
COL_DARK_BLUE   = (0.05, 0.12, 0.45, 1)
COL_HEALTH      = COL_RED
COL_STAMINA     = COL_BLUE
COL_HUNGER      = COL_ORANGE
COL_THIRST      = (0.20, 0.60, 1.00, 1)
COL_XP          = COL_PURPLE
COL_UI_BG       = (0.08, 0.08, 0.12, 0.88)
COL_UI_BORDER   = (0.35, 0.35, 0.42, 1)
COL_SLOT_BG     = (0.16, 0.16, 0.22, 1)
COL_SLOT_SEL    = (0.28, 0.42, 0.75, 1)
COL_SLOT_HOVER  = (0.24, 0.30, 0.50, 1)
COL_TEXT        = COL_WHITE
COL_TEXT_DIM    = (0.70, 0.70, 0.75, 1)
COL_NOTIFY_BG   = (0.05, 0.05, 0.08, 0.80)

TILE_COLORS = {
    TILE_GRASS:     COL_GRASS,
    TILE_DIRT:      COL_DIRT,
    TILE_WATER:     COL_WATER,
    TILE_STONE:     COL_STONE,
    TILE_SAND:      COL_SAND,
    TILE_MUD:       COL_MUD,
    TILE_LEAVES:    COL_LEAVES,
    TILE_CLOVER:    COL_CLOVER,
    TILE_DRY_GRASS: COL_DRY_GRASS,
    TILE_GRAVEL:    COL_GRAVEL,
}

# ── Enemy type IDs ──────────────────────────────────────────
E_WORKER_ANT   = "worker_ant"
E_FIRE_ANT     = "fire_ant"
E_SOLDIER_ANT  = "soldier_ant"
E_SPIDER       = "orb_weaver"
E_WOLF_SPIDER  = "wolf_spider"
E_LADYBUG      = "ladybug"
E_STINKBUG     = "stinkbug"
E_BOMBARDIER   = "bombardier"
E_WEEVIL       = "weevil"
E_APHID        = "aphid"
E_GNAT         = "gnat"
E_MOSQUITO     = "mosquito"
E_CRICKET      = "cricket"

# ── Resource type IDs ───────────────────────────────────────
R_GRASS_BLADE  = "grass_blade"
R_DRY_GRASS    = "dry_grass"
R_PEBBLE       = "pebble"
R_QUARTZITE    = "quartzite"
R_ACORN        = "acorn"
R_SPRIG        = "sprig"
R_MUSHROOM     = "mushroom"
R_BERRY        = "berry"
R_CLOVER       = "clover"
R_STEM         = "stem"
R_TWIG         = "twig"
R_CLAY         = "clay"
R_SAP          = "sap"
R_DEW          = "dew"
R_THISTLE      = "thistle"
R_FLOWER       = "flower"
R_DANDELION    = "dandelion"
R_APHID_FARM   = "aphid_farm"

# ── Status effects ──────────────────────────────────────────
SE_POISON      = "poison"
SE_BURN        = "burn"
SE_STINK       = "stink"
SE_SLOW        = "slow"
SE_STUN        = "stun"
SE_BLEED       = "bleed"
SE_REGEN       = "regen"
SE_BOOST_ATK   = "boost_atk"
SE_BOOST_DEF   = "boost_def"
SE_BOOST_SPD   = "boost_spd"

# ── Game states ─────────────────────────────────────────────
GS_LOADING     = "loading"
GS_MAIN_MENU   = "main_menu"
GS_PLAYING     = "playing"
GS_INVENTORY   = "inventory"
GS_CRAFTING    = "crafting"
GS_BUILDING    = "building"
GS_CHEST       = "chest"
GS_PAUSED      = "paused"
GS_DEAD        = "dead"
GS_SETTINGS    = "settings"

# ── Audio cue IDs ───────────────────────────────────────────
SFX_HIT        = "hit"
SFX_COLLECT    = "collect"
SFX_CRAFT      = "craft"
SFX_BUILD      = "build"
SFX_EAT        = "eat"
SFX_WALK_GRASS = "walk_grass"
SFX_WALK_STONE = "walk_stone"
SFX_ENEMY_DIE  = "enemy_die"
SFX_PLAYER_HIT = "player_hit"
SFX_LEVEL_UP   = "level_up"
SFX_SWING      = "swing"
