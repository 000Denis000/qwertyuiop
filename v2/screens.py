# ============================================================
#  BACKYARD SURVIVAL v2  –  Screen overlays (inventory,
#  crafting, building, pause, death)
# ============================================================
from __future__ import annotations
import math
from typing import Optional, List, TYPE_CHECKING
from ursina import (
    Entity, Text, Button, camera, color, Vec2,
    destroy, mouse, held_keys, invoke
)
from constants import *
from items import Item, make, ITEM_REGISTRY
from crafting import RECIPE_CATEGORIES, RECIPES_BY_CATEGORY
from world import BUILDING_CATEGORY_MAP, BUILDING_COSTS, STRUCTURE_DEFS
from building import BUILDING_NAMES

if TYPE_CHECKING:
    from player import Player
    from crafting import CraftingSystem
    from building import BuildingSystem


def _col(c: tuple):
    return color.rgba(*[int(v*255) for v in c])


def _panel(parent, x, y, w, h, col=None, z=0.0):
    bg_col = col or _col(COL_UI_BG)
    e = Entity(parent=parent, model="quad", color=bg_col,
               position=(x, y, z), scale=(w, h))
    border = Entity(parent=parent, model="quad",
                    color=_col(COL_UI_BORDER),
                    position=(x, y, z-0.01),
                    scale=(w+0.005, h+0.005),
                    wire=False)
    return e, border


def _text(parent, txt, x, y, scale=0.7, col=None, origin=(0,0)):
    return Text(txt, parent=parent, position=(x, y),
                scale=scale, color=col or color.white,
                origin=origin)


def _item_icon_color(item: Optional[Item]):
    if item is None:
        return color.clear
    return _col(item.color)


