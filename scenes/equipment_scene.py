"""
Equipment Scene - List-based equipment management.
Shows owned equipment, equip/unequip with CP limit.
Optimized for 128x128 display.
"""

import pygame
from scenes.base_scene import BaseScene
from combat.equipment import EQUIPMENT_DB


class EquipmentScene(BaseScene):
    """Equipment management scene."""
    
    target_fps = 30
    
    def __init__(self, manager):
        super().__init__(manager)
        self.selected_index = 0
        self.scroll_offset = 0
        self.max_visible = 3  # Show 3 items at a time
    
    def handle_event(self, event):
        if event.type != pygame.USEREVENT:
            return
        
        action = event.dict.get("action")
        equipment = self.game_state["equipment"]
        owned_items = equipment.get_all_owned_items()
        
        if not owned_items:
            if action == "cancel":
                self.manager.pop_scene()
            return
        
        if action == "up":
            self.selected_index = max(0, self.selected_index - 1)
            self._update_scroll()
        elif action == "down":
            self.selected_index = min(len(owned_items) - 1, self.selected_index + 1)
            self._update_scroll()
        elif action == "confirm":
            # Toggle equip/unequip
            item_name = owned_items[self.selected_index]
            
            if equipment.is_equipped(item_name):
                equipment.unequip(item_name)
            else:
                if not equipment.can_equip(item_name):
                    # Show "Not enough CP!" feedback
                    pass
                else:
                    equipment.equip(item_name)
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
        self.draw_text(screen, "EQUIPMENT", self.width // 2, 6,
                      size=12, center=True, color=self.colors["accent_cyan"])
        
        equipment = self.game_state["equipment"]
        owned_items = equipment.get_all_owned_items()
        
        if not owned_items:
            self.draw_text(screen, "No equipment!", self.width // 2, 60,
                          size=10, center=True, color=self.colors["text_dim"])
            self.draw_text(screen, "[X] Back", self.width // 2, self.height - 8,
                          size=7, center=True, color=self.colors["text_dim"])
            return
        
        # Draw equipment list
        y = 24
        item_height = 26
        
        visible_items = owned_items[self.scroll_offset:self.scroll_offset + self.max_visible]
        
        for i, item_name in enumerate(visible_items):
            idx = self.scroll_offset + i
            is_selected = idx == self.selected_index
            is_equipped = equipment.is_equipped(item_name)
            
            # Background color
            if is_selected:
                bg = self.colors["accent_cyan"]
            else:
                bg = self.colors["bg_panel"]
            
            self.draw_panel(screen, 4, y, self.width - 8, item_height - 2, 
                          color=bg, border_width=1)
            
            # Text color
            tc = self.colors["bg_dark"] if is_selected else self.colors["text_white"]
            
            # Get equipment data
            item_data = EQUIPMENT_DB.get(item_name, {})
            cost = item_data.get("cost", 0)
            
            # Item name
            name_display = item_name[:12]  # Truncate if too long
            self.draw_text(screen, name_display, 8, y + 3, size=9, color=tc)
            
            # CP cost (small, below name)
            self.draw_text(screen, f"CP:{cost}", 8, y + 15, size=6, color=tc)
            
            # Equipped marker
            if is_equipped:
                self.draw_text(screen, "E", self.width - 14, y + 8, 
                              size=12, color=tc, center=True)
            
            # Quantity (if more than 1)
            qty = equipment.owned.get(item_name, 0)
            if qty > 1:
                self.draw_text(screen, f"x{qty}", self.width - 28, y + 3, 
                              size=7, color=tc)
            
            y += item_height
        
        # Scroll indicators
        if self.scroll_offset > 0:
            self.draw_text(screen, "▲", self.width // 2, 22, 
                          size=8, center=True, color=self.colors["accent_cyan"])
        if self.scroll_offset + self.max_visible < len(owned_items):
            self.draw_text(screen, "▼", self.width // 2, y, 
                          size=8, center=True, color=self.colors["accent_cyan"])
        
        # Footer - CP usage
        footer_y = self.height - 20
        used_cp = equipment.get_used_cp()
        max_cp = equipment.max_cp
        
        self.draw_text(screen, f"CP: {used_cp}/{max_cp}", 
                      self.width // 2, footer_y, 
                      size=10, center=True, color=self.colors["text_white"])
        
        # Controls
        self.draw_text(screen, "[Z]Equip [X]Back", 
                      self.width // 2, self.height - 8,
                      size=7, center=True, color=self.colors["text_dim"])
