# player.py - Player entity: movement, combat, stats, rendering

import pygame
import math
from constants import *
from items import make_item, Item, ITEM_DATA


class Player:
    def __init__(self, world):
        self.world  = world
        # Position (world pixels, center)
        cx = world.width  * TILE_SIZE // 2
        cy = world.height * TILE_SIZE // 2
        self.x   = float(cx)
        self.y   = float(cy)
        self.radius = PLAYER_RADIUS

        # Stats
        self.max_health   = PLAYER_MAX_HEALTH
        self.max_stamina  = PLAYER_MAX_STAMINA
        self.max_hunger   = PLAYER_MAX_HUNGER
        self.max_thirst   = PLAYER_MAX_THIRST
        self.health       = float(self.max_health)
        self.stamina      = float(self.max_stamina)
        self.hunger       = float(self.max_hunger)
        self.thirst       = float(self.max_thirst)
        self.xp           = 0
        self.level        = 1
        self.xp_to_next   = 100

        # Combat
        self.atk_cooldown  = 0.0
        self.invincible    = 0.0   # seconds of iframes
        self.is_blocking   = False
        self.block_stam_drain = BLOCK_STAMINA_COST
        self.facing_angle  = 0.0  # radians, direction player faces

        # Equipped items (item_id or None)
        self.equipped = {
            SLOT_HEAD:    None,
            SLOT_CHEST:   None,
            SLOT_LEGS:    None,
            SLOT_WEAPON:  None,
            SLOT_OFFHAND: None,
        }

        # Hotbar (5 slots, each None or Item)
        self.hotbar       = [None] * 5
        self.hotbar_index = 0

        # Main inventory (8x5 grid)
        self.inventory    = [[None]*5 for _ in range(8)]

        # Flags
        self.is_dead    = False
        self.sprint_key = False
        self.collected_items = []   # items to add this frame (shown as popup)
        self._dmg_flash = 0.0       # red flash timer

        # Visual
        self.body_col   = (200, 180, 140)
        self.shirt_col  = (60,  100, 180)
        self.pants_col  = (50,  60,  100)
        self.hair_col   = (80,  50,  20)

        # Give starting items
        self._give_starting_items()

    # ── Starting Items ──────────────────────────────────────────────────────
    def _give_starting_items(self):
        self.add_item(make_item("plant_fiber", 5))
        self.add_item(make_item("pebble", 3))
        self.add_item(make_item("sprig", 3))
        self.add_item(make_item("raw_mushroom", 2))

    # ── Inventory helpers ───────────────────────────────────────────────────
    def add_item(self, item):
        """Add item to hotbar first, then inventory. Returns leftover count."""
        remaining = item.count
        # Try stacking in hotbar
        for slot in self.hotbar:
            if slot and slot.item_id == item.item_id and slot.count < slot.max_stack:
                add = min(remaining, slot.max_stack - slot.count)
                slot.count += add
                remaining  -= add
                if remaining == 0:
                    return 0
        # Try stacking in inventory
        for row in self.inventory:
            for j, slot in enumerate(row):
                if slot and slot.item_id == item.item_id and slot.count < slot.max_stack:
                    add = min(remaining, slot.max_stack - slot.count)
                    slot.count += add
                    remaining  -= add
                    if remaining == 0:
                        return 0
        # Empty hotbar slot
        for i, slot in enumerate(self.hotbar):
            if slot is None:
                new_item = make_item(item.item_id, remaining)
                self.hotbar[i] = new_item
                return 0
        # Empty inventory slot
        for row in self.inventory:
            for j in range(len(row)):
                if row[j] is None:
                    row[j] = make_item(item.item_id, remaining)
                    return 0
        return remaining  # couldn't fit all

    def remove_item(self, item_id, count=1):
        """Remove count of item_id from all slots. Returns True if successful."""
        # Count available
        total = self.count_item(item_id)
        if total < count:
            return False
        remaining = count
        for row in (self.hotbar, *self.inventory):
            for i, slot in enumerate(row if isinstance(row, list) else list(row)):
                if slot and slot.item_id == item_id:
                    take = min(remaining, slot.count)
                    slot.count -= take
                    remaining  -= take
                    # zero out
                    if slot.count <= 0:
                        if row is self.hotbar:
                            self.hotbar[self.hotbar.index(slot)] = None
                        else:
                            for r in range(len(self.inventory)):
                                for c in range(len(self.inventory[r])):
                                    if self.inventory[r][c] is slot:
                                        self.inventory[r][c] = None
                    if remaining == 0:
                        return True
        return True

    def count_item(self, item_id):
        total = 0
        for slot in self.hotbar:
            if slot and slot.item_id == item_id:
                total += slot.count
        for row in self.inventory:
            for slot in row:
                if slot and slot.item_id == item_id:
                    total += slot.count
        return total

    def get_hotbar_item(self):
        return self.hotbar[self.hotbar_index]

    def get_equipped_weapon(self):
        weapon_item = self.equipped.get(SLOT_WEAPON)
        if weapon_item:
            return weapon_item
        # Check hotbar for weapons/tools
        item = self.get_hotbar_item()
        if item and item.itype in (ITYPE_WEAPON, ITYPE_TOOL):
            return item
        return None

    def get_defense(self):
        defense = 0
        for slot_id in (SLOT_HEAD, SLOT_CHEST, SLOT_LEGS, SLOT_OFFHAND):
            item = self.equipped.get(slot_id)
            if item:
                defense += item.defense
        return defense

    def get_speed(self):
        bonus = 0
        for slot_id in (SLOT_HEAD, SLOT_CHEST, SLOT_LEGS):
            item = self.equipped.get(slot_id)
            if item:
                bonus += item.speed_bonus
        return PLAYER_SPEED * (1 + bonus)

    # ── Movement ────────────────────────────────────────────────────────────
    def move(self, dx, dy, dt):
        if self.is_dead:
            return

        length = math.hypot(dx, dy)
        if length == 0:
            return

        sprinting = self.sprint_key and self.stamina > 0
        speed = self.get_speed() * (PLAYER_SPRINT_MULT if sprinting else 1.0)
        if sprinting:
            self.stamina = max(0, self.stamina - SPRINT_STAMINA_COST * dt)

        vx = (dx / length) * speed * dt
        vy = (dy / length) * speed * dt

        # Update facing
        self.facing_angle = math.atan2(dy, dx)

        # Resolve movement axis-by-axis for smooth wall sliding
        new_x = self.x + vx
        if not self.world.is_solid_at(new_x, self.y, self.radius - 2):
            self.x = new_x
        new_y = self.y + vy
        if not self.world.is_solid_at(self.x, new_y, self.radius - 2):
            self.y = new_y

        # Clamp to world bounds
        margin = self.radius
        self.x = max(margin, min(self.world.width  * TILE_SIZE - margin, self.x))
        self.y = max(margin, min(self.world.height * TILE_SIZE - margin, self.y))

    # ── Combat ──────────────────────────────────────────────────────────────
    def attack(self, enemies):
        """Swing weapon, return list of hit enemies."""
        if self.is_dead or self.atk_cooldown > 0:
            return []

        weapon = self.get_equipped_weapon()
        if weapon:
            damage = weapon.damage
            cooldown = PLAYER_ATK_COOLDOWN / weapon.attack_speed
            knockback = weapon.knockback
            tool_type = weapon.tool_type
        else:
            damage = 5   # bare hands
            cooldown = PLAYER_ATK_COOLDOWN
            knockback = 60
            tool_type = None

        self.atk_cooldown = cooldown
        self.stamina = max(0, self.stamina - 8)

        hit_list = []
        for enemy in enemies:
            dx = enemy.x - self.x
            dy = enemy.y - self.y
            dist = math.hypot(dx, dy)
            if dist > PLAYER_ATTACK_RANGE + enemy.radius:
                continue
            # Check angle
            angle_to = math.atan2(dy, dx)
            diff = abs(math.atan2(math.sin(angle_to - self.facing_angle),
                                   math.cos(angle_to - self.facing_angle)))
            if diff > math.pi * 0.65:
                continue
            enemy.take_damage(damage, dx/max(dist,1), dy/max(dist,1), knockback)
            hit_list.append(enemy)

        return hit_list

    def swing_at_resource(self):
        """Attack the nearest collectible resource."""
        if self.atk_cooldown > 0 or self.is_dead:
            return []
        weapon = self.get_equipped_weapon()
        tool_type = weapon.tool_type if weapon else None
        damage    = weapon.damage if weapon else 5
        cooldown  = (PLAYER_ATK_COOLDOWN / weapon.attack_speed) if weapon else PLAYER_ATK_COOLDOWN

        near = self.world.get_nearby_resources(self.x, self.y, PLAYER_ATTACK_RANGE)
        drops = []
        for res in near:
            dropped = res.hit(damage, tool_type)
            drops.extend(dropped)
            if dropped:
                break  # one resource per swing
        self.atk_cooldown = cooldown
        return drops

    def collect_nearby(self):
        """Press E to collect the nearest resource without damaging."""
        if self.is_dead:
            return []
        near = self.world.get_nearby_resources(self.x, self.y, PLAYER_COLLECT_RANGE)
        drops = []
        for res in near[:1]:  # only closest
            dropped = res.hit(999, None)  # always collects
            drops.extend(dropped)
        return drops

    def take_damage(self, amount, knockback_x=0, knockback_y=0):
        if self.invincible > 0 or self.is_dead:
            return
        defense = self.get_defense()
        if self.is_blocking:
            defense += 30
        reduced = max(1, amount - defense // 3)
        self.health = max(0, self.health - reduced)
        self.invincible = 0.5
        self._dmg_flash = 0.3
        # Apply knockback
        dist = math.hypot(knockback_x, knockback_y)
        if dist > 0:
            kb = 80
            nx = knockback_x / dist
            ny = knockback_y / dist
            new_x = self.x + nx * kb
            new_y = self.y + ny * kb
            if not self.world.is_solid_at(new_x, self.y, self.radius - 2):
                self.x = new_x
            if not self.world.is_solid_at(self.x, new_y, self.radius - 2):
                self.y = new_y
        if self.health <= 0:
            self.is_dead = True

    def eat(self, item):
        """Consume a food item from hotbar."""
        if item.itype != ITYPE_FOOD:
            return False
        self.hunger = min(self.max_hunger, self.hunger + item.hunger_val)
        self.thirst = min(self.max_thirst, self.thirst + item.thirst_val)
        self.health = min(self.max_health, self.health + item.heal_val)
        return True

    # ── Update ──────────────────────────────────────────────────────────────
    def update(self, dt, enemies):
        if self.is_dead:
            return

        # Cooldowns
        if self.atk_cooldown > 0:
            self.atk_cooldown = max(0, self.atk_cooldown - dt)
        if self.invincible > 0:
            self.invincible = max(0, self.invincible - dt)
        if self._dmg_flash > 0:
            self._dmg_flash = max(0, self._dmg_flash - dt)

        # Stamina regen when not blocking/sprinting
        if not self.is_blocking and not self.sprint_key:
            self.stamina = min(self.max_stamina, self.stamina + STAMINA_REGEN * dt)

        # Blocking stamina drain
        if self.is_blocking:
            self.stamina = max(0, self.stamina - self.block_stam_drain * dt)
            if self.stamina <= 0:
                self.is_blocking = False

        # Hunger / thirst drain
        self.hunger = max(0, self.hunger - HUNGER_DRAIN_RATE * dt)
        self.thirst = max(0, self.thirst - THIRST_DRAIN_RATE * dt)

        # Starvation / dehydration damage
        if self.hunger <= 0 or self.thirst <= 0:
            self.health = max(0, self.health - 2 * dt)

        # Health regen if well fed
        if self.hunger > 60 and self.thirst > 60:
            self.health = min(self.max_health, self.health + 1.5 * dt)

        if self.health <= 0:
            self.is_dead = True

    # ── XP / Leveling ───────────────────────────────────────────────────────
    def gain_xp(self, amount):
        self.xp += amount
        while self.xp >= self.xp_to_next:
            self.xp       -= self.xp_to_next
            self.level    += 1
            self.xp_to_next = int(self.xp_to_next * 1.4)
            self.max_health  += 10
            self.max_stamina += 5
            self.health       = self.max_health
            self.stamina      = self.max_stamina

    # ── Draw ────────────────────────────────────────────────────────────────
    def draw(self, surface, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        r  = self.radius

        # Damage flash overlay
        flash_alpha = int(self._dmg_flash * 255 / 0.3) if self._dmg_flash > 0 else 0

        # Shadow
        pygame.draw.ellipse(surface, (0,0,0,80), (sx-r, sy+r-4, r*2, 8))

        # Legs
        leg_off_x = int(math.cos(self.facing_angle + math.pi/2) * 6)
        leg_off_y = int(math.sin(self.facing_angle + math.pi/2) * 6)
        pygame.draw.circle(surface, self.pants_col, (sx+leg_off_x, sy+6), r//2)
        pygame.draw.circle(surface, self.pants_col, (sx-leg_off_x, sy+6), r//2)

        # Body (shirt)
        body_rect = pygame.Rect(sx-r+2, sy-r+4, (r-2)*2, (r-2)*2)
        pygame.draw.ellipse(surface, self.shirt_col, body_rect)

        # Arm with weapon
        arm_angle = self.facing_angle
        ax = sx + int(math.cos(arm_angle) * r)
        ay = sy + int(math.sin(arm_angle) * r)
        pygame.draw.line(surface, self.body_col, (sx, sy), (ax, ay), 4)
        # Weapon tip
        weapon = self.get_equipped_weapon()
        if weapon:
            tip_dist = r + 12
            tip_x = sx + int(math.cos(arm_angle) * tip_dist)
            tip_y = sy + int(math.sin(arm_angle) * tip_dist)
            wcol = weapon.color
            if weapon.tool_type == "bow":
                pygame.draw.line(surface, wcol, (ax, ay), (tip_x, tip_y), 3)
                pygame.draw.arc(surface, wcol, (tip_x-8, tip_y-8, 16, 16),
                                arm_angle-0.8, arm_angle+0.8, 2)
            else:
                pygame.draw.line(surface, wcol, (ax, ay), (tip_x, tip_y), 4)
                pygame.draw.circle(surface, wcol, (tip_x, tip_y), 4)

        # Head
        pygame.draw.circle(surface, self.body_col, (sx, sy-r//2), r//2 + 2)
        # Hair
        pygame.draw.arc(surface, self.hair_col,
                        (sx-r//2-1, sy-r-2, r+2, r//2+4),
                        0, math.pi, 4)
        # Eyes
        ex = int(math.cos(self.facing_angle) * 4)
        ey = int(math.sin(self.facing_angle) * 4)
        pygame.draw.circle(surface, WHITE,
                           (sx-r//4+ex, sy-r//2+ey), 3)
        pygame.draw.circle(surface, BLACK,
                           (sx-r//4+ex, sy-r//2+ey), 1)

        # Shield (offhand)
        offhand = self.equipped.get(SLOT_OFFHAND)
        if offhand and self.is_blocking:
            shield_angle = self.facing_angle + math.pi * 0.4
            shx = sx + int(math.cos(shield_angle) * (r+4))
            shy = sy + int(math.sin(shield_angle) * (r+4))
            pygame.draw.circle(surface, offhand.color, (shx, shy), 10)
            pygame.draw.circle(surface, WHITE, (shx, shy), 10, 2)

        # Block indicator ring
        if self.is_blocking:
            pygame.draw.circle(surface, (100, 200, 255), (sx, sy), r+6, 2)

        # Invincible flash
        if self.invincible > 0 and int(self.invincible * 10) % 2 == 0:
            surf_flash = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
            pygame.draw.circle(surf_flash, (255,255,255,100), (r+2, r+2), r)
            surface.blit(surf_flash, (sx-r-2, sy-r-2))

        # Attack arc indicator
        if self.atk_cooldown > PLAYER_ATK_COOLDOWN * 0.6:
            pygame.draw.arc(surface, (255,200,50),
                            (sx-PLAYER_ATTACK_RANGE, sy-PLAYER_ATTACK_RANGE,
                             PLAYER_ATTACK_RANGE*2, PLAYER_ATTACK_RANGE*2),
                            self.facing_angle - 0.65,
                            self.facing_angle + 0.65, 2)

    def get_world_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                           self.radius*2, self.radius*2)