class InventoryScreen:
    """Full inventory + equipment overlay."""

    SLOT_W = 0.078
    SLOT_H = 0.078
    GAP    = 0.005

    def __init__(self):
        self.ui       = Entity(parent=camera.ui)
        self.entities = []
        self._slots_grid   = []   # list of {bg, icon, count_t, row, col}
        self._slots_hotbar = []
        self._slots_equip  = {}   # slot_id -> {bg, icon, label}
        self._built = False

    def _clear(self):
        for e in self.entities:
            destroy(e)
        self.entities.clear()
        self._slots_grid.clear()
        self._slots_hotbar.clear()
        self._slots_equip.clear()

    def show(self, player: "Player"):
        self._clear()
        p = self.ui
        W, H = self.SLOT_W, self.SLOT_H
        G = self.GAP

        # Background overlay
        overlay = Entity(parent=p, model="quad",
                          color=color.rgba(0,0,0,160),
                          scale=(2,2), position=(0,0,0.1))
        self.entities.append(overlay)

        # ── Main grid panel ─────────────────────────────────────────────
        cols, rows = INV_COLS, INV_ROWS
        grid_w = cols*(W+G)
        grid_h = rows*(H+G)
        panel_w, panel_h = grid_w+0.04, grid_h+0.08

        bg, bdr = _panel(p, -0.15, 0, panel_w, panel_h, z=0.05)
        self.entities += [bg, bdr]
        _text(p, "INVENTORY", -0.15, panel_h/2-0.03, 0.75,
              color.white, (0,0)).parent = p
        self.entities.append(_text(p, "INVENTORY", -0.15,
                                    panel_h/2-0.03, 0.75))

        start_x = -0.15 - grid_w/2 + W/2 + G/2
        start_y = grid_h/2 - H/2 - 0.04

        for r in range(rows):
            row_data = []
            for c in range(cols):
                sx = start_x + c*(W+G)
                sy = start_y - r*(H+G)
                bg_s = Entity(parent=p, model="quad",
                               color=_col(COL_SLOT_BG),
                               position=(sx, sy, 0.06),
                               scale=(W, H))
                bdr_s = Entity(parent=p, model="quad",
                                color=_col(COL_UI_BORDER),
                                position=(sx, sy, 0.055),
                                scale=(W+0.003, H+0.003))
                icon_e = Entity(parent=p, model="quad",
                                 color=color.clear,
                                 position=(sx, sy, 0.07),
                                 scale=(W*0.62, H*0.62))
                cnt_t  = Text("", parent=p,
                               position=(sx+W*0.38, sy-H*0.35),
                               scale=0.45, color=color.white,
                               origin=(0.5, 0))
                self.entities += [bg_s, bdr_s, icon_e, cnt_t]
                row_data.append({"bg":bg_s,"bdr":bdr_s,"icon":icon_e,
                                  "count":cnt_t,"row":r,"col":c})
            self._slots_grid.append(row_data)

        # ── Equipment panel (right) ──────────────────────────────────────
        eq_x, eq_y = 0.38, 0.05
        eq_bg, eq_bdr = _panel(p, eq_x, eq_y, 0.26, panel_h, z=0.05)
        self.entities += [eq_bg, eq_bdr]
        self.entities.append(_text(p, "EQUIPPED", eq_x, panel_h/2-0.03,
                                    0.65, color.white, (0,0)))

        equip_order = [
            (ESLOT_HEAD,    "Head",    eq_x, 0.22),
            (ESLOT_CHEST,   "Chest",   eq_x, 0.12),
            (ESLOT_LEGS,    "Legs",    eq_x, 0.02),
            (ESLOT_FEET,    "Feet",    eq_x,-0.08),
            (ESLOT_WEAPON,  "Weapon",  eq_x,-0.18),
            (ESLOT_OFFHAND, "Offhand", eq_x,-0.28),
        ]
        for slot_id, label, ex, ey in equip_order:
            lbl = _text(p, label, ex-0.08, ey+H*0.55+0.005, 0.52,
                         color.light_gray, (0,0))
            bg_s = Entity(parent=p, model="quad",
                           color=_col(COL_SLOT_BG),
                           position=(ex, ey, 0.06), scale=(W, H))
            bdr_s= Entity(parent=p, model="quad",
                           color=_col(COL_UI_BORDER),
                           position=(ex, ey, 0.055),
                           scale=(W+0.003, H+0.003))
            icon_e= Entity(parent=p, model="quad",
                            color=color.clear,
                            position=(ex, ey, 0.07),
                            scale=(W*0.62, H*0.62))
            self.entities += [lbl, bg_s, bdr_s, icon_e]
            self._slots_equip[slot_id] = {"bg":bg_s,"icon":icon_e}

        # ── Stats panel (left) ───────────────────────────────────────────
        st_x = -0.60
        st_bg, st_bdr = _panel(p, st_x, eq_y, 0.22, panel_h, z=0.05)
        self.entities += [st_bg, st_bdr]
        self.entities.append(_text(p, "STATS", st_x, panel_h/2-0.03,
                                    0.65, color.white, (0,0)))
        stats = [
            (f"Level    {player.level}",        COL_XP),
            (f"XP  {player.xp}/{player.xp_to_next}", COL_XP),
            (f"HP  {int(player.health)}/{int(player.max_health)}", COL_HEALTH),
            (f"SP  {int(player.stamina)}/{int(player.max_stamina)}", COL_STAMINA),
            (f"HNG {int(player.hunger)}/{int(player.max_hunger)}", COL_HUNGER),
            (f"THR {int(player.thirst)}/{int(player.max_thirst)}", COL_THIRST),
            ("", COL_WHITE),
            (f"DEF {int(player.defense)}", COL_CYAN),
        ]
        weapon = player.inv.weapon
        if weapon:
            stats.append((f"DMG {weapon.damage}", COL_RED))
        for i, (txt, col_t) in enumerate(stats):
            t = _text(p, txt, st_x-0.08, panel_h/2-0.07 - i*0.038,
                       0.50, _col(col_t), (0,0))
            self.entities.append(t)

        # Hint
        hint = _text(p, "[I] Close  |  Click item to equip/use",
                      0, -panel_h/2-0.02, 0.50, color.gray, (0,0))
        self.entities.append(hint)

        self._refresh_items(player)

    def _refresh_items(self, player: "Player"):
        # Grid
        for r, row in enumerate(self._slots_grid):
            for c, slot_d in enumerate(row):
                item = player.inv.grid.slots[r][c].item
                if item and not item.is_empty():
                    slot_d["icon"].color = _col(item.color)
                    slot_d["count"].text = (str(item.count)
                                            if item.max_stack > 1 else "")
                else:
                    slot_d["icon"].color = color.clear
                    slot_d["count"].text = ""
        # Equipment
        for slot_id, slot_d in self._slots_equip.items():
            item = player.inv.equipment.get(slot_id)
            slot_d["icon"].color = (_col(item.color) if item
                                    else _col((0.28,0.28,0.32,0.5)))

    def hide(self):
        self._clear()

    def update(self, player: "Player"):
        if self._slots_grid:
            self._refresh_items(player)


