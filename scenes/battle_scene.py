"""
Battle Scene - Grid-based combat with MMBN-style mechanics.

This version adds BN-style chip behaviors:
- projectile (default)
- spreader (on-hit behind/diagonals)
- shotgun (on-hit tile behind)
- airshot push (push enemy back)
- lob bomb (delayed impact on a panel)
- invis (timed invulnerability)

Works even if Chip doesn't define behavior/params:
- Falls back to name-based behavior mapping.
"""

import pygame
import math
import random
from scenes.base_scene import BaseScene
from combat.chips import Chip, CHIP_DATABASE, roll_chip_drop
from navi_sprites import get_navi_sprites

class Projectile:
    """A moving projectile on the battle grid."""
    def __init__(
        self,
        x, y, dx, dy,
        damage,
        color,
        from_enemy=True,
        speed=4.0,
        pierce=False,
        on_hit=None,
        hit_radius=0.6
    ):
        self.x, self.y = float(x), float(y)
        self.dx, self.dy = dx, dy
        self.damage = damage
        self.color = color
        self.from_enemy = from_enemy
        self.alive = True
        self.speed = speed

        # BN-style extensions
        self.pierce = pierce          # If True, doesn't die on first hit
        self.on_hit = on_hit          # callback(enemy_or_none, hit_x, hit_y)
        self.hit_radius = hit_radius  # collision radius


class SlashEffect:
    """Visual effect for sword attacks."""
    def __init__(self, positions, color, duration=0.3):
        self.positions = positions  # List of (grid_x, grid_y)
        self.color = color
        self.timer = duration
        self.max_time = duration


class ImpactEffect:
    """Delayed impact for lobbed chips (bombs)."""
    def __init__(self, gx, gy, damage, color, delay=0.45, splash=None, on_impact=None):
        self.gx = gx
        self.gy = gy
        self.damage = damage
        self.color = color
        self.timer = delay
        self.splash = splash  # None | "single" | "cross1" | "cross2" | "square1"
        self.on_impact = on_impact
        self.alive = True


class Enemy:
    """An enemy virus in battle."""
    def __init__(self, name, hp, attack, defense, x, y, is_boss=False):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.attack = attack
        self.defense = defense
        self.x = x
        self.y = y
        self.is_boss = is_boss
        self.attack_timer = random.uniform(0.5, 1.5)  # Stagger attacks
        self.move_timer = random.uniform(0.3, 0.8)
        self.alive = True


