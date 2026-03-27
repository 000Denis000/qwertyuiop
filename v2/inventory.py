# ============================================================
#  BACKYARD SURVIVAL v2  –  Inventory System
# ============================================================
from __future__ import annotations
from typing import Optional, List, Tuple, Dict
from constants import *
from items import Item, make


class Slot:
    """One grid slot that holds either nothing or an Item stack."""
    __slots__ = ("item",)

    def __init__(self):
        self.item: Optional[Item] = None

    def is_empty(self) -> bool:
        return self.item is None or self.item.is_empty()

    def clear(self):
        self.item = None

    def put(self, item: Item) -> int:
        """Put item into slot. Returns overflow."""
        if self.item is None or self.item.is_empty():
            self.item = item
            return 0
        if self.item.item_id == item.item_id:
            return self.item.add(item.count)
        return item.count  # different item — no merge

    def take(self, count: int = None) -> Optional[Item]:
        """Take count (or all) from slot. Returns item taken."""
        if self.item is None or self.item.is_empty():
            return None
        if count is None or count >= self.item.count:
            taken = self.item
            self.item = None
            return taken
        taken = self.item.clone(count)
        self.item.remove(count)
        return taken

    def take_half(self) -> Optional[Item]:
        if self.item is None or self.item.is_empty():
            return None
        half = max(1, self.item.count // 2)
        return self.take(half)

    def __repr__(self):
        return f"<Slot {self.item}>"


class Grid:
    """A 2-D grid of Slots."""

    def __init__(self, rows: int, cols: int):
        self.rows  = rows
        self.cols  = cols
        self.slots = [[Slot() for _ in range(cols)] for _ in range(rows)]

    def slot_at(self, row: int, col: int) -> Optional[Slot]:
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.slots[row][col]
        return None

    def flat(self) -> List[Slot]:
        return [self.slots[r][c] for r in range(self.rows) for c in range(self.cols)]

    def add_item(self, item: Item) -> int:
        """Stack first, then empty slot. Returns leftover count."""
        remaining = item.count
        # 1. Try stacking on existing same-id slots
        for s in self.flat():
            if not s.is_empty() and s.item.item_id == item.item_id:
                space = s.item.max_stack - s.item.count
                if space > 0:
                    add = min(remaining, space)
                    s.item.count += add
                    remaining    -= add
                    if remaining == 0:
                        return 0
        # 2. Try empty slots
        for s in self.flat():
            if s.is_empty():
                take = min(remaining, item.max_stack)
                s.item = make(item.item_id, take)
                remaining -= take
                if remaining == 0:
                    return 0
        return remaining

    def remove_item(self, item_id: str, count: int) -> bool:
        have = self.count_item(item_id)
        if have < count:
            return False
        remaining = count
        for s in self.flat():
            if not s.is_empty() and s.item.item_id == item_id:
                take = min(remaining, s.item.count)
                s.item.remove(take)
                remaining -= take
                if s.item.is_empty():
                    s.clear()
                if remaining == 0:
                    return True
        return True

    def count_item(self, item_id: str) -> int:
        return sum(s.item.count for s in self.flat()
                   if not s.is_empty() and s.item.item_id == item_id)

    def has_item(self, item_id: str, count: int = 1) -> bool:
        return self.count_item(item_id) >= count

    def clear_slot(self, row: int, col: int):
        s = self.slot_at(row, col)
        if s:
            s.clear()

    def swap(self, r1: int, c1: int, r2: int, c2: int):
        a = self.slot_at(r1, c1)
        b = self.slot_at(r2, c2)
        if a and b:
            a.item, b.item = b.item, a.item

    def serialize(self) -> list:
        out = []
        for r in range(self.rows):
            row_data = []
            for c in range(self.cols):
                s = self.slots[r][c]
                if s.is_empty():
                    row_data.append(None)
                else:
                    row_data.append({"id": s.item.item_id, "count": s.item.count})
            out.append(row_data)
        return out

    def deserialize(self, data: list):
        for r, row in enumerate(data):
            for c, cell in enumerate(row):
                s = self.slot_at(r, c)
                if s is None:
                    continue
                if cell is None:
                    s.clear()
                else:
                    s.item = make(cell["id"], cell["count"])


class EquipmentSlots:
    """Named equipment slots (head, chest, legs, feet, weapon, offhand)."""

    def __init__(self):
        self._slots: Dict[str, Optional[Item]] = {slot: None for slot in ALL_EQUIP_SLOTS}

    def equip(self, item: Item) -> Optional[Item]:
        """Equip item. Returns previously equipped item (or None)."""
        slot_id = item.equip_slot
        if slot_id not in self._slots:
            return item  # can't equip
        prev = self._slots[slot_id]
        self._slots[slot_id] = item
        return prev

    def unequip(self, slot_id: str) -> Optional[Item]:
        if slot_id not in self._slots:
            return None
        item = self._slots[slot_id]
        self._slots[slot_id] = None
        return item

    def get(self, slot_id: str) -> Optional[Item]:
        return self._slots.get(slot_id)

    def weapon(self) -> Optional[Item]:
        return self._slots[ESLOT_WEAPON]

    def offhand(self) -> Optional[Item]:
        return self._slots[ESLOT_OFFHAND]

    def head(self) -> Optional[Item]:
        return self._slots[ESLOT_HEAD]

    def chest(self) -> Optional[Item]:
        return self._slots[ESLOT_CHEST]

    def legs(self) -> Optional[Item]:
        return self._slots[ESLOT_LEGS]

    def feet(self) -> Optional[Item]:
        return self._slots[ESLOT_FEET]

    def total_defense(self) -> int:
        total = 0
        for item in self._slots.values():
            if item:
                total += item.defense
        return total

    def total_speed_bonus(self) -> float:
        bonus = 0.0
        for item in self._slots.values():
            if item:
                bonus += item.speed_bonus
        return bonus

    def total_bonus(self, stat: str) -> float:
        total = 0.0
        for item in self._slots.values():
            if item and item.equip_bonus:
                total += item.equip_bonus.get(stat, 0.0)
        return total

    def items(self) -> List[Item]:
        return [v for v in self._slots.values() if v is not None]

    def serialize(self) -> dict:
        out = {}
        for k, v in self._slots.items():
            if v:
                out[k] = {"id": v.item_id, "count": v.count}
            else:
                out[k] = None
        return out

    def deserialize(self, data: dict):
        for k, v in data.items():
            if v:
                self._slots[k] = make(v["id"], v["count"])
            else:
                self._slots[k] = None


class Hotbar:
    """The hotbar — a flat list of HOTBAR_SLOTS slots."""

    def __init__(self):
        self.slots   = [Slot() for _ in range(HOTBAR_SLOTS)]
        self.active  = 0   # currently selected index

    def select(self, index: int):
        self.active = max(0, min(HOTBAR_SLOTS - 1, index))

    def next(self):
        self.active = (self.active + 1) % HOTBAR_SLOTS

    def prev(self):
        self.active = (self.active - 1) % HOTBAR_SLOTS

    def active_item(self) -> Optional[Item]:
        s = self.slots[self.active]
        return s.item if not s.is_empty() else None

    def add_item(self, item: Item) -> int:
        """Try to add to hotbar. Returns leftover."""
        remaining = item.count
        # Stack existing
        for s in self.slots:
            if not s.is_empty() and s.item.item_id == item.item_id:
                space = s.item.max_stack - s.item.count
                if space > 0:
                    add = min(remaining, space)
                    s.item.count += add
                    remaining    -= add
                    if remaining == 0:
                        return 0
        # Empty slot
        for s in self.slots:
            if s.is_empty():
                take = min(remaining, item.max_stack)
                s.item = make(item.item_id, take)
                remaining -= take
                if remaining == 0:
                    return 0
        return remaining

    def remove_item(self, item_id: str, count: int = 1) -> bool:
        remaining = count
        for s in self.slots:
            if not s.is_empty() and s.item.item_id == item_id:
                take = min(remaining, s.item.count)
                s.item.remove(take)
                remaining -= take
                if s.item.is_empty():
                    s.clear()
                if remaining == 0:
                    return True
        return remaining == 0

    def count_item(self, item_id: str) -> int:
        return sum(s.item.count for s in self.slots
                   if not s.is_empty() and s.item.item_id == item_id)

    def serialize(self) -> list:
        out = []
        for s in self.slots:
            if s.is_empty():
                out.append(None)
            else:
                out.append({"id": s.item.item_id, "count": s.item.count})
        return out

    def deserialize(self, data: list):
        for i, cell in enumerate(data):
            if i >= len(self.slots):
                break
            if cell is None:
                self.slots[i].clear()
            else:
                self.slots[i].item = make(cell["id"], cell["count"])


class PlayerInventory:
    """
    Top-level inventory container for the player.
    Holds: hotbar, main grid, equipment slots.
    """

    def __init__(self):
        self.hotbar    = Hotbar()
        self.grid      = Grid(INV_ROWS, INV_COLS)
        self.equipment = EquipmentSlots()

    # ── Add / Remove ──────────────────────────────────────────────────────
    def add(self, item: Item) -> int:
        """Add to hotbar first, then grid. Returns leftover."""
        leftover = self.hotbar.add_item(item)
        if leftover > 0:
            temp = make(item.item_id, leftover)
            leftover = self.grid.add_item(temp)
        return leftover

    def add_many(self, items: List[Item]) -> List[Item]:
        """Add a list of items. Returns list of items that couldn't fit."""
        overflow = []
        for item in items:
            leftover = self.add(item)
            if leftover > 0:
                overflow.append(make(item.item_id, leftover))
        return overflow

    def remove(self, item_id: str, count: int = 1) -> bool:
        have = self.count(item_id)
        if have < count:
            return False
        rem = count
        # Hotbar first
        hb_have = self.hotbar.count_item(item_id)
        if hb_have > 0:
            take = min(rem, hb_have)
            self.hotbar.remove_item(item_id, take)
            rem -= take
        # Grid
        if rem > 0:
            self.grid.remove_item(item_id, rem)
        return True

    def count(self, item_id: str) -> int:
        return self.hotbar.count_item(item_id) + self.grid.count_item(item_id)

    def has(self, item_id: str, count: int = 1) -> bool:
        return self.count(item_id) >= count

    # ── Equipment ─────────────────────────────────────────────────────────
    def equip_from_grid(self, row: int, col: int) -> bool:
        slot = self.grid.slot_at(row, col)
        if not slot or slot.is_empty():
            return False
        item = slot.item
        if item.equip_slot is None:
            return False
        prev = self.equipment.equip(item)
        slot.clear()
        if prev:
            leftover = self.grid.add_item(prev)
            if leftover > 0:
                leftover = self.hotbar.add_item(prev)
        return True

    def equip_from_hotbar(self, index: int) -> bool:
        s = self.hotbar.slots[index]
        if s.is_empty():
            return False
        item = s.item
        if item.equip_slot is None:
            return False
        prev = self.equipment.equip(item)
        s.clear()
        if prev:
            leftover = self.hotbar.add_item(prev)
            if leftover > 0:
                self.grid.add_item(prev)
        return True

    def unequip(self, slot_id: str) -> bool:
        item = self.equipment.unequip(slot_id)
        if item is None:
            return False
        leftover = self.add(item)
        return True

    # ── Shortcuts ─────────────────────────────────────────────────────────
    @property
    def weapon(self):
        # Equipped weapon takes priority, then hotbar active
        w = self.equipment.weapon()
        if w:
            return w
        return self.hotbar.active_item()

    @property
    def offhand(self):
        return self.equipment.offhand()

    @property
    def defense(self) -> int:
        return self.equipment.total_defense()

    @property
    def speed_bonus(self) -> float:
        return self.equipment.total_speed_bonus()

    # ── Serialization ─────────────────────────────────────────────────────
    def serialize(self) -> dict:
        return {
            "hotbar":    self.hotbar.serialize(),
            "grid":      self.grid.serialize(),
            "equipment": self.equipment.serialize(),
        }

    def deserialize(self, data: dict):
        if "hotbar" in data:
            self.hotbar.deserialize(data["hotbar"])
        if "grid" in data:
            self.grid.deserialize(data["grid"])
        if "equipment" in data:
            self.equipment.deserialize(data["equipment"])
