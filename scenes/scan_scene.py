"""
Scan Scene - WiFi scanning and Area selection.
Displays nearby networks as explorable cyber areas with modern polished UI.
"""

import pygame
import math
import random
from scenes.base_scene import BaseScene
from wifi.scanner import WiFiScanner
from worldgen.area_gen import AreaGenerator


class ScanScene(BaseScene):
    """WiFi scan and Area selection screen - Modern polished UI."""
    
    target_fps = 30
    
    def __init__(self, manager):
        super().__init__(manager)
        
        self.wifi_scanner = WiFiScanner()
        self.area_generator = AreaGenerator()
        
        # Scan state
        self.is_scanning = False
        self.scan_complete = False
        self.scan_timer = 0.0
        self.scan_duration = 2.0  # Fake scan time for effect
        
        # Areas found
        self.areas = []
        self.selected_index = 0
        self.scroll_offset = 0
        self.max_visible = 4
        
        # Animation
        self.pulse_timer = 0.0
        self.scan_angle = 0.0
        self.card_scales = []
        self.card_bobs = []
        self.anim_timer = 0.0
    
    def on_enter(self):
        """Start scanning when entering scene."""
        self._start_scan()
    
    def _start_scan(self):
        """Begin WiFi scan."""
        self.is_scanning = True
        self.scan_complete = False
        self.scan_timer = 0.0
        self.areas = []
    
    def _complete_scan(self):
        """Process scan results."""
        import time
        
        self.is_scanning = False
        self.scan_complete = True
        
        # Get WiFi networks
        networks = self.wifi_scanner.scan()
        
        # Get completed areas (24hr cooldown)
        completed = self.game_state.get("completed_areas", {})
        current_time = time.time()
        
        # Convert to game Areas
        self.areas = []
        for network in networks:
            area = self.area_generator.generate_area(network)
            
            # Check if on cooldown
            ssid = network.get("ssid", "")
            if ssid in completed:
                time_since = current_time - completed[ssid]
                hours_left = 24 - (time_since / 3600)
                if hours_left > 0:
                    area["on_cooldown"] = True
                    area["cooldown_hours"] = int(hours_left) + 1
                else:
                    # Cooldown expired, remove from completed
                    del completed[ssid]
                    area["on_cooldown"] = False
            else:
                area["on_cooldown"] = False
            
            self.areas.append(area)
        
        # Sort by signal strength (strongest = closest = boss area)
        self.areas.sort(key=lambda a: a["signal"], reverse=True)
        
        # Mark strongest as "boss area"
        if self.areas:
            self.areas[0]["is_boss_area"] = True
        
        # Initialize card animations
        self.card_scales = [1.0] * len(self.areas)
        self.card_bobs = [0.0] * len(self.areas)
        
        self.selected_index = 0
        self.scroll_offset = 0
    
    def update(self, dt: float):
        """Update scan animation."""
        self.pulse_timer += dt
        self.anim_timer += dt
        
        if self.is_scanning:
            self.scan_timer += dt
            self.scan_angle += dt * 360  # Rotating scan effect
            
            if self.scan_timer >= self.scan_duration:
                self._complete_scan()
        else:
            # Update card animations
            for i in range(len(self.areas)):
                # Bob animation (increased speed from 2 to 3.5)
                self.card_bobs[i] = math.sin(self.anim_timer * 3.5 + i * 0.5) * 2
                
                # Scale animation - selected card is larger (increased responsiveness from 0.12 to 0.20)
                target_scale = 1.08 if i == self.selected_index else 0.96
                if i < len(self.card_scales):
                    self.card_scales[i] += (target_scale - self.card_scales[i]) * 0.20
    
    def handle_event(self, event: pygame.event.Event):
        """Handle input."""
        if event.type == pygame.USEREVENT:
            action = event.dict.get("action")
            
            if self.is_scanning:
                return  # No input during scan
            
            if action == "up" and self.areas:
                self.selected_index = max(0, self.selected_index - 1)
                self._update_scroll()
            elif action == "down" and self.areas:
                self.selected_index = min(len(self.areas) - 1, self.selected_index + 1)
                self._update_scroll()
            elif action == "confirm" and self.areas:
                self._jack_in()
            elif action == "cancel":
                self.manager.change_scene("hub")
            elif action == "start":
                # Rescan
                self._start_scan()
    
    def _update_scroll(self):
        """Keep selected item visible."""
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + self.max_visible:
            self.scroll_offset = self.selected_index - self.max_visible + 1
    
    def _jack_in(self):
        """Enter selected area."""
        if self.areas:
            selected_area = self.areas[self.selected_index]
            
            # Check cooldown
            if selected_area.get("on_cooldown"):
                return  # Can't enter, on cooldown
            
            self.game_state["current_area"] = selected_area
            self.manager.change_scene("jack_in", area=selected_area)
    
    def draw(self, screen: pygame.Surface):
        """Draw the scan screen."""
        if self.is_scanning:
            self._draw_scanning(screen)
        else:
            self._draw_area_list(screen)
    
    def _draw_scanning(self, screen: pygame.Surface):
        """Draw scanning animation."""
        center_x = self.width // 2
        center_y = self.height // 2
        
        # Gradient background
        for y in range(self.height):
            color_val = int(15 + (y / self.height) * 25)
            pygame.draw.line(screen, (color_val, color_val, color_val + 5), (0, y), (self.width, y))
        
        # Radar sweep effect
        max_radius = 80
        
        # Concentric circles
        for i in range(4):
            radius = 20 + i * 20
            alpha = 100 - i * 20
            color = (0, alpha, alpha)
            pygame.draw.circle(screen, color, (center_x, center_y), radius, 1)
        
        # Rotating sweep line
        angle_rad = math.radians(self.scan_angle)
        end_x = center_x + int(math.cos(angle_rad) * max_radius)
        end_y = center_y + int(math.sin(angle_rad) * max_radius)
        pygame.draw.line(screen, self.colors["accent_cyan"],
                        (center_x, center_y), (end_x, end_y), 2)
        
        # Sweep trail (fading arc)
        for i in range(10):
            trail_angle = self.scan_angle - i * 5
            trail_rad = math.radians(trail_angle)
            trail_x = center_x + int(math.cos(trail_rad) * max_radius)
            trail_y = center_y + int(math.sin(trail_rad) * max_radius)
            alpha = 255 - i * 25
            color = (0, max(0, alpha // 2), max(0, alpha))
            pygame.draw.line(screen, color,
                           (center_x, center_y), (trail_x, trail_y), 1)
        
        # Scanning text
        dots = "." * (int(self.scan_timer * 3) % 4)
        self.draw_text(screen, f"Scanning{dots}", center_x, center_y + 100,
                      color=self.colors["accent_cyan"], size=20, center=True)
        
        # Progress bar
        progress = self.scan_timer / self.scan_duration
        bar_width = 150
        bar_x = center_x - bar_width // 2
        bar_y = center_y + 120
        self.draw_progress_bar(screen, bar_x, bar_y, bar_width, 8,
                              progress * 100, 100,
                              fill_color=self.colors["accent_cyan"])
    
    def _draw_area_list(self, screen: pygame.Surface):
        """Draw list of found areas with modern card design."""
        # Gradient background
        for y in range(self.height):
            color_val = int(15 + (y / self.height) * 25)
            pygame.draw.line(screen, (color_val, color_val, color_val + 5), (0, y), (self.width, y))
        
        # Header panel
        pygame.draw.rect(screen, (10, 10, 15), (0, 0, self.width, 55))
        pygame.draw.line(screen, (0, 200, 200), (0, 55), (self.width, 55), 2)
        
        self.draw_text(screen, "AREA SELECT", self.width // 2, 12,
                      color=self.colors["accent_cyan"], size=20, center=True)
        
        area_count = f"{len(self.areas)} networks found"
        self.draw_text(screen, area_count, self.width // 2, 32,
                      color=self.colors["text_dim"], size=11, center=True)
        
        if not self.areas:
            # No networks found
            self.draw_text(screen, "No networks found!", 
                          self.width // 2, self.height // 2,
                          color=self.colors["hp_red"], size=16, center=True)
            self.draw_text(screen, "Press START to rescan",
                          self.width // 2, self.height // 2 + 25,
                          color=self.colors["text_dim"], size=14, center=True)
            return
        
        # Area cards
        card_height = 65
        start_y = 70
        
        for i in range(self.max_visible):
            area_idx = self.scroll_offset + i
            if area_idx >= len(self.areas):
                break
            
            area = self.areas[area_idx]
            y = start_y + i * (card_height + 6)
            bob = self.card_bobs[area_idx] if area_idx < len(self.card_bobs) else 0
            scale = self.card_scales[area_idx] if area_idx < len(self.card_scales) else 1.0
            
            self._draw_area_card(screen, area, 8, y + bob, 
                                self.width - 16, card_height,
                                selected=(area_idx == self.selected_index),
                                scale=scale)
        
        # Footer
        footer_y = self.height - 35
        pygame.draw.line(screen, (0, 200, 200), (0, footer_y), (self.width, footer_y), 1)
        
        self.draw_text(screen, "[Z] Jack In  [X] Back  [START] Rescan",
                      self.width // 2, footer_y + 15,
                      color=self.colors["text_dim"], size=10, center=True)
    
    def _draw_area_card(self, screen: pygame.Surface, area: dict,
                        x: int, y: int, width: int, height: int,
                        selected: bool = False, scale: float = 1.0):
        """Draw a modern area card with polish."""
        is_cooldown = area.get("on_cooldown", False)
        
        # Apply scale from center
        scaled_width = int(width * scale)
        scaled_height = int(height * scale)
        offset_x = (width - scaled_width) // 2
        offset_y = (height - scaled_height) // 2
        
        x = int(x + offset_x)
        y = int(y + offset_y)
        
        # Card background and border
        if is_cooldown:
            border_color = (100, 100, 120)
            bg_color = (30, 30, 40)
        elif selected:
            border_color = (0, 255, 200)
            bg_color = (40, 60, 70)
            # Glow effect for selected
            pygame.draw.rect(screen, border_color, (x - 2, y - 2, scaled_width + 4, scaled_height + 4), 3)
        else:
            border_color = (80, 100, 120)
            bg_color = (25, 35, 45)
        
        pygame.draw.rect(screen, bg_color, (x, y, scaled_width, scaled_height))
        pygame.draw.rect(screen, border_color, (x, y, scaled_width, scaled_height), 2)
        
        # Gradient overlay on card
        for i in range(scaled_height):
            alpha = int((1 - i / scaled_height) * 20)
            if not is_cooldown and area.get("is_boss_area"):
                color = (200 + alpha, 50 + alpha, 50 + alpha)
            else:
                color = (alpha, alpha // 2, alpha)
            pygame.draw.line(screen, color, (x, y + i), (x + scaled_width, y + i))
        
        # Boss indicator bar
        if area.get("is_boss_area") and not is_cooldown:
            pygame.draw.rect(screen, (255, 100, 100), (x + 1, y + 1, 3, scaled_height - 2))
        
        # Left side - Network name and status
        name = area["display_name"]
        if len(name) > 16:
            name = name[:14] + ".."
        
        name_color = self.colors["text_dim"] if is_cooldown else self.colors["text_white"]
        self.draw_text(screen, name, x + 12, y + 8, size=13, color=name_color)
        
        # Level badge (top right)
        if not is_cooldown:
            level = area["recommended_level"]
            if level > self.game_state["navi"]["level"] + 2:
                badge_color = self.colors["hp_red"]
            elif level <= self.game_state["navi"]["level"]:
                badge_color = self.colors["hp_green"]
            else:
                badge_color = (200, 150, 50)
            
            badge_text = f"Lv.{level}"
            self.draw_text(screen, badge_text, x + scaled_width - 28, y + 8, 
                          size=11, color=badge_color)
        
        # Signal bars (left side, lower)
        signal = area["signal"]
        bars = min(4, max(1, signal // 25 + 1))
        bar_width = 3
        bar_spacing = 1
        bars_x = x + 12
        bars_y = y + 26
        
        for i in range(4):
            bar_height = 3 + i * 3
            bar_x = bars_x + i * (bar_width + bar_spacing)
            bar_y = bars_y + 12 - bar_height
            
            if i < bars:
                bar_color = self.colors["hp_green"] if bars >= 3 else (200, 150, 50)
            else:
                bar_color = (40, 40, 50)
            
            pygame.draw.rect(screen, bar_color, (bar_x, bar_y, bar_width, bar_height))
        
        self.draw_text(screen, f"{signal}%", bars_x + 20, bars_y - 3, size=9, 
                      color=self.colors["text_dim"])
        
        # Cooldown or theme indicator (right side)
        if is_cooldown:
            hours = area.get("cooldown_hours", 24)
            self.draw_text(screen, f"Cooldown", x + scaled_width - 70, y + 12,
                          size=10, color=self.colors["hp_red"])
            self.draw_text(screen, f"{hours}h", x + scaled_width - 70, y + 28,
                          size=12, color=self.colors["hp_red"])
        else:
            # Theme icon
            theme_colors = {
                "digital": (0, 200, 255),
                "fire": (255, 100, 50),
                "aqua": (50, 150, 255),
                "forest": (50, 200, 100),
                "electric": (255, 255, 100),
                "dark": (150, 50, 200),
            }
            theme_color = theme_colors.get(area["theme"], (150, 150, 150))
            pygame.draw.circle(screen, theme_color, 
                             (x + scaled_width - 18, y + scaled_height // 2), 10)
            
            # Security indicator
            if area.get("security") != "Open":
                pygame.draw.rect(screen, self.colors["accent_yellow"],
                               (x + scaled_width - 18, y + scaled_height - 15, 6, 8))
                pygame.draw.line(screen, self.colors["accent_yellow"],
                               (x + scaled_width - 19, y + scaled_height - 18),
                               (x + scaled_width - 17, y + scaled_height - 18), 1)
        
        # Selection indicator triangle
        if selected:
            indicator_y = y + scaled_height + 6
            pygame.draw.polygon(screen, (0, 255, 200), [
                (x + scaled_width // 2 - 6, indicator_y),
                (x + scaled_width // 2 + 6, indicator_y),
                (x + scaled_width // 2, indicator_y + 7)
            ])
