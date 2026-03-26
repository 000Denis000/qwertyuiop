# ui.py - All UI rendering: HUD, inventory, crafting panel, tooltips, notifications

import pygame
import math
from constants import *
from items import make_item, ITEM_DATA
from crafting import ALL_RECIPES, RECIPES_BY_CATEGORY, CATEGORIES, CraftingSystem
from building import BUILDING_NAMES, BUILDING_COSTS, BUILD_CATEGORY_NAMES


def _load_fonts():
    return {
        "xs":   pygame.font.SysFont("monospace", 11),
        "sm":   pygame.font.SysFont("monospace", 13),
        "md":   pygame.font.SysFont("monospace", 15, bold=True),
        "lg":   pygame.font.SysFont("monospace", 20, bold=True),
        "xl":   pygame.font.SysFont("monospace", 28, bold=True),
        "huge": pygame.font.SysFont("monospace", 48, bold=True),
    }


class GameUI:
    SLOT_SIZE = 52

    def __init__(self, screen):
        self.screen  = screen
        self.fonts   = _load_fonts()
        self.notifications = []   # [(text, color, timer)]
        self.damage_numbers= []   # [(text, x, y, timer, color)]
        self.floating_items= []   # [(item_name, x, y, timer)]
        # Inventory drag-drop
        self.drag_item   = None
        self.drag_source = None   # ("hotbar", idx) or ("inv", row, col) or ("equip", slot)

    # ── Notifications ────────────────────────────────────────────────────
    def notify(self, text, color=WHITE, duration=2.5):
        self.notifications.append([text, color, duration])

    def add_damage_number(self, value, wx, wy, cam_x, cam_y, color=RED):
        sx = wx - cam_x
        sy = wy - cam_y
        self.damage_numbers.append([f"-{value}", sx, sy - 20, 1.0, color])

    def add_item_popup(self, item_name, wx, wy, cam_x, cam_y):
        sx = wx - cam_x
        sy = wy - cam_y
        self.floating_items.append([f"+{item_name}", sx, sy - 30, 1.5])

    def update(self, dt):
        self.notifications = [[t, c, d-dt] for t,c,d in self.notifications if d-dt > 0]
        for dn in self.damage_numbers:
            dn[2] -= 25 * dt  # float upward
            dn[3] -= dt
        self.damage_numbers = [d for d in self.damage_numbers if d[3] > 0]
        for fi in self.floating_items:
            fi[2] -= 22 * dt
            fi[3] -= dt
        self.floating_items = [f for f in self.floating_items if f[3] > 0]

    # ── HUD ──────────────────────────────────────────────────────────────
    def draw_hud(self, player, day_time, game_time):
        self._draw_stat_bars(player)
        self._draw_hotbar(player)
        self._draw_notifications()
        self._draw_damage_numbers()
        self._draw_floating_items()
        self._draw_day_indicator(day_time)
        self._draw_level(player)
        self._draw_minimap_hud(player)

    def _draw_stat_bars(self, player):
        font = self.fonts["sm"]
        bars = [
            ("HP",  player.health,  player.max_health,  HEALTH_COL,  (140,20,20)),
            ("SP",  player.stamina, player.max_stamina, STAMINA_COL, (20,60,120)),
            ("HNG", player.hunger,  player.max_hunger,  HUNGER_COL,  (120,80,10)),
            ("THR", player.thirst,  player.max_thirst,  THIRST_COL,  (10,80,120)),
        ]
        bar_w, bar_h = 140, 16
        x0, y0 = 12, 12
        gap    = 22
        for i, (label, val, max_val, col, bg) in enumerate(bars):
            bx = x0
            by = y0 + i * gap
            ratio = max(0, val / max_val) if max_val > 0 else 0
            # Background
            bg_surf = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
            bg_surf.fill((20, 20, 20, 160))
            self.screen.blit(bg_surf, (bx, by))
            pygame.draw.rect(self.screen, bg, (bx, by, bar_w, bar_h), border_radius=3)
            # Fill
            fw = max(0, int(bar_w * ratio))
            if fw > 0:
                pygame.draw.rect(self.screen, col, (bx, by, fw, bar_h), border_radius=3)
            # Border
            pygame.draw.rect(self.screen, LIGHT_GRAY, (bx, by, bar_w, bar_h), 1, border_radius=3)
            # Label
            lbl = font.render(f"{label} {int(val)}/{int(max_val)}", True, WHITE)
            self.screen.blit(lbl, (bx + 4, by + 1))

    def _draw_hotbar(self, player):
        sz   = self.SLOT_SIZE
        gap  = 6
        n    = len(player.hotbar)
        total_w = n * sz + (n-1) * gap
        hx   = SCREEN_WIDTH // 2 - total_w // 2
        hy   = SCREEN_HEIGHT - sz - 16
        font = self.fonts["xs"]

        # Background panel
        bg_surf = pygame.Surface((total_w + 16, sz + 16), pygame.SRCALPHA)
        bg_surf.fill((20, 20, 25, 200))
        self.screen.blit(bg_surf, (hx - 8, hy - 8))
        pygame.draw.rect(self.screen, UI_BORDER, (hx-8, hy-8, total_w+16, sz+16), 1, border_radius=6)

        for i, item in enumerate(player.hotbar):
            sx = hx + i * (sz + gap)
            selected = (i == player.hotbar_index)
            col = UI_SLOT_SEL if selected else UI_SLOT_BG
            slot_rect = pygame.Rect(sx, hy, sz, sz)
            pygame.draw.rect(self.screen, col, slot_rect, border_radius=5)
            pygame.draw.rect(self.screen, WHITE if selected else UI_BORDER,
                             slot_rect, 2 if selected else 1, border_radius=5)

            if item:
                item.draw_icon(self.screen, slot_rect.inflate(-8, -8))
                if item.max_stack > 1:
                    cnt = font.render(str(item.count), True, WHITE)
                    self.screen.blit(cnt, (sx + sz - cnt.get_width() - 4, hy + sz - 14))

            # Keybind label
            lbl = font.render(str(i+1), True, LIGHT_GRAY)
            self.screen.blit(lbl, (sx + 3, hy + 3))

        # Equipped weapon info
        weapon = player.get_equipped_weapon()
        if weapon:
            name_surf = self.fonts["sm"].render(weapon.name, True, YELLOW)
            self.screen.blit(name_surf, (hx, hy - 22))

    def _draw_day_indicator(self, day_time):
        """day_time: 0.0 to 1.0 (0=midnight, 0.5=noon)"""
        font  = self.fonts["sm"]
        angle = day_time * 2 * math.pi - math.pi / 2
        cx, cy, r = SCREEN_WIDTH - 50, 50, 30
        # Circle background
        pygame.draw.circle(self.screen, DARK_GRAY, (cx, cy), r + 2)
        if day_time > 0.25 and day_time < 0.75:
            col = YELLOW
            label = "DAY"
        else:
            col = (100, 100, 200)
            label = "NIGHT"
        pygame.draw.circle(self.screen, col, (cx, cy), r - 4)
        # Sun/moon position indicator
        sx = cx + int(math.cos(angle) * (r - 8))
        sy = cy + int(math.sin(angle) * (r - 8))
        dot_col = YELLOW if label == "DAY" else WHITE
        pygame.draw.circle(self.screen, dot_col, (sx, sy), 6)
        # Label
        lbl = font.render(label, True, WHITE)
        self.screen.blit(lbl, (cx - lbl.get_width()//2, cy + r + 4))

    def _draw_level(self, player):
        font = self.fonts["md"]
        xp_w = 120
        xp_h = 10
        xp_x = SCREEN_WIDTH // 2 - xp_w // 2
        xp_y = SCREEN_HEIGHT - self.SLOT_SIZE - 44

        bg = pygame.Surface((xp_w, xp_h), pygame.SRCALPHA)
        bg.fill((20,20,20,160))
        self.screen.blit(bg, (xp_x, xp_y))
        ratio = player.xp / player.xp_to_next if player.xp_to_next > 0 else 0
        pygame.draw.rect(self.screen, XP_COL, (xp_x, xp_y, int(xp_w * ratio), xp_h), border_radius=3)
        pygame.draw.rect(self.screen, LIGHT_GRAY, (xp_x, xp_y, xp_w, xp_h), 1, border_radius=3)
        lv = font.render(f"Lv {player.level}", True, XP_COL)
        self.screen.blit(lv, (xp_x - lv.get_width() - 6, xp_y - 2))

    def _draw_minimap_hud(self, player):
        """Small corner minimap."""
        mm_size = 90
        mm_x = SCREEN_WIDTH - mm_size - 10
        mm_y = SCREEN_HEIGHT - mm_size - 10
        mm_rect = pygame.Rect(mm_x, mm_y, mm_size, mm_size)
        pygame.draw.rect(self.screen, (10, 10, 15), mm_rect)
        pygame.draw.rect(self.screen, UI_BORDER, mm_rect, 1)

    def _draw_notifications(self):
        font = self.fonts["sm"]
        for i, (text, col, _) in enumerate(reversed(self.notifications[-6:])):
            surf = font.render(text, True, col)
            self.screen.blit(surf, (SCREEN_WIDTH - surf.get_width() - 15,
                                    SCREEN_HEIGHT - 80 - i * 20))

    def _draw_damage_numbers(self):
        font = self.fonts["md"]
        for dn in self.damage_numbers:
            text, x, y, timer, col = dn
            alpha = int(255 * min(1.0, timer))
            surf  = font.render(text, True, col)
            surf.set_alpha(alpha)
            self.screen.blit(surf, (int(x), int(y)))

    def _draw_floating_items(self):
        font = self.fonts["sm"]
        for fi in self.floating_items:
            text, x, y, timer = fi
            alpha = int(255 * min(1.0, timer))
            surf  = font.render(text, True, LIME)
            surf.set_alpha(alpha)
            self.screen.blit(surf, (int(x), int(y)))

    # ── Inventory Screen ─────────────────────────────────────────────────
    def draw_inventory(self, player):
        self._draw_overlay()
        font_lg = self.fonts["lg"]
        font_sm = self.fonts["sm"]
        sz      = self.SLOT_SIZE
        gap     = 6

        # Main inventory grid (8 rows x 5 cols)
        inv_cols, inv_rows = 5, 8
        inv_w = inv_cols * sz + (inv_cols-1) * gap
        inv_h = inv_rows * sz + (inv_rows-1) * gap
        inv_x = SCREEN_WIDTH//2 - inv_w//2
        inv_y = SCREEN_HEIGHT//2 - inv_h//2 + 20

        # Panel
        panel_w = inv_w + 32
        panel_h = inv_h + 100
        panel_x = inv_x - 16
        panel_y = inv_y - 50
        self._draw_panel(panel_x, panel_y, panel_w, panel_h)

        title = font_lg.render("INVENTORY", True, WHITE)
        self.screen.blit(title, (panel_x + panel_w//2 - title.get_width()//2, panel_y + 10))

        # Grid slots
        for row in range(inv_rows):
            for col in range(inv_cols):
                sx = inv_x + col * (sz + gap)
                sy = inv_y + row * (sz + gap)
                slot_rect = pygame.Rect(sx, sy, sz, sz)
                item = player.inventory[row][col]
                self._draw_slot(slot_rect, item, selected=False)
                if item and item.max_stack > 1:
                    cnt = self.fonts["xs"].render(str(item.count), True, WHITE)
                    self.screen.blit(cnt, (sx + sz - cnt.get_width() - 4, sy + sz - 14))

        # Equipment panel (right side)
        eq_x = panel_x + panel_w + 20
        eq_y = panel_y
        eq_w = 180
        self._draw_panel(eq_x, eq_y, eq_w, panel_h)
        eq_title = font_lg.render("EQUIPPED", True, WHITE)
        self.screen.blit(eq_title, (eq_x + eq_w//2 - eq_title.get_width()//2, eq_y + 10))

        slots_order = [
            (SLOT_HEAD,    "Head",    eq_x+10, eq_y+50),
            (SLOT_CHEST,   "Chest",   eq_x+10, eq_y+110),
            (SLOT_LEGS,    "Legs",    eq_x+10, eq_y+170),
            (SLOT_WEAPON,  "Weapon",  eq_x+10, eq_y+230),
            (SLOT_OFFHAND, "Shield",  eq_x+10, eq_y+290),
        ]
        for slot_id, label, sx, sy in slots_order:
            lbl_surf = font_sm.render(label, True, LIGHT_GRAY)
            self.screen.blit(lbl_surf, (sx, sy - 16))
            slot_rect = pygame.Rect(sx, sy, sz, sz)
            item = player.equipped.get(slot_id)
            self._draw_slot(slot_rect, item, selected=False)

        # Stats panel
        stat_x = panel_x - 160
        stat_y = panel_y
        self._draw_panel(stat_x, stat_y, 155, panel_h)
        stat_title = font_sm.render("STATS", True, WHITE)
        self.screen.blit(stat_title, (stat_x + 10, stat_y + 8))
        stats = [
            (f"Level:  {player.level}",     WHITE),
            (f"XP:     {player.xp}/{player.xp_to_next}", XP_COL),
            (f"Health: {int(player.health)}/{player.max_health}", HEALTH_COL),
            (f"Stamina:{int(player.stamina)}/{player.max_stamina}", STAMINA_COL),
            (f"Hunger: {int(player.hunger)}/{player.max_hunger}", HUNGER_COL),
            (f"Thirst: {int(player.thirst)}/{player.max_thirst}", THIRST_COL),
            ("", WHITE),
            (f"Defense:{player.get_defense()}", CYAN),
        ]
        weapon = player.get_equipped_weapon()
        if weapon:
            stats.append((f"Damage: {weapon.damage}", RED))
        for i, (text, col) in enumerate(stats):
            s = self.fonts["xs"].render(text, True, col)
            self.screen.blit(s, (stat_x + 8, stat_y + 30 + i * 20))

        # Help text
        hint = self.fonts["xs"].render("I: Close  |  Click to select", True, LIGHT_GRAY)
        self.screen.blit(hint, (panel_x + 8, panel_y + panel_h - 18))

    # ── Crafting Screen ───────────────────────────────────────────────────
    def draw_crafting(self, player, crafting_system):
        self._draw_overlay()
        font_lg = self.fonts["lg"]
        font_sm = self.fonts["sm"]
        font_xs = self.fonts["xs"]
        sz      = self.SLOT_SIZE

        panel_w, panel_h = 680, 500
        panel_x = SCREEN_WIDTH//2 - panel_w//2
        panel_y = SCREEN_HEIGHT//2 - panel_h//2
        self._draw_panel(panel_x, panel_y, panel_w, panel_h)

        title = font_lg.render("CRAFTING", True, WHITE)
        self.screen.blit(title, (panel_x + panel_w//2 - title.get_width()//2, panel_y + 10))

        # Station indicator
        stn = crafting_system.available_station
        stn_str = f"Station: {stn.upper()}" if stn else "Station: None (hands only)"
        stn_surf = font_sm.render(stn_str, True, CYAN if stn else LIGHT_GRAY)
        self.screen.blit(stn_surf, (panel_x + 10, panel_y + 38))

        # Category tabs
        tab_w = panel_w // len(CATEGORIES)
        for i, cat in enumerate(CATEGORIES):
            tx = panel_x + i * tab_w
            ty = panel_y + 58
            col = UI_HIGHLIGHT if i == crafting_system.selected_category else UI_SLOT_BG
            pygame.draw.rect(self.screen, col, (tx, ty, tab_w, 26), border_radius=4)
            pygame.draw.rect(self.screen, UI_BORDER, (tx, ty, tab_w, 26), 1, border_radius=4)
            lbl = font_xs.render(cat[:8].upper(), True, WHITE)
            self.screen.blit(lbl, (tx + tab_w//2 - lbl.get_width()//2, ty + 5))

        # Recipe list (left panel)
        list_x = panel_x + 10
        list_y = panel_y + 92
        list_w = 220
        list_h = panel_h - 115

        recipes = crafting_system.get_visible_recipes(player)
        visible = 8
        start = crafting_system.scroll_offset
        for idx in range(start, min(start + visible, len(recipes))):
            rec = recipes[idx]
            ry  = list_y + (idx - start) * 48
            is_sel = (idx == crafting_system.selected_recipe)
            can    = rec.can_craft(player, crafting_system.available_station)
            row_col = UI_SLOT_SEL if is_sel else UI_SLOT_BG
            row_rect = pygame.Rect(list_x, ry, list_w, 44)
            pygame.draw.rect(self.screen, row_col, row_rect, border_radius=4)
            pygame.draw.rect(self.screen, UI_BORDER, row_rect, 1, border_radius=4)

            # Icon
            icon_rect = pygame.Rect(list_x + 4, ry + 4, 36, 36)
            from items import Item
            preview = Item(rec.result_id, rec.result_count)
            preview.draw_icon(self.screen, icon_rect, False)

            # Name
            name_col = WHITE if can else (130, 130, 130)
            name_surf = font_sm.render(rec.name[:18], True, name_col)
            self.screen.blit(name_surf, (list_x + 46, ry + 4))
            # Result count
            count_surf = font_xs.render(f"x{rec.result_count}", True, YELLOW)
            self.screen.blit(count_surf, (list_x + 46, ry + 22))

        # Recipe detail (right panel)
        detail_x = panel_x + 240
        detail_y = panel_y + 92
        detail_w = panel_w - 260

        if recipes and crafting_system.selected_recipe < len(recipes):
            rec = recipes[crafting_system.selected_recipe]
            can = rec.can_craft(player, crafting_system.available_station)

            # Result
            res_title = font_sm.render("RESULT:", True, LIGHT_GRAY)
            self.screen.blit(res_title, (detail_x, detail_y))
            from items import Item
            result_item = Item(rec.result_id, rec.result_count)
            result_rect = pygame.Rect(detail_x, detail_y + 20, sz, sz)
            result_item.draw_icon(self.screen, result_rect, True)
            name_surf = font_sm.render(rec.name, True, WHITE)
            self.screen.blit(name_surf, (detail_x + sz + 10, detail_y + 26))
            cnt_surf = font_xs.render(f"Produces: x{rec.result_count}", True, YELLOW)
            self.screen.blit(cnt_surf, (detail_x + sz + 10, detail_y + 46))

            # Ingredients
            ing_title = font_sm.render("REQUIRES:", True, LIGHT_GRAY)
            self.screen.blit(ing_title, (detail_x, detail_y + 90))
            for j, (item_id, needed) in enumerate(rec.ingredients.items()):
                have  = player.count_item(item_id)
                col2  = LIME if have >= needed else RED
                name  = ITEM_DATA.get(item_id, {}).get("name", item_id)
                ing_surf = font_sm.render(f"  {name}: {have}/{needed}", True, col2)
                self.screen.blit(ing_surf, (detail_x, detail_y + 112 + j * 20))

            # Station requirement
            if rec.station:
                stn_req = font_sm.render(f"Station: {rec.station.upper()}", True,
                                          CYAN if crafting_system.available_station == rec.station else RED)
                self.screen.blit(stn_req, (detail_x, detail_y + 240))

            # Craft button
            btn_col = (40, 160, 40) if can else (80, 40, 40)
            btn_rect = pygame.Rect(detail_x, detail_y + 280, 140, 40)
            pygame.draw.rect(self.screen, btn_col, btn_rect, border_radius=6)
            pygame.draw.rect(self.screen, LIGHT_GRAY, btn_rect, 2, border_radius=6)
            btn_text = font_sm.render("CRAFT [ENTER]" if can else "CANNOT CRAFT", True, WHITE)
            self.screen.blit(btn_text, (btn_rect.centerx - btn_text.get_width()//2,
                                         btn_rect.centery - btn_text.get_height()//2))

        # Result popup
        if crafting_system.result_popup:
            item, timer = crafting_system.result_popup
            alpha = int(255 * min(1.0, timer * 0.6))
            pop_surf = self.fonts["lg"].render(f"Crafted: {item.name} x{item.count}", True, LIME)
            pop_surf.set_alpha(alpha)
            self.screen.blit(pop_surf, (SCREEN_WIDTH//2 - pop_surf.get_width()//2,
                                         panel_y - 40))

        # Controls hint
        hint = font_xs.render("C/ESC: Close  |  ↑↓: Select  |  ←→: Category  |  ENTER: Craft", True, LIGHT_GRAY)
        self.screen.blit(hint, (panel_x + 10, panel_y + panel_h - 18))

    # ── Death Screen ──────────────────────────────────────────────────────
    def draw_death_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((100, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        font = self.fonts["huge"]
        text = font.render("YOU DIED", True, RED)
        self.screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2,
                                 SCREEN_HEIGHT//2 - text.get_height()//2 - 30))
        hint = self.fonts["lg"].render("Press R to Respawn", True, WHITE)
        self.screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2,
                                 SCREEN_HEIGHT//2 + 40))

    # ── Pause Screen ──────────────────────────────────────────────────────
    def draw_pause_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))
        font = self.fonts["huge"]
        text = font.render("PAUSED", True, WHITE)
        self.screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2,
                                 SCREEN_HEIGHT//2 - 60))
        hint = self.fonts["lg"].render("ESC to Resume", True, LIGHT_GRAY)
        self.screen.blit(hint, (SCREEN_WIDTH//2 - hint.get_width()//2,
                                 SCREEN_HEIGHT//2 + 20))

    # ── Controls overlay ─────────────────────────────────────────────────
    def draw_controls_hint(self):
        lines = [
            "WASD: Move    SHIFT: Sprint    SPACE: Attack",
            "E: Collect    F: Eat hotbar item    R: Block",
            "1-5: Hotbar   I: Inventory    C: Crafting",
            "B: Build      ESC: Pause/Close",
        ]
        font = self.fonts["xs"]
        x0, y0 = 8, SCREEN_HEIGHT - 120
        for i, line in enumerate(lines):
            surf = font.render(line, True, (200, 200, 200, 180))
            surf.set_alpha(160)
            self.screen.blit(surf, (x0, y0 + i * 14))

    # ── Tooltip ───────────────────────────────────────────────────────────
    def draw_tooltip(self, item, mx, my):
        if not item:
            return
        font_sm = self.fonts["sm"]
        font_xs = self.fonts["xs"]
        lines = [item.name]
        if item.damage:
            lines.append(f"Damage: {item.damage}")
        if item.defense:
            lines.append(f"Defense: {item.defense}")
        if item.hunger_val:
            lines.append(f"Hunger: +{item.hunger_val}")
        if item.thirst_val:
            lines.append(f"Thirst: +{item.thirst_val}")
        if item.heal_val:
            lines.append(f"Heals: +{item.heal_val}")
        if item.description:
            lines.append(f"  {item.description}")

        tw = max(len(l) * 7 + 16 for l in lines)
        th = len(lines) * 16 + 12
        tx = min(mx + 10, SCREEN_WIDTH - tw - 4)
        ty = min(my + 10, SCREEN_HEIGHT - th - 4)

        bg = pygame.Surface((tw, th), pygame.SRCALPHA)
        bg.fill((20, 20, 30, 220))
        self.screen.blit(bg, (tx, ty))
        pygame.draw.rect(self.screen, YELLOW, (tx, ty, tw, th), 1, border_radius=4)
        for i, line in enumerate(lines):
            col = YELLOW if i == 0 else WHITE
            s = (font_sm if i == 0 else font_xs).render(line, True, col)
            self.screen.blit(s, (tx + 8, ty + 6 + i * 16))

    # ── Helpers ───────────────────────────────────────────────────────────
    def _draw_overlay(self):
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 150))
        self.screen.blit(ov, (0, 0))

    def _draw_panel(self, x, y, w, h):
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((20, 20, 30, 220))
        self.screen.blit(surf, (x, y))
        pygame.draw.rect(self.screen, UI_BORDER, (x, y, w, h), 2, border_radius=8)

    def _draw_slot(self, rect, item, selected=False):
        col = UI_SLOT_SEL if selected else UI_SLOT_BG
        pygame.draw.rect(self.screen, col, rect, border_radius=4)
        pygame.draw.rect(self.screen, UI_BORDER, rect, 1, border_radius=4)
        if item:
            item.draw_icon(self.screen, rect.inflate(-8, -8))
