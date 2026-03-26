# enemy.py - Enemy classes with AI behavior

import pygame
import math
import random
from constants import *
from items import make_item


class Projectile:
    """Enemy projectile (e.g. bombardier acid spray)."""
    def __init__(self, x, y, angle, speed, damage, color, radius=6, lifetime=2.5):
        self.x       = float(x)
        self.y       = float(y)
        self.vx      = math.cos(angle) * speed
        self.vy      = math.sin(angle) * speed
        self.damage  = damage
        self.color   = color
        self.radius  = radius
        self.lifetime= lifetime
        self.active  = True

    def update(self, dt, world):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.active = False
        tx, ty = int(self.x // TILE_SIZE), int(self.y // TILE_SIZE)
        if world.is_solid_tile(tx, ty):
            self.active = False

    def draw(self, surface, cam_x, cam_y):
        if not self.active:
            return
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        pygame.draw.circle(surface, self.color, (sx, sy), self.radius)
        pygame.draw.circle(surface, WHITE, (sx, sy), self.radius, 1)


# ─── Base Enemy ────────────────────────────────────────────────────────────────
class Enemy:
    ETYPE = "base"

    def __init__(self, x, y):
        self.x       = float(x)
        self.y       = float(y)
        self.target_x = self.x
        self.target_y = self.y
        self.max_health = 30
        self.health     = float(self.max_health)
        self.damage     = 8
        self.speed      = 80
        self.radius     = 20
        self.atk_range  = 40
        self.atk_cd     = 0.0
        self.atk_rate   = 1.2
        self.knockback  = 100
        self.xp_reward  = 15
        self.aggro_range= 250
        self.deaggro_range = 400
        self.color      = RED
        self.color2     = DARK_RED
        self.active     = True
        self.is_aggro   = False
        self.wander_timer = random.uniform(1, 3)
        self.wander_angle = random.uniform(0, 2*math.pi)
        self.facing     = 0.0
        self.hurt_flash = 0.0
        self.drops      = []   # list of (item_id, lo, hi)
        self.projectiles= []

    # ── AI helpers ──────────────────────────────────────────────────────────
    def _move_toward(self, tx, ty, dt, world):
        dx = tx - self.x
        dy = ty - self.y
        dist = math.hypot(dx, dy)
        if dist < 2:
            return
        self.facing = math.atan2(dy, dx)
        nx = dx / dist
        ny = dy / dist
        new_x = self.x + nx * self.speed * dt
        new_y = self.y + ny * self.speed * dt
        if not world.is_solid_at(new_x, self.y, self.radius - 2):
            self.x = new_x
        if not world.is_solid_at(self.x, new_y, self.radius - 2):
            self.y = new_y

    def _wander(self, dt, world):
        self.wander_timer -= dt
        if self.wander_timer <= 0:
            self.wander_angle += random.uniform(-1.2, 1.2)
            self.wander_timer  = random.uniform(1.5, 4.0)
        wx = self.x + math.cos(self.wander_angle) * 60
        wy = self.y + math.sin(self.wander_angle) * 60
        self._move_toward(wx, wy, dt * 0.5, world)

    def dist_to_player(self, player):
        return math.hypot(self.x - player.x, self.y - player.y)

    def try_attack_player(self, player, dt):
        self.atk_cd = max(0, self.atk_cd - dt)
        if self.atk_cd > 0:
            return
        dist = self.dist_to_player(player)
        if dist <= self.atk_range + player.radius:
            dx = player.x - self.x
            dy = player.y - self.y
            player.take_damage(self.damage, dx, dy)
            self.atk_cd = self.atk_rate

    def take_damage(self, amount, dir_x=0, dir_y=0, kb_force=100):
        self.health -= amount
        self.hurt_flash = 0.25
        # Knockback
        dist = math.hypot(dir_x, dir_y)
        if dist > 0 and kb_force > 0:
            self.x += (dir_x / dist) * kb_force * 0.3
            self.y += (dir_y / dist) * kb_force * 0.3
        self.is_aggro = True
        if self.health <= 0:
            self.active = False
            return True  # dead
        return False

    def get_drops(self):
        result = []
        for (item_id, lo, hi) in self.drops:
            count = random.randint(lo, hi)
            if count > 0:
                result.append(make_item(item_id, count))
        return result

    def update(self, dt, player, world):
        if not self.active:
            return
        self.hurt_flash = max(0, self.hurt_flash - dt)
        self.atk_cd    = max(0, self.atk_cd - dt)

        dist = self.dist_to_player(player)

        if self.is_aggro:
            if dist > self.deaggro_range:
                self.is_aggro = False
            else:
                self._move_toward(player.x, player.y, dt, world)
                self.try_attack_player(player, dt)
        else:
            if dist < self.aggro_range:
                self.is_aggro = True
            else:
                self._wander(dt, world)

        # Update projectiles
        for proj in self.projectiles:
            proj.update(dt, world)
            if proj.active:
                px, py = player.x, player.y
                if math.hypot(proj.x - px, proj.y - py) < proj.radius + player.radius:
                    player.take_damage(proj.damage)
                    proj.active = False
        self.projectiles = [p for p in self.projectiles if p.active]

    def draw(self, surface, cam_x, cam_y):
        if not self.active:
            return
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        if not (-80 < sx < SCREEN_WIDTH+80 and -80 < sy < SCREEN_HEIGHT+80):
            return

        self._draw_body(surface, sx, sy)

        # Health bar
        if self.health < self.max_health:
            bw = self.radius * 2
            bx = sx - self.radius
            by = sy - self.radius - 10
            pygame.draw.rect(surface, DARK_RED, (bx, by, bw, 5))
            hw = int(bw * self.health / self.max_health)
            pygame.draw.rect(surface, HEALTH_COL, (bx, by, hw, 5))

        # Hurt flash
        if self.hurt_flash > 0 and int(self.hurt_flash * 20) % 2 == 0:
            flash = pygame.Surface((self.radius*2+4, self.radius*2+4), pygame.SRCALPHA)
            pygame.draw.circle(flash, (255, 255, 255, 160), (self.radius+2, self.radius+2), self.radius)
            surface.blit(flash, (sx-self.radius-2, sy-self.radius-2))

        # Draw projectiles
        for proj in self.projectiles:
            proj.draw(surface, cam_x, cam_y)

    def _draw_body(self, surface, sx, sy):
        pygame.draw.circle(surface, self.color, (sx, sy), self.radius)
        pygame.draw.circle(surface, self.color2, (sx, sy), self.radius, 2)


# ─── Specific Enemies ──────────────────────────────────────────────────────────

class WorkerAnt(Enemy):
    ETYPE = ENEMY_ANT
    def __init__(self, x, y):
        super().__init__(x, y)
        self.max_health = 35
        self.health     = 35
        self.damage     = 7
        self.speed      = 95
        self.radius     = 16
        self.color      = (180, 90, 30)
        self.color2     = (120, 50, 10)
        self.xp_reward  = 12
        self.aggro_range= 200
        self.drops      = [("ant_part", 1, 3), ("ant_mandible", 0, 1)]

    def _draw_body(self, surf, sx, sy):
        # Three-segment ant body
        for i, (dy, rx, ry, col) in enumerate([
            (10, 14, 10, self.color),  # abdomen
            (0,  10, 8,  self.color),  # thorax
            (-10, 8, 7,  self.color2), # head
        ]):
            pygame.draw.ellipse(surf, col, (sx-rx, sy+dy-ry, rx*2, ry*2))
        # Antennae
        pygame.draw.line(surf, self.color2, (sx-4, sy-16), (sx-10, sy-26), 2)
        pygame.draw.line(surf, self.color2, (sx+4, sy-16), (sx+10, sy-26), 2)
        # Legs (6)
        for side in (-1, 1):
            for leg_y in (-2, 2, 6):
                ex = sx + side * (self.radius + 8)
                ey = sy + leg_y + 4
                pygame.draw.line(surf, self.color2, (sx + side*8, sy+leg_y), (ex, ey), 2)


class FireAnt(Enemy):
    ETYPE = ENEMY_FIRE_ANT
    def __init__(self, x, y):
        super().__init__(x, y)
        self.max_health = 50
        self.health     = 50
        self.damage     = 14
        self.speed      = 110
        self.radius     = 17
        self.color      = (220, 60, 20)
        self.color2     = (160, 20, 0)
        self.xp_reward  = 25
        self.aggro_range= 280
        self.atk_rate   = 1.0
        self.drops      = [("ant_part", 1, 3), ("ant_mandible", 1, 2), ("ant_head", 0, 1)]

    def _draw_body(self, surf, sx, sy):
        for i, (dy, rx, ry, col) in enumerate([
            (10, 14, 10, (200, 50, 10)),
            (0,  10, 8,  self.color),
            (-10, 8, 7,  self.color2),
        ]):
            pygame.draw.ellipse(surf, col, (sx-rx, sy+dy-ry, rx*2, ry*2))
        # Fire particles
        for _ in range(3):
            fx = sx + random.randint(-6, 6)
            fy = sy - 8 + random.randint(-4, 0)
            pygame.draw.circle(surf, (255, random.randint(100,200), 0), (fx, fy), 3)
        pygame.draw.line(surf, self.color2, (sx-4, sy-16), (sx-10, sy-26), 2)
        pygame.draw.line(surf, self.color2, (sx+4, sy-16), (sx+10, sy-26), 2)


class OrbWeaverSpider(Enemy):
    ETYPE = ENEMY_SPIDER
    def __init__(self, x, y):
        super().__init__(x, y)
        self.max_health = 60
        self.health     = 60
        self.damage     = 18
        self.speed      = 130
        self.radius     = 22
        self.color      = (40, 30, 50)
        self.color2     = (80, 50, 100)
        self.xp_reward  = 40
        self.aggro_range= 300
        self.atk_rate   = 1.5
        self.drops      = [("spider_silk", 1, 4), ("spider_fang", 0, 2), ("spider_part", 1, 3)]
        self._web_cd    = 0.0

    def update(self, dt, player, world):
        super().update(dt, player, world)
        # Web slow: periodically leaves web trap (visual only for now)
        self._web_cd = max(0, self._web_cd - dt)

    def _draw_body(self, surf, sx, sy):
        r = self.radius
        # 8 legs
        for i in range(8):
            angle = math.pi * i / 4 + self.facing
            ex = sx + int(math.cos(angle) * (r + 14))
            ey = sy + int(math.sin(angle) * (r + 14))
            pygame.draw.line(surf, self.color2, (sx + int(math.cos(angle)*r//2), sy + int(math.sin(angle)*r//2)), (ex, ey), 2)
        # Body
        pygame.draw.ellipse(surf, self.color, (sx-r, sy-r//2, r*2, int(r*1.2)))
        pygame.draw.circle(surf, (60, 40, 80), (sx, sy-r//3), r//2)
        # Eyes (8 tiny)
        for ex, ey in [(-6,-4),(0,-4),(6,-4),(-8,0),(8,0)]:
            pygame.draw.circle(surf, (255, 50, 50), (sx+ex-r//3, sy+ey-r//3), 2)


class LadyBug(Enemy):
    ETYPE = ENEMY_LADYBUG
    def __init__(self, x, y):
        super().__init__(x, y)
        self.max_health = 120
        self.health     = 120
        self.damage     = 12
        self.speed      = 55
        self.radius     = 28
        self.color      = (210, 40, 40)
        self.color2     = (140, 10, 10)
        self.xp_reward  = 50
        self.aggro_range= 150   # passive unless attacked
        self.atk_rate   = 2.0
        self.drops      = [("ladybug_shell", 1, 2)]
        self._passive   = True  # won't aggro until hit

    def take_damage(self, amount, dir_x=0, dir_y=0, kb_force=100):
        self._passive = False
        return super().take_damage(amount, dir_x, dir_y, kb_force)

    def update(self, dt, player, world):
        if self._passive:
            self._wander(dt, world)
            self.hurt_flash = max(0, self.hurt_flash - dt)
            self.atk_cd    = max(0, self.atk_cd - dt)
        else:
            super().update(dt, player, world)

    def _draw_body(self, surf, sx, sy):
        r = self.radius
        # Shell
        pygame.draw.ellipse(surf, self.color, (sx-r, sy-r, r*2, int(r*1.3)))
        # Black center line
        pygame.draw.line(surf, BLACK, (sx, sy-r), (sx, sy+r-4), 3)
        # Spots
        for (ox, oy) in [(-r//3, -r//3), (r//3, -r//3), (-r//4, r//4), (r//4, r//4)]:
            pygame.draw.circle(surf, BLACK, (sx+ox, sy+oy), r//5)
        # Head
        pygame.draw.circle(surf, BLACK, (sx, sy-r+4), r//3)


class StinkBug(Enemy):
    ETYPE = ENEMY_STINKBUG
    def __init__(self, x, y):
        super().__init__(x, y)
        self.max_health = 70
        self.health     = 70
        self.damage     = 10
        self.speed      = 65
        self.radius     = 24
        self.color      = (80, 130, 50)
        self.color2     = (50, 90, 20)
        self.xp_reward  = 30
        self.aggro_range= 220
        self.atk_rate   = 2.5
        self.drops      = [("stinkbug_gas", 1, 2), ("ant_part", 0, 1)]
        self._gas_cd    = 0.0

    def update(self, dt, player, world):
        super().update(dt, player, world)
        self._gas_cd = max(0, self._gas_cd - dt)
        # Gas cloud attack when player is close
        if self.is_aggro and self._gas_cd <= 0:
            dist = self.dist_to_player(player)
            if dist < 80:
                player.take_damage(6)
                self._gas_cd = 3.0

    def _draw_body(self, surf, sx, sy):
        r = self.radius
        # Pentagonal shield body
        pts = [(sx, sy-r), (sx+r, sy-r//3), (sx+r*2//3, sy+r),
               (sx-r*2//3, sy+r), (sx-r, sy-r//3)]
        pygame.draw.polygon(surf, self.color, pts)
        pygame.draw.polygon(surf, self.color2, pts, 2)
        # Gas vents
        for ox in (-8, 0, 8):
            pygame.draw.circle(surf, (60, 200, 60, 120), (sx+ox, sy+r-4), 3)


class BombardierBeetle(Enemy):
    ETYPE = ENEMY_BOMBARDIER
    def __init__(self, x, y):
        super().__init__(x, y)
        self.max_health = 55
        self.health     = 55
        self.damage     = 6   # melee weak, ranged strong
        self.speed      = 75
        self.radius     = 20
        self.color      = (60, 50, 20)
        self.color2     = (120, 100, 30)
        self.xp_reward  = 35
        self.aggro_range= 320
        self.atk_rate   = 3.0
        self.drops      = [("bombardier_gland", 1, 2), ("ant_part", 0, 1)]
        self._shoot_cd  = 0.0
        self.preferred_range = 200

    def update(self, dt, player, world):
        if not self.active:
            return
        self.hurt_flash = max(0, self.hurt_flash - dt)
        self.atk_cd    = max(0, self.atk_cd - dt)
        self._shoot_cd = max(0, self._shoot_cd - dt)

        dist = self.dist_to_player(player)
        if dist < self.aggro_range:
            self.is_aggro = True

        if self.is_aggro:
            if dist > self.deaggro_range:
                self.is_aggro = False
                return
            # Keep preferred range
            if dist < self.preferred_range - 30:
                # Back away
                dx = self.x - player.x
                dy = self.y - player.y
                self._move_toward(self.x + dx*0.5, self.y + dy*0.5, dt, world)
            elif dist > self.preferred_range + 30:
                self._move_toward(player.x, player.y, dt, world)
            # Ranged attack
            if self._shoot_cd <= 0 and dist < self.preferred_range + 50:
                angle = math.atan2(player.y - self.y, player.x - self.x)
                self.projectiles.append(
                    Projectile(self.x, self.y, angle, 280, 20, ORANGE, 8)
                )
                self._shoot_cd = 2.0
        else:
            self._wander(dt, world)

        for proj in self.projectiles:
            proj.update(dt, world)
            if proj.active:
                if math.hypot(proj.x - player.x, proj.y - player.y) < proj.radius + player.radius:
                    player.take_damage(proj.damage)
                    proj.active = False
        self.projectiles = [p for p in self.projectiles if p.active]

    def _draw_body(self, surf, sx, sy):
        r = self.radius
        pygame.draw.ellipse(surf, self.color2, (sx-r, sy-r//2, r*2, r))
        pygame.draw.ellipse(surf, self.color, (sx-r+4, sy-r+2, r*2-8, r*2-4))
        pygame.draw.circle(surf, (80, 70, 20), (sx, sy-r+4), r//3)
        # Cannon nozzle
        angle = self.facing
        nx = int(math.cos(angle) * r)
        ny = int(math.sin(angle) * r)
        pygame.draw.line(surf, (40, 30, 10), (sx, sy), (sx+nx, sy+ny), 5)


class Weevil(Enemy):
    ETYPE = ENEMY_WEEVIL
    def __init__(self, x, y):
        super().__init__(x, y)
        self.max_health = 40
        self.health     = 40
        self.damage     = 9
        self.speed      = 70
        self.radius     = 18
        self.color      = (70, 55, 35)
        self.color2     = (50, 35, 15)
        self.xp_reward  = 18
        self.aggro_range= 180
        self.drops      = [("weevil_nose", 0, 1), ("ant_part", 1, 2)]

    def _draw_body(self, surf, sx, sy):
        r = self.radius
        pygame.draw.ellipse(surf, self.color, (sx-r, sy-int(r*0.7), r*2, int(r*1.4)))
        # Long snout
        angle = self.facing
        nx = int(math.cos(angle) * (r+10))
        ny = int(math.sin(angle) * (r+10))
        pygame.draw.line(surf, self.color2, (sx, sy), (sx+nx, sy+ny), 4)
        pygame.draw.circle(surf, self.color2, (sx, sy-r//3), r//3)


class Aphid(Enemy):
    ETYPE = ENEMY_APHID
    def __init__(self, x, y):
        super().__init__(x, y)
        self.max_health = 15
        self.health     = 15
        self.damage     = 3
        self.speed      = 40
        self.radius     = 12
        self.color      = (180, 210, 80)
        self.color2     = (120, 160, 40)
        self.xp_reward  = 5
        self.aggro_range= 0   # passive
        self.drops      = [("aphid_honeydew", 1, 3)]
        self._passive   = True

    def take_damage(self, amount, dir_x=0, dir_y=0, kb_force=100):
        return super().take_damage(amount, dir_x, dir_y, kb_force)

    def update(self, dt, player, world):
        self.hurt_flash = max(0, self.hurt_flash - dt)
        if not self.active:
            return
        if self.health < self.max_health:
            self._move_toward(self.x - (player.x - self.x), self.y - (player.y - self.y), dt*0.5, world)
        else:
            self._wander(dt, world)

    def _draw_body(self, surf, sx, sy):
        r = self.radius
        pygame.draw.ellipse(surf, self.color, (sx-r, sy-r//2, r*2, r))
        pygame.draw.circle(surf, self.color2, (sx, sy-r//2), r//2)


# ─── Enemy Spawner ─────────────────────────────────────────────────────────────
ENEMY_TYPES = [WorkerAnt, FireAnt, OrbWeaverSpider, LadyBug,
               StinkBug, BombardierBeetle, Weevil, Aphid]

BIOME_ENEMIES = {
    TILE_GRASS:     [WorkerAnt, WorkerAnt, Aphid, LadyBug],
    TILE_DRY_GRASS: [WorkerAnt, FireAnt, Weevil],
    TILE_DIRT:      [WorkerAnt, Weevil, FireAnt],
    TILE_LEAVES:    [OrbWeaverSpider, OrbWeaverSpider, LadyBug, StinkBug],
    TILE_STONE:     [BombardierBeetle, StinkBug, Weevil],
    TILE_SAND:      [WorkerAnt, Aphid, Weevil],
    TILE_MUD:       [StinkBug, Aphid],
    TILE_CLOVER:    [Aphid, Aphid, LadyBug, WorkerAnt],
}

def spawn_enemies(world, count=60):
    enemies = []
    attempts = 0
    while len(enemies) < count and attempts < count * 10:
        attempts += 1
        tx = random.randint(5, world.width - 5)
        ty = random.randint(5, world.height - 5)
        tile = world.get_tile(tx, ty)
        if tile == TILE_WATER:
            continue
        cx = world.width // 2
        cy = world.height // 2
        if abs(tx-cx) < 8 and abs(ty-cy) < 8:
            continue  # Don't spawn near player start
        elist = BIOME_ENEMIES.get(tile, [WorkerAnt])
        EClass = random.choice(elist)
        wx = tx * TILE_SIZE + random.randint(10, TILE_SIZE-10)
        wy = ty * TILE_SIZE + random.randint(10, TILE_SIZE-10)
        enemies.append(EClass(wx, wy))
    return enemies
