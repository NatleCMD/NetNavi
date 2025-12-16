"""
Area Scene - Isometric map exploration with wandering Navi.
Encounters random battles and collectible items.
"""

import pygame
import math
import random
from scenes.base_scene import BaseScene


class AreaScene(BaseScene):
    """Isometric area exploration with auto-wandering Navi."""

    target_fps = 20

    TILE_FLOOR = 0
    TILE_WALL = 1
    TILE_EXIT = 3
    TILE_DANGER = 4

    def __init__(self, manager, area: dict = None):
        super().__init__(manager)
        self.area = area or {}

        # Isometric settings for small screen
        self.tile_width = 24
        self.tile_height = 12
        self.map_width = 10
        self.map_height = 10

        # Generate map
        seed = self.area.get("seed", random.randint(0, 99999))
        self.rng = random.Random(seed)
        self.map_data = self._generate_map()
        self.items = self._place_items()

        # Navi position
        self.navi_x, self.navi_y = 1, 1
        self.navi_target_x, self.navi_target_y = 1, 1
        self.navi_moving = False
        self.move_progress = 0.0
        self.visual_x, self.visual_y = 1.0, 1.0

        # AI
        self.ai_timer = 0.0

        # Stats
        self.items_collected = 0
        self.battles_won = 0
        self.boss_defeated = False
        self.steps = 0
        self.total_steps = 0  # Track for HP regen (1000 steps = 10 HP)

        # Item popup display
        self.item_popup = None  # {"text": "Got 50z!", "timer": 2.0}

        # State
        self.state = "exploring"
        self.flash_timer = 0.0
        self.anim_timer = 0.0

    def _generate_map(self):
        tiles = [[self.TILE_FLOOR] * self.map_width for _ in range(self.map_height)]

        # Borders
        for x in range(self.map_width):
            tiles[0][x] = self.TILE_WALL
            tiles[self.map_height-1][x] = self.TILE_WALL
        for y in range(self.map_height):
            tiles[y][0] = self.TILE_WALL
            tiles[y][self.map_width-1] = self.TILE_WALL

        # Random walls
        for _ in range(self.rng.randint(5, 10)):
            x, y = self.rng.randint(2, self.map_width-3), self.rng.randint(2, self.map_height-3)
            tiles[y][x] = self.TILE_WALL

        # Danger zones
        for _ in range(self.rng.randint(4, 8)):
            x, y = self.rng.randint(2, self.map_width-3), self.rng.randint(2, self.map_height-3)
            if tiles[y][x] == self.TILE_FLOOR:
                tiles[y][x] = self.TILE_DANGER

        # Exit
        tiles[self.map_height-2][self.map_width-2] = self.TILE_EXIT
        tiles[1][1] = self.TILE_FLOOR

        return tiles

    def _place_items(self):
        items = []
        for _ in range(self.rng.randint(3, 5)):
            for _ in range(20):
                x, y = self.rng.randint(2, self.map_width-3), self.rng.randint(2, self.map_height-3)
                if self.map_data[y][x] == self.TILE_FLOOR:
                    if not any(i[0] == x and i[1] == y for i in items):
                        items.append([x, y, self.rng.choice(["zenny", "hp"])])
                        break
        return items

    def _grid_to_screen(self, gx, gy):
        ix = (gx - gy) * (self.tile_width // 2) + self.width // 2
        iy = (gx + gy) * (self.tile_height // 2) + 30
        return ix, iy

    def _is_walkable(self, x, y):
        if 0 <= x < self.map_width and 0 <= y < self.map_height:
            return self.map_data[y][x] != self.TILE_WALL
        return False

    def update(self, dt):
        self.anim_timer += dt

        # Update item popup
        if self.item_popup:
            self.item_popup["timer"] -= dt
            if self.item_popup["timer"] <= 0:
                self.item_popup = None

        if self.state == "exploring":
            if not self.navi_moving:
                self.ai_timer += dt
                if self.ai_timer > 0.4:
                    self.ai_timer = 0
                    self._ai_move()
            else:
                self.move_progress += dt * 2.5
                if self.move_progress >= 1.0:
                    self.navi_x, self.navi_y = self.navi_target_x, self.navi_target_y
                    self.visual_x, self.visual_y = float(self.navi_x), float(self.navi_y)
                    self.navi_moving = False
                    self.move_progress = 0
                    self._on_arrive()
                else:
                    self.visual_x = self.navi_x + (self.navi_target_x - self.navi_x) * self.move_progress
                    self.visual_y = self.navi_y + (self.navi_target_y - self.navi_y) * self.move_progress

        elif self.state == "flash":
            self.flash_timer -= dt
            if self.flash_timer <= 0:
                self._start_battle()

    def _ai_move(self):
        """Navi AI prioritizes: 1) Collect items, 2) Head to exit if done, 3) Explore."""
        # Priority 1: Go to nearest item
        if self.items:
            nearest = None
            nearest_d = 999
            for ix, iy, _ in self.items:
                d = abs(ix - self.navi_x) + abs(iy - self.navi_y)
                if d < nearest_d:
                    nearest_d, nearest = d, (ix, iy)

            if nearest:
                self._move_toward(nearest[0], nearest[1])
                return

        # Priority 2: Head to exit if boss defeated or enough battles won
        if self.boss_defeated or self.battles_won >= 3:
            self._move_toward(self.map_width-2, self.map_height-2)
            return

        # Priority 3: Random exploration
        self._wander()

    def _move_toward(self, tx, ty):
        dx = 0 if tx == self.navi_x else (1 if tx > self.navi_x else -1)
        dy = 0 if ty == self.navi_y else (1 if ty > self.navi_y else -1)

        if dx and self._is_walkable(self.navi_x + dx, self.navi_y):
            self._do_move(dx, 0)
        elif dy and self._is_walkable(self.navi_x, self.navi_y + dy):
            self._do_move(0, dy)
        else:
            self._wander()

    def _wander(self):
        dirs = [(1,0), (-1,0), (0,1), (0,-1)]
        self.rng.shuffle(dirs)
        for dx, dy in dirs:
            if self._is_walkable(self.navi_x + dx, self.navi_y + dy):
                self._do_move(dx, dy)
                return

    def _do_move(self, dx, dy):
        self.navi_target_x = self.navi_x + dx
        self.navi_target_y = self.navi_y + dy
        self.navi_moving = True
        self.move_progress = 0

    def _on_arrive(self):
        # Track total steps for HP regen
        self.total_steps += 1
        self._check_step_hp_regen()

        # Collect items
        for item in self.items[:]:
            if item[0] == self.navi_x and item[1] == self.navi_y:
                self._collect(item)
                self.items.remove(item)

        tile = self.map_data[self.navi_y][self.navi_x]

        # Exit check
        if tile == self.TILE_EXIT and (self.boss_defeated or self.battles_won >= 3):
            self._complete_area()
            return

        # Encounter check - randomized with cooldown
        self.steps += 1

        # Minimum steps between encounters (3-6 steps)
        min_steps = 3 + self.rng.randint(0, 3)
        if self.steps < min_steps:
            return

        # Variable encounter rate
        if tile == self.TILE_DANGER:
            # Danger tiles: 20-40% chance
            chance = 0.2 + self.rng.random() * 0.2
        else:
            # Normal tiles: 5-12% chance
            chance = 0.05 + self.rng.random() * 0.07

        # Increase chance slightly with more steps (max 50%)
        chance = min(0.5, chance + (self.steps - min_steps) * 0.02)

        if self.rng.random() < chance:
            self.steps = 0  # Reset step counter
            self.state = "flash"
            self.flash_timer = 0.4

    def _collect(self, item):
        navi = self.game_state["navi"]
        popup_text = ""

        if item[2] == "zenny":
            amount = self.rng.randint(20, 50)
            self.game_state["zenny"] += amount
            popup_text = f"+{amount}z"
        elif item[2] == "hp":
            heal = 30
            navi["hp"] = min(navi["max_hp"], navi["hp"] + heal)
            popup_text = f"+{heal} HP"

        self.items_collected += 1
        self.item_popup = {"text": popup_text, "timer": 1.5}

    def _check_step_hp_regen(self):
        """Check if we've walked 1000 steps for HP regen."""
        if self.total_steps >= 1000:
            self.total_steps -= 1000
            navi = self.game_state["navi"]
            if navi["hp"] < navi["max_hp"]:
                heal = min(10, navi["max_hp"] - navi["hp"])
                navi["hp"] += heal
                self.item_popup = {"text": f"+{heal} HP (steps)", "timer": 1.5}

    def _start_battle(self):
        is_boss = self.battles_won >= 2 and not self.boss_defeated
        if is_boss:
            enemy = {"name": "BossVirus", "hp": 100, "attack": 18, "defense": 4, "is_boss": True}
        else:
            enemy = {"name": self.rng.choice(["Mettaur", "Spikey", "Bunny"]),
                    "hp": 40, "attack": 10, "defense": 2, "is_boss": False}
        self.manager.push_scene("battle", enemy=enemy, area=self.area)

    def _complete_area(self):
        """Mark area as completed with 24hr cooldown."""
        import time

        # Mark this area as completed
        ssid = self.area.get("ssid", "")
        if ssid:
            if "completed_areas" not in self.game_state:
                self.game_state["completed_areas"] = {}
            self.game_state["completed_areas"][ssid] = time.time()

        # Return to hub
        self.manager.change_scene("hub")

    def on_enter(self):
        """Called when scene becomes active (including returning from battle)."""
        # Check if we're returning from a battle
        if self.state == "flash":
            # We were in flash state before battle, battle must have ended
            self.state = "exploring"
            self.battles_won += 1

            # Check if that was the boss
            if self.battles_won >= 3 and not self.boss_defeated:
                self.boss_defeated = True

    def handle_event(self, event):
        if event.type == pygame.USEREVENT and event.dict.get("action") == "cancel":
            self.manager.change_scene("hub")

    def draw(self, screen):
        # Background
        screen.fill((20, 25, 35))

        # Tiles
        for y in range(self.map_height):
            for x in range(self.map_width):
                self._draw_tile(screen, x, y)

        # Items
        for ix, iy, reward in self.items:
            self._draw_item(screen, ix, iy, reward)

        # Navi
        self._draw_navi(screen)

        # UI
        self._draw_ui(screen)

        # Flash
        if self.state == "flash":
            s = pygame.Surface((self.width, self.height))
            s.fill((255, 255, 255))
            s.set_alpha(int(180 * (self.flash_timer / 0.4)))
            screen.blit(s, (0, 0))

    def _draw_tile(self, screen, gx, gy):
        tile = self.map_data[gy][gx]
        sx, sy = self._grid_to_screen(gx, gy)
        tw, th = self.tile_width // 2, self.tile_height // 2

        if tile == self.TILE_WALL:
            color = (50, 55, 70)
        elif tile == self.TILE_EXIT:
            color = (80, 180, 220)
        elif tile == self.TILE_DANGER:
            pulse = (math.sin(self.anim_timer * 2 + gx) + 1) / 2
            color = (70 + int(pulse * 30), 40, 40)
        else:
            color = (35 + (gx + gy) % 10, 45 + (gx + gy) % 10, 60 + (gx + gy) % 10)

        pts = [(sx, sy - th), (sx + tw, sy), (sx, sy + th), (sx - tw, sy)]
        pygame.draw.polygon(screen, color, pts)
        pygame.draw.polygon(screen, (70, 75, 90), pts, 1)

    def _draw_item(self, screen, gx, gy, reward):
        sx, sy = self._grid_to_screen(gx, gy)
        bob = math.sin(self.anim_timer * 3 + gx) * 2
        spin = abs(math.sin(self.anim_timer * 2 + gx * 0.3))
        hw = int(4 * spin + 2)

        color = (255, 220, 50) if reward == "zenny" else (80, 255, 120)
        pts = [(sx, sy - 8 - bob), (sx + hw, sy - bob), (sx, sy + 6 - bob), (sx - hw, sy - bob)]
        pygame.draw.polygon(screen, color, pts)

    def _draw_navi(self, screen):
        sx, sy = self._grid_to_screen(self.visual_x, self.visual_y)
        bob = math.sin(self.anim_timer * 4) * 2
        sy -= 8 + bob

        pygame.draw.circle(screen, (0, 100, 220), (int(sx), int(sy)), 8)
        pygame.draw.circle(screen, (0, 220, 200), (int(sx), int(sy)), 8, 2)
        pygame.draw.ellipse(screen, (0, 220, 200), (sx - 5, sy - 2, 10, 4))

    def _draw_ui(self, screen):
        navi = self.game_state["navi"]
        self.draw_panel(screen, 2, 2, 90, 16, border_width=1)
        name = self.area.get("display_name", "Area")[:12]
        self.draw_text(screen, name, 5, 3, size=11, color=self.colors["accent_cyan"])

        self.draw_progress_bar(screen, 2, 20, 50, 6, navi["hp"], navi["max_hp"])
        self.draw_text(screen, f"W:{self.battles_won}", 2, 30, size=10, color=self.colors["text_dim"])

        # Item popup (centered, prominent)
        if self.item_popup:
            popup_y = self.height // 2 - 40
            # Background box
            self.draw_panel(screen, self.width // 2 - 50, popup_y - 5, 100, 25,
                           color=(20, 60, 40), border_color=self.colors["hp_green"])
            self.draw_text(screen, self.item_popup["text"], self.width // 2, popup_y + 5,
                          size=16, center=True, color=self.colors["hp_green"])

        # Step counter
        self.draw_text(screen, f"Steps:{self.total_steps}/1000", 2, self.height - 12,
                      size=9, color=self.colors["text_dim"])