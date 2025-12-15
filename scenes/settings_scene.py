"""
Settings Scene - Game options.
"""

import pygame
from scenes.base_scene import BaseScene


class SettingsScene(BaseScene):
    """Game settings menu."""
    
    target_fps = 30
    
    def __init__(self, manager):
        super().__init__(manager)
        self.options = [
            ("Show SSID Names", "show_ssid_names"),
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
        
        self.draw_panel(screen, 5, 5, self.width - 10, 25)
        self.draw_text(screen, "SETTINGS", self.width // 2, 10,
                      size=18, center=True, color=self.colors["accent_cyan"])
        
        settings = self.game_state["settings"]
        y = 50
        for i, (label, key) in enumerate(self.options):
            sel = i == self.selected_index
            bg = self.colors["accent_cyan"] if sel else self.colors["bg_panel"]
            self.draw_panel(screen, 20, y, self.width - 40, 30, color=bg, border_width=1)
            
            tc = self.colors["bg_dark"] if sel else self.colors["text_white"]
            self.draw_text(screen, label, 30, y + 7, size=14, color=tc)
            
            val = "ON" if settings[key] else "OFF"
            vc = self.colors["hp_green"] if settings[key] else self.colors["hp_red"]
            if sel:
                vc = self.colors["bg_dark"]
            self.draw_text(screen, val, self.width - 50, y + 7, size=14, color=vc)
            y += 38
        
        self.draw_text(screen, "[Z] Toggle  [X] Back", self.width // 2, self.height - 20,
                      size=12, center=True, color=self.colors["text_dim"])