class CraftingScreen:
    """Crafting menu overlay."""

    def __init__(self):
        self.ui       = Entity(parent=camera.ui)
        self.entities = []
        self._recipe_buttons = []
        self._built = False

    def _clear(self):
        for e in self.entities:
            destroy(e)
        self.entities.clear()
        self._recipe_buttons.clear()

    def show(self, player: "Player", crafting: "CraftingSystem"):
        self._clear()
        p  = self.ui
        pw = 0.88
        ph = 0.72
        overlay = Entity(parent=p, model="quad",
                          color=color.rgba(0,0,0,160),
                          scale=(2,2), position=(0,0,0.1))
        self.entities.append(overlay)
        main_bg, _ = _panel(p, 0, 0, pw, ph, z=0.05)
        self.entities += [main_bg, _]

        # Title
        t = _text(p, "CRAFTING", 0, ph/2-0.03, 0.80,
                   color.white, (0,0))
        self.entities.append(t)

        # Station indicator
        stn = crafting.active_station
        stn_str = f"Station: {stn.upper()}" if stn else "Station: None (hands only)"
        stn_col = _col(COL_CYAN) if stn else color.gray
        self.entities.append(_text(p, stn_str, 0, ph/2-0.065,
                                    0.55, stn_col, (0,0)))

        # Category tabs
        tab_y  = ph/2 - 0.105
        tab_w  = pw / len(RECIPE_CATEGORIES)
        cat_x0 = -pw/2 + tab_w/2
        for i, cat in enumerate(RECIPE_CATEGORIES):
            tx   = cat_x0 + i*tab_w
            is_s = (i == crafting.selected_cat)
            col_t= _col(COL_SLOT_SEL) if is_s else _col(COL_SLOT_BG)
            bg   = Entity(parent=p, model="quad", color=col_t,
                           position=(tx, tab_y, 0.06),
                           scale=(tab_w-0.004, 0.03))
            lbl  = _text(p, cat[:8].upper(), tx, tab_y-0.004,
                          0.48, color.white, (0,0))
            self.entities += [bg, lbl]

        # Recipe list panel
        list_x  = -pw/2 + 0.17
        list_y  =  tab_y - 0.04
        LIST_H  = ph - 0.18
        list_bg, _ = _panel(p, list_x, list_y - LIST_H/2 + 0.01,
                             0.32, LIST_H, z=0.055)
        self.entities += [list_bg, _]

        recipes = crafting.visible_recipes(player)
        ROW_H   = 0.058
        VIS     = 9
        start   = crafting.scroll_offset
        for idx in range(start, min(start+VIS, len(recipes))):
            rec = recipes[idx]
            ry  = list_y - (idx - start)*ROW_H
            is_s = (idx == crafting.selected_index)
            can  = rec.can_craft(player.inv, crafting.active_station)
            row_col = (_col(COL_SLOT_SEL) if is_s else _col(COL_SLOT_BG))
            bg_r = Entity(parent=p, model="quad", color=row_col,
                           position=(list_x, ry, 0.06),
                           scale=(0.30, ROW_H-0.005))
            icon = Entity(parent=p, model="quad",
                           color=_col(rec.color),
                           position=(list_x-0.11, ry, 0.07),
                           scale=(ROW_H*0.55, ROW_H*0.55))
            name_col = color.white if can else color.gray
            nm = _text(p, rec.name[:20], list_x-0.02, ry+0.01,
                        0.52, name_col, (0,0))
            cnt = _text(p, f"x{rec.result_count}",
                         list_x+0.10, ry-0.01, 0.46, _col(COL_YELLOW), (0,0))
            self.entities += [bg_r, icon, nm, cnt]
            self._recipe_buttons.append(idx)

        # Recipe detail panel
        det_x   = pw/2 - 0.20
        det_y   = list_y - 0.02
        det_bg, _ = _panel(p, det_x, det_y - LIST_H/2 + 0.01,
                            0.38, LIST_H, z=0.055)
        self.entities += [det_bg, _]

        rec = crafting.selected_recipe(player.inv)
        if rec:
            # Result icon
            res_icon = Entity(parent=p, model="quad",
                               color=_col(rec.color),
                               position=(det_x-0.12, det_y-0.02, 0.07),
                               scale=(0.07, 0.07))
            res_name = _text(p, rec.name, det_x-0.04, det_y-0.01,
                              0.58, color.white, (0,0))
            res_cnt  = _text(p, f"Produces x{rec.result_count}",
                              det_x-0.04, det_y-0.042, 0.50,
                              _col(COL_YELLOW), (0,0))
            self.entities += [res_icon, res_name, res_cnt]

            # Description
            desc = ITEM_REGISTRY.get(rec.result_id, {}).get("desc","")
            if desc:
                self.entities.append(
                    _text(p, desc[:40], det_x-0.17, det_y-0.075,
                           0.46, color.gray, (0,0))
                )

            # Ingredients
            ing_title = _text(p, "REQUIRES:", det_x-0.17, det_y-0.115,
                               0.52, color.light_gray, (0,0))
            self.entities.append(ing_title)
            for j, (iid, need) in enumerate(rec.ingredients.items()):
                have    = player.inv.count(iid)
                ok      = have >= need
                ing_col = _col(COL_LIME) if ok else _col(COL_RED)
                iname   = ITEM_REGISTRY.get(iid,{}).get("name",iid)
                ing_t   = _text(p, f"  {iname}: {have}/{need}",
                                  det_x-0.17, det_y-0.14 - j*0.033,
                                  0.48, ing_col, (0,0))
                self.entities.append(ing_t)

            # Station requirement
            if rec.station:
                stn_ok = crafting.active_station == rec.station
                stn_c  = _col(COL_CYAN) if stn_ok else _col(COL_RED)
                self.entities.append(
                    _text(p, f"Needs station: {rec.station.upper()}",
                           det_x-0.17, det_y-0.14 - len(rec.ingredients)*0.033 - 0.02,
                           0.48, stn_c, (0,0))
                )

            # Craft button
            can   = rec.can_craft(player.inv, crafting.active_station)
            b_col = _col((0.15,0.55,0.15,1)) if can else _col((0.35,0.15,0.15,1))
            craft_bg = Entity(parent=p, model="quad", color=b_col,
                               position=(det_x, det_y - LIST_H/2 + 0.06, 0.07),
                               scale=(0.30, 0.055))
            craft_t  = _text(p, "CRAFT [ENTER]" if can else "CANNOT CRAFT",
                              det_x, det_y - LIST_H/2 + 0.06,
                              0.55, color.white, (0,0))
            self.entities += [craft_bg, craft_t]

        # Result popup
        if crafting.result_popup:
            item, timer = crafting.result_popup
            alpha = min(1.0, timer)
            pop_col = color.rgba(int(0.2*255), int(0.9*255), int(0.2*255),
                                  int(alpha*220))
            pop_t = _text(p, f"Crafted: {item.name} x{item.count}",
                           0, ph/2 + 0.05, 0.72, pop_col, (0,0))
            self.entities.append(pop_t)

        # Hint
        self.entities.append(
            _text(p, "[C/ESC] Close  |[↑↓] Select  |[←→] Category  |[ENTER] Craft",
                   0, -ph/2-0.025, 0.45, color.gray, (0,0))
        )

    def hide(self):
        self._clear()


