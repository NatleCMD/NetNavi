"""
Scan Scene - WiFi scanning and Area selection.
Displays nearby networks as explorable cyber areas.
"""

import pygame
import math
import random
from scenes.base_scene import BaseScene
from wifi.scanner import WiFiScanner
from worldgen.area_gen import AreaGenerator


class ScanScene(BaseScene):
    """WiFi scan and Area selection screen."""
    
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
        self.max_visible = 5
        
        # Animation
        self.pulse_timer = 0.0
        self.scan_angle = 0.0
    
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
        
        self.selected_index = 0
        self.scroll_offset = 0
    
    def update(self, dt: float):
        """Update scan animation."""
        self.pulse_timer += dt
        
        if self.is_scanning:
            self.scan_timer += dt
            self.scan_angle += dt * 360  # Rotating scan effect
            
            if self.scan_timer >= self.scan_duration:
                self._complete_scan()
    
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
        
        # Background
        screen.fill(self.colors["bg_dark"])
        
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
        """Draw list of found areas."""
        # Header
        self.draw_panel(screen, 5, 5, self.width - 10, 30)
        self.draw_text(screen, "AREA SELECT", self.width // 2, 12,
                      color=self.colors["accent_cyan"], size=18, center=True)
        
        area_count = f"{len(self.areas)} networks found"
        self.draw_text(screen, area_count, self.width // 2, 26,
                      color=self.colors["text_dim"], size=12, center=True)
        
        if not self.areas:
            # No networks found
            self.draw_text(screen, "No networks found!", 
                          self.width // 2, self.height // 2,
                          color=self.colors["hp_red"], size=16, center=True)
            self.draw_text(screen, "Press START to rescan",
                          self.width // 2, self.height // 2 + 25,
                          color=self.colors["text_dim"], size=14, center=True)
            return
        
        # Area list
        list_y = 45
        item_height = 36
        
        for i in range(self.max_visible):
            area_idx = self.scroll_offset + i
            if area_idx >= len(self.areas):
                break
            
            area = self.areas[area_idx]
            y = list_y + i * item_height
            
            self._draw_area_item(screen, area, 10, y, 
                                self.width - 20, item_height - 4,
                                selected=(area_idx == self.selected_index))
        
        # Scroll indicators
        if self.scroll_offset > 0:
            self.draw_text(screen, "▲", self.width - 15, list_y - 5,
                          color=self.colors["accent_cyan"], size=14)
        if self.scroll_offset + self.max_visible < len(self.areas):
            self.draw_text(screen, "▼", self.width - 15, 
                          list_y + self.max_visible * item_height - 10,
                          color=self.colors["accent_cyan"], size=14)
        
        # Instructions
        self.draw_text(screen, "[Z] Jack In  [X] Back  [START] Rescan",
                      self.width // 2, self.height - 15,
                      color=self.colors["text_dim"], size=12, center=True)
    
    def _draw_area_item(self, screen: pygame.Surface, area: dict,
                        x: int, y: int, width: int, height: int,
                        selected: bool = False):
        """Draw a single area list item."""
        is_cooldown = area.get("on_cooldown", False)
        
        # Background
        if is_cooldown:
            bg_color = (40, 40, 50)  # Grayed out
            border_color = self.colors["text_dim"]
        elif selected:
            bg_color = (40, 50, 70)
            border_color = self.colors["accent_cyan"]
        else:
            bg_color = self.colors["bg_panel"]
            border_color = self.colors["text_dim"]
        
        self.draw_panel(screen, x, y, width, height, 
                       color=bg_color, border_color=border_color, border_width=1)
        
        # Boss indicator
        if area.get("is_boss_area") and not is_cooldown:
            pygame.draw.rect(screen, self.colors["hp_red"],
                           (x + 2, y + 2, 4, height - 4))
        
        # Area name
        name = area["display_name"]
        if len(name) > 18:
            name = name[:16] + ".."
        
        if is_cooldown:
            name_color = self.colors["text_dim"]
        elif area.get("is_boss_area"):
            name_color = self.colors["accent_cyan"]
        else:
            name_color = self.colors["text_white"]
        
        self.draw_text(screen, name, x + 10, y + 3, color=name_color, size=14)
        
        # Cooldown indicator
        if is_cooldown:
            hours = area.get("cooldown_hours", 24)
            self.draw_text(screen, f"{hours}hr", x + width - 35, y + 3,
                          size=12, color=self.colors["hp_red"])
        else:
            # Theme icon (colored circle placeholder)
            theme_colors = {
                "digital": (0, 200, 255),
                "fire": (255, 100, 50),
                "aqua": (50, 150, 255),
                "forest": (50, 200, 100),
                "electric": (255, 255, 100),
                "dark": (150, 50, 200),
            }
            theme_color = theme_colors.get(area["theme"], (150, 150, 150))
            pygame.draw.circle(screen, theme_color, (x + width - 25, y + height // 2), 8)
        
        # Signal bars
        self._draw_signal_bars(screen, x + width - 55, y + 5, area["signal"])
        
        # Difficulty/Level
        diff_text = f"Lv.{area['recommended_level']}"
        if is_cooldown:
            diff_color = self.colors["text_dim"]
        elif area["recommended_level"] > self.game_state["navi"]["level"] + 2:
            diff_color = self.colors["hp_red"]
        elif area["recommended_level"] <= self.game_state["navi"]["level"]:
            diff_color = self.colors["hp_green"]
        else:
            diff_color = self.colors["text_dim"]
        self.draw_text(screen, diff_text, x + 10, y + 18, 
                      color=diff_color, size=12)
        
        # Security type indicator
        if area["security"] != "Open" and not is_cooldown:
            pygame.draw.rect(screen, self.colors["accent_yellow"],
                           (x + 60, y + 18, 8, 10))
            pygame.draw.rect(screen, self.colors["accent_yellow"],
                           (x + 62, y + 15, 4, 5), 1)
    
    def _draw_signal_bars(self, screen: pygame.Surface, x: int, y: int, signal: int):
        """Draw signal strength bars (0-100 -> 1-4 bars)."""
        bars = min(4, max(1, signal // 25 + 1))
        bar_width = 4
        bar_spacing = 2
        max_height = 16
        
        for i in range(4):
            bar_height = 4 + i * 4
            bar_x = x + i * (bar_width + bar_spacing)
            bar_y = y + max_height - bar_height
            
            if i < bars:
                color = self.colors["hp_green"] if bars >= 3 else self.colors["accent_yellow"]
            else:
                color = (50, 50, 60)
            
            pygame.draw.rect(screen, color, (bar_x, bar_y, bar_width, bar_height))
