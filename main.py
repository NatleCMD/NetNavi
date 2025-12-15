#!/usr/bin/env python3
"""
NetNavi PET - WiFi Dungeon Crawler
A handheld PET game where nearby WiFi networks become explorable cyber dungeons.

Main entry point - handles game loop, scene management, and frame limiting.
"""

import pygame
import sys
from typing import Optional, Dict, Any

# Import scenes
from scenes.hub_scene import HubScene
from scenes.scan_scene import ScanScene
from scenes.area_scene import AreaScene
from scenes.battle_scene import BattleScene
from scenes.folder_scene import FolderScene
from scenes.settings_scene import SettingsScene
from scenes.jack_in_scene import JackInScene
from scenes.navi_cust_scene import NaviCustScene

# Import core systems
from storage.save_manager import SaveManager
from combat.chips import ChipFolder


# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG = {
    # Display settings for Waveshare 1.96" HAT (320x240 or adjust as needed)
    # Common sizes: 320x240, 280x240, 240x240
    "screen_width": 320,
    "screen_height": 240,
    "fullscreen": False,  # Set True for Pi deployment with Waveshare HAT
    
    # FPS caps by scene type
    "fps_hub": 30,
    "fps_explore": 20,
    "fps_battle": 24,
    "fps_menu": 30,
    
    # Colors (placeholder - will be replaced with sprites)
    "colors": {
        "bg_dark": (15, 15, 25),
        "bg_panel": (25, 30, 45),
        "accent_cyan": (0, 255, 200),
        "accent_pink": (255, 100, 150),
        "accent_yellow": (255, 220, 100),
        "text_white": (240, 240, 240),
        "text_dim": (150, 150, 160),
        "hp_green": (100, 255, 120),
        "hp_yellow": (255, 220, 80),
        "hp_red": (255, 80, 80),
        "energy_blue": (80, 180, 255),
    },
    
    # Game balance
    "starting_hp": 100,
    "starting_energy": 50,
    "energy_per_node": 2,
    "chip_folder_size": 10,
}


# =============================================================================
# SCENE MANAGER
# =============================================================================

class SceneManager:
    """Manages scene transitions and maintains game state across scenes."""
    
    def __init__(self, screen: pygame.Surface, config: Dict[str, Any]):
        self.screen = screen
        self.config = config
        self.current_scene = None
        self.scene_stack = []  # For scenes that return to previous
        
        # Shared game state
        self.game_state = {
            "navi": {
                "name": "MegaMan",
                "hp": config["starting_hp"],
                "max_hp": config["starting_hp"],
                "energy": config["starting_energy"],
                "max_energy": config["starting_energy"],
                "level": 1,
                "exp": 0,
                "exp_to_next": 100,
                "attack": 10,
                "defense": 5,
                # Buster stats (from NaviCust)
                "buster_attack": 1,  # Base 1 damage
                "buster_speed": 0,
                "buster_charge": 0,
                # Abilities
                "undershirt": False,
                "sneak_run": False,
            },
            "zenny": 0,  # Start with 0 zenny
            "day": 1,
            "current_area": None,
            "chip_folder": ChipFolder.get_starter_folder(),  # Just 3 cannons
            "settings": {
                "show_ssid_names": True,
                "sound_enabled": True,
                "vibration": False,
            },
            "daily_quests": [],
            "explored_areas": [],
            "completed_areas": {},  # For 24hr cooldowns
            "deleted_time": 0,
            "last_hp_regen_time": 0,
        }
        
        # Save manager
        self.save_manager = SaveManager()
        
        # Scene registry
        self.scenes = {
            "hub": HubScene,
            "scan": ScanScene,
            "area": AreaScene,
            "battle": BattleScene,
            "folder": FolderScene,
            "settings": SettingsScene,
            "jack_in": JackInScene,
            "navicust": NaviCustScene,
        }
    
    def change_scene(self, scene_name: str, **kwargs):
        """Switch to a new scene."""
        if scene_name not in self.scenes:
            print(f"Warning: Unknown scene '{scene_name}'")
            return
        
        # Clean up current scene
        if self.current_scene:
            self.current_scene.on_exit()
        
        # Create new scene
        scene_class = self.scenes[scene_name]
        self.current_scene = scene_class(self, **kwargs)
        self.current_scene.on_enter()
    
    def push_scene(self, scene_name: str, **kwargs):
        """Push current scene to stack and switch to new one."""
        if self.current_scene:
            self.scene_stack.append(self.current_scene)
        self.change_scene(scene_name, **kwargs)
    
    def pop_scene(self):
        """Return to previous scene on stack."""
        if self.scene_stack:
            if self.current_scene:
                self.current_scene.on_exit()
            self.current_scene = self.scene_stack.pop()
            self.current_scene.on_enter()
        else:
            self.change_scene("hub")
    
    def get_fps_for_current_scene(self) -> int:
        """Return appropriate FPS cap for current scene."""
        if self.current_scene is None:
            return self.config["fps_menu"]
        return self.current_scene.target_fps
    
    def update(self, dt: float):
        """Update current scene."""
        if self.current_scene:
            self.current_scene.update(dt)
    
    def draw(self):
        """Draw current scene."""
        if self.current_scene:
            self.current_scene.draw(self.screen)
    
    def handle_event(self, event: pygame.event.Event):
        """Pass events to current scene."""
        if self.current_scene:
            self.current_scene.handle_event(event)


