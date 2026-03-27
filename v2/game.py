# ============================================================
#  BACKYARD SURVIVAL v2  –  Main Game Controller
# ============================================================
import math
import random
import sys
from typing import List, Optional

from ursina import (
    Ursina, Entity, camera, mouse, held_keys, color,
    Vec3, Vec2, window, time, application,
    destroy, invoke, scene, Text
)
from ursina.prefabs.first_person_controller import FirstPersonController

from constants import *
from world  import World
from player import Player
from enemy  import Enemy, spawn_enemies
from crafting import CraftingSystem
from building import BuildingSystem
from hud     import HUD
from screens import (InventoryScreen, CraftingScreen,
                      BuildingScreen, PauseScreen, DeathScreen)
from renderer import (TerrainRenderer, ResourceRenderer,
                       StructureRenderer, EnemyRenderer,
                       PlayerRenderer, WorldLighting)
from items  import make


# ════════════════════════════════════════════════════════════
#  THIRD-PERSON CAMERA CONTROLLER
# ════════════════════════════════════════════════════════════

class ThirdPersonCamera:
    def __init__(self):
        self.yaw      = 0.0
        self.pitch    = 20.0
        self.distance = CAM_DISTANCE
        self.height   = 0.0
        self._target_yaw   = 0.0
        self._target_pitch = 20.0
        camera.parent = scene
        camera.position = Vec3(0, 5, -8)
        camera.rotation = Vec3(20, 0, 0)

    def update(self, player: Player, dt: float):
        # Mouse look (only when not in menu)
        if mouse.locked:
            self._target_yaw   += mouse.velocity[0] * CAM_SENSITIVITY
            self._target_pitch  = max(CAM_MIN_PITCH,
                                      min(CAM_MAX_PITCH,
                                          self._target_pitch - mouse.velocity[1] * CAM_SENSITIVITY))

        # Smooth lerp
        self.yaw   += (self._target_yaw   - self.yaw)   * CAM_LERP * dt
        self.pitch += (self._target_pitch - self.pitch)  * CAM_LERP * dt

        # Update player yaw to match camera (for movement direction)
        player.yaw   = self.yaw
        player.pitch = self.pitch

        # Orbit position
        yaw_r   = math.radians(self.yaw)
        pitch_r = math.radians(self.pitch)
        cam_dx  =  math.sin(yaw_r)   * math.cos(pitch_r) * self.distance
        cam_dy  = -math.sin(pitch_r) * self.distance + 1.5
        cam_dz  =  math.cos(yaw_r)   * math.cos(pitch_r) * self.distance

        tx = player.x + cam_dx
        ty = player.y + cam_dy + 1.0
        tz = player.z - cam_dz

        # Smooth follow
        camera.position = Vec3(
            camera.x + (tx - camera.x) * CAM_LERP * dt,
            camera.y + (ty - camera.y) * CAM_LERP * dt,
            camera.z + (tz - camera.z) * CAM_LERP * dt,
        )
        camera.look_at(Vec3(player.x, player.y + 0.8, player.z))

    def lock_mouse(self):
        mouse.locked = True

    def unlock_mouse(self):
        mouse.locked = False


# ════════════════════════════════════════════════════════════
#  GAME
# ════════════════════════════════════════════════════════════

