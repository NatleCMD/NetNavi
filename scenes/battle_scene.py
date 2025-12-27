"""
Battle Scene - Grid-based combat with MMBN-style mechanics.
Optimized for 128x128 display with Metaur enemy and wave attack.

This version adds BN-style chip behaviors and Metaur virus with wave attack.
"""

import pygame
import math
import random
from scenes.base_scene import BaseScene
from combat.chips import Chip, CHIP_DATABASE, roll_chip_drop
from combat.equipment import roll_equipment_drop  # NEW: Equipment drops
from navi_sprites import get_navi_sprites
from enemy_sprites import get_enemy_sprites, WaveAttack

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
        self.pierce = pierce
        self.on_hit = on_hit
        self.hit_radius = hit_radius


class SlashEffect:
    """Visual effect for sword attacks."""
    def __init__(self, positions, color, duration=0.3):
        self.positions = positions
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
        self.splash = splash
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
        self.attack_timer = random.uniform(0.5, 1.5)
        self.move_timer = random.uniform(0.3, 0.8)
        self.alive = True
        self.attack_cooldown = 0.25  # Metaur attack animation duration
        self.is_attacking = False
        self.attack_anim_timer = 0.0
        
        # Load sprite manager if it's Metaur (case-insensitive)
        self.sprite_manager = None
        name_lower = name.lower()
        if "metaur" in name_lower or "mettaur" in name_lower:
            print(f"[BATTLE] Loading sprite manager for enemy: {name}")
            self.sprite_manager = get_enemy_sprites("metaur")


