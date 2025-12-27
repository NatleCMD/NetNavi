"""
Base Scene class - all game scenes inherit from this.
"""

import pygame
from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from main import SceneManager


class BaseScene:
    """Abstract base class for all game scenes."""
    
    # Override in subclasses
    target_fps = 30
    
    def __init__(self, manager: "SceneManager"):
        self.manager = manager
        self.config = manager.config
        self.game_state = manager.game_state
        self.colors = self.config["colors"]
        
        # Screen dimensions
        self.width = self.config["screen_width"]
        self.height = self.config["screen_height"]
        
        # Common fonts (created lazily)
        self._fonts = {}
    
    def get_font(self, size: int) -> pygame.font.Font:
        """Get or create a font of the specified size."""
        if size not in self._fonts:
            # Use default font for now - replace with custom font path later
            self._fonts[size] = pygame.font.Font(None, size)
        return self._fonts[size]
    
    def on_enter(self):
        """Called when scene becomes active."""
        pass
    
    def on_exit(self):
        """Called when scene is being left."""
        pass
    
    def update(self, dt: float):
        """Update scene logic. dt is delta time in seconds."""
        pass
    
    def draw(self, screen: pygame.Surface):
        """Draw the scene."""
        pass
    
    def handle_event(self, event: pygame.event.Event):
        """Handle input events."""
        pass
    
    # =========================================================================
    # DRAWING HELPERS
    # =========================================================================
    
    def draw_text(self, screen: pygame.Surface, text: str, x: int, y: int, 
                  color=None, size: int = 20, center: bool = False):
        """Draw text with optional centering."""
        if color is None:
            color = self.colors["text_white"]
        
        font = self.get_font(size)
        surface = font.render(text, True, color)
        
        if center:
            rect = surface.get_rect(center=(x, y))
            screen.blit(surface, rect)
        else:
            screen.blit(surface, (x, y))
        
        return surface.get_rect()
    
    def draw_panel(self, screen: pygame.Surface, x: int, y: int, 
                   width: int, height: int, color=None, border_color=None, 
                   border_width: int = 2):
        """Draw a UI panel with optional border."""
        if color is None:
            color = self.colors["bg_panel"]
        if border_color is None:
            border_color = self.colors["accent_cyan"]
        
        # Background
        pygame.draw.rect(screen, color, (x, y, width, height))
        
        # Border
        if border_width > 0:
            pygame.draw.rect(screen, border_color, (x, y, width, height), border_width)
    
    def draw_progress_bar(self, screen: pygame.Surface, x: int, y: int,
                          width: int, height: int, value: float, max_value: float,
                          fill_color=None, bg_color=None, border_color=None):
        """Draw a progress/health bar."""
        if bg_color is None:
            bg_color = (30, 30, 40)
        if border_color is None:
            border_color = self.colors["text_dim"]
        
        # Determine fill color based on percentage if not specified
        if fill_color is None:
            pct = value / max_value if max_value > 0 else 0
            if pct > 0.5:
                fill_color = self.colors["hp_green"]
            elif pct > 0.25:
                fill_color = self.colors["hp_yellow"]
            else:
                fill_color = self.colors["hp_red"]
        
        # Background
        pygame.draw.rect(screen, bg_color, (x, y, width, height))
        
        # Fill
        fill_width = int((value / max_value) * width) if max_value > 0 else 0
        if fill_width > 0:
            pygame.draw.rect(screen, fill_color, (x, y, fill_width, height))
        
        # Border
        pygame.draw.rect(screen, border_color, (x, y, width, height), 1)
    
    def draw_placeholder_sprite(self, screen: pygame.Surface, x: int, y: int,
                                 width: int, height: int, color, label: str = ""):
        """Draw a colored rectangle as placeholder for sprites."""
        pygame.draw.rect(screen, color, (x, y, width, height))
        pygame.draw.rect(screen, self.colors["text_white"], (x, y, width, height), 1)
        
        if label:
            self.draw_text(screen, label, x + width // 2, y + height // 2,
                          size=12, center=True)
    
    def draw_circle_sprite(self, screen: pygame.Surface, x: int, y: int,
                           radius: int, color, label: str = ""):
        """Draw a colored circle as placeholder for sprites."""
        pygame.draw.circle(screen, color, (x, y), radius)
        pygame.draw.circle(screen, self.colors["text_white"], (x, y), radius, 2)
        
        if label:
            self.draw_text(screen, label, x, y, size=12, center=True)