class BuildingScreen:
    """Building mode side panel."""

    def __init__(self):
        self.ui       = Entity(parent=camera.ui)
        self.entities = []

    def _clear(self):
        for e in self.entities:
            destroy(e)
        self.entities.clear()

    def show(self, player: "Player", building: "BuildingSystem"):
        self._clear()
        p   = self.ui
        pw  = 0.26
        ph  = 0.78
        px  = 0.82
        py  = 0.0

        bg, bdr = _panel(p, px, py, pw, ph, z=0.05)
        self.entities += [bg, bdr]

        mode_col = _col(COL_RED) if building.demolish_mode else _col(COL_LIME)
        mode_str = "[ DEMOLISH ]" if building.demolish_mode else "[ PLACE ]"
        t = _text(p, mode_str, px, py+ph/2-0.03, 0.60, mode_col, (0,0))
        self.entities.append(t)

        # Category tabs
        cats = list(BUILDING_CATEGORY_MAP.keys())
        tab_h  = ph / (len(cats)+1)
        tab_x0 = px - pw/2 + 0.01
        tab_w  = pw - 0.02

        self.entities.append(
            _text(p, "CATEGORY", px, py+ph/2-0.062, 0.48, color.gray, (0,0))
        )
        for i, cat in enumerate(cats):
            ty   = py + ph/2 - 0.10 - i*0.068
            is_s = (i == building.selected_cat)
            bg_c = _col(COL_SLOT_SEL) if is_s else _col(COL_SLOT_BG)
            bg_e = Entity(parent=p, model="quad", color=bg_c,
                           position=(px, ty, 0.06),
                           scale=(tab_w, 0.060))
            lbl  = _text(p, cat, px, ty-0.003, 0.52, color.white, (0,0))
            self.entities += [bg_e, lbl]

        # Items in current category
        items_y0 = py + ph/2 - 0.10 - len(cats)*0.068 - 0.04
        self.entities.append(
            _text(p, "SELECT:", px, items_y0+0.02, 0.48, color.gray, (0,0))
        )
        for j, btype in enumerate(building.current_items):
            iy    = items_y0 - j*0.068
            is_s  = (j == building.selected_index)
            can   = building._can_afford(player, btype)
            bg_c  = _col(COL_SLOT_SEL) if is_s else _col(COL_SLOT_BG)
            strdef = STRUCTURE_DEFS.get(btype, {})
            st_col = _col(strdef.get("color", COL_STONE))
            bge   = Entity(parent=p, model="quad", color=bg_c,
                            position=(px, iy, 0.06),
                            scale=(tab_w, 0.060))
            icon  = Entity(parent=p, model="quad",
                            color=st_col,
                            position=(px-pw/2+0.03, iy, 0.07),
                            scale=(0.038, 0.038))
            name_c= color.white if can else color.gray
            nm    = _text(p, BUILDING_NAMES.get(btype,btype)[:16],
                           px-pw/2+0.055, iy-0.002, 0.48, name_c, (0,0))
            self.entities += [bge, icon, nm]

            # Show cost if selected
            if is_s:
                cost = BUILDING_COSTS.get(btype, {})
                for k, (iid, need) in enumerate(cost.items()):
                    have   = player.inv.count(iid)
                    ok     = have >= need
                    iname  = ITEM_REGISTRY.get(iid,{}).get("name",iid)
                    c_col  = _col(COL_LIME) if ok else _col(COL_RED)
                    ct = _text(p, f"  {iname[:14]}: {have}/{need}",
                                px-pw/2+0.01, iy-0.030-k*0.025, 0.40, c_col, (0,0))
                    self.entities.append(ct)

        # Hints
        hints = [
            "[←→] Category", "[↑↓] Item",
            "[LMB] Place", "[X] Demolish",
            "[R] Rotate", "[B] Close",
        ]
        for i, h in enumerate(hints):
            ht = _text(p, h, px, py-ph/2+0.045+i*0.025,
                        0.40, color.gray, (0,0))
            self.entities.append(ht)

    def hide(self):
        self._clear()


