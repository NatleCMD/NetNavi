"""
Navi Customizer Scene - Grid-based program placement for stat boosts.
"""

import pygame
from scenes.base_scene import BaseScene
from combat.navi_cust import NaviCustomizer, NCP_DATABASE


class NaviCustScene(BaseScene):
    """Navi Customizer - place programs on grid for stat boosts."""
    
    target_fps = 30
    
    def __init__(self, manager):
        super().__init__(manager)
        
        # Get or create NaviCust
        if "navi_cust" not in self.game_state:
            self.game_state["navi_cust"] = NaviCustomizer()
        self.navi_cust = self.game_state["navi_cust"]
        
        # UI state
        self.mode = "grid"  # grid, programs, dialog
        self.cursor_x = 0
        self.cursor_y = 0
        self.selected_program = None
        self.program_list_index = 0
        self.placing = False
        self.rotation = 0
        
        # Dialog state
        self.dialog_text = ""
        self.dialog_ok = True
        self.dialog_timer = 0
        
        # Grid display settings
        self.grid_cell = 20
        self.grid_offset_x = 20
        self.grid_offset_y = 50
        
        # Program colors
        self.prog_colors = {
            "pink": (255, 150, 200),
            "yellow": (255, 255, 100),
            "white": (240, 240, 240),
            "blue": (100, 150, 255),
            "red": (255, 100, 100),
            "green": (100, 255, 100),
        }
    
    def handle_event(self, event):
        if event.type != pygame.USEREVENT:
            return
        action = event.dict.get("action")
        
        if self.mode == "grid":
            self._handle_grid_input(action)
        elif self.mode == "programs":
            self._handle_programs_input(action)
        elif self.mode == "dialog":
            if action in ["confirm", "cancel"]:
                self.mode = "grid"
    
    def _handle_grid_input(self, action):
        gs = self.navi_cust.grid_size
        
        if action == "up":
            self.cursor_y = max(0, self.cursor_y - 1)
        elif action == "down":
            self.cursor_y = min(gs - 1, self.cursor_y + 1)
        elif action == "left":
            self.cursor_x = max(0, self.cursor_x - 1)
        elif action == "right":
            self.cursor_x = min(gs - 1, self.cursor_x + 1)
        elif action == "confirm":
            if self.placing and self.selected_program:
                success, msg = self.navi_cust.install(
                    self.selected_program, self.cursor_x, self.cursor_y, self.rotation
                )
                if success:
                    self.placing = False
                    self.selected_program = None
            else:
                prog_at = self.navi_cust.grid[self.cursor_y][self.cursor_x]
                if prog_at:
                    self.navi_cust.uninstall(prog_at)
                else:
                    self.mode = "programs"
                    self.program_list_index = 0
        elif action == "cancel":
            if self.placing:
                self.placing = False
                self.selected_program = None
            else:
                self.manager.pop_scene()
        elif action == "chip_left" or action == "chip_right":
            if self.placing:
                self.rotation = (self.rotation + (1 if action == "chip_right" else -1)) % 4
        elif action == "start":
            # RUN the NaviCust
            self._run_navicust()
    
    def _run_navicust(self):
        """Run the NaviCust and show dialog."""
        success, message = self.navi_cust.run_programs()
        self.dialog_ok = success
        self.dialog_text = message
        self.mode = "dialog"
        
        # Apply stats to Navi
        self._apply_stats_to_navi()
    
    def _apply_stats_to_navi(self):
        """Apply computed NaviCust stats to the Navi."""
        navi = self.game_state["navi"]
        stats = self.navi_cust.computed_stats
        
        # Base stats + NaviCust bonuses
        base_max_hp = 100  # Base HP
        navi["max_hp"] = base_max_hp + stats["max_hp"]
        navi["hp"] = min(navi["hp"], navi["max_hp"])
        
        # Buster stats (used in battle)
        navi["buster_attack"] = 1 + stats["buster_attack"]  # Base 1 + bonuses
        navi["buster_speed"] = stats["buster_speed"]
        navi["buster_charge"] = stats["buster_charge"]
        
        # Other abilities
        navi["undershirt"] = stats["undershirt"]
        navi["sneak_run"] = stats["sneak_run"]
    
    def _handle_programs_input(self, action):
        available = self.navi_cust.get_available_to_install()
        
        if action == "up":
            self.program_list_index = max(0, self.program_list_index - 1)
        elif action == "down":
            self.program_list_index = min(len(available) - 1, self.program_list_index + 1)
        elif action == "confirm":
            if available:
                prog_name, remaining = available[self.program_list_index]
                self.selected_program = prog_name
                self.placing = True
                self.rotation = 0
                self.mode = "grid"
        elif action == "cancel":
            self.mode = "grid"
    
    def draw(self, screen):
        screen.fill((80, 30, 40))
        
        self.draw_text(screen, "NAVI CUSTOMIZER", self.width // 2, 8,
                      size=14, center=True, color=self.colors["text_white"])
        
        self._draw_grid(screen)
        self._draw_stats(screen)
        
        if self.mode == "programs":
            self._draw_program_list(screen)
        elif self.mode == "dialog":
            self._draw_dialog(screen)
        
        self._draw_controls(screen)
        
        bugs = self.navi_cust.check_bugs()
        if bugs:
            self.draw_text(screen, "! BUGS DETECTED !", self.width // 2, self.height - 25,
                          size=10, center=True, color=self.colors["hp_red"])
    
    def _draw_grid(self, screen):
        gs = self.navi_cust.grid_size
        ox, oy = self.grid_offset_x, self.grid_offset_y
        cs = self.grid_cell
        
        cmd_y = oy + self.navi_cust.command_line * cs
        pygame.draw.rect(screen, (60, 40, 50), (ox - 2, cmd_y, gs * cs + 4, cs))
        self.draw_text(screen, "CMD", ox - 18, cmd_y + 5, size=8, color=self.colors["text_dim"])
        
        for y in range(gs):
            for x in range(gs):
                cell_x = ox + x * cs
                cell_y = oy + y * cs
                
                prog = self.navi_cust.grid[y][x]
                if prog:
                    prog_data = NCP_DATABASE.get(prog)
                    color = self.prog_colors.get(prog_data.color if prog_data else "white", (150, 150, 150))
                    pygame.draw.rect(screen, color, (cell_x + 1, cell_y + 1, cs - 2, cs - 2))
                    # Draw texture pattern for Plus parts
                    if prog_data and not prog_data.is_solid:
                        pygame.draw.line(screen, (200, 200, 200), (cell_x + 4, cell_y + cs//2), (cell_x + cs - 4, cell_y + cs//2), 1)
                        pygame.draw.line(screen, (200, 200, 200), (cell_x + cs//2, cell_y + 4), (cell_x + cs//2, cell_y + cs - 4), 1)
                else:
                    pygame.draw.rect(screen, (40, 30, 35), (cell_x + 1, cell_y + 1, cs - 2, cs - 2))
                
                pygame.draw.rect(screen, (100, 80, 90), (cell_x, cell_y, cs, cs), 1)
        
        if self.placing and self.selected_program:
            prog = NCP_DATABASE.get(self.selected_program)
            if prog:
                can_place, _ = self.navi_cust.can_install(
                    self.selected_program, self.cursor_x, self.cursor_y, self.rotation
                )
                color = (100, 200, 100) if can_place else (200, 100, 100)
                shape = self.navi_cust._rotate_shape(prog.shape, self.rotation)
                for dx, dy in shape:
                    px = ox + (self.cursor_x + dx) * cs
                    py = oy + (self.cursor_y + dy) * cs
                    if 0 <= self.cursor_x + dx < gs and 0 <= self.cursor_y + dy < gs:
                        pygame.draw.rect(screen, color, (px + 2, py + 2, cs - 4, cs - 4), 2)
        
        cx = ox + self.cursor_x * cs
        cy = oy + self.cursor_y * cs
        pygame.draw.rect(screen, self.colors["accent_cyan"], (cx, cy, cs, cs), 2)
    
    def _draw_stats(self, screen):
        stats = self.navi_cust.computed_stats
        panel_x = self.width - 110
        panel_y = 30
        
        self.draw_panel(screen, panel_x, panel_y, 105, 100, 
                       color=(60, 40, 50), border_color=(150, 100, 120))
        
        self.draw_text(screen, "MEGA BUSTER", panel_x + 52, panel_y + 5,
                      size=9, center=True, color=self.colors["text_white"])
        
        y = panel_y + 18
        self.draw_text(screen, f"Attack  Lv {stats['buster_attack']}", panel_x + 5, y, size=10)
        y += 14
        self.draw_text(screen, f"Speed   Lv {stats['buster_speed']}", panel_x + 5, y, size=10)
        y += 14
        self.draw_text(screen, f"Charge  Lv {stats['buster_charge']}", panel_x + 5, y, size=10)
        y += 18
        self.draw_text(screen, f"HP Bonus: +{stats['max_hp']}", panel_x + 5, y, size=9,
                      color=self.colors["hp_green"])
        
        y += 16
        abilities = []
        if stats["undershirt"]:
            abilities.append("UndrSht")
        if stats["sneak_run"]:
            abilities.append("Sneak")
        if stats["float_shoes"]:
            abilities.append("Float")
        
        if abilities:
            self.draw_text(screen, ", ".join(abilities), panel_x + 5, y, size=8,
                          color=self.colors["accent_cyan"])
    
    def _draw_program_list(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        panel_w, panel_h = 180, 160
        px = (self.width - panel_w) // 2
        py = (self.height - panel_h) // 2
        
        self.draw_panel(screen, px, py, panel_w, panel_h,
                       color=(50, 35, 45), border_color=self.colors["accent_cyan"])
        
        self.draw_text(screen, "SELECT PROGRAM", px + panel_w // 2, py + 8,
                      size=12, center=True, color=self.colors["accent_cyan"])
        
        available = self.navi_cust.get_available_to_install()
        max_visible = 5
        scroll = max(0, self.program_list_index - max_visible + 1)
        
        y = py + 28
        for i, (prog_name, remaining) in enumerate(available[scroll:scroll + max_visible]):
            idx = scroll + i
            selected = idx == self.program_list_index
            
            prog = NCP_DATABASE.get(prog_name)
            color = self.prog_colors.get(prog.color if prog else "white", (200, 200, 200))
            
            if selected:
                pygame.draw.rect(screen, (80, 60, 70), (px + 5, y - 2, panel_w - 10, 20))
            
            pygame.draw.rect(screen, color, (px + 10, y, 12, 12))
            
            self.draw_text(screen, f"{prog_name} x{remaining}", px + 28, y, size=11,
                          color=self.colors["text_white"] if selected else self.colors["text_dim"])
            
            y += 22
        
        if not available:
            self.draw_text(screen, "No programs available", px + panel_w // 2, py + 60,
                          size=10, center=True, color=self.colors["text_dim"])
        
        if available and self.program_list_index < len(available):
            prog_name, _ = available[self.program_list_index]
            prog = NCP_DATABASE.get(prog_name)
            if prog:
                self.draw_text(screen, prog.description, px + panel_w // 2, py + panel_h - 20,
                              size=9, center=True, color=self.colors["text_dim"])
    
    def _draw_dialog(self, screen):
        """Draw MegaMan dialog box after RUN."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        # Dialog box
        panel_w, panel_h = 200, 100
        px = (self.width - panel_w) // 2
        py = (self.height - panel_h) // 2
        
        border_color = self.colors["hp_green"] if self.dialog_ok else self.colors["accent_yellow"]
        self.draw_panel(screen, px, py, panel_w, panel_h,
                       color=(50, 40, 50), border_color=border_color, border_width=2)
        
        # MegaMan portrait placeholder (blue circle)
        portrait_x = px + 25
        portrait_y = py + panel_h // 2
        pygame.draw.circle(screen, (0, 100, 220), (portrait_x, portrait_y), 20)
        pygame.draw.circle(screen, (0, 220, 200), (portrait_x, portrait_y), 20, 2)
        pygame.draw.ellipse(screen, (0, 220, 200), (portrait_x - 8, portrait_y - 3, 16, 6))
        
        # Status text
        status = "OK!" if self.dialog_ok else "BUG"
        status_color = self.colors["hp_green"] if self.dialog_ok else self.colors["hp_red"]
        self.draw_text(screen, status, px + panel_w - 30, py + 10, size=12, color=status_color)
        
        # Dialog text
        lines = self.dialog_text.split("\n")
        y = py + 20
        for line in lines:
            self.draw_text(screen, line, px + 55, y, size=11, color=self.colors["text_white"])
            y += 16
        
        self.draw_text(screen, "[Z] OK", px + panel_w // 2, py + panel_h - 15,
                      size=10, center=True, color=self.colors["text_dim"])
    
    def _draw_controls(self, screen):
        if self.mode == "grid":
            if self.placing:
                text = "[Z]Place [X]Cancel [A/S]Rotate"
            else:
                text = "[Z]Select [X]Back [START]RUN!"
        elif self.mode == "programs":
            text = "[Z]Select [X]Back"
        else:
            text = "[Z]OK"
        
        self.draw_text(screen, text, self.width // 2, self.height - 10,
                      size=9, center=True, color=self.colors["text_dim"])
