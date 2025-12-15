"""
Jack In Scene - Transition animation when entering an Area.
"""

import pygame
import math
from scenes.base_scene import BaseScene


class JackInScene(BaseScene):
    """Transition animation when jacking into an area."""
    
    target_fps = 30
    
    def __init__(self, manager, area: dict = None):
        super().__init__(manager)
        self.area = area or {}
        
        # Animation state
        self.phase = "zoom_out"  # zoom_out -> tunnel -> zoom_in
        self.timer = 0.0
        self.total_duration = 2.5
        
        # Phase timings
        self.zoom_out_end = 0.5
        self.tunnel_end = 2.0
        
        # Tunnel effect
        self.tunnel_rings = []
        self.ring_spawn_timer = 0.0
    
    def update(self, dt: float):
        """Update animation."""
        self.timer += dt
        
        # Update phase
        if self.timer < self.zoom_out_end:
            self.phase = "zoom_out"
        elif self.timer < self.tunnel_end:
            self.phase = "tunnel"
            self._update_tunnel(dt)
        else:
            self.phase = "zoom_in"
        
        # End transition
        if self.timer >= self.total_duration:
            self.manager.change_scene("area", area=self.area)
    
    def _update_tunnel(self, dt: float):
        """Update tunnel ring effect."""
        self.ring_spawn_timer += dt
        
        # Spawn new rings
        if self.ring_spawn_timer > 0.05:
            self.ring_spawn_timer = 0
            self.tunnel_rings.append({
                "z": 1.0,  # Start far away
                "speed": 2.0 + len(self.tunnel_rings) * 0.1,
            })
        
        # Update existing rings
        for ring in self.tunnel_rings:
            ring["z"] -= dt * ring["speed"]
        
        # Remove rings that passed camera
        self.tunnel_rings = [r for r in self.tunnel_rings if r["z"] > 0]
    
    def draw(self, screen: pygame.Surface):
        """Draw transition effect."""
        screen.fill((0, 0, 0))
        
        center_x = self.width // 2
        center_y = self.height // 2
        
        if self.phase == "zoom_out":
            self._draw_zoom_out(screen, center_x, center_y)
        elif self.phase == "tunnel":
            self._draw_tunnel(screen, center_x, center_y)
        else:
            self._draw_zoom_in(screen, center_x, center_y)
        
        # "JACK IN" text
        if self.timer < 1.5:
            alpha = min(255, int(self.timer * 500))
            if self.timer > 1.0:
                alpha = max(0, 255 - int((self.timer - 1.0) * 500))
            
            # Flash effect
            if int(self.timer * 10) % 2 == 0:
                self.draw_text(screen, "JACK IN!", center_x, center_y - 50,
                              color=self.colors["accent_cyan"], size=28, center=True)
        
        # Area name
        if self.timer > 1.0:
            name = self.area.get("display_name", "Unknown Area")
            self.draw_text(screen, name, center_x, self.height - 40,
                          color=self.colors["text_white"], size=16, center=True)
    
    def _draw_zoom_out(self, screen: pygame.Surface, cx: int, cy: int):
        """Navi zooming away effect."""
        progress = self.timer / self.zoom_out_end
        
        # Shrinking circle (Navi placeholder)
        radius = int(40 * (1 - progress * 0.8))
        if radius > 0:
            pygame.draw.circle(screen, self.colors["accent_cyan"], (cx, cy), radius)
            pygame.draw.circle(screen, self.colors["text_white"], (cx, cy), radius, 2)
        
        # Speed lines
        num_lines = 12
        for i in range(num_lines):
            angle = (i / num_lines) * math.pi * 2
            inner_r = 50 + progress * 30
            outer_r = inner_r + 20 + progress * 50
            
            x1 = cx + int(math.cos(angle) * inner_r)
            y1 = cy + int(math.sin(angle) * inner_r)
            x2 = cx + int(math.cos(angle) * outer_r)
            y2 = cy + int(math.sin(angle) * outer_r)
            
            pygame.draw.line(screen, self.colors["accent_cyan"], (x1, y1), (x2, y2), 2)
    
    def _draw_tunnel(self, screen: pygame.Surface, cx: int, cy: int):
        """Cyber tunnel effect."""
        # Draw rings from far to near
        sorted_rings = sorted(self.tunnel_rings, key=lambda r: r["z"], reverse=True)
        
        for ring in sorted_rings:
            z = ring["z"]
            
            # Perspective scaling
            scale = 1 / (z + 0.1)
            radius = int(20 * scale)
            
            if radius > 200:
                continue
            
            # Color based on depth
            intensity = int(255 * (1 - z))
            color = (0, intensity // 2, intensity)
            
            # Draw ring
            if radius > 2:
                pygame.draw.circle(screen, color, (cx, cy), radius, 2)
        
        # Central glow
        pygame.draw.circle(screen, self.colors["accent_cyan"], (cx, cy), 5)
    
    def _draw_zoom_in(self, screen: pygame.Surface, cx: int, cy: int):
        """Arriving at destination effect."""
        progress = (self.timer - self.tunnel_end) / (self.total_duration - self.tunnel_end)
        
        # Expanding circle
        radius = int(progress * 150)
        
        # Theme color based on area
        theme_colors = {
            "digital": (0, 150, 200),
            "fire": (200, 80, 30),
            "aqua": (30, 100, 200),
            "forest": (30, 150, 80),
            "electric": (200, 200, 50),
            "dark": (100, 30, 150),
        }
        theme = self.area.get("theme", "digital")
        color = theme_colors.get(theme, (100, 100, 100))
        
        # Draw expanding area
        if radius > 0:
            pygame.draw.circle(screen, color, (cx, cy), radius)
            
            # Grid overlay
            grid_alpha = int(100 * (1 - progress))
            grid_color = (grid_alpha, grid_alpha, grid_alpha)
            for i in range(-5, 6):
                offset = i * 20
                if abs(offset) < radius:
                    # Horizontal
                    pygame.draw.line(screen, grid_color,
                                   (cx - radius, cy + offset),
                                   (cx + radius, cy + offset), 1)
                    # Vertical
                    pygame.draw.line(screen, grid_color,
                                   (cx + offset, cy - radius),
                                   (cx + offset, cy + radius), 1)
    
    def handle_event(self, event: pygame.event.Event):
        """Allow skipping with confirm button."""
        if event.type == pygame.USEREVENT:
            action = event.dict.get("action")
            if action == "confirm" and self.timer > 0.5:
                # Skip to area
                self.manager.change_scene("area", area=self.area)
