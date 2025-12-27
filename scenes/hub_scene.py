"""
Hub Scene - The main "Operator Desk" screen.
Shows Navi status, menu options, and acts as home base.
Optimized for 128x128 display with mugshot image.
"""

import pygame
import math
import os
from pathlib import Path
from scenes.base_scene import BaseScene


class HubScene(BaseScene):
    """Main hub - Navi display with menu options."""
    
    target_fps = 30
    
    def __init__(self, manager):
        super().__init__(manager)
        
        # Menu options
        self.menu_items = [
            ("Scan", "scan"),
            ("Folder", "folder"),
            ("Equipment", "equipment"),  # Changed from NaviCust
            ("Settings", "settings"),
        ]
        self.selected_index = 0
        
        # Animation timers
        self.idle_timer = 0.0
        self.blink_timer = 0.0
        self.pulse_timer = 0.0
        
        # Navi mood based on HP
        self.mood = "normal"  # normal, happy, damaged, critical
        
        # Load mugshot image
        self.mugshot = self._load_mugshot()
    
    def _load_mugshot(self) -> pygame.Surface:
        """Load the Navi mugshot image."""
        mugshot_path = Path("assets/Mugshot/mugshot.png")
        
        # Try multiple possible paths
        possible_paths = [
            mugshot_path,
            Path("C:/Users/Tan/OneDrive/Desktop/Mega/NetNavi/assets/Mugshot/mugshot.png"),
            Path("assets/Mugshot/mugshot.webp"),
        ]
        
        for path in possible_paths:
            if path.exists():
                try:
                    img = pygame.image.load(str(path)).convert_alpha()
                    # Scale to fit 128x128 display (about 40x40 for mugshot)
                    scaled = pygame.transform.scale(img, (40, 40))
                    print(f"[HUB] Loaded mugshot from {path}")
                    return scaled
                except Exception as e:
                    print(f"[HUB] Failed to load {path}: {e}")
        
        # Fallback: create placeholder
        print("[HUB] Using placeholder mugshot")
        placeholder = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(placeholder, (0, 120, 255), (20, 20), 18)
        pygame.draw.circle(placeholder, (0, 255, 200), (20, 20), 18, 2)
        return placeholder
    
    def on_enter(self):
        """Update mood when entering hub."""
        self._update_mood()
    
    def _update_mood(self):
        """Set Navi mood based on current HP percentage."""
        navi = self.game_state["navi"]
        hp_pct = navi["hp"] / navi["max_hp"]
        
        if hp_pct > 0.75:
            self.mood = "happy"
        elif hp_pct > 0.4:
            self.mood = "normal"
        elif hp_pct > 0.15:
            self.mood = "damaged"
        else:
            self.mood = "critical"
    
    def update(self, dt: float):
        """Update animations."""
        self.idle_timer += dt
        self.blink_timer += dt
        self.pulse_timer += dt * 2  # Faster pulse
        
        # Reset blink every 3-4 seconds
        if self.blink_timer > 3.5:
            self.blink_timer = 0
    
    def handle_event(self, event: pygame.event.Event):
        """Handle menu navigation."""
        if event.type == pygame.USEREVENT:
            action = event.dict.get("action")
            
            if action == "up":
                self.selected_index = (self.selected_index - 1) % len(self.menu_items)
            elif action == "down":
                self.selected_index = (self.selected_index + 1) % len(self.menu_items)
            elif action == "confirm":
                self._select_menu_item()
            elif action == "cancel":
                pass  # Maybe show quit dialog?
    
    def _select_menu_item(self):
        """Handle menu selection."""
        _, scene_name = self.menu_items[self.selected_index]
        
        if scene_name == "scan":
            self.manager.change_scene("scan")
        elif scene_name == "folder":
            self.manager.push_scene("folder")
        elif scene_name == "settings":
            self.manager.push_scene("settings")
        elif scene_name == "equipment":  # Changed from navicust
            self.manager.push_scene("equipment")
    
    def draw(self, screen: pygame.Surface):
        """Draw the hub screen."""
        # Background gradient effect (simple)
        self._draw_background(screen)
        
        # Draw Navi mugshot in center
        self._draw_navi(screen)
        
        # Draw status bars (top)
        self._draw_status_bars(screen)
        
        # Draw menu (bottom)
        self._draw_menu(screen)
        
        # Draw info bar
        self._draw_info_bar(screen)
    
    def _draw_background(self, screen: pygame.Surface):
        """Draw animated background."""
        # Base color
        screen.fill(self.colors["bg_dark"])
        
        # Animated grid lines (cyber effect)
        grid_color = (25, 35, 50)
        grid_spacing = 16
        offset = int(self.idle_timer * 8) % grid_spacing
        
        # Horizontal lines
        for y in range(-offset, self.height + grid_spacing, grid_spacing):
            pygame.draw.line(screen, grid_color, (0, y), (self.width, y), 1)
        
        # Vertical lines
        for x in range(-offset, self.width + grid_spacing, grid_spacing):
            pygame.draw.line(screen, grid_color, (x, 0), (x, self.height), 1)
    
    def _draw_navi(self, screen: pygame.Surface):
        """Draw the Navi character mugshot."""
        center_x = self.width // 2
        center_y = 40
        
        # Idle animation - gentle bob
        bob = math.sin(self.idle_timer * 2) * 2
        center_y += int(bob)
        
        # Draw mugshot
        mugshot_rect = self.mugshot.get_rect(center=(center_x, center_y))
        screen.blit(self.mugshot, mugshot_rect)
        
        # Navi name below
        self.draw_text(screen, self.game_state["navi"]["name"],
                      center_x, center_y + 26, 
                      color=self.colors["accent_cyan"],
                      size=10, center=True)
        
        # Level
        self.draw_text(screen, f"Lv{self.game_state['navi']['level']}",
                      center_x, center_y + 36,
                      color=self.colors["text_dim"],
                      size=8, center=True)
    
    def _draw_status_bars(self, screen: pygame.Surface):
        """Draw HP and Energy bars at top."""
        navi = self.game_state["navi"]
        
        # Compact bars for 128x128
        bar_y = 2
        bar_width = self.width - 8
        
        # HP Bar
        self.draw_text(screen, "HP", 4, bar_y, size=8, color=self.colors["text_dim"])
        self.draw_progress_bar(screen, 16, bar_y, bar_width - 16, 6,
                              navi["hp"], navi["max_hp"])
        
        # Energy Bar
        bar_y += 8
        self.draw_text(screen, "EN", 4, bar_y, size=8, color=self.colors["text_dim"])
        self.draw_progress_bar(screen, 16, bar_y, bar_width - 16, 6,
                              navi["energy"], navi["max_energy"],
                              fill_color=self.colors["energy_blue"])
    
    def _draw_menu(self, screen: pygame.Surface):
        """Draw menu as one-item carousel (bottom area, no mugshot obstruction)."""
        # Menu container - below mugshot
        menu_y = 70
        menu_height = 40
        
        # Get current menu item
        current_label, _ = self.menu_items[self.selected_index]
        
        # Draw container box
        self.draw_panel(screen, 4, menu_y, self.width - 8, menu_height, 
                       color=self.colors["bg_panel"], border_width=2)
        
        # Draw current item (LARGE text, centered)
        text_y = menu_y + menu_height // 2 - 6
        
        # Pulse effect for selection
        pulse = (math.sin(self.pulse_timer * 3) + 1) / 2
        text_color = self.colors["accent_cyan"]
        
        # Arrow indicator (animated)
        arrow_x = 8 + int(pulse * 2)
        self.draw_text(screen, "▶", arrow_x, text_y, 
                      size=16, color=text_color)
        
        # Menu item text (very large, readable)
        self.draw_text(screen, current_label, self.width // 2, text_y,
                      size=24, center=True, color=self.colors["text_white"])
        
        # Scroll indicators
        indicator_y = menu_y + menu_height - 8
        
        # Up arrow (if not first item)
        if self.selected_index > 0:
            self.draw_text(screen, "▲", self.width // 2 - 20, indicator_y,
                          size=8, center=True, color=self.colors["text_dim"])
        
        # Down arrow (if not last item)
        if self.selected_index < len(self.menu_items) - 1:
            self.draw_text(screen, "▼", self.width // 2 + 20, indicator_y,
                          size=8, center=True, color=self.colors["text_dim"])
    
    def _draw_info_bar(self, screen: pygame.Surface):
        """Draw day and zenny at bottom."""
        # Bottom info
        info_y = self.height - 10
        
        # Day
        self.draw_text(screen, f"D{self.game_state['day']}", 
                      4, info_y, size=8,
                      color=self.colors["text_dim"])
        
        # Zenny (currency)
        zenny_text = f"{self.game_state['zenny']}z"
        self.draw_text(screen, zenny_text,
                      self.width - 30, info_y, size=8,
                      color=self.colors["accent_yellow"])