class PauseScreen:
    def __init__(self):
        self.ui       = Entity(parent=camera.ui)
        self.entities = []

    def show(self, day: int):
        for e in self.entities:
            destroy(e)
        self.entities.clear()
        p = self.ui
        overlay = Entity(parent=p, model="quad",
                          color=color.rgba(0,0,0,180),
                          scale=(2,2), z=0.1)
        self.entities.append(overlay)
        self.entities.append(
            _text(p, "PAUSED", 0, 0.10, 1.5, color.white, (0,0))
        )
        self.entities.append(
            _text(p, f"Day {day}", 0, 0.02, 0.70, _col(COL_YELLOW), (0,0))
        )
        self.entities.append(
            _text(p, "[ESC] Resume   [Q] Quit to desktop",
                   0, -0.06, 0.65, color.gray, (0,0))
        )

    def hide(self):
        for e in self.entities:
            destroy(e)
        self.entities.clear()


class DeathScreen:
    def __init__(self):
        self.ui       = Entity(parent=camera.ui)
        self.entities = []

    def show(self, enemies_killed: int, level: int):
        for e in self.entities:
            destroy(e)
        self.entities.clear()
        p = self.ui
        overlay = Entity(parent=p, model="quad",
                          color=color.rgba(120,0,0,200),
                          scale=(2,2), z=0.1)
        self.entities.append(overlay)
        self.entities.append(
            _text(p, "YOU DIED", 0, 0.12, 2.0, _col(COL_RED), (0,0))
        )
        self.entities.append(
            _text(p, f"Enemies slain: {enemies_killed}   Level: {level}",
                   0, 0.01, 0.65, color.white, (0,0))
        )
        self.entities.append(
            _text(p, "[R] Respawn", 0, -0.08, 0.80, color.white, (0,0))
        )

    def hide(self):
        for e in self.entities:
            destroy(e)
        self.entities.clear()
