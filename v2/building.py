# ============================================================
#  BACKYARD SURVIVAL v2  –  Building System
# ============================================================
from __future__ import annotations
import math
from typing import Optional, List, Dict, TYPE_CHECKING
from constants import *
from world import BUILDING_COSTS, BUILDING_CATEGORY_MAP, STRUCTURE_DEFS
from items import make

if TYPE_CHECKING:
    from world import World, Structure
    from player import Player


BUILD_CAT_NAMES = list(BUILDING_CATEGORY_MAP.keys())

BUILDING_NAMES: Dict[str, str] = {
    btype: STRUCTURE_DEFS[btype]["name"]
    for btype in STRUCTURE_DEFS
}


class BuildingSystem:
    """Manages building placement, demolition, and menu state."""

    def __init__(self, world: "World"):
        self.world           = world
        self.active          = False
        self.demolish_mode   = False
        self.selected_cat    = 0
        self.selected_index  = 0
        # Blueprint state
        self.blueprint_tx    = -1
        self.blueprint_tz    = -1
        self.blueprint_valid = False
        # Rotation (0=N,1=E,2=S,3=W) for walls/ramps
        self.rotation        = 0

    # ── Selection ────────────────────────────────────────────────────────
    @property
    def current_category(self) -> str:
        return BUILD_CAT_NAMES[self.selected_cat % len(BUILD_CAT_NAMES)]

    @property
    def current_items(self) -> List[str]:
        return BUILDING_CATEGORY_MAP[self.current_category]

    @property
    def selected_type(self) -> Optional[str]:
        items = self.current_items
        if not items or self.selected_index >= len(items):
            return None
        return items[self.selected_index]

    def next_category(self):
        self.selected_cat   = (self.selected_cat + 1) % len(BUILD_CAT_NAMES)
        self.selected_index = 0

    def prev_category(self):
        self.selected_cat   = (self.selected_cat - 1) % len(BUILD_CAT_NAMES)
        self.selected_index = 0

    def next_item(self):
        items = self.current_items
        if items:
            self.selected_index = (self.selected_index + 1) % len(items)

    def prev_item(self):
        items = self.current_items
        if items:
            self.selected_index = (self.selected_index - 1) % len(items)

    def rotate(self):
        self.rotation = (self.rotation + 1) % 4

    # ── Blueprint ────────────────────────────────────────────────────────
    def update_blueprint(self, wx: float, wz: float, player: "Player"):
        """Given mouse world-XZ, update the blueprint tile position."""
        self.blueprint_tx = int(wx / self.world.scale)
        self.blueprint_tz = int(wz / self.world.scale)

        stype = self.selected_type
        if stype is None:
            self.blueprint_valid = False
            return

        # Tile must be valid
        tile = self.world.tile_at(self.blueprint_tx, self.blueprint_tz)
        if tile == TILE_WATER:
            self.blueprint_valid = False
            return

        # Not already occupied
        if (self.blueprint_tx, self.blueprint_tz) in self.world.structures:
            self.blueprint_valid = False
            return

        # Check bounds
        if not (0 <= self.blueprint_tx < self.world.size and
                0 <= self.blueprint_tz < self.world.size):
            self.blueprint_valid = False
            return

        # Affordability
        self.blueprint_valid = self._can_afford(player, stype)

    def _can_afford(self, player: "Player", stype: str) -> bool:
        cost = BUILDING_COSTS.get(stype, {})
        for item_id, count in cost.items():
            if player.inv.count(item_id) < count:
                return False
        return True

    def get_cost(self, stype: str) -> Dict[str, int]:
        return BUILDING_COSTS.get(stype, {})

    def get_missing(self, player: "Player", stype: str) -> Dict[str, tuple]:
        """Returns {item_id: (have, need)} for items where have < need."""
        missing = {}
        for item_id, need in BUILDING_COSTS.get(stype, {}).items():
            have = player.inv.count(item_id)
            if have < need:
                missing[item_id] = (have, need)
        return missing

    # ── Place ─────────────────────────────────────────────────────────────
    def place(self, player: "Player") -> Optional["Structure"]:
        stype = self.selected_type
        if stype is None or not self.blueprint_valid:
            return None

        cost = BUILDING_COSTS.get(stype, {})
        for item_id, count in cost.items():
            player.inv.remove(item_id, count)

        struct = self.world.place_structure(
            self.blueprint_tx, self.blueprint_tz, stype)
        if struct:
            player.structures_built += 1
            player.gain_xp(6)
        return struct

    # ── Demolish ──────────────────────────────────────────────────────────
    def demolish(self, tx: int, tz: int, player: "Player") -> bool:
        struct = self.world.structures.get((tx, tz))
        if not struct:
            return False
        stype = struct.btype
        # Refund 60% of materials
        cost = BUILDING_COSTS.get(stype, {})
        for item_id, count in cost.items():
            refund = max(1, int(count * 0.6))
            player.inv.add(make(item_id, refund))
        self.world.remove_structure(tx, tz)
        return True

    def demolish_at_world(self, wx: float, wz: float, player: "Player") -> bool:
        tx = int(wx / self.world.scale)
        tz = int(wz / self.world.scale)
        return self.demolish(tx, tz, player)

    # ── Info helpers ──────────────────────────────────────────────────────
    def structure_info(self, struct: "Structure") -> dict:
        data = STRUCTURE_DEFS.get(struct.btype, {})
        return {
            "name":       data.get("name", struct.btype),
            "hp":         struct.health,
            "max_hp":     struct.max_health,
            "is_station": struct.is_station,
            "station_id": struct.station_id,
            "is_storage": struct.is_storage,
        }