# =============================================================================
# MAIN GAME CLASS
# =============================================================================

class NetNaviPET:
    """Main game class - handles initialization and game loop."""
    
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        
        # Set up display
        flags = pygame.FULLSCREEN if CONFIG["fullscreen"] else 0
        self.screen = pygame.display.set_mode(
            (CONFIG["screen_width"], CONFIG["screen_height"]), 
            flags
        )
        pygame.display.set_caption("NetNavi PET")
        
        # Hide mouse cursor for handheld feel
        if CONFIG["fullscreen"]:
            pygame.mouse.set_visible(False)
        
        # Clock for frame limiting
        self.clock = pygame.time.Clock()
        
        # Scene manager
        self.scene_manager = SceneManager(self.screen, CONFIG)
        
        # Input mapping (for easy remapping on Pi)
        self.input_map = {
            pygame.K_UP: "up",
            pygame.K_DOWN: "down",
            pygame.K_LEFT: "left",
            pygame.K_RIGHT: "right",
            pygame.K_z: "confirm",      # A button
            pygame.K_x: "cancel",       # B button
            pygame.K_a: "chip_left",    # L shoulder
            pygame.K_s: "chip_right",   # R shoulder
            pygame.K_RETURN: "start",
            pygame.K_ESCAPE: "quit",
        }
        
        self.running = True
    
    def run(self):
        """Main game loop."""
        # Start at hub
        self.scene_manager.change_scene("hub")
        
        while self.running:
            # Get delta time
            dt = self.clock.tick(self.scene_manager.get_fps_for_current_scene()) / 1000.0
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    else:
                        # Map input and pass to scene
                        mapped = self.input_map.get(event.key)
                        if mapped:
                            mapped_event = pygame.event.Event(
                                pygame.USEREVENT, 
                                {"action": mapped}
                            )
                            self.scene_manager.handle_event(mapped_event)
                        else:
                            self.scene_manager.handle_event(event)
                else:
                    self.scene_manager.handle_event(event)
            
            # Update
            self.scene_manager.update(dt)
            
            # Draw
            self.screen.fill(CONFIG["colors"]["bg_dark"])
            self.scene_manager.draw()
            
            # Flip display
            pygame.display.flip()
        
        # Cleanup
        pygame.quit()
        sys.exit()


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    game = NetNaviPET()
    game.run()
