# ============================================================
#  BACKYARD SURVIVAL v2  –  HUD (Ursina UI elements)
# ============================================================
from __future__ import annotations
import math
from typing import List, Optional, TYPE_CHECKING
from ursina import (
    Entity, Text, camera, color, Vec2, Vec4, destroy,
    Quad, invoke, lerp, scene
)
from ursina.prefabs.health_bar import HealthBar
from constants import *

if TYPE_CHECKING:
    from player import Player
    from crafting import CraftingSystem


def _col(c: tuple) -> color:
    return color.rgba(*[int(v*255) for v in c])


def _make_bar(parent, x, y, scale_x=0.22, scale_y=0.018,
              bar_color=None, bg_color=None, name=""):
    from ursina import Entity, color as ucol
    if bg_color is None:
        bg_color = color.rgba(30, 30, 30, 180)
    bg = Entity(parent=parent, model="quad",
                color=bg_color,
                position=(x, y, 0),
                scale=(scale_x + 0.004, scale_y + 0.004))
    fill = Entity(parent=parent, model="quad",
                  color=bar_color or color.green,
                  position=(x - scale_x/2, y, -0.01),
                  scale=(scale_x, scale_y),
                  origin=(-0.5, 0))
    return bg, fill


class Notification:
    def __init__(self, parent, text: str, col, duration: float = 2.5):
        self.duration  = duration
        self.age       = 0.0
        self.entity    = Text(
            text, parent=parent,
            position=(0.55, -0.38),
            scale=0.7, color=_col(col),
            origin=(0.5, 0)
        )
        self.entity.background = True

    def update(self, dt: float) -> bool:
        self.age += dt
        ratio = self.age / self.duration
        if ratio >= 1.0:
            destroy(self.entity)
            return False
        # Fade out last 30%
        if ratio > 0.70:
            alpha = 1.0 - (ratio - 0.70) / 0.30
            self.entity.alpha = alpha
        # Float up
        self.entity.y = -0.38 + ratio * 0.06
        return True


class DamageNumber:
    def __init__(self, parent, text: str, sx: float, sy: float,
                 col=(1,0.2,0.2,1), duration: float = 0.9):
        self.age      = 0.0
        self.duration = duration
        self.entity   = Text(
            text, parent=parent,
            position=(sx, sy, -0.2),
            scale=1.0, color=_col(col)
        )

    def update(self, dt: float) -> bool:
        self.age += dt
        if self.age >= self.duration:
            destroy(self.entity)
            return False
        alpha = 1.0 - self.age / self.duration
        self.entity.alpha = alpha
        self.entity.y    += dt * 0.06
        return True