class BattleScene(BaseScene):
    """Grid-based battle with custom screen chip selection."""

    target_fps = 24

    def __init__(self, manager, enemy: dict = None, area: dict = None, **kwargs):
        super().__init__(manager)
        self.area = area or {}
        # Sprite manager for Navi animations
        self.navi_sprites = get_navi_sprites()
        self.navi_sprites.play_idle()

        # Grid: 3 rows x 6 cols
        self.grid_cols = 6
        self.grid_rows = 3
        self.cell_width = 40
        self.cell_height = 28
        self.grid_x = (self.width - self.grid_cols * self.cell_width) // 2
        self.grid_y = 70

        # Spawn 1-3 enemies
        self.enemies = self._spawn_enemies(enemy)

        # Navi state
        self.navi_x, self.navi_y = 1, 1
        self.navi_move_timer = 0.0
        self.navi_buster_timer = 0.0
        self.buster_cooldown = 0.8  # Auto-fire buster every 0.8 sec

        # BN-style defensive timers
        self.navi_invis_timer = 0.0

        # Projectiles and effects
        self.projectiles = []
        self.slash_effects = []
        self.impact_effects = []  # lob impacts

        # Custom screen / chip system
        self.custom_gauge = 0.0
        self.custom_gauge_max = 15.0
        self.in_custom_screen = False
        self.drawn_chips = []
        self.selected_chips = []
        self.chip_cursor = 0
        self.chip_queue = []

        # Battle state
        self.phase = "intro"  # intro, battle, custom, win, lose
        self.phase_timer = 1.0

        # Animation
        self.anim_timer = 0.0
        self.hit_flash = 0.0
        self.shake = 0.0

        # Damage popups
        self.damage_popups = []

        # Rewards
        self.rewards = {"zenny": 0, "chips": []}
        self.battle_result = None

    def _spawn_enemies(self, enemy_data):
        enemies = []
        enemy_data = enemy_data or {}

        roll = random.random()
        if roll < 0.5:
            count = 1
        elif roll < 0.85:
            count = 2
        else:
            count = 3

        virus_types = [
            {"name": "Mettaur", "hp": 40, "attack": 10, "defense": 2},
            {"name": "Spikey", "hp": 50, "attack": 12, "defense": 1},
            {"name": "Bunny", "hp": 35, "attack": 15, "defense": 0},
            {"name": "Fishy", "hp": 45, "attack": 14, "defense": 2},
            {"name": "Canodumb", "hp": 60, "attack": 8, "defense": 4},
        ]

        if enemy_data.get("is_boss"):
            boss = Enemy(
                enemy_data.get("name", "BossVirus"),
                enemy_data.get("hp", 120),
                enemy_data.get("attack", 20),
                enemy_data.get("defense", 5),
                4, 1, is_boss=True
            )
            return [boss]

        positions = [(4, 0), (5, 1), (4, 2), (5, 0), (5, 2)]
        random.shuffle(positions)

        for i in range(count):
            template = random.choice(virus_types)
            pos = positions[i]
            e = Enemy(
                template["name"],
                template["hp"],
                template["attack"],
                template["defense"],
                pos[0], pos[1]
            )
            enemies.append(e)

        return enemies

    def update(self, dt):
        # Update Navi sprite animation
        self.navi_sprites.update(dt)
        self.anim_timer += dt
        self.hit_flash = max(0, self.hit_flash - dt * 5)
        self.shake = max(0, self.shake - dt * 8)

        # BN timers
        self.navi_invis_timer = max(0.0, self.navi_invis_timer - dt)

        # Update damage popups
        for p in self.damage_popups[:]:
            p[3] -= dt
            if p[3] <= 0:
                self.damage_popups.remove(p)

        # Update slash effects
        for s in self.slash_effects[:]:
            s.timer -= dt
            if s.timer <= 0:
                self.slash_effects.remove(s)

        # Update bomb impacts
        self._update_impacts(dt)

        # Phase logic
        if self.phase == "intro":
            self.phase_timer -= dt
            if self.phase_timer <= 0:
                self.phase = "battle"
                self.custom_gauge = self.custom_gauge_max

        elif self.phase == "battle":
            self._update_battle(dt)

        elif self.phase == "custom":
            pass

        elif self.phase in ["win", "lose"]:
            self.phase_timer -= dt

    def _update_battle(self, dt):
        self._update_projectiles(dt)
        self._update_navi(dt)
        self._update_enemies(dt)

        self.custom_gauge += dt
        self.custom_gauge = min(self.custom_gauge, self.custom_gauge_max)

        # Return to idle if hit flash and invis are over
        if self.hit_flash <= 0 and self.navi_invis_timer <= 0:
            # Only return to idle if not in other animation
            if self.navi_sprites.current_animation in ["hurt", "move"]:
                self.navi_sprites.play_idle()

        if all(not e.alive for e in self.enemies):
            self._win()
        elif self.game_state["navi"]["hp"] <= 0:
            self._lose()

    def _update_impacts(self, dt):
        for imp in self.impact_effects[:]:
            imp.timer -= dt
            if imp.timer <= 0 and imp.alive:
                imp.alive = False
                self._resolve_impact(imp)
                if imp.on_impact:
                    try:
                        imp.on_impact(imp.gx, imp.gy)
                    except Exception:
                        pass

        self.impact_effects = [i for i in self.impact_effects if i.alive]

    def _resolve_impact(self, imp: ImpactEffect):
        hit_tiles = [(imp.gx, imp.gy)]
        if imp.splash == "cross1":
            hit_tiles += [(imp.gx - 1, imp.gy), (imp.gx + 1, imp.gy), (imp.gx, imp.gy - 1), (imp.gx, imp.gy + 1)]
        elif imp.splash == "cross2":
            for r in (1, 2):
                hit_tiles += [(imp.gx - r, imp.gy), (imp.gx + r, imp.gy), (imp.gx, imp.gy - r), (imp.gx, imp.gy + r)]
        elif imp.splash == "square1":
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    hit_tiles.append((imp.gx + dx, imp.gy + dy))

        # clamp + apply damage to enemies on those tiles
        for tx, ty in hit_tiles:
            if not (0 <= tx < self.grid_cols and 0 <= ty < self.grid_rows):
                continue
            for enemy in self.enemies:
                if enemy.alive and enemy.x == tx and enemy.y == ty:
                    self._enemy_hit(enemy, imp.damage)

        # light screen shake / popup feedback
        sx, sy = self._grid_to_screen(imp.gx, imp.gy)
        self.damage_popups.append([sx, sy - 20, "BOOM", 0.6, imp.color])
        self.shake = max(self.shake, 0.5)

    def _update_projectiles(self, dt):
        for proj in self.projectiles[:]:
            proj.x += proj.dx * proj.speed * dt
            proj.y += proj.dy * proj.speed * dt

            if proj.x < -1 or proj.x > self.grid_cols or proj.y < -1 or proj.y > self.grid_rows:
                proj.alive = False
                continue

            # Enemy projectile hits Navi
            if proj.from_enemy and proj.alive:
                if abs(proj.x - self.navi_x) < proj.hit_radius and abs(proj.y - self.navi_y) < proj.hit_radius:
                    self._navi_hit(proj.damage)
                    proj.alive = False

            # Navi projectile hits enemies
            if not proj.from_enemy and proj.alive:
                for enemy in self.enemies:
                    if enemy.alive and abs(proj.x - enemy.x) < proj.hit_radius and abs(proj.y - enemy.y) < proj.hit_radius:
                        # primary hit
                        self._enemy_hit(enemy, proj.damage)

                        # on-hit behavior
                        if proj.on_hit:
                            try:
                                proj.on_hit(enemy, enemy.x, enemy.y)
                            except Exception:
                                pass

                        if not proj.pierce:
                            proj.alive = False
                        break

        self.projectiles = [p for p in self.projectiles if p.alive]

    def _update_navi(self, dt):
        # Movement
        self.navi_move_timer += dt
        if self.navi_move_timer >= 0.5:
            self.navi_move_timer = 0
            self._navi_ai_move()

        # Auto-fire buster only
        self.navi_buster_timer += dt
        if self.navi_buster_timer >= self.buster_cooldown:
            self.navi_buster_timer = 0
            self._fire_buster()

    def _navi_ai_move(self):
        danger_row = None
        for proj in self.projectiles:
            if proj.from_enemy and proj.dx < 0 and 0 < proj.x < 3.5:
                if abs(proj.y - self.navi_y) < 0.6:
                    danger_row = int(round(proj.y))
                    break

        if danger_row is not None:
            safe = [r for r in range(3) if r != danger_row]
            if safe:
                safe.sort(key=lambda r: abs(r - self.navi_y))
                self.navi_y = safe[0]
                self.navi_sprites.play_move()
                return

        if random.random() < 0.3:
            if random.random() < 0.7:
                self.navi_y = random.randint(0, 2)
                self.navi_sprites.play_move()
            else:
                self.navi_x = max(0, min(2, self.navi_x + random.choice([-1, 1])))
                self.navi_sprites.play_move()

    def _fire_buster(self):
        navi = self.game_state["navi"]
        buster_attack = navi.get("buster_attack", 1)
        
        # Play buster attack animation only if not already playing
        if self.navi_sprites.current_animation != "buster":
            self.navi_sprites.play_buster()

        proj = Projectile(
            self.navi_x + 0.5, self.navi_y,
            1, 0,
            buster_attack,
            (255, 255, 100),
            from_enemy=False,
            speed=8.0
        )
        self.projectiles.append(proj)

    # ----------------------------
    # BN CHIP BEHAVIOR DISPATCH
    # ----------------------------
    def _use_chip(self, chip):
        """Use a battle chip with BN-style behavior resolution."""
        # 1) Heal chip type stays simple
        if getattr(chip, "chip_type", "") == "heal":
            navi = self.game_state["navi"]
            navi["hp"] = min(navi["max_hp"], navi["hp"] + chip.power)
            sx, sy = self._grid_to_screen(self.navi_x, self.navi_y)
            self.damage_popups.append([sx, sy - 20, f"+{chip.power}", 1.0, self.colors["hp_green"]])
            return

        # 2) Defensive: Invis (either by behavior or by name fallback)
        if self._chip_is_invis(chip):
            self._apply_invis(chip)
            return

        # 3) Melee: swords (your existing logic)
        if chip.chip_type in ["sword", "widesword", "longsword"]:
            self._use_sword(chip)
            return

        # 4) Attacks: choose behavior
        if getattr(chip, "chip_type", "") == "attack":
            behavior = getattr(chip, "behavior", None)
            params = getattr(chip, "params", {}) or {}

            # name-based fallback mapping (works even without chip.behavior)
            if behavior is None:
                behavior, params = self._infer_behavior_from_name(chip, params)

            if behavior == "lob":
                self._use_lob_chip(chip, params)
            elif behavior == "spreader":
                self._fire_spreader(chip, params)
            elif behavior == "shotgun":
                self._fire_shotgun(chip, params)
            elif behavior == "airshot":
                self._fire_airshot(chip, params)
            else:
                # default: straight projectile
                self._fire_chip_projectile(chip, params)
            return

        # 5) If unknown type: do nothing
        return

    def _chip_is_invis(self, chip) -> bool:
        if getattr(chip, "behavior", None) in ("buff_invis", "invis"):
            return True
        name = (getattr(chip, "name", "") or "").lower()
        return "invis" in name

    def _infer_behavior_from_name(self, chip, params):
        name = (chip.name or "").lower()

        # Bomb family
        if "bomb" in name:
            # MiniBomb: single tile; Bomb: cross splash (tweak freely)
            if "mini" in name:
                return "lob", {**params, "dist": 3, "delay": 0.45, "splash": "single"}
            return "lob", {**params, "dist": 3, "delay": 0.5, "splash": "cross1"}

        # Spreader
        if "spreader" in name:
            return "spreader", {**params, "diagonals": True}

        # Shotgun
        if "shotgun" in name:
            return "shotgun", params

        # AirShot
        if "airshot" in name or "air shot" in name:
            return "airshot", {**params, "push": 1}

        return "projectile", params

    # ----------------------------
    # CHIP IMPLEMENTATIONS
    # ----------------------------
    def _apply_invis(self, chip):
        # Default 3 seconds, allow override
        dur = 3.0
        params = getattr(chip, "params", {}) or {}
        if "duration" in params:
            dur = float(params["duration"])
        self.navi_invis_timer = max(self.navi_invis_timer, dur)

        sx, sy = self._grid_to_screen(self.navi_x, self.navi_y)
        self.damage_popups.append([sx, sy - 22, "INVIS", 0.8, self.colors["accent_cyan"]])

    def _use_lob_chip(self, chip, params):
        # Play throw animation
        self.navi_sprites.play_throw()
        
        # Land ~3 panels ahead on same row (simple BN-like baseline)
        dist = int(params.get("dist", 3))
        delay = float(params.get("delay", 0.45))
        splash = params.get("splash", "single")

        gx = min(self.grid_cols - 1, self.navi_x + dist)
        gy = int(self.navi_y)

        imp = ImpactEffect(
            gx, gy,
            damage=chip.power,
            color=self.colors["accent_cyan"],
            delay=delay,
            splash=splash
        )
        self.impact_effects.append(imp)

    def _fire_chip_projectile(self, chip, params=None):
        params = params or {}
        
        # Play buster animation only if not already playing
        if self.navi_sprites.current_animation != "buster":
            self.navi_sprites.play_buster()
        
        proj = Projectile(
            self.navi_x + 0.5, self.navi_y,
            1, 0,
            chip.power,
            self.colors["accent_cyan"],
            from_enemy=False,
            speed=float(params.get("speed", 6.0)),
            pierce=bool(params.get("pierce", False))
        )
        self.projectiles.append(proj)

    def _fire_shotgun(self, chip, params):
        # Play buster animation only if not already playing
        if self.navi_sprites.current_animation != "buster":
            self.navi_sprites.play_buster()
        
        # Like Cannon projectile, but on hit also hits the tile behind target (same row)
        def on_hit(enemy, hx, hy):
            bx, by = int(hx) + 1, int(hy)
            for e in self.enemies:
                if e.alive and e.x == bx and e.y == by:
                    self._enemy_hit(e, chip.power)

        proj = Projectile(
            self.navi_x + 0.5, self.navi_y,
            1, 0,
            chip.power,
            self.colors["accent_cyan"],
            from_enemy=False,
            speed=float(params.get("speed", 6.5)),
            pierce=False,
            on_hit=on_hit
        )
        self.projectiles.append(proj)

    def _fire_spreader(self, chip, params):
        # Play buster animation only if not already playing
        if self.navi_sprites.current_animation != "buster":
            self.navi_sprites.play_buster()
        
        diagonals = bool(params.get("diagonals", True))

        def on_hit(enemy, hx, hy):
            # "behind" meaning further away from Navi (to the right)
            base_x, base_y = int(hx), int(hy)
            targets = [(base_x + 1, base_y)]
            if diagonals:
                targets += [(base_x + 1, base_y - 1), (base_x + 1, base_y + 1)]

            for tx, ty in targets:
                if not (0 <= tx < self.grid_cols and 0 <= ty < self.grid_rows):
                    continue
                for e in self.enemies:
                    if e.alive and e.x == tx and e.y == ty:
                        self._enemy_hit(e, chip.power)

        proj = Projectile(
            self.navi_x + 0.5, self.navi_y,
            1, 0,
            chip.power,
            self.colors["accent_cyan"],
            from_enemy=False,
            speed=float(params.get("speed", 6.0)),
            pierce=False,
            on_hit=on_hit
        )
        self.projectiles.append(proj)

    def _fire_airshot(self, chip, params):
        # Play buster animation only if not already playing
        if self.navi_sprites.current_animation != "buster":
            self.navi_sprites.play_buster()
        
        push = int(params.get("push", 1))

        def on_hit(enemy, hx, hy):
            # Push enemy back (to the right), clamp to enemy side [3..5]
            new_x = min(5, enemy.x + push)
            # don't push into occupied tile
            occupied = any(e.alive and e is not enemy and e.x == new_x and e.y == enemy.y for e in self.enemies)
            if not occupied:
                enemy.x = max(3, new_x)

        proj = Projectile(
            self.navi_x + 0.5, self.navi_y,
            1, 0,
            chip.power,
            self.colors["accent_cyan"],
            from_enemy=False,
            speed=float(params.get("speed", 7.0)),
            pierce=False,
            on_hit=on_hit
        )
        self.projectiles.append(proj)

    # ----------------------------
    # SWORDS (unchanged core)
    # ----------------------------
    def _use_sword(self, chip):
        # Play sword attack animation
        self.navi_sprites.play_sword()
        
        hit_positions = []

        for dx, dy in chip.range_pattern:
            target_x = self.navi_x + dx
            target_y = self.navi_y + dy

            if 0 <= target_x < self.grid_cols and 0 <= target_y < self.grid_rows:
                hit_positions.append((target_x, target_y))

                for enemy in self.enemies:
                    if enemy.alive and enemy.x == target_x and int(enemy.y) == target_y:
                        self._enemy_hit(enemy, chip.power)

        color = self.colors["accent_cyan"]
        if "Fire" in chip.name:
            color = (255, 100, 50)
        elif "Aqua" in chip.name:
            color = (50, 150, 255)

        self.slash_effects.append(SlashEffect(hit_positions, color, 0.25))

    # ----------------------------
    # ENEMY AI (unchanged)
    # ----------------------------
    def _update_enemies(self, dt):
        for enemy in self.enemies:
            if not enemy.alive:
                continue

            enemy.move_timer -= dt
            if enemy.move_timer <= 0:
                enemy.move_timer = random.uniform(0.6, 1.2)
                self._enemy_move(enemy)

            enemy.attack_timer -= dt
            if enemy.attack_timer <= 0:
                enemy.attack_timer = random.uniform(1.0, 2.0)
                self._enemy_attack(enemy)

    def _enemy_move(self, enemy):
        if random.random() < 0.5:
            return

        if random.random() < 0.6:
            if enemy.y < self.navi_y and enemy.y < 2:
                enemy.y += 1
            elif enemy.y > self.navi_y and enemy.y > 0:
                enemy.y -= 1
        else:
            if enemy.x < 5 and random.random() < 0.3:
                enemy.x += 1
            elif enemy.x > 3 and random.random() < 0.4:
                enemy.x -= 1

        enemy.x = max(3, min(5, enemy.x))
        enemy.y = max(0, min(2, enemy.y))

    def _enemy_attack(self, enemy):
        color = (255, 100, 50) if enemy.is_boss else (255, 180, 50)
        proj = Projectile(
            enemy.x - 0.5, enemy.y,
            -1, 0,
            enemy.attack,
            color,
            from_enemy=True,
            speed=3.5
        )
        self.projectiles.append(proj)

    # ----------------------------
    # DAMAGE RESOLUTION (BN: invis blocks hits)
    # ----------------------------
    def _navi_hit(self, damage):
        # Invis: ignore hits
        if self.navi_invis_timer > 0:
            return

        navi = self.game_state["navi"]
        actual = max(1, damage - navi["defense"])
        navi["hp"] = max(0, navi["hp"] - actual)
        self.hit_flash = 1.0
        self.navi_sprites.play_hurt()
        self.shake = 1.0
        sx, sy = self._grid_to_screen(self.navi_x, self.navi_y)
        self.damage_popups.append([sx, sy - 20, f"-{actual}", 1.0, self.colors["hp_red"]])

    def _enemy_hit(self, enemy, damage):
        actual = max(1, damage - enemy.defense)
        enemy.hp -= actual
        if enemy.hp <= 0:
            enemy.alive = False
        self.shake = 0.4
        sx, sy = self._grid_to_screen(enemy.x, enemy.y)
        self.damage_popups.append([sx, sy - 20, f"-{actual}", 1.0, self.colors["accent_cyan"]])

    # ----------------------------
    # CUSTOM SCREEN / RESULTS (unchanged)
    # ----------------------------
    def _open_custom_screen(self):
        self.phase = "custom"
        self.custom_gauge = 0

        folder = self.game_state["chip_folder"]
        self.drawn_chips = folder.draw_chips(5)
        self.selected_chips = []
        self.chip_cursor = 0

        if not self.drawn_chips:
            self.phase = "battle"

    def _close_custom_screen(self):
        self.chip_queue = self.selected_chips.copy()
        self.selected_chips = []
        self.phase = "battle"

    def _win(self):
        self.phase = "win"
        self.phase_timer = 2.5

        base_zenny = sum(20 + e.max_hp for e in self.enemies)
        self.rewards = {"zenny": base_zenny, "chips": []}
        self.game_state["zenny"] += base_zenny

        for enemy in self.enemies:
            dropped = roll_chip_drop(enemy.name)
            if dropped:
                self.rewards["chips"].append(dropped)
                self.game_state["chip_folder"].add_chip(dropped)

        self.battle_result = "win"

    def _lose(self):
        self.phase = "lose"
        self.phase_timer = 2.5
        self.battle_result = "lose"

    def handle_event(self, event):
        if event.type != pygame.USEREVENT:
            return
        action = event.dict.get("action")

        if self.phase == "battle":
            if action == "confirm" and self.custom_gauge >= self.custom_gauge_max:
                self._open_custom_screen()
            elif action == "cancel" and self.chip_queue:
                self._use_chip(self.chip_queue.pop(0))

        elif self.phase == "custom":
            if action == "left":
                self.chip_cursor = max(0, self.chip_cursor - 1)
            elif action == "right":
                self.chip_cursor = min(len(self.drawn_chips) - 1, self.chip_cursor + 1)
            elif action == "confirm":
                if self.chip_cursor < len(self.drawn_chips):
                    chip = self.drawn_chips[self.chip_cursor]
                    if chip in self.selected_chips:
                        self.selected_chips.remove(chip)
                    elif len(self.selected_chips) < 5:
                        self.selected_chips.append(chip)
            elif action == "cancel" or action == "start":
                self._close_custom_screen()

        elif self.phase in ["win", "lose"] and action == "confirm":
            if self.phase == "win":
                self.manager.pop_scene()
            else:
                self.manager.change_scene("hub")

    def _grid_to_screen(self, gx, gy):
        sx = self.grid_x + int(gx) * self.cell_width + self.cell_width // 2
        sy = self.grid_y + int(gy) * self.cell_height + self.cell_height // 2
        return sx, sy

    # ----------------------------
    # DRAWING (small invis flicker)
    # ----------------------------
    def draw(self, screen):
        screen.fill((15, 15, 25))

        shake_x = int(math.sin(self.anim_timer * 50) * self.shake * 3) if self.shake > 0 else 0

        self._draw_grid(screen, shake_x)
        self._draw_slashes(screen, shake_x)
        self._draw_impacts(screen, shake_x)
        self._draw_projectiles(screen, shake_x)

        for enemy in self.enemies:
            if enemy.alive:
                self._draw_enemy(screen, enemy, shake_x)

        self._draw_navi(screen, shake_x)
        self._draw_popups(screen)
        self._draw_ui(screen)

        if self.phase == "custom":
            self._draw_custom_screen(screen)

        if self.phase == "win":
            self._draw_win(screen)
        elif self.phase == "lose":
            self._draw_lose(screen)

    def _draw_grid(self, screen, shake_x):
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                x = self.grid_x + col * self.cell_width + shake_x
                y = self.grid_y + row * self.cell_height

                if col < 3:
                    panel_color = (40, 80, 160)
                    panel_light = (60, 110, 200)
                    panel_dark = (25, 50, 110)
                else:
                    panel_color = (160, 50, 60)
                    panel_light = (200, 70, 80)
                    panel_dark = (110, 30, 40)

                pygame.draw.rect(screen, panel_color, (x+1, y+1, self.cell_width-2, self.cell_height-2))
                pygame.draw.line(screen, panel_light, (x+2, y+2), (x+self.cell_width-3, y+2), 2)
                pygame.draw.line(screen, panel_dark, (x+2, y+self.cell_height-3), (x+self.cell_width-3, y+self.cell_height-3), 2)
                pygame.draw.rect(screen, (80, 80, 100), (x, y, self.cell_width, self.cell_height), 1)

    def _draw_slashes(self, screen, shake_x):
        for slash in self.slash_effects:
            for gx, gy in slash.positions:
                sx, sy = self._grid_to_screen(gx, gy)
                sx += shake_x
                pygame.draw.arc(screen, slash.color, (sx-15, sy-15, 30, 30), 0.5, 2.5, 3)
                pygame.draw.arc(screen, (255, 255, 255), (sx-12, sy-12, 24, 24), 0.7, 2.3, 2)

    def _draw_impacts(self, screen, shake_x):
        # simple "target marker" for pending bomb impacts
        for imp in self.impact_effects:
            sx, sy = self._grid_to_screen(imp.gx, imp.gy)
            sx += shake_x
            t = max(0.0, min(1.0, 1.0 - imp.timer / 0.6))
            r = 6 + int(6 * t)
            pygame.draw.circle(screen, imp.color, (sx, sy), r, 2)

    def _draw_projectiles(self, screen, shake_x):
        for proj in self.projectiles:
            sx = self.grid_x + proj.x * self.cell_width + shake_x
            sy = self.grid_y + proj.y * self.cell_height + self.cell_height // 2
            pygame.draw.circle(screen, proj.color, (int(sx), int(sy)), 5)
            pygame.draw.circle(screen, (255, 255, 200), (int(sx), int(sy)), 2)

    def _draw_enemy(self, screen, enemy, shake_x):
        sx, sy = self._grid_to_screen(enemy.x, enemy.y)
        sx += shake_x

        size = 16 if enemy.is_boss else 12
        color = (200, 60, 60) if enemy.is_boss else (180, 140, 60)
        bob = math.sin(self.anim_timer * 3 + enemy.x) * 2

        pygame.draw.circle(screen, color, (int(sx), int(sy - bob)), size)
        pygame.draw.circle(screen, (255, 255, 255), (int(sx), int(sy - bob)), size, 2)

        pygame.draw.circle(screen, (255, 255, 255), (int(sx-4), int(sy-3-bob)), 3)
        pygame.draw.circle(screen, (255, 255, 255), (int(sx+4), int(sy-3-bob)), 3)
        pygame.draw.circle(screen, (0, 0, 0), (int(sx-4), int(sy-3-bob)), 1)
        pygame.draw.circle(screen, (0, 0, 0), (int(sx+4), int(sy-3-bob)), 1)

        bar_w = 24
        hp_pct = enemy.hp / enemy.max_hp
        pygame.draw.rect(screen, (40, 20, 20), (sx - bar_w//2, sy - size - 10, bar_w, 4))
        pygame.draw.rect(screen, (220, 60, 60), (sx - bar_w//2, sy - size - 10, int(bar_w * hp_pct), 4))

    def _draw_navi(self, screen, shake_x):
        """Draw Navi with sprite animations."""
        sx, sy = self._grid_to_screen(self.navi_x, self.navi_y)
        sx += shake_x

        # Hit flash (blink white)
        if self.hit_flash > 0 and int(self.hit_flash * 10) % 2 == 0:
            return

        # Invis flicker
        if self.navi_invis_timer > 0 and int(self.anim_timer * 12) % 2 == 0:
            return

        # Draw sprite (centered on grid cell)
        # Sprites are 76-84px, grid cells are 40px, scale 1.2 makes them smaller but visible
        self.navi_sprites.draw(screen, sx, sy, scale=1.2, center=True)

    def _draw_popups(self, screen):
        for popup in self.damage_popups:
            x, y, text, timer, color = popup
            y -= (1.0 - timer) * 15
            self.draw_text(screen, text, int(x), int(y), size=12, center=True, color=color)

    def _draw_ui(self, screen):
        navi = self.game_state["navi"]

        self.draw_panel(screen, 2, 2, 75, 20, border_width=1)
        self.draw_progress_bar(screen, 5, 5, 68, 8, navi["hp"], navi["max_hp"])
        self.draw_text(screen, f"{navi['hp']}", 5, 14, size=9, color=self.colors["text_white"])

        # show invis
        if self.navi_invis_timer > 0:
            self.draw_text(screen, "INVIS", 55, 14, size=9, color=self.colors["accent_cyan"])

        if self.chip_queue:
            self.draw_panel(screen, 2, 25, 75, 20, border_width=1)
            chip_name = self.chip_queue[0].name[:8]
            self.draw_text(screen, f"[X]{chip_name}", 5, 28, size=10, color=self.colors["accent_cyan"])
            if len(self.chip_queue) > 1:
                self.draw_text(screen, f"+{len(self.chip_queue)-1}", 65, 28, size=8, color=self.colors["text_dim"])

        gauge_pct = self.custom_gauge / self.custom_gauge_max
        bar_w = self.width - 20
        pygame.draw.rect(screen, (30, 30, 50), (10, self.height - 12, bar_w, 8))
        pygame.draw.rect(screen, self.colors["accent_cyan"], (10, self.height - 12, int(bar_w * gauge_pct), 8))
        pygame.draw.rect(screen, (100, 100, 120), (10, self.height - 12, bar_w, 8), 1)

        if gauge_pct >= 1.0:
            self.draw_text(screen, "[Z] CUSTOM!", self.width - 60, self.height - 11, size=10, color=self.colors["accent_cyan"])
        else:
            pct_text = f"{int(gauge_pct * 100)}%"
            self.draw_text(screen, pct_text, self.width - 30, self.height - 11, size=9, color=self.colors["text_dim"])

        alive = sum(1 for e in self.enemies if e.alive)
        self.draw_text(screen, f"Virus: {alive}", self.width - 50, 5, size=10, color=self.colors["text_dim"])

    def _draw_custom_screen(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        self.draw_text(screen, "SELECT CHIPS", self.width // 2, 15, size=14, center=True, color=self.colors["accent_cyan"])
        self.draw_text(screen, f"Selected: {len(self.selected_chips)}/5", self.width // 2, 32, size=10, center=True, color=self.colors["text_dim"])

        card_w, card_h = 50, 55
        total = len(self.drawn_chips) * (card_w + 4) - 4
        start_x = (self.width - total) // 2
        y = 50

        for i, chip in enumerate(self.drawn_chips):
            x = start_x + i * (card_w + 4)
            is_cursor = i == self.chip_cursor
            is_selected = chip in self.selected_chips

            if is_selected:
                bg = self.colors["hp_green"]
            elif is_cursor:
                bg = self.colors["accent_cyan"]
            else:
                bg = self.colors["bg_panel"]

            self.draw_panel(screen, x, y, card_w, card_h, color=bg, border_width=2 if is_cursor else 1)

            tc = self.colors["bg_dark"] if (is_cursor or is_selected) else self.colors["text_white"]
            self.draw_text(screen, chip.name[:6], x + card_w // 2, y + 8, size=9, center=True, color=tc)
            self.draw_text(screen, str(chip.power), x + card_w // 2, y + 25, size=14, center=True, color=tc)
            self.draw_text(screen, chip.chip_type[:4], x + card_w // 2, y + 42, size=8, center=True, color=tc)

        self.draw_text(screen, "[Z] Select  [X] Done", self.width // 2, self.height - 20, size=10, center=True, color=self.colors["text_dim"])

    def _draw_win(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        self.draw_text(screen, "VICTORY!", self.width // 2, 40, size=22, center=True, color=self.colors["accent_cyan"])
        self.draw_text(screen, f"+{self.rewards['zenny']}z", self.width // 2, 70, size=16, center=True, color=self.colors["accent_yellow"])

        y = 95
        if self.rewards["chips"]:
            self.draw_text(screen, "GOT CHIP:", self.width // 2, y, size=12, center=True, color=self.colors["hp_green"])
            for chip_name in self.rewards["chips"]:
                y += 15
                self.draw_text(screen, chip_name, self.width // 2, y, size=14, center=True, color=self.colors["accent_pink"])

        self.draw_text(screen, "[Z] Continue", self.width // 2, self.height - 25, size=11, center=True, color=self.colors["text_dim"])

    def _draw_lose(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((40, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        self.draw_text(screen, "DELETED...", self.width // 2, self.height // 2 - 20, size=22, center=True, color=self.colors["hp_red"])
        self.draw_text(screen, "Wait 1 hour to recover", self.width // 2, self.height // 2 + 10, size=11, center=True, color=self.colors["text_dim"])
        self.draw_text(screen, "[Z] Continue", self.width // 2, self.height - 25, size=11, center=True, color=self.colors["text_dim"])
