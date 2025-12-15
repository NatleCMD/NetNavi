"""
Hub Scene - The main "Operator Desk" screen.
Shows Navi status, menu options, and acts as home base.
"""

import pygame
import math
from scenes.base_scene import BaseScene


class HubScene(BaseScene):
    """Main hub - Navi display with menu options."""
    
    target_fps = 30
    
    def __init__(self, manager):
        super().__init__(manager)
        
        # Menu options
        self.menu_items = [
            ("Scan Areas", "scan"),
            ("Chip Folder", "folder"),
            ("Navi Cust", "navicust"),
            ("Settings", "settings"),
        ]
        self.selected_index = 0
        
        # Animation timers
        self.idle_timer = 0.0
        self.blink_timer = 0.0
        self.pulse_timer = 0.0
        
        # Navi mood based on HP
        self.mood = "normal"  # normal, happy, damaged, critical
        
        # Navi placeholder colors (will be sprite later)
        self.navi_colors = {
            "body": (0, 120, 255),      # Blue body
            "helmet": (0, 80, 200),      # Darker blue helmet
            "visor": (0, 255, 200),      # Cyan visor
            "accent": (255, 220, 0),     # Yellow accents
        }
    
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
        elif scene_name == "navicust":
            self.manager.push_scene("navicust")
    
    def draw(self, screen: pygame.Surface):
        """Draw the hub screen."""
        # Background gradient effect (simple)
        self._draw_background(screen)
        
        # Draw Navi in center
        self._draw_navi(screen)
        
        # Draw status bars (top)
        self._draw_status_bars(screen)
        
        # Draw menu (bottom/side)
        self._draw_menu(screen)
        
        # Draw day counter and zenny
        self._draw_info_bar(screen)
    
    def _draw_background(self, screen: pygame.Surface):
        """Draw animated background."""
        # Base color
        screen.fill(self.colors["bg_dark"])
        
        # Animated grid lines (cyber effect)
        grid_color = (25, 35, 50)
        grid_spacing = 20
        offset = int(self.idle_timer * 10) % grid_spacing
        
        # Horizontal lines
        for y in range(-offset, self.height + grid_spacing, grid_spacing):
            pygame.draw.line(screen, grid_color, (0, y), (self.width, y), 1)
        
        # Vertical lines
        for x in range(-offset, self.width + grid_spacing, grid_spacing):
            pygame.draw.line(screen, grid_color, (x, 0), (x, self.height), 1)
        
        # Center glow effect
        pulse = (math.sin(self.pulse_timer) + 1) / 2  # 0 to 1
        glow_radius = 60 + int(pulse * 10)
        glow_alpha = 30 + int(pulse * 20)
        
        # Draw glow circles (simple radial gradient)
        center_x, center_y = self.width // 2, self.height // 2 - 20
        for i in range(3):
            r = glow_radius - i * 15
            alpha = glow_alpha - i * 10
            color = (0, alpha, alpha // 2)
            pygame.draw.circle(screen, color, (center_x, center_y), r)
    
    def _draw_navi(self, screen: pygame.Surface):
        """Draw the Navi character (placeholder circles for now)."""
        center_x = self.width // 2
        center_y = self.height // 2 - 20
        
        # Idle animation - gentle bob
        bob = math.sin(self.idle_timer * 2) * 3
        center_y += int(bob)
        
        # Body (large circle)
        body_radius = 35
        pygame.draw.circle(screen, self.navi_colors["body"], 
                          (center_x, center_y), body_radius)
        pygame.draw.circle(screen, self.navi_colors["helmet"], 
                          (center_x, center_y), body_radius, 3)
        
        # Helmet top (smaller circle)
        helmet_y = center_y - 25
        pygame.draw.circle(screen, self.navi_colors["helmet"],
                          (center_x, helmet_y), 20)
        
        # Visor (eye area)
        visor_y = center_y - 5
        visor_width = 40
        visor_height = 12
        
        # Visor glow pulse
        pulse = (math.sin(self.pulse_timer * 1.5) + 1) / 2
        visor_color = (
            int(self.navi_colors["visor"][0] * (0.7 + pulse * 0.3)),
            int(self.navi_colors["visor"][1] * (0.7 + pulse * 0.3)),
            int(self.navi_colors["visor"][2] * (0.7 + pulse * 0.3)),
        )
        
        pygame.draw.ellipse(screen, visor_color,
                           (center_x - visor_width // 2, visor_y - visor_height // 2,
                            visor_width, visor_height))
        
        # Blink effect (close visor briefly)
        if 0 < self.blink_timer < 0.15:
            pygame.draw.ellipse(screen, self.navi_colors["helmet"],
                               (center_x - visor_width // 2, visor_y - visor_height // 2,
                                visor_width, visor_height))
        
        # Mood indicator - small expression
        self._draw_mood_indicator(screen, center_x, center_y + 15)
        
        # Emblem (chest circle)
        emblem_y = center_y + 20
        pygame.draw.circle(screen, self.navi_colors["accent"],
                          (center_x, emblem_y), 8)
        pygame.draw.circle(screen, self.colors["text_white"],
                          (center_x, emblem_y), 8, 2)
        
        # Navi name below
        self.draw_text(screen, self.game_state["navi"]["name"],
                      center_x, center_y + 55, 
                      color=self.colors["accent_cyan"],
                      size=18, center=True)
        
        # Level
        self.draw_text(screen, f"Lv.{self.game_state['navi']['level']}",
                      center_x, center_y + 70,
                      color=self.colors["text_dim"],
                      size=14, center=True)
    
    def _draw_mood_indicator(self, screen: pygame.Surface, x: int, y: int):
        """Draw small mood expression."""
        color = self.colors["text_white"]
        
        if self.mood == "happy":
            # Simple smile arc
            pygame.draw.arc(screen, color, (x - 8, y - 8, 16, 16), 
                           3.14, 0, 2)
        elif self.mood == "normal":
            # Neutral line
            pygame.draw.line(screen, color, (x - 6, y), (x + 6, y), 2)
        elif self.mood == "damaged":
            # Worried squiggle
            points = [(x - 6, y), (x - 2, y - 2), (x + 2, y + 2), (x + 6, y)]
            pygame.draw.lines(screen, color, False, points, 2)
        elif self.mood == "critical":
            # Distressed
            pygame.draw.arc(screen, self.colors["hp_red"], 
                           (x - 8, y - 2, 16, 16), 0, 3.14, 2)
    
    def _draw_status_bars(self, screen: pygame.Surface):
        """Draw HP and Energy bars at top."""
        navi = self.game_state["navi"]
        
        # Panel background
        self.draw_panel(screen, 5, 5, 150, 45, border_width=1)
        
        # HP Bar
        self.draw_text(screen, "HP", 10, 10, size=12, 
                      color=self.colors["text_dim"])
        self.draw_progress_bar(screen, 30, 10, 115, 12,
                              navi["hp"], navi["max_hp"])
        self.draw_text(screen, f"{navi['hp']}/{navi['max_hp']}", 
                      90, 10, size=10, center=True,
                      color=self.colors["text_white"])
        
        # Energy Bar
        self.draw_text(screen, "EN", 10, 28, size=12,
                      color=self.colors["text_dim"])
        self.draw_progress_bar(screen, 30, 28, 115, 12,
                              navi["energy"], navi["max_energy"],
                              fill_color=self.colors["energy_blue"])
        self.draw_text(screen, f"{navi['energy']}/{navi['max_energy']}",
                      90, 28, size=10, center=True,
                      color=self.colors["text_white"])
    
    def _draw_menu(self, screen: pygame.Surface):
        """Draw menu options."""
        menu_x = self.width - 110
        menu_y = 50
        item_height = 28
        
        # Menu panel
        panel_height = len(self.menu_items) * item_height + 15
        self.draw_panel(screen, menu_x - 5, menu_y - 5, 
                       110, panel_height, border_width=1)
        
        for i, (label, _) in enumerate(self.menu_items):
            y = menu_y + i * item_height
            
            # Selection indicator
            if i == self.selected_index:
                # Highlight bar
                pygame.draw.rect(screen, self.colors["accent_cyan"],
                               (menu_x, y, 100, item_height - 4))
                text_color = self.colors["bg_dark"]
                
                # Arrow indicator
                arrow_x = menu_x - 8
                pulse = (math.sin(self.pulse_timer * 3) + 1) / 2
                arrow_x -= int(pulse * 3)
                self.draw_text(screen, ">", arrow_x, y + 2, 
                              color=self.colors["accent_cyan"], size=18)
            else:
                text_color = self.colors["text_white"]
            
            self.draw_text(screen, label, menu_x + 5, y + 3,
                          color=text_color, size=16)
    
    def _draw_info_bar(self, screen: pygame.Surface):
        """Draw day and zenny at bottom."""
        # Bottom panel
        self.draw_panel(screen, 5, self.height - 30, self.width - 10, 25,
                       border_width=1)
        
        # Day
        self.draw_text(screen, f"Day {self.game_state['day']}", 
                      15, self.height - 25, size=14,
                      color=self.colors["text_dim"])
        
        # Zenny (currency)
        zenny_text = f"{self.game_state['zenny']}z"
        self.draw_text(screen, zenny_text,
                      self.width - 60, self.height - 25, size=14,
                      color=self.colors["accent_yellow"])