class BattleScene(BaseScene):
    """Grid-based battle with custom screen chip selection."""

    target_fps = 24

    def __init__(self, manager, enemy: dict = None, area: dict = None, **kwargs):
        super().__init__(manager)
        self.area = area or {}
        
        # Apply equipment bonuses to Navi stats
        self._apply_equipment_bonuses()
        
        # Sprite manager for Navi animations
        self.navi_sprites = get_navi_sprites()
        self.navi_sprites.play_idle()

        # Grid: 3 rows x 6 cols (smaller cells for 128x128)
        self.grid_cols = 6
        self.grid_rows = 3
        self.cell_width = 18  # Reduced from 40
        self.cell_height = 12  # Reduced from 28
        self.grid_x = (self.width - self.grid_cols * self.cell_width) // 2
        self.grid_y = 30  # Adjusted for smaller screen

        # Spawn 1-3 enemies
        self.enemies = self._spawn_enemies(enemy)

        # Navi state
        self.navi_x, self.navi_y = 1, 1
        self.navi_move_timer = 0.0
        self.navi_buster_timer = 0.0
        self.buster_cooldown = 0.8

        # Defensive timers
        self.navi_invis_timer = 0.0

        # Projectiles and effects
        self.projectiles = []
        self.wave_attacks = []  # Separate list for Metaur wave attacks
        self.slash_effects = []
        self.impact_effects = []

        # Custom screen / chip system
        self.custom_gauge = 0.0
        self.custom_gauge_max = 15.0
        self.in_custom_screen = False
        self.drawn_chips = []
        self.selected_chips = []
        self.chip_cursor = 0
        self.chip_queue = []

        # Battle state
        self.phase = "intro"
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

        # TEMPORARY: All enemies are Metaur until more sprites are added
        virus_types = [
            {"name": "Metaur", "hp": 40, "attack": 10, "defense": 2},
            {"name": "Metaur", "hp": 50, "attack": 12, "defense": 1},
            {"name": "Metaur", "hp": 35, "attack": 15, "defense": 0},
            {"name": "Metaur", "hp": 45, "attack": 14, "defense": 2},
            {"name": "Metaur", "hp": 60, "attack": 8, "defense": 4},
        ]

        if enemy_data.get("is_boss"):
            boss = Enemy(
                enemy_data.get("name", "Metaur"),  # Boss is also Metaur for now
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
    
    def _apply_equipment_bonuses(self):
        """Apply equipment stat bonuses to Navi."""
        equipment = self.game_state.get("equipment")
        if not equipment:
            return
        
        bonuses = equipment.get_stat_bonuses()
        navi = self.game_state["navi"]
        
        # Apply stat bonuses
        if "attack" in bonuses:
            navi["buster_attack"] = 1 + bonuses["attack"]  # Base 1 + bonuses
        if "max_hp" in bonuses:
            # Don't exceed new max
            old_max = navi["max_hp"]
            navi["max_hp"] = 100 + bonuses["max_hp"]  # Base 100 + bonuses
            # Adjust current HP proportionally
            if old_max > 0:
                hp_pct = navi["hp"] / old_max
                navi["hp"] = int(navi["max_hp"] * hp_pct)
        if "defense" in bonuses:
            navi["defense"] = 5 + bonuses["defense"]  # Base 5 + bonuses
        if "buster_speed" in bonuses:
            navi["buster_speed"] = bonuses["buster_speed"]
        if "charge_speed" in bonuses:
            navi["buster_charge"] = bonuses["charge_speed"]

    def update(self, dt):
        # Update Navi sprite animation
        self.navi_sprites.update(dt)
        self.anim_timer += dt
        self.hit_flash = max(0, self.hit_flash - dt * 5)
        self.shake = max(0, self.shake - dt * 8)

        # Timers
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

        # Update enemy attack animations
        for enemy in self.enemies:
            if enemy.is_attacking:
                enemy.attack_anim_timer -= dt
                if enemy.attack_anim_timer <= 0:
                    enemy.is_attacking = False
                    if enemy.sprite_manager:
                        enemy.sprite_manager.play_idle()

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
        self._update_wave_attacks(dt)
        self._update_navi(dt)
        self._update_enemies(dt)

        self.custom_gauge += dt
        self.custom_gauge = min(self.custom_gauge, self.custom_gauge_max)

        # Return to idle animation
        if self.hit_flash <= 0 and self.navi_invis_timer <= 0:
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

        for tx, ty in hit_tiles:
            if not (0 <= tx < self.grid_cols and 0 <= ty < self.grid_rows):
                continue
            for enemy in self.enemies:
                if enemy.alive and enemy.x == tx and enemy.y == ty:
                    self._enemy_hit(enemy, imp.damage)

        sx, sy = self._grid_to_screen(imp.gx, imp.gy)
        self.damage_popups.append([sx, sy - 10, "BOOM", 0.6, imp.color])
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
                        self._enemy_hit(enemy, proj.damage)

                        if proj.on_hit:
                            try:
                                proj.on_hit(enemy, enemy.x, enemy.y)
                            except Exception:
                                pass

                        if not proj.pierce:
                            proj.alive = False
                        break

        self.projectiles = [p for p in self.projectiles if p.alive]

    def _update_wave_attacks(self, dt):
        """Update Metaur wave attacks separately."""
        for wave in self.wave_attacks[:]:
            wave.update(dt)

            # Check bounds
            if wave.x < -1 or wave.x > self.grid_cols:
                wave.alive = False
                continue

            # Check collision with Navi
            if abs(wave.x - self.navi_x) < wave.hit_radius and abs(wave.y - self.navi_y) < wave.hit_radius:
                self._navi_hit(wave.damage)
                wave.alive = False

        self.wave_attacks = [w for w in self.wave_attacks if w.alive]

    def _update_navi(self, dt):
        # Movement
        self.navi_move_timer += dt
        if self.navi_move_timer >= 0.5:
            self.navi_move_timer = 0
            self._navi_ai_move()

        # Auto-fire buster
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

        # Also check wave attacks
        if danger_row is None:
            for wave in self.wave_attacks:
                if wave.dx < 0 and 0 < wave.x < 3.5:
                    if abs(wave.y - self.navi_y) < 0.6:
                        danger_row = int(round(wave.y))
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

    # Chip usage methods (same as before but with shorter code)
    def _use_chip(self, chip):
        """Use a battle chip with BN-style behavior resolution."""
        if getattr(chip, "chip_type", "") == "heal":
            navi = self.game_state["navi"]
            navi["hp"] = min(navi["max_hp"], navi["hp"] + chip.power)
            sx, sy = self._grid_to_screen(self.navi_x, self.navi_y)
            self.damage_popups.append([sx, sy - 10, f"+{chip.power}", 1.0, self.colors["hp_green"]])
            return

        if self._chip_is_invis(chip):
            self._apply_invis(chip)
            return

        if chip.chip_type in ["sword", "widesword", "longsword"]:
            self._use_sword(chip)
            return

        if getattr(chip, "chip_type", "") == "attack":
            behavior = getattr(chip, "behavior", None)
            params = getattr(chip, "params", {}) or {}

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
                self._fire_chip_projectile(chip, params)
            return

    def _chip_is_invis(self, chip) -> bool:
        if getattr(chip, "behavior", None) in ("buff_invis", "invis"):
            return True
        name = (getattr(chip, "name", "") or "").lower()
        return "invis" in name

    def _infer_behavior_from_name(self, chip, params):
        name = (chip.name or "").lower()
        if "bomb" in name:
            if "mini" in name:
                return "lob", {**params, "dist": 3, "delay": 0.45, "splash": "single"}
            return "lob", {**params, "dist": 3, "delay": 0.5, "splash": "cross1"}
        if "spreader" in name:
            return "spreader", {**params, "diagonals": True}
        if "shotgun" in name:
            return "shotgun", params
        if "airshot" in name or "air shot" in name:
            return "airshot", {**params, "push": 1}
        return "projectile", params

    def _apply_invis(self, chip):
        dur = 3.0
        params = getattr(chip, "params", {}) or {}
        if "duration" in params:
            dur = float(params["duration"])
        self.navi_invis_timer = max(self.navi_invis_timer, dur)
        sx, sy = self._grid_to_screen(self.navi_x, self.navi_y)
        self.damage_popups.append([sx, sy - 12, "INVIS", 0.8, self.colors["accent_cyan"]])

    def _use_lob_chip(self, chip, params):
        self.navi_sprites.play_throw()
        dist = int(params.get("dist", 3))
        delay = float(params.get("delay", 0.45))
        splash = params.get("splash", "single")
        gx = min(self.grid_cols - 1, self.navi_x + dist)
        gy = int(self.navi_y)
        imp = ImpactEffect(gx, gy, damage=chip.power, color=self.colors["accent_cyan"], delay=delay, splash=splash)
        self.impact_effects.append(imp)

    def _fire_chip_projectile(self, chip, params=None):
        params = params or {}
        if self.navi_sprites.current_animation != "buster":
            self.navi_sprites.play_buster()
        proj = Projectile(
            self.navi_x + 0.5, self.navi_y, 1, 0,
            chip.power, self.colors["accent_cyan"], from_enemy=False,
            speed=float(params.get("speed", 6.0)),
            pierce=bool(params.get("pierce", False))
        )
        self.projectiles.append(proj)

    def _fire_shotgun(self, chip, params):
        if self.navi_sprites.current_animation != "buster":
            self.navi_sprites.play_buster()

        def on_hit(enemy, hx, hy):
            bx, by = int(hx) + 1, int(hy)
            for e in self.enemies:
                if e.alive and e.x == bx and e.y == by:
                    self._enemy_hit(e, chip.power)

        proj = Projectile(
            self.navi_x + 0.5, self.navi_y, 1, 0,
            chip.power, self.colors["accent_cyan"], from_enemy=False,
            speed=float(params.get("speed", 6.5)),
            pierce=False, on_hit=on_hit
        )
        self.projectiles.append(proj)

    def _fire_spreader(self, chip, params):
        if self.navi_sprites.current_animation != "buster":
            self.navi_sprites.play_buster()
        diagonals = bool(params.get("diagonals", True))

        def on_hit(enemy, hx, hy):
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
            self.navi_x + 0.5, self.navi_y, 1, 0,
            chip.power, self.colors["accent_cyan"], from_enemy=False,
            speed=float(params.get("speed", 6.0)),
            pierce=False, on_hit=on_hit
        )
        self.projectiles.append(proj)

    def _fire_airshot(self, chip, params):
        if self.navi_sprites.current_animation != "buster":
            self.navi_sprites.play_buster()
        push = int(params.get("push", 1))

        def on_hit(enemy, hx, hy):
            new_x = min(5, enemy.x + push)
            occupied = any(e.alive and e is not enemy and e.x == new_x and e.y == enemy.y for e in self.enemies)
            if not occupied:
                enemy.x = max(3, new_x)

        proj = Projectile(
            self.navi_x + 0.5, self.navi_y, 1, 0,
            chip.power, self.colors["accent_cyan"], from_enemy=False,
            speed=float(params.get("speed", 7.0)),
            pierce=False, on_hit=on_hit
        )
        self.projectiles.append(proj)

    def _use_sword(self, chip):
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

    def _update_enemies(self, dt):
        for enemy in self.enemies:
            if not enemy.alive:
                continue

            # Update sprite animation
            if enemy.sprite_manager:
                enemy.sprite_manager.update(dt)

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
        """Enemy attack - use wave attack for Metaur, normal projectile for others."""
        name_lower = enemy.name.lower()
        if "metaur" in name_lower or "mettaur" in name_lower:
            # Metaur uses wave attack
            print(f"[BATTLE] {enemy.name} using wave attack")
            enemy.is_attacking = True
            enemy.attack_anim_timer = 0.25  # Animation duration
            if enemy.sprite_manager:
                enemy.sprite_manager.play_attack()

            # Create wave attack
            wave = WaveAttack(
                enemy.x - 0.5,
                enemy.y,
                -1,  # Moving left
                enemy.attack
            )
            self.wave_attacks.append(wave)
        else:
            # Other enemies use normal projectile
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

    def _navi_hit(self, damage):
        if self.navi_invis_timer > 0:
            return

        navi = self.game_state["navi"]
        actual = max(1, damage - navi["defense"])
        navi["hp"] = max(0, navi["hp"] - actual)
        self.hit_flash = 1.0
        self.navi_sprites.play_hurt()
        self.shake = 1.0
        sx, sy = self._grid_to_screen(self.navi_x, self.navi_y)
        self.damage_popups.append([sx, sy - 10, f"-{actual}", 1.0, self.colors["hp_red"]])

    def _enemy_hit(self, enemy, damage):
        actual = max(1, damage - enemy.defense)
        enemy.hp -= actual
        if enemy.hp <= 0:
            enemy.alive = False
        self.shake = 0.4
        sx, sy = self._grid_to_screen(enemy.x, enemy.y)
        self.damage_popups.append([sx, sy - 10, f"-{actual}", 1.0, self.colors["accent_cyan"]])

    def _open_custom_screen(self):
        self.phase = "custom"
        self.custom_gauge = 0

        # chip_folder is now a dict with "folder_chips" list
        folder_chips = self.game_state["chip_folder"].get("folder_chips", [])
        
        # Draw 5 random chips from folder
        if len(folder_chips) >= 5:
            self.drawn_chips = random.sample(folder_chips, 5)
        else:
            self.drawn_chips = folder_chips.copy()
        
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
        self.rewards = {"zenny": base_zenny, "chips": [], "equipment": None}
        self.game_state["zenny"] += base_zenny

        # Chip drops
        for enemy in self.enemies:
            dropped = roll_chip_drop(enemy.name)
            if dropped:
                self.rewards["chips"].append(dropped)
                # Add to owned chips
                owned_chips = self.game_state["chip_folder"]["owned_chips"]
                chip_obj = Chip(dropped, CHIP_DATABASE[dropped].power, CHIP_DATABASE[dropped].chip_type)
                owned_chips.append(chip_obj)
        
        # Equipment drop (3% chance)
        equipment_drop = roll_equipment_drop()
        if equipment_drop:
            self.rewards["equipment"] = equipment_drop
            self.game_state["equipment"].add_item(equipment_drop)

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

    def draw(self, screen):
        screen.fill((15, 15, 25))

        shake_x = int(math.sin(self.anim_timer * 50) * self.shake * 2) if self.shake > 0 else 0

        self._draw_grid(screen, shake_x)
        self._draw_slashes(screen, shake_x)
        self._draw_impacts(screen, shake_x)
        self._draw_projectiles(screen, shake_x)
        self._draw_wave_attacks(screen, shake_x)

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
                pygame.draw.line(screen, panel_light, (x+1, y+1), (x+self.cell_width-2, y+1), 1)
                pygame.draw.line(screen, panel_dark, (x+1, y+self.cell_height-2), (x+self.cell_width-2, y+self.cell_height-2), 1)
                pygame.draw.rect(screen, (80, 80, 100), (x, y, self.cell_width, self.cell_height), 1)

    def _draw_slashes(self, screen, shake_x):
        for slash in self.slash_effects:
            for gx, gy in slash.positions:
                sx, sy = self._grid_to_screen(gx, gy)
                sx += shake_x
                pygame.draw.arc(screen, slash.color, (sx-8, sy-8, 16, 16), 0.5, 2.5, 2)
                pygame.draw.arc(screen, (255, 255, 255), (sx-6, sy-6, 12, 12), 0.7, 2.3, 1)

    def _draw_impacts(self, screen, shake_x):
        for imp in self.impact_effects:
            sx, sy = self._grid_to_screen(imp.gx, imp.gy)
            sx += shake_x
            t = max(0.0, min(1.0, 1.0 - imp.timer / 0.6))
            r = 3 + int(3 * t)
            pygame.draw.circle(screen, imp.color, (sx, sy), r, 1)

    def _draw_projectiles(self, screen, shake_x):
        for proj in self.projectiles:
            sx = self.grid_x + proj.x * self.cell_width + shake_x
            sy = self.grid_y + proj.y * self.cell_height + self.cell_height // 2
            pygame.draw.circle(screen, proj.color, (int(sx), int(sy)), 3)
            pygame.draw.circle(screen, (255, 255, 200), (int(sx), int(sy)), 1)

    def _draw_wave_attacks(self, screen, shake_x):
        """Draw Metaur wave attacks."""
        for wave in self.wave_attacks:
            wave.draw(screen, self.grid_x, self.grid_y, self.cell_width, self.cell_height, shake_x)

    def _draw_enemy(self, screen, enemy, shake_x):
        sx, sy = self._grid_to_screen(enemy.x, enemy.y)
        sx += shake_x

        # Use sprite if available (Metaur)
        if enemy.sprite_manager:
            bob = math.sin(self.anim_timer * 3 + enemy.x) * 1
            enemy.sprite_manager.draw(screen, sx, int(sy - bob), scale=0.55, center=True)
        else:
            # Placeholder for other enemies
            size = 8 if enemy.is_boss else 6
            color = (200, 60, 60) if enemy.is_boss else (180, 140, 60)
            bob = math.sin(self.anim_timer * 3 + enemy.x) * 1

            pygame.draw.circle(screen, color, (int(sx), int(sy - bob)), size)
            pygame.draw.circle(screen, (255, 255, 255), (int(sx), int(sy - bob)), size, 1)

        # HP bar
        bar_w = 12
        hp_pct = enemy.hp / enemy.max_hp
        pygame.draw.rect(screen, (40, 20, 20), (sx - bar_w//2, sy - 10, bar_w, 2))
        pygame.draw.rect(screen, (220, 60, 60), (sx - bar_w//2, sy - 10, int(bar_w * hp_pct), 2))

    def _draw_navi(self, screen, shake_x):
        """Draw Navi with sprite animations."""
        sx, sy = self._grid_to_screen(self.navi_x, self.navi_y)
        sx += shake_x

        # Hit flash
        if self.hit_flash > 0 and int(self.hit_flash * 10) % 2 == 0:
            return

        # Invis flicker
        if self.navi_invis_timer > 0 and int(self.anim_timer * 12) % 2 == 0:
            return

        # Draw sprite (increased scale for better visibility - 25% larger)
        self.navi_sprites.draw(screen, sx, sy, scale=0.44, center=True)

    def _draw_popups(self, screen):
        for popup in self.damage_popups:
            x, y, text, timer, color = popup
            y -= (1.0 - timer) * 8
            self.draw_text(screen, text, int(x), int(y), size=7, center=True, color=color)

    def _draw_ui(self, screen):
        navi = self.game_state["navi"]

        # Compact UI for 128x128
        self.draw_panel(screen, 1, 1, 35, 10, border_width=1)
        self.draw_progress_bar(screen, 2, 2, 30, 4, navi["hp"], navi["max_hp"])
        self.draw_text(screen, f"{navi['hp']}", 2, 6, size=6, color=self.colors["text_white"])

        # Invis indicator
        if self.navi_invis_timer > 0:
            self.draw_text(screen, "INV", 25, 6, size=6, color=self.colors["accent_cyan"])

        # Chip queue
        if self.chip_queue:
            self.draw_panel(screen, 1, 12, 35, 8, border_width=1)
            chip_name = self.chip_queue[0].name[:6]
            self.draw_text(screen, f"[X]{chip_name}", 2, 13, size=6, color=self.colors["accent_cyan"])

        # Custom gauge
        gauge_pct = self.custom_gauge / self.custom_gauge_max
        bar_w = self.width - 4
        pygame.draw.rect(screen, (30, 30, 50), (2, self.height - 6, bar_w, 4))
        pygame.draw.rect(screen, self.colors["accent_cyan"], (2, self.height - 6, int(bar_w * gauge_pct), 4))
        pygame.draw.rect(screen, (100, 100, 120), (2, self.height - 6, bar_w, 4), 1)

        if gauge_pct >= 1.0:
            self.draw_text(screen, "[Z]CSTM", self.width - 25, self.height - 5, size=6, color=self.colors["accent_cyan"])

        # Enemy count
        alive = sum(1 for e in self.enemies if e.alive)
        self.draw_text(screen, f"V:{alive}", self.width - 15, 2, size=6, color=self.colors["text_dim"])

    def _draw_custom_screen(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        self.draw_text(screen, "SELECT CHIP", self.width // 2, 5, size=10, center=True, color=self.colors["accent_cyan"])
        self.draw_text(screen, f"{len(self.selected_chips)}/5", self.width // 2, 15, size=7, center=True, color=self.colors["text_dim"])

        # Show only 1 chip at a time for readability on small screen
        if not self.drawn_chips:
            self.draw_text(screen, "No chips!", self.width // 2, self.height // 2, size=10, center=True, color=self.colors["text_dim"])
            return
        
        chip = self.drawn_chips[self.chip_cursor]
        is_selected = chip in self.selected_chips
        
        # Large centered card
        card_w, card_h = 80, 70
        x = (self.width - card_w) // 2
        y = 30
        
        bg = self.colors["hp_green"] if is_selected else self.colors["accent_cyan"]
        self.draw_panel(screen, x, y, card_w, card_h, color=bg, border_width=2)
        
        tc = self.colors["bg_dark"]
        # Chip name (larger, readable)
        self.draw_text(screen, chip.name, x + card_w // 2, y + 8, size=11, center=True, color=tc)
        # Power (very large)
        self.draw_text(screen, str(chip.power), x + card_w // 2, y + 28, size=20, center=True, color=tc)
        # Type
        self.draw_text(screen, chip.chip_type, x + card_w // 2, y + 52, size=9, center=True, color=tc)
        
        # Navigation arrows
        if self.chip_cursor > 0:
            self.draw_text(screen, "◄", 10, self.height // 2, size=16, center=True, color=self.colors["accent_cyan"])
        if self.chip_cursor < len(self.drawn_chips) - 1:
            self.draw_text(screen, "►", self.width - 10, self.height // 2, size=16, center=True, color=self.colors["accent_cyan"])
        
        # Chip counter
        self.draw_text(screen, f"{self.chip_cursor + 1}/{len(self.drawn_chips)}", self.width // 2, y + card_h + 8, size=8, center=True, color=self.colors["text_white"])
        
        # Controls
        self.draw_text(screen, "[Z]Sel [X]OK", self.width // 2, self.height - 10, size=7, center=True, color=self.colors["text_dim"])

    def _draw_win(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        self.draw_text(screen, "VICTORY!", self.width // 2, 20, size=12, center=True, color=self.colors["accent_cyan"])
        self.draw_text(screen, f"+{self.rewards['zenny']}z", self.width // 2, 35, size=10, center=True, color=self.colors["accent_yellow"])

        y = 48
        if self.rewards["chips"]:
            self.draw_text(screen, "CHIPS:", self.width // 2, y, size=7, center=True, color=self.colors["hp_green"])
            for chip_name in self.rewards["chips"]:
                y += 10
                self.draw_text(screen, chip_name, self.width // 2, y, size=8, center=True, color=self.colors["accent_pink"])
        
        # Show equipment drop if any
        if self.rewards.get("equipment"):
            y += 14
            self.draw_text(screen, "EQUIPMENT:", self.width // 2, y, size=7, center=True, color=self.colors["hp_green"])
            y += 10
            self.draw_text(screen, self.rewards["equipment"], self.width // 2, y, size=9, center=True, color=self.colors["accent_cyan"])

        self.draw_text(screen, "[Z]Continue", self.width // 2, self.height - 12, size=6, center=True, color=self.colors["text_dim"])

    def _draw_lose(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((40, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        self.draw_text(screen, "DELETED", self.width // 2, self.height // 2 - 10, size=12, center=True, color=self.colors["hp_red"])
        self.draw_text(screen, "Wait 1hr", self.width // 2, self.height // 2 + 5, size=7, center=True, color=self.colors["text_dim"])
        self.draw_text(screen, "[Z]Continue", self.width // 2, self.height - 12, size=6, center=True, color=self.colors["text_dim"])