class Game:
    def __init__(self):
        self.state   = GS_LOADING
        self.day_num = 1
        self.game_time = DAY_LENGTH * 0.30   # start mid-morning

        # Systems
        print("[BACKYARD] Generating world...")
        self.world    = World()
        print("[BACKYARD] Spawning player...")
        self.player   = Player(self.world)
        print("[BACKYARD] Spawning enemies...")
        self.enemies  : List[Enemy] = spawn_enemies(self.world, 80)
        self.crafting = CraftingSystem()
        self.building = BuildingSystem(self.world)

        # Renderers
        print("[BACKYARD] Building terrain...")
        self.terrain_r  = TerrainRenderer(self.world)
        print("[BACKYARD] Placing resources...")
        self.resource_r = ResourceRenderer(self.world)
        self.struct_r   = StructureRenderer(self.world)
        self.enemy_r    = EnemyRenderer()
        self.player_r   = PlayerRenderer()
        self.lighting   = WorldLighting()

        # Spawn enemy visuals
        for enemy in self.enemies:
            self.enemy_r.add(enemy)

        # Camera
        self.cam        = ThirdPersonCamera()
        self.cam.lock_mouse()

        # UI
        self.hud          = HUD()
        self.hud.build()
        self.inv_screen   = InventoryScreen()
        self.craft_screen = CraftingScreen()
        self.build_screen = BuildingScreen()
        self.pause_screen = PauseScreen()
        self.death_screen = DeathScreen()

        # Respawn timer for enemies
        self._enemy_respawn_cd = 45.0

        # Input state
        self._prev_keys = set()

        # Blueprint ghost entity
        self._blueprint_ent = None

        # Notify on start
        self.hud.notify("Welcome to Backyard Survival!", COL_LIME, 5.0)
        self.hud.notify("WASD: Move | SHIFT: Sprint | LMB: Attack | E: Collect", COL_WHITE, 7.0)
        self.hud.notify("I: Inventory | C: Crafting | B: Build | ESC: Pause", COL_WHITE, 9.0)

        self.state = GS_PLAYING

    # ════════════════════════════════════════════════════════
    #  URSINA HOOKS
    # ════════════════════════════════════════════════════════

    def update(self):
        dt = min(time.dt, 0.05)
        self._handle_input(dt)

        if self.state == GS_PLAYING:
            self._update_playing(dt)
        elif self.state == GS_BUILDING:
            self._update_building(dt)

        # HUD always updates
        day_t = (self.game_time % DAY_LENGTH) / DAY_LENGTH
        self.hud.update(dt, self.player, day_t)

    def input(self, key):
        """Called by Ursina for key events."""
        self._on_key(key)

    # ════════════════════════════════════════════════════════
    #  INPUT HANDLING
    # ════════════════════════════════════════════════════════

    def _handle_input(self, dt: float):
        if self.state in (GS_DEAD, GS_PAUSED):
            return

        # Movement
        if self.state in (GS_PLAYING, GS_BUILDING):
            dx = (held_keys["d"] - held_keys["a"])
            dz = (held_keys["w"] - held_keys["s"])
            if dx != 0 or dz != 0:
                sprint = held_keys["left shift"] or held_keys["right shift"]
                self.player.move(dx, -dz, dt, sprint)

            # Block (hold right mouse)
            self.player.is_blocking = mouse.right

    def _on_key(self, key):
        state = self.state

        # Universal
        if key == "escape":
            if state == GS_PLAYING:
                self._enter_state(GS_PAUSED)
            elif state == GS_PAUSED:
                self._enter_state(GS_PLAYING)
            else:
                self._enter_state(GS_PLAYING)
            return

        # Dead
        if state == GS_DEAD:
            if key == "r":
                self._respawn()
            return

        # Pause
        if state == GS_PAUSED:
            if key == "q":
                application.quit()
            return

        # Toggle screens
        if key == "i":
            if state == GS_INVENTORY:
                self._enter_state(GS_PLAYING)
            else:
                self._enter_state(GS_INVENTORY)
            return

        if key == "c":
            if state == GS_CRAFTING:
                self._enter_state(GS_PLAYING)
            else:
                station = self.world.nearest_station(
                    self.player.x, self.player.z)
                self.crafting.open_at_station(
                    station.station_id if station else None)
                self._enter_state(GS_CRAFTING)
            return

        if key == "b":
            if state == GS_BUILDING:
                self._enter_state(GS_PLAYING)
            else:
                self._enter_state(GS_BUILDING)
            return

        # Hotbar
        for i, num in enumerate(["1","2","3","4","5"]):
            if key == num:
                self.player.inv.hotbar.select(i)
                return

        if key == "scroll up":
            self.player.inv.hotbar.prev()
        if key == "scroll down":
            self.player.inv.hotbar.next()

        # Playing / Building actions
        if state in (GS_PLAYING, GS_BUILDING):
            if key == "space":  # jump
                self.player.jump()
            if key == "e":      # collect / interact
                self._do_collect_or_interact()
            if key == "f":      # eat
                self._do_eat()

        # Attack (LMB)
        if key == "left mouse button" and state == GS_PLAYING:
            self._do_attack()

        if key == "left mouse button" and state == GS_BUILDING:
            self._do_place()

        if key == "right mouse button" and state == GS_BUILDING:
            self._do_demolish_at_cursor()

        # Crafting navigation
        if state == GS_CRAFTING:
            if key == "up arrow":
                self.crafting.prev_recipe(self.player.inv)
                self._refresh_craft_screen()
            elif key == "down arrow":
                self.crafting.next_recipe(self.player.inv)
                self._refresh_craft_screen()
            elif key == "left arrow":
                self.crafting.prev_cat()
                self._refresh_craft_screen()
            elif key == "right arrow":
                self.crafting.next_cat()
                self._refresh_craft_screen()
            elif key in ("return", "enter"):
                self._do_craft()

        # Building navigation
        if state == GS_BUILDING:
            if key == "left arrow":
                self.building.prev_category()
                self._refresh_build_screen()
            elif key == "right arrow":
                self.building.next_category()
                self._refresh_build_screen()
            elif key == "up arrow":
                self.building.prev_item()
                self._refresh_build_screen()
            elif key == "down arrow":
                self.building.next_item()
                self._refresh_build_screen()
            elif key == "x":
                self.building.demolish_mode = not self.building.demolish_mode
                self._refresh_build_screen()
                mode = "DEMOLISH" if self.building.demolish_mode else "PLACE"
                self.hud.notify(f"Mode: {mode}", COL_YELLOW)
            elif key == "r":
                self.building.rotate()

    # ════════════════════════════════════════════════════════
    #  ACTIONS
    # ════════════════════════════════════════════════════════

    def _do_attack(self):
        # 1. Try enemies
        results = self.player.attack(self.enemies)
        weapon  = self.player.inv.weapon
        for enemy, dmg, is_crit in results:
            # Screen-space damage number (approximate)
            self.hud.add_damage_number(dmg, 0, 0, is_crit)
            if not enemy.active:
                drops = enemy.get_drops()
                for drop in drops:
                    self.player.inv.add(drop)
                    self.hud.notify(f"+{drop.count} {drop.name}", COL_ORANGE, 2.0)
                for msg in self.player.pop_level_ups():
                    self.hud.show_level_up(msg)

        # 2. Try resources
        near = self.world.resources_near(self.player.x, self.player.z,
                                          PLAYER_ATTACK_RANGE + 1.0)
        drops = self.player.harvest(near)
        for drop in drops:
            self.player.inv.add(drop)
            self.hud.notify(f"+{drop.count} {drop.name}", COL_LIME, 1.5)
            # Hide harvested resource visual
            for res in near:
                if not res.active and res.entity:
                    res.entity.enabled = False

    def _do_collect_or_interact(self):
        # Collect nearest resource
        near  = self.world.resources_near(self.player.x, self.player.z,
                                           PLAYER_COLLECT_RANGE)
        drops = self.player.collect(near)
        for drop in drops:
            self.player.inv.add(drop)
            self.hud.notify(f"+{drop.count} {drop.name}", COL_LIME, 1.5)
        for res in near[:1]:
            if not res.active and res.entity:
                res.entity.enabled = False

        # Interact with nearby station → open crafting
        station = self.world.nearest_station(self.player.x, self.player.z)
        if station:
            self.player.nearby_station = station
            self.crafting.open_at_station(station.station_id)
            self._enter_state(GS_CRAFTING)
        else:
            self.player.nearby_station = None

    def _do_eat(self):
        item = self.player.inv.hotbar.active_item()
        if item and item.itype == ITYPE_FOOD:
            if self.player.eat(item):
                self.player.inv.hotbar.remove_item(item.item_id, 1)
                self.hud.notify(f"Ate: {item.name}", COL_PEACH, 2.0)
        else:
            self.hud.notify("No food in hand! (press F)", COL_ORANGE, 1.5)

    def _do_craft(self):
        result = self.crafting.craft(self.player.inv)
        if result:
            self.player.items_crafted += 1
            self.player.gain_xp(10)
            self.hud.notify(f"Crafted: {result.name} x{result.count}", COL_LIME)
            for msg in self.player.pop_level_ups():
                self.hud.show_level_up(msg)
            self._refresh_craft_screen()
        else:
            self.hud.notify("Cannot craft — missing materials or station!", COL_RED)

    def _do_place(self):
        struct = self.building.place(self.player)
        if struct:
            self.struct_r.add(struct)
            from world import BUILDING_NAMES
            self.hud.notify(f"Built: {struct.name}", COL_LIME)
            self._refresh_build_screen()
        else:
            if self.building.blueprint_valid is False:
                self.hud.notify("Cannot place here or missing materials!", COL_RED)

    def _do_demolish_at_cursor(self):
        # Pick the tile the player is looking at (simplified: nearest structure)
        best_struct = self.world.structure_at_world(
            self.player.x + math.sin(math.radians(self.player.yaw)) * 2,
            self.player.z + math.cos(math.radians(self.player.yaw)) * 2,
        )
        if best_struct:
            tx, tz = best_struct.tx, best_struct.ty
            if self.building.demolish(tx, tz, self.player):
                self.struct_r.remove(tx, tz)
                self.hud.notify("Demolished!", COL_ORANGE)

    # ════════════════════════════════════════════════════════
    #  UPDATE LOOPS
    # ════════════════════════════════════════════════════════

    def _update_playing(self, dt: float):
        self.game_time += dt

        # Day/night cycle
        if self.game_time >= DAY_LENGTH:
            self.game_time -= DAY_LENGTH
            self.day_num   += 1
            self.hud.notify(f"Day {self.day_num}!", COL_YELLOW, 3.0)

        day_t = self.game_time / DAY_LENGTH
        night_mult = NIGHT_ENEMY_MULT if day_t < 0.25 or day_t > 0.75 else 1.0
        self.lighting.update(day_t)

        # Player
        self.player.update(dt)
        for msg in self.player.pop_level_ups():
            self.hud.show_level_up(msg)

        if self.player.is_dead:
            self._enter_state(GS_DEAD)
            return

        # Enemies
        alive = []
        for enemy in self.enemies:
            enemy._night_mult = night_mult
            enemy.update(dt, self.player, self.world)
            self.enemy_r.update_enemy(enemy)
            if enemy.active:
                alive.append(enemy)
            else:
                # Keep entity but disable
                pass
        self.enemies = alive

        # Enemy respawn
        self._enemy_respawn_cd -= dt
        if self._enemy_respawn_cd <= 0:
            self._enemy_respawn_cd = 45.0
            if len(self.enemies) < 70:
                new_batch = spawn_enemies(self.world, 12)
                for e in new_batch:
                    self.enemies.append(e)
                    self.enemy_r.add(e)

        # World (resource respawn)
        events = self.world.update(dt)
        self.resource_r.update(events)

        # Camera
        self.cam.update(self.player, dt)

        # Player renderer
        self.player_r.update(self.player, dt)

        # Nearby station check
        station = self.world.nearest_station(self.player.x, self.player.z,
                                              INTERACT_RANGE)
        self.player.nearby_station = station

        # Crafting update
        self.crafting.update(dt)

    def _update_building(self, dt: float):
        # Still update player + camera
        self.player.update(dt)
        self.cam.update(self.player, dt)
        self.player_r.update(self.player, dt)
        self.world.update(dt)

        # Blueprint — aim at ground in front of player
        look_dist = 3.5
        yaw_r     = math.radians(self.player.yaw)
        look_x    = self.player.x + math.sin(yaw_r) * look_dist
        look_z    = self.player.z + math.cos(yaw_r) * look_dist
        self.building.update_blueprint(look_x, look_z, self.player)
        self._update_blueprint_ghost()

    def _update_blueprint_ghost(self):
        from world import STRUCTURE_DEFS, BUILDING_COSTS
        from renderer import _col as rcol
        stype = self.building.selected_type
        if stype is None:
            if self._blueprint_ent:
                self._blueprint_ent.enabled = False
            return

        data   = STRUCTURE_DEFS.get(stype, {})
        sc     = data.get("scale", (1.0, 1.0, 1.0))
        tx, tz = self.building.blueprint_tx, self.building.blueprint_tz
        px     = (tx + 0.5) * self.world.scale
        pz_    = (tz + 0.5) * self.world.scale
        py_    = self.world.height_at_world_xz(px, pz_) + sc[1] / 2

        valid  = self.building.blueprint_valid
        ghost_col = color.rgba(50,220,50,120) if valid else color.rgba(220,50,50,120)

        if self._blueprint_ent is None:
            self._blueprint_ent = Entity(model="cube", color=ghost_col,
                                          scale=(sc[0]*TILE_WORLD_SCALE, sc[1],
                                                 sc[2]*TILE_WORLD_SCALE))
        self._blueprint_ent.position = Vec3(px, py_, pz_)
        self._blueprint_ent.color    = ghost_col
        self._blueprint_ent.enabled  = True

    # ════════════════════════════════════════════════════════
    #  STATE MACHINE
    # ════════════════════════════════════════════════════════

    def _enter_state(self, new_state: str):
        old = self.state

        # Exit old state
        if old == GS_INVENTORY:
            self.inv_screen.hide()
            self.cam.lock_mouse()
        elif old == GS_CRAFTING:
            self.craft_screen.hide()
            self.cam.lock_mouse()
        elif old == GS_BUILDING:
            self.build_screen.hide()
            if self._blueprint_ent:
                self._blueprint_ent.enabled = False
            self.cam.lock_mouse()
        elif old == GS_PAUSED:
            self.pause_screen.hide()
            self.cam.lock_mouse()
        elif old == GS_DEAD:
            self.death_screen.hide()

        self.state = new_state

        # Enter new state
        if new_state == GS_INVENTORY:
            self.cam.unlock_mouse()
            self.inv_screen.show(self.player)
        elif new_state == GS_CRAFTING:
            self.cam.unlock_mouse()
            self.craft_screen.show(self.player, self.crafting)
        elif new_state == GS_BUILDING:
            self.build_screen.show(self.player, self.building)
        elif new_state == GS_PAUSED:
            self.cam.unlock_mouse()
            self.pause_screen.show(self.day_num)
        elif new_state == GS_DEAD:
            self.cam.unlock_mouse()
            self.death_screen.show(self.player.enemies_killed,
                                    self.player.level)

    def _refresh_craft_screen(self):
        if self.state == GS_CRAFTING:
            self.craft_screen.show(self.player, self.crafting)

    def _refresh_build_screen(self):
        if self.state == GS_BUILDING:
            self.build_screen.show(self.player, self.building)

    def _respawn(self):
        self.player.respawn()
        self._enter_state(GS_PLAYING)
        self.hud.notify("Respawned!", COL_LIME, 3.0)
