"""
Folder Scene - Chip folder management with add/remove.
"""

import pygame
from scenes.base_scene import BaseScene
from combat.chips import CHIP_DATABASE


class FolderScene(BaseScene):
    """Manage battle chip folder - add and remove chips."""
    
    target_fps = 30
    
    def __init__(self, manager):
        super().__init__(manager)
        self.selected_index = 0
        self.scroll_offset = 0
        self.max_visible = 5
        self.mode = "folder"  # folder or library
        self.library_index = 0
    
    def handle_event(self, event):
        if event.type != pygame.USEREVENT:
            return
        action = event.dict.get("action")
        folder = self.game_state["chip_folder"]
        
        if self.mode == "folder":
            if action == "up":
                self.selected_index = max(0, self.selected_index - 1)
                self._update_scroll()
            elif action == "down":
                self.selected_index = min(len(folder.chips) - 1, self.selected_index + 1)
                self._update_scroll()
            elif action == "confirm":
                # Remove chip from folder
                if folder.chips:
                    folder.chips.pop(self.selected_index)
                    self.selected_index = min(self.selected_index, len(folder.chips) - 1)
            elif action == "start":
                # Switch to library to add chips
                self.mode = "library"
                self.library_index = 0
            elif action == "cancel":
                self.manager.pop_scene()
        
        elif self.mode == "library":
            library = list(CHIP_DATABASE.keys())
            if action == "up":
                self.library_index = max(0, self.library_index - 1)
            elif action == "down":
                self.library_index = min(len(library) - 1, self.library_index + 1)
            elif action == "confirm":
                # Add chip to folder
                if len(folder.chips) < folder.max_size:
                    chip_name = library[self.library_index]
                    folder.add_chip(chip_name)
            elif action == "cancel":
                self.mode = "folder"
    
    def _update_scroll(self):
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + self.max_visible:
            self.scroll_offset = self.selected_index - self.max_visible + 1
    
    def draw(self, screen):
        screen.fill(self.colors["bg_dark"])
        
        self.draw_panel(screen, 5, 5, self.width - 10, 25)
        self.draw_text(screen, "CHIP FOLDER", self.width // 2, 10,
                      size=18, center=True, color=self.colors["accent_cyan"])
        
        folder = self.game_state["chip_folder"]
        
        if self.mode == "folder":
            self._draw_folder(screen, folder)
        else:
            self._draw_library(screen, folder)
    
    def _draw_folder(self, screen, folder):
        y = 40
        if not folder.chips:
            self.draw_text(screen, "Folder empty!", self.width // 2, 80,
                          size=14, center=True, color=self.colors["text_dim"])
        else:
            for i, chip in enumerate(folder.chips[self.scroll_offset:self.scroll_offset + self.max_visible]):
                idx = self.scroll_offset + i
                sel = idx == self.selected_index
                bg = self.colors["accent_cyan"] if sel else self.colors["bg_panel"]
                self.draw_panel(screen, 10, y, self.width - 20, 28, color=bg, border_width=1)
                tc = self.colors["bg_dark"] if sel else self.colors["text_white"]
                self.draw_text(screen, chip.name, 20, y + 5, size=14, color=tc)
                self.draw_text(screen, str(chip.power), self.width - 70, y + 5, size=14, color=tc)
                self.draw_text(screen, chip.chip_type[:5], self.width - 40, y + 5, size=10, color=tc)
                y += 32
        
        self.draw_text(screen, f"{len(folder.chips)}/{folder.max_size}",
                      self.width // 2, self.height - 35, size=12, center=True,
                      color=self.colors["text_dim"])
        self.draw_text(screen, "[Z]Remove [START]Add [X]Back",
                      self.width // 2, self.height - 15, size=10, center=True,
                      color=self.colors["text_dim"])
    
    def _draw_library(self, screen, folder):
        # Overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        self.draw_text(screen, "ADD CHIP", self.width // 2, 15,
                      size=16, center=True, color=self.colors["accent_cyan"])
        
        library = list(CHIP_DATABASE.keys())
        max_vis = 6
        scroll = max(0, self.library_index - max_vis + 1)
        
        y = 40
        for i, chip_name in enumerate(library[scroll:scroll + max_vis]):
            idx = scroll + i
            sel = idx == self.library_index
            chip = CHIP_DATABASE[chip_name]
            
            bg = self.colors["accent_cyan"] if sel else self.colors["bg_panel"]
            self.draw_panel(screen, 15, y, self.width - 30, 26, color=bg, border_width=1)
            
            tc = self.colors["bg_dark"] if sel else self.colors["text_white"]
            self.draw_text(screen, chip_name, 25, y + 4, size=12, color=tc)
            self.draw_text(screen, str(chip.power), self.width - 60, y + 4, size=12, color=tc)
            y += 30
        
        self.draw_text(screen, f"Folder: {len(folder.chips)}/{folder.max_size}",
                      self.width // 2, self.height - 35, size=11, center=True,
                      color=self.colors["text_dim"])
        self.draw_text(screen, "[Z]Add [X]Back",
                      self.width // 2, self.height - 15, size=10, center=True,
                      color=self.colors["text_dim"])
