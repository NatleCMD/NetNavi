"""
Settings Scene - Game options.
Optimized for 128x128 display.
"""

import pygame
from scenes.base_scene import BaseScene


class SettingsScene(BaseScene):
    """Game settings menu."""
    
    target_fps = 30
    
    def __init__(self, manager):
        super().__init__(manager)
        self.options = [
            ("SSID Names", "show_ssid_names"),
            ("Sound", "sound_enabled"),
            ("Vibration", "vibration"),
        ]
        self.selected_index = 0
    
    def handle_event(self, event):
        if event.type != pygame.USEREVENT:
            return
        action = event.dict.get("action")
        settings = self.game_state["settings"]
        
        if action == "up":
            self.selected_index = (self.selected_index - 1) % len(self.options)
        elif action == "down":
            self.selected_index = (self.selected_index + 1) % len(self.options)
        elif action == "confirm":
            key = self.options[self.selected_index][1]
            settings[key] = not settings[key]
        elif action == "cancel":
            self.manager.pop_scene()
    
    def draw(self, screen):
        screen.fill(self.colors["bg_dark"])
        
        self.draw_panel(screen, 2, 2, self.width - 4, 18)
        self.draw_text(screen, "SETTINGS", self.width // 2, 6,
                      size=12, center=True, color=self.colors["accent_cyan"])
        
        settings = self.game_state["settings"]
        y = 26
        item_height = 24  # Tighter spacing
        
        for i, (label, key) in enumerate(self.options):
            sel = i == self.selected_index
            bg = self.colors["accent_cyan"] if sel else self.colors["bg_panel"]
            self.draw_panel(screen, 8, y, self.width - 16, item_height - 2, color=bg, border_width=1)
            
            tc = self.colors["bg_dark"] if sel else self.colors["text_white"]
            self.draw_text(screen, label, 12, y + 4, size=9, color=tc)
            
            val = "ON" if settings[key] else "OFF"
            vc = self.colors["hp_green"] if settings[key] else self.colors["hp_red"]
            if sel:
                vc = self.colors["bg_dark"]
            self.draw_text(screen, val, self.width - 28, y + 4, size=9, color=vc)
            y += item_height
        
        self.draw_text(screen, "[Z]Toggle [X]Back", self.width // 2, self.height - 8,
                      size=7, center=True, color=self.colors["text_dim"])