class HUD:
    """All in-game HUD elements rendered with Ursina UI."""

    def __init__(self):
        from ursina import camera
        self.ui        = Entity(parent=camera.ui)
        self._bars     = {}   # stat_name -> (bg, fill, max_scale)
        self._hotbar_slots = []
        self._notifications: List[Notification] = []
        self._damage_numbers: List[DamageNumber] = []
        self._effect_icons: List[Entity] = []
        self._built  = False
        self.visible = True
        self._slot_sel_indicator = None

    def build(self):
        if self._built:
            return
        self._built = True
        p = self.ui

        # ── Stat bars (top-left) ────────────────────────────────────────
        bar_configs = [
            ("health",  -0.86,  0.46, _col(COL_HEALTH),  "HP"),
            ("stamina", -0.86,  0.42, _col(COL_STAMINA), "SP"),
            ("hunger",  -0.86,  0.38, _col(COL_HUNGER),  "HNG"),
            ("thirst",  -0.86,  0.34, _col(COL_THIRST),  "THR"),
        ]
        for name, x, y, col, label in bar_configs:
            bg_e = Entity(parent=p, model="quad",
                          color=color.rgba(20,20,20,180),
                          position=(x, y, 0),
                          scale=(0.24, 0.022))
            fill_e = Entity(parent=p, model="quad",
                            color=col,
                            position=(x - 0.12, y, -0.01),
                            scale=(0.24, 0.018),
                            origin=(-0.5, 0))
            lbl = Text(label, parent=p,
                       position=(x - 0.135, y - 0.003),
                       scale=0.55, color=color.white)
            self._bars[name] = (bg_e, fill_e, 0.24)

        # ── XP bar (under stat bars) ────────────────────────────────────
        xp_bg = Entity(parent=p, model="quad",
                        color=color.rgba(20,20,20,180),
                        position=(-0.86, 0.29, 0),
                        scale=(0.24, 0.016))
        xp_fill = Entity(parent=p, model="quad",
                          color=_col(COL_XP),
                          position=(-0.86-0.12, 0.29, -0.01),
                          scale=(0.24, 0.012),
                          origin=(-0.5, 0))
        self._bars["xp"] = (xp_bg, xp_fill, 0.24)
        self._level_text = Text("Lv 1", parent=p,
                                 position=(-0.86+0.04, 0.29-0.003),
                                 scale=0.55, color=_col(COL_XP))

        # ── Hotbar ──────────────────────────────────────────────────────
        slot_size = 0.075
        gap       = 0.005
        total_w   = HOTBAR_SLOTS * slot_size + (HOTBAR_SLOTS-1) * gap
        start_x   = -total_w / 2 + slot_size / 2

        for i in range(HOTBAR_SLOTS):
            sx = start_x + i * (slot_size + gap)
            sy = -0.44

            bg = Entity(parent=p, model="quad",
                        color=_col(COL_SLOT_BG),
                        position=(sx, sy, 0),
                        scale=(slot_size, slot_size))
            border = Entity(parent=p, model="quad",
                            color=_col(COL_UI_BORDER),
                            position=(sx, sy, 0.01),
                            scale=(slot_size+0.004, slot_size+0.004),
                            wire=True if hasattr(Entity, 'wire') else False)
            key_lbl = Text(str(i+1), parent=p,
                            position=(sx - slot_size*0.4,
                                      sy + slot_size*0.4),
                            scale=0.45, color=color.gray)
            icon_holder = Entity(parent=p, model="quad",
                                  color=color.clear,
                                  position=(sx, sy, -0.01),
                                  scale=(slot_size*0.7, slot_size*0.7))
            count_text = Text("", parent=p,
                               position=(sx + slot_size*0.35,
                                         sy - slot_size*0.38),
                               scale=0.50, color=color.white,
                               origin=(0.5, 0))
            self._hotbar_slots.append({
                "bg": bg, "border": border, "icon": icon_holder,
                "count": count_text, "key": key_lbl,
                "sx": sx, "sy": sy, "size": slot_size,
            })

        # Selection indicator
        self._slot_sel_indicator = Entity(
            parent=p, model="quad",
            color=color.rgba(100,160,255,200),
            position=(start_x, -0.44, 0.02),
            scale=(slot_size+0.006, slot_size+0.006),
        )

        # ── Day/night indicator ─────────────────────────────────────────
        self._day_bg = Entity(parent=p, model="circle",
                               color=color.rgba(20,20,20,160),
                               position=(0.82, 0.44),
                               scale=(0.068, 0.068))
        self._day_dot = Entity(parent=p, model="circle",
                                color=_col(COL_YELLOW),
                                position=(0.82, 0.44+0.028),
                                scale=(0.018, 0.018))
        self._day_text = Text("DAY", parent=p,
                               position=(0.82, 0.38),
                               scale=0.6, color=color.white,
                               origin=(0, 0))

        # ── Status effect icons row ─────────────────────────────────────
        self._effect_row_x = -0.86
        self._effect_row_y = 0.24

        # ── Crosshair ───────────────────────────────────────────────────
        ch_size = 0.012
        ch_col  = color.rgba(220, 220, 220, 180)
        Entity(parent=p, model="quad", color=ch_col,
               scale=(ch_size*0.2, ch_size), position=(0, 0, 0))
        Entity(parent=p, model="quad", color=ch_col,
               scale=(ch_size, ch_size*0.2), position=(0, 0, 0))

        # ── Attack cooldown arc (bottom center) ─────────────────────────
        self._atk_cd_bar_bg = Entity(parent=p, model="quad",
                                      color=color.rgba(20,20,20,160),
                                      position=(0, -0.48),
                                      scale=(0.08, 0.012))
        self._atk_cd_bar    = Entity(parent=p, model="quad",
                                      color=_col(COL_RED),
                                      position=(-0.04, -0.48, -0.01),
                                      scale=(0.08, 0.008),
                                      origin=(-0.5, 0))

        # ── Interact prompt ─────────────────────────────────────────────
        self._interact_text = Text("", parent=p,
                                    position=(0, -0.10),
                                    scale=0.75, color=color.yellow,
                                    origin=(0, 0))

    # ── Update ──────────────────────────────────────────────────────────
    def update(self, dt: float, player, day_t: float):
        if not self._built:
            return

        # Stat bars
        stats = {
            "health":  (player.health,  player.max_health),
            "stamina": (player.stamina, player.max_stamina),
            "hunger":  (player.hunger,  player.max_hunger),
            "thirst":  (player.thirst,  player.max_thirst),
        }
        for name, (val, maxv) in stats.items():
            _, fill, max_scale = self._bars[name]
            ratio = max(0.0, min(1.0, val / maxv)) if maxv > 0 else 0
            fill.scale_x = max_scale * ratio

        # XP bar
        _, xp_fill, xp_max = self._bars["xp"]
        xp_ratio = player.xp / player.xp_to_next if player.xp_to_next > 0 else 0
        xp_fill.scale_x = xp_max * max(0, min(1, xp_ratio))
        self._level_text.text = f"Lv {player.level}"

        # Hotbar
        self._update_hotbar(player)

        # Attack cooldown bar
        atk_ratio = 1.0 - (player.atk_cooldown / PLAYER_ATK_COOLDOWN) \
                    if player.atk_cooldown > 0 else 1.0
        self._atk_cd_bar.scale_x = 0.08 * max(0, min(1, atk_ratio))
        self._atk_cd_bar.color   = (color.green if atk_ratio >= 1.0
                                    else _col(COL_RED))

        # Day/night
        self._update_day(day_t)

        # Status effect icons
        self._update_effect_icons(player)

        # Interact prompt
        station = getattr(player, "nearby_station", None)
        if station:
            self._interact_text.text = f"[E] Open {station.name}"
        else:
            self._interact_text.text = ""

        # Notifications
        self._notifications = [n for n in self._notifications if n.update(dt)]

        # Damage numbers
        self._damage_numbers = [d for d in self._damage_numbers if d.update(dt)]

    def _update_hotbar(self, player):
        slot_size = self._hotbar_slots[0]["size"]
        active    = player.inv.hotbar.active
        for i, slot_data in enumerate(self._hotbar_slots):
            is_sel = (i == active)
            slot_data["bg"].color = (_col(COL_SLOT_SEL) if is_sel
                                     else _col(COL_SLOT_BG))
            slot = player.inv.hotbar.slots[i]
            if slot.is_empty():
                slot_data["icon"].color = color.clear
                slot_data["count"].text = ""
            else:
                item = slot.item
                slot_data["icon"].color = _col(item.color)
                if item.max_stack > 1:
                    slot_data["count"].text = str(item.count)
                else:
                    slot_data["count"].text = ""

        # Move selection indicator
        sel = self._hotbar_slots[active]
        self._slot_sel_indicator.x = sel["sx"]

    def _update_day(self, day_t: float):
        angle   = day_t * math.pi * 2 - math.pi / 2
        radius  = 0.028
        self._day_dot.x = 0.82 + math.cos(angle) * radius
        self._day_dot.y = 0.44 + math.sin(angle) * radius * 0.8
        if 0.25 < day_t < 0.75:
            self._day_dot.color = _col(COL_YELLOW)
            self._day_text.text = "DAY"
            self._day_text.color= _col(COL_YELLOW)
        else:
            self._day_dot.color = color.white
            self._day_text.text = "NIGHT"
            self._day_text.color= color.light_gray

    def _update_effect_icons(self, player):
        # Destroy old icons
        for icon in self._effect_icons:
            destroy(icon)
        self._effect_icons.clear()

        effects = player.effects.active_list()
        for i, eff in enumerate(effects[:6]):
            x = self._effect_row_x + i * 0.038
            y = self._effect_row_y
            icon = Entity(parent=self.ui, model="circle",
                           color=_col(eff.color),
                           position=(x, y, 0),
                           scale=(0.028, 0.028))
            self._effect_icons.append(icon)
            lbl = Text(eff.label[:3], parent=self.ui,
                        position=(x, y - 0.02),
                        scale=0.42, color=color.white,
                        origin=(0, 0))
            self._effect_icons.append(lbl)

    # ── Notifications / popups ───────────────────────────────────────────
    def notify(self, text: str, col=COL_WHITE, duration: float = 2.5):
        # Shift existing notifications up
        for n in self._notifications:
            n.entity.y += 0.022
        n = Notification(self.ui, text, col, duration)
        self._notifications.append(n)

    def add_damage_number(self, amount: int, sx: float, sy: float,
                           is_crit: bool = False):
        col = COL_YELLOW if is_crit else COL_RED
        txt = f"{'CRIT! ' if is_crit else ''}{amount}"
        dn  = DamageNumber(self.ui, txt, sx, sy, col)
        self._damage_numbers.append(dn)

    def add_item_pickup(self, item_name: str, count: int,
                         sx: float, sy: float):
        txt = f"+{count} {item_name}"
        dn  = DamageNumber(self.ui, txt, sx, sy, COL_LIME, duration=1.4)
        self._damage_numbers.append(dn)

    def show_level_up(self, msg: str):
        self.notify(f"LEVEL UP! {msg}", COL_YELLOW, 4.0)

    def set_visible(self, vis: bool):
        self.visible = vis
        self.ui.enabled = vis

    def destroy(self):
        destroy(self.ui)
