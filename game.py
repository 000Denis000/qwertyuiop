# game.py - Main game loop, state management, camera, event handling

import pygame
import math
import random
import sys
from constants import *
from world import World
from player import Player
from enemy import spawn_enemies
from crafting import CraftingSystem
from building import BuildingSystem
from ui import GameUI
from items import make_item, ITEM_DATA


class Camera:
    def __init__(self, world_w, world_h):
        self.x       = 0.0
        self.y       = 0.0
        self.world_w = world_w * TILE_SIZE
        self.world_h = world_h * TILE_SIZE
        self.smooth  = 6.0   # lerp factor

    def update(self, target_x, target_y, dt):
        tx = target_x - SCREEN_WIDTH  / 2
        ty = target_y - SCREEN_HEIGHT / 2
        tx = max(0, min(tx, self.world_w - SCREEN_WIDTH))
        ty = max(0, min(ty, self.world_h - SCREEN_HEIGHT))
        self.x += (tx - self.x) * self.smooth * dt
        self.y += (ty - self.y) * self.smooth * dt

    @property
    def ox(self): return self.x
    @property
    def oy(self): return self.y


class Game:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock  = clock
        self.state  = STATE_PLAYING
        self.running= True

        # Systems
        self.world    = World()
        self.player   = Player(self.world)
        self.enemies  = spawn_enemies(self.world, 80)
        self.camera   = Camera(self.world.width, self.world.height)
        self.crafting = CraftingSystem()
        self.building = BuildingSystem(self.world)
        self.ui       = GameUI(screen)

        # Camera starts on player
        self.camera.x = self.player.x - SCREEN_WIDTH  / 2
        self.camera.y = self.player.y - SCREEN_HEIGHT / 2

        # Day/night
        self.game_time = DAY_LENGTH * 0.3   # start mid-morning
        self.day_number= 1

        # Respawn timer
        self.respawn_timer = 0.0
        self.enemy_respawn_cd = 30.0   # respawn new enemies periodically

        # Building mode mouse tracking
        self.mouse_world_x = 0.0
        self.mouse_world_y = 0.0

        # Tooltip
        self.tooltip_item = None

        # Show controls hint for first 10 seconds
        self.controls_hint_timer = 12.0

        self.ui.notify("Welcome to Backyard Survival!", LIME, 4.0)
        self.ui.notify("WASD move | E collect | SPACE attack | I inventory | C craft | B build", LIGHT_GRAY, 6.0)

    # ─── Main Loop ──────────────────────────────────────────────────────────
    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            self._handle_events()
            self._update(dt)
            self._draw()

    # ─── Events ─────────────────────────────────────────────────────────────
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mousedown(event)

            elif event.type == pygame.MOUSEWHEEL:
                self._handle_mousewheel(event)

    def _handle_keydown(self, event):
        key = event.key

        # Universal
        if key == pygame.K_ESCAPE:
            if self.state == STATE_PLAYING:
                self.state = STATE_PAUSED
            elif self.state == STATE_PAUSED:
                self.state = STATE_PLAYING
            else:
                self.state = STATE_PLAYING
                self.building.active = False
            return

        if self.state == STATE_DEAD:
            if key == pygame.K_r:
                self._respawn()
            return

        if self.state == STATE_PAUSED:
            return

        # Playing / overlay states
        if key == pygame.K_i:
            self.state = STATE_INVENTORY if self.state != STATE_INVENTORY else STATE_PLAYING

        elif key == pygame.K_c:
            if self.state != STATE_CRAFTING:
                self.state = STATE_CRAFTING
                station = self.world.get_nearby_station(self.player.x, self.player.y)
                self.crafting.set_station(station.station_id if station else None)
            else:
                self.state = STATE_PLAYING

        elif key == pygame.K_b:
            if self.state == STATE_BUILDING:
                self.state = STATE_PLAYING
                self.building.active = False
            else:
                self.state = STATE_BUILDING
                self.building.active = True

        # Hotbar selection
        elif key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
            self.player.hotbar_index = key - pygame.K_1

        # Attack (SPACE)
        elif key == pygame.K_SPACE:
            if self.state == STATE_PLAYING:
                self._do_attack()

        # Collect (E)
        elif key == pygame.K_e:
            if self.state == STATE_PLAYING:
                drops = self.player.collect_nearby()
                for item in drops:
                    self.player.add_item(item)
                    self.ui.notify(f"+{item.count} {item.name}", LIME)
                    self.ui.add_item_popup(item.name, self.player.x, self.player.y,
                                           self.camera.ox, self.camera.oy)
                # Also interact with nearest station
                station = self.world.get_nearby_station(self.player.x, self.player.y)
                if station and station.is_station:
                    self.state = STATE_CRAFTING
                    self.crafting.set_station(station.station_id)

        # Eat (F)
        elif key == pygame.K_f:
            if self.state == STATE_PLAYING:
                item = self.player.get_hotbar_item()
                if item and item.itype == "food":
                    if self.player.eat(item):
                        item.count -= 1
                        if item.count <= 0:
                            self.player.hotbar[self.player.hotbar_index] = None
                        self.ui.notify(f"Ate {item.name}", PEACH)

        # Block (R)
        elif key == pygame.K_r:
            if self.state == STATE_PLAYING:
                self.player.is_blocking = not self.player.is_blocking
                if self.player.is_blocking:
                    self.ui.notify("Blocking...", CYAN, 1.0)

        # Crafting navigation
        elif self.state == STATE_CRAFTING:
            if key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
                result = self.crafting.craft_selected(self.player)
                if result:
                    self.ui.notify(f"Crafted: {result.name} x{result.count}", LIME)
                else:
                    self.ui.notify("Cannot craft - missing materials or station!", RED)
            elif key == pygame.K_UP:
                self.crafting.selected_recipe = max(0, self.crafting.selected_recipe - 1)
                recipes = self.crafting.get_visible_recipes(self.player)
                # Adjust scroll
                if self.crafting.selected_recipe < self.crafting.scroll_offset:
                    self.crafting.scroll_offset = self.crafting.selected_recipe
            elif key == pygame.K_DOWN:
                recipes = self.crafting.get_visible_recipes(self.player)
                self.crafting.selected_recipe = min(len(recipes)-1, self.crafting.selected_recipe + 1)
                if self.crafting.selected_recipe >= self.crafting.scroll_offset + 8:
                    self.crafting.scroll_offset += 1
            elif key == pygame.K_LEFT:
                self.crafting.prev_category()
            elif key == pygame.K_RIGHT:
                self.crafting.next_category()

        # Building navigation
        elif self.state == STATE_BUILDING:
            if key == pygame.K_LEFT:
                self.building.prev_category()
            elif key == pygame.K_RIGHT:
                self.building.next_category()
            elif key == pygame.K_UP:
                self.building.prev_item()
            elif key == pygame.K_DOWN:
                self.building.next_item()
            elif key == pygame.K_x:
                self.building.demolish_mode = not self.building.demolish_mode
                mode = "DEMOLISH" if self.building.demolish_mode else "PLACE"
                self.ui.notify(f"Building mode: {mode}", YELLOW)

    def _handle_mousedown(self, event):
        mx, my = pygame.mouse.get_pos()
        self.mouse_world_x = mx + self.camera.ox
        self.mouse_world_y = my + self.camera.oy

        if event.button == 1:   # Left click
            if self.state == STATE_BUILDING:
                if self.building.demolish_mode:
                    tx = int(self.mouse_world_x // TILE_SIZE)
                    ty = int(self.mouse_world_y // TILE_SIZE)
                    if self.building.demolish(tx, ty, self.player):
                        self.ui.notify("Structure demolished!", ORANGE)
                    else:
                        self.ui.notify("No structure there.", LIGHT_GRAY, 1.0)
                else:
                    if self.building.place(self.player):
                        stype = self.building.selected_type
                        from building import BUILDING_NAMES
                        self.ui.notify(f"Built: {BUILDING_NAMES.get(stype, stype)}", LIME)
                    else:
                        self.ui.notify("Cannot place here or missing materials!", RED)

            elif self.state == STATE_PLAYING:
                # Left click attack
                # Update facing toward mouse
                dx = self.mouse_world_x - self.player.x
                dy = self.mouse_world_y - self.player.y
                self.player.facing_angle = math.atan2(dy, dx)
                self._do_attack()

        elif event.button == 3:  # Right click - block
            if self.state == STATE_PLAYING:
                self.player.is_blocking = True

    def _handle_mousewheel(self, event):
        if self.state == STATE_BUILDING:
            if event.y > 0:
                self.building.prev_item()
            else:
                self.building.next_item()
        elif self.state == STATE_PLAYING:
            # Cycle hotbar
            self.player.hotbar_index = (self.player.hotbar_index - event.y) % 5

    def _do_attack(self):
        # First try resource harvesting
        drops = self.player.swing_at_resource()
        for item in drops:
            leftover = self.player.add_item(item)
            self.ui.notify(f"+{item.count} {item.name}", LIME, 1.5)
            self.ui.add_item_popup(item.name, self.player.x, self.player.y,
                                   self.camera.ox, self.camera.oy)

        # Then try hitting enemies
        hit_list = self.player.attack(self.enemies)
        weapon = self.player.get_equipped_weapon()
        dmg = weapon.damage if weapon else 5
        for enemy in hit_list:
            self.ui.add_damage_number(dmg, enemy.x, enemy.y, self.camera.ox, self.camera.oy)
            if not enemy.active:
                # Enemy died
                enemy_drops = enemy.get_drops()
                for drop in enemy_drops:
                    self.player.add_item(drop)
                    self.ui.notify(f"+{drop.count} {drop.name}", ORANGE, 2.0)
                self.player.gain_xp(enemy.xp_reward)
                self.ui.notify(f"+{enemy.xp_reward} XP", XP_COL, 1.5)

    # ─── Update ─────────────────────────────────────────────────────────────
    def _update(self, dt):
        if self.state == STATE_DEAD:
            self.respawn_timer = max(0, self.respawn_timer - dt)
            self.ui.update(dt)
            return

        if self.state == STATE_PAUSED:
            return

        # Update controls hint timer
        self.controls_hint_timer = max(0, self.controls_hint_timer - dt)

        # Day/night cycle
        self.game_time += dt
        if self.game_time >= DAY_LENGTH:
            self.game_time -= DAY_LENGTH
            self.day_number += 1
            self.ui.notify(f"Day {self.day_number} begins!", YELLOW, 3.0)

        # Camera mouse tracking for building
        mx, my = pygame.mouse.get_pos()
        self.mouse_world_x = mx + self.camera.ox
        self.mouse_world_y = my + self.camera.oy

        # Player movement input (available in all non-dead states)
        if self.state in (STATE_PLAYING, STATE_BUILDING):
            self._handle_movement(dt)

        # Player sprint key
        keys = pygame.key.get_pressed()
        self.player.sprint_key = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        # Right mouse button held = block
        mouse_buttons = pygame.mouse.get_pressed()
        if self.state == STATE_PLAYING:
            self.player.is_blocking = mouse_buttons[2]

        # Player update
        self.player.update(dt, self.enemies)

        if self.player.is_dead:
            self.state = STATE_DEAD
            self.ui.notify("You died! Press R to respawn.", RED, 99)
            return

        # World update
        self.world.update(dt)

        # Enemy update + cleanup
        alive = []
        for enemy in self.enemies:
            enemy.update(dt, self.player, self.world)
            if enemy.active:
                alive.append(enemy)
        self.enemies = alive

        # Enemy respawn
        self.enemy_respawn_cd -= dt
        if self.enemy_respawn_cd <= 0:
            self.enemy_respawn_cd = 30.0
            from enemy import spawn_enemies
            if len(self.enemies) < 60:
                new_batch = spawn_enemies(self.world, 10)
                self.enemies.extend(new_batch)

        # Camera
        self.camera.update(self.player.x, self.player.y, dt)

        # Building blueprint update
        if self.state == STATE_BUILDING:
            self.building.update_blueprint(self.mouse_world_x, self.mouse_world_y, self.player)

        # Crafting system update
        self.crafting.update(dt)

        # UI update
        self.ui.update(dt)

        # Tooltip: hover over hotbar
        self._update_tooltip(mx, my)

    def _handle_movement(self, dt):
        keys = pygame.key.get_pressed()
        dx, dy = 0.0, 0.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:    dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1

        # Update facing angle toward mouse when playing
        if self.state == STATE_PLAYING:
            mx, my = pygame.mouse.get_pos()
            mwx = mx + self.camera.ox
            mwy = my + self.camera.oy
            self.player.facing_angle = math.atan2(mwy - self.player.y, mwx - self.player.x)

        if dx != 0 or dy != 0:
            self.player.move(dx, dy, dt)

    def _update_tooltip(self, mx, my):
        sz  = self.ui.SLOT_SIZE
        gap = 6
        n   = len(self.player.hotbar)
        total_w = n * sz + (n-1) * gap
        hx  = SCREEN_WIDTH // 2 - total_w // 2
        hy  = SCREEN_HEIGHT - sz - 16
        self.tooltip_item = None
        for i in range(n):
            sx = hx + i * (sz + gap)
            r  = pygame.Rect(sx, hy, sz, sz)
            if r.collidepoint(mx, my):
                self.tooltip_item = self.player.hotbar[i]

    # ─── Draw ────────────────────────────────────────────────────────────────
    def _draw(self):
        # Sky color based on time of day
        day_t = self.game_time / DAY_LENGTH
        sky_col = self._lerp_color(NIGHT_SKY, DAY_SKY, self._day_brightness(day_t))
        self.screen.fill(sky_col)

        # World + entities
        self.world.draw(self.screen, self.camera.ox, self.camera.oy)
        self._draw_enemies()

        # Player
        self.player.draw(self.screen, self.camera.ox, self.camera.oy)

        # Building overlay
        if self.state == STATE_BUILDING:
            self.building.draw_blueprint(self.screen, self.camera.ox, self.camera.oy)
            self.building.draw_menu(self.screen)

        # Night overlay
        brightness = self._day_brightness(day_t)
        if brightness < 0.5:
            darkness = int((0.5 - brightness) * 2 * 180)
            dark_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            dark_surf.fill((0, 0, 30, darkness))
            self.screen.blit(dark_surf, (0, 0))

        # HUD
        self.ui.draw_hud(self.player, day_t, self.game_time)

        # Controls hint
        if self.controls_hint_timer > 0:
            self.ui.draw_controls_hint()

        # Minimap (draw world onto minimap area)
        mm_size = 90
        mm_x = SCREEN_WIDTH - mm_size - 10
        mm_y = SCREEN_HEIGHT - mm_size - 10
        mm_rect = pygame.Rect(mm_x, mm_y, mm_size, mm_size)
        # Create minimap surface
        mm_surf = pygame.Surface((mm_size, mm_size))
        self.world.draw_minimap(mm_surf, pygame.Rect(0, 0, mm_size, mm_size))
        # Player dot
        px_mm = int(self.player.x / (self.world.width * TILE_SIZE) * mm_size)
        py_mm = int(self.player.y / (self.world.height * TILE_SIZE) * mm_size)
        pygame.draw.circle(mm_surf, WHITE, (px_mm, py_mm), 3)
        # Enemy dots
        for enemy in self.enemies:
            ex_mm = int(enemy.x / (self.world.width * TILE_SIZE) * mm_size)
            ey_mm = int(enemy.y / (self.world.height * TILE_SIZE) * mm_size)
            if 0 <= ex_mm < mm_size and 0 <= ey_mm < mm_size:
                pygame.draw.circle(mm_surf, RED, (ex_mm, ey_mm), 1)
        self.screen.blit(mm_surf, (mm_x, mm_y))
        pygame.draw.rect(self.screen, WHITE, mm_rect, 1)

        # Overlays based on state
        if self.state == STATE_INVENTORY:
            self.ui.draw_inventory(self.player)
        elif self.state == STATE_CRAFTING:
            self.ui.draw_crafting(self.player, self.crafting)
        elif self.state == STATE_DEAD:
            self.ui.draw_death_screen()
        elif self.state == STATE_PAUSED:
            self.ui.draw_pause_screen()

        # Tooltip
        if self.tooltip_item:
            mx, my = pygame.mouse.get_pos()
            self.ui.draw_tooltip(self.tooltip_item, mx, my)

        # Day indicator text
        self._draw_day_info(day_t)

        pygame.display.flip()

    def _draw_enemies(self):
        for enemy in self.enemies:
            enemy.draw(self.screen, self.camera.ox, self.camera.oy)

    def _draw_day_info(self, day_t):
        font = pygame.font.SysFont("monospace", 13)
        day_str = f"Day {self.day_number}  {'Day' if 0.25 < day_t < 0.75 else 'Night'}"
        surf = font.render(day_str, True, WHITE)
        self.screen.blit(surf, (SCREEN_WIDTH - surf.get_width() - 90, 8))

    # ─── Helpers ────────────────────────────────────────────────────────────
    def _respawn(self):
        self.player.health   = self.player.max_health
        self.player.stamina  = self.player.max_stamina
        self.player.hunger   = 60.0
        self.player.thirst   = 60.0
        self.player.is_dead  = False
        self.player.x = self.world.width  * TILE_SIZE // 2 + random.randint(-64, 64)
        self.player.y = self.world.height * TILE_SIZE // 2 + random.randint(-64, 64)
        self.state = STATE_PLAYING
        self.ui.notifications.clear()
        self.ui.notify("Respawned!", LIME, 3.0)

    def _day_brightness(self, day_t):
        """Returns 0.0 (night) to 1.0 (full day)."""
        if 0.25 <= day_t <= 0.75:
            t = (day_t - 0.25) / 0.5
            return 0.3 + 0.7 * math.sin(t * math.pi)
        elif day_t < 0.25:
            return day_t / 0.25 * 0.3
        else:
            return (1.0 - day_t) / 0.25 * 0.3

    def _lerp_color(self, c1, c2, t):
        t = max(0, min(1, t))
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )
