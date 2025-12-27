"""
Folder Scene - Chip folder management with equip/unequip.
Shows all owned chips, select which go into battle folder.
Optimized for 128x128 display - shows 3 chips at a time.
"""

import pygame
from scenes.base_scene import BaseScene
from combat.chips import CHIP_DATABASE


class FolderScene(BaseScene):
    """Manage battle chip folder - equip/unequip chips."""
    
    target_fps = 30
    
    def __init__(self, manager):
        super().__init__(manager)
        self.selected_index = 0
        self.scroll_offset = 0
        self.max_visible = 3  # Show 3 chips at a time
    
    def handle_event(self, event):
        if event.type != pygame.USEREVENT:
            return
        
        action = event.dict.get("action")
        chip_folder = self.game_state["chip_folder"]
        owned_chips = chip_folder.get("owned_chips", [])
        folder_chips = chip_folder.get("folder_chips", [])
        max_size = chip_folder.get("max_size", 30)
        
        if not owned_chips:
            if action == "cancel":
                self.manager.pop_scene()
            return
        
        if action == "up":
            self.selected_index = max(0, self.selected_index - 1)
            self._update_scroll()
        elif action == "down":
            self.selected_index = min(len(owned_chips) - 1, self.selected_index + 1)
            self._update_scroll()
        elif action == "confirm":
            # Toggle chip in/out of folder using INDEX tracking
            chip = owned_chips[self.selected_index]
            
            # Check if this specific chip index is already in folder
            chip_already_in_folder = False
            for i, folder_chip in enumerate(folder_chips):
                # Compare by object identity (is same object)
                if folder_chip is chip:
                    # Remove this specific instance
                    folder_chips.pop(i)
                    chip_already_in_folder = True
                    break
            
            # If not in folder, add it
            if not chip_already_in_folder:
                if len(folder_chips) < max_size:
                    folder_chips.append(chip)
        elif action == "cancel":
            self.manager.pop_scene()
    
    def _update_scroll(self):
        """Keep selected item in view."""
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + self.max_visible:
            self.scroll_offset = self.selected_index - self.max_visible + 1
    
    def draw(self, screen):
        screen.fill(self.colors["bg_dark"])
        
        # Header
        self.draw_panel(screen, 2, 2, self.width - 4, 18)
        self.draw_text(screen, "CHIP FOLDER", self.width // 2, 6,
                      size=12, center=True, color=self.colors["accent_cyan"])
        
        chip_folder = self.game_state["chip_folder"]
        owned_chips = chip_folder.get("owned_chips", [])
        folder_chips = chip_folder.get("folder_chips", [])
        max_size = chip_folder.get("max_size", 30)
        
        if not owned_chips:
            self.draw_text(screen, "No chips!", self.width // 2, 60,
                          size=10, center=True, color=self.colors["text_dim"])
            self.draw_text(screen, "[X] Back", self.width // 2, self.height - 8,
                          size=7, center=True, color=self.colors["text_dim"])
            return
        
        # Draw chip list (3 visible at a time)
        y = 24
        item_height = 26
        
        # Calculate which chips to show
        start_idx = self.scroll_offset
        end_idx = min(start_idx + self.max_visible, len(owned_chips))
        visible_chips = owned_chips[start_idx:end_idx]
        
        for i, chip in enumerate(visible_chips):
            actual_idx = start_idx + i
            is_selected = actual_idx == self.selected_index
            
            # Check if THIS specific chip object is in folder
            is_equipped = chip in folder_chips
            
            # Background color
            if is_selected:
                bg = self.colors["accent_cyan"]
            else:
                bg = self.colors["bg_panel"]
            
            self.draw_panel(screen, 4, y, self.width - 8, item_height - 2,
                          color=bg, border_width=1)
            
            # Text color
            tc = self.colors["bg_dark"] if is_selected else self.colors["text_white"]
            
            # Chip name (truncate if needed)
            chip_name = chip.name[:12]
            self.draw_text(screen, chip_name, 8, y + 3, size=9, color=tc)
            
            # Power
            self.draw_text(screen, str(chip.power), self.width - 36, y + 3, 
                          size=9, color=tc)
            
            # Type (below name, smaller)
            self.draw_text(screen, chip.chip_type[:6], 8, y + 15, 
                          size=6, color=tc)
            
            # Equipped marker
            if is_equipped:
                self.draw_text(screen, "E", self.width - 14, y + 8,
                              size=12, color=tc, center=True)
            
            y += item_height
        
        # Scroll indicators
        if self.scroll_offset > 0:
            self.draw_text(screen, "▲", self.width // 2, 22,
                          size=8, center=True, color=self.colors["accent_cyan"])
        if self.scroll_offset + self.max_visible < len(owned_chips):
            self.draw_text(screen, "▼", self.width // 2, y,
                          size=8, center=True, color=self.colors["accent_cyan"])
        
        # Footer - folder count
        footer_y = self.height - 20
        self.draw_text(screen, f"Folder: {len(folder_chips)}/{max_size}",
                      self.width // 2, footer_y,
                      size=9, center=True, color=self.colors["text_white"])
        
        # Controls
        self.draw_text(screen, "[Z]Equip [X]Back",
                      self.width // 2, self.height - 8,
                      size=7, center=True, color=self.colors["text_dim"])
