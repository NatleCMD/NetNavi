"""
Resource Manager - Centralized asset loading and sprite paths.
Point these paths to your sprite folders/files.
"""

import os
import pygame
from typing import Dict, Optional


class Resources:
    """
    Centralized resource paths and sprite loading.
    
    Configure your sprite locations here:
    """
    
    # ===========================================
    # CONFIGURE YOUR ASSET PATHS HERE
    # ===========================================
    
    # Base asset directory (relative to main.py)
    ASSET_DIR = "assets"
    
    # Sprite directories
    SPRITES = {
        # Character sprites
        "navi_idle": "sprites/navi/idle",           # Navi idle animation frames
        "navi_walk": "sprites/navi/walk",           # Navi walking animation
        "navi_attack": "sprites/navi/attack",       # Navi attack animation
        "navi_hurt": "sprites/navi/hurt",           # Navi hurt/hit animation
        "navi_portrait": "sprites/navi/portrait.png",  # Navi dialog portrait
        
        # Enemy sprites
        "mettaur": "sprites/enemies/mettaur",       # Mettaur animation
        "spikey": "sprites/enemies/spikey",         # Spikey animation
        "bunny": "sprites/enemies/bunny",           # Bunny animation
        "fishy": "sprites/enemies/fishy",           # Fishy animation
        "canodumb": "sprites/enemies/canodumb",     # Canodumb animation
        "boss": "sprites/enemies/boss",             # Generic boss animation
        
        # Effects
        "buster_shot": "sprites/effects/buster.png",
        "sword_slash": "sprites/effects/slash",     # Slash animation frames
        "explosion": "sprites/effects/explosion",   # Explosion animation
        "heal": "sprites/effects/heal",             # Heal effect
        
        # UI elements
        "chip_icons": "sprites/chips",              # Chip icon images
        "panel_blue": "sprites/ui/panel_blue.png",  # Blue battle panel
        "panel_red": "sprites/ui/panel_red.png",    # Red battle panel
        "hp_bar": "sprites/ui/hp_bar.png",
        "custom_gauge": "sprites/ui/gauge.png",
        
        # Map/Area
        "tile_floor": "sprites/tiles/floor.png",
        "tile_wall": "sprites/tiles/wall.png",
        "item_zenny": "sprites/items/zenny.png",
        "item_hp": "sprites/items/hp.png",
        "item_chip": "sprites/items/chip.png",
        
        # Backgrounds
        "bg_hub": "sprites/bg/hub.png",
        "bg_battle": "sprites/bg/battle.png",
        "bg_area": "sprites/bg/area.png",
    }
    
    # Sound directories
    SOUNDS = {
        "buster": "sounds/buster.wav",
        "sword": "sounds/sword.wav",
        "hit": "sounds/hit.wav",
        "heal": "sounds/heal.wav",
        "chip_select": "sounds/chip_select.wav",
        "custom_open": "sounds/custom.wav",
        "victory": "sounds/victory.wav",
        "defeat": "sounds/defeat.wav",
        "menu_move": "sounds/menu.wav",
        "menu_select": "sounds/select.wav",
    }
    
    # Font
    FONTS = {
        "main": "fonts/pixel.ttf",
        "bold": "fonts/pixel_bold.ttf",
    }
    
    # ===========================================
    # RESOURCE LOADING (Don't modify below)
    # ===========================================
    
    _instance = None
    _loaded_images: Dict[str, pygame.Surface] = {}
    _loaded_sounds: Dict[str, pygame.mixer.Sound] = {}
    _loaded_animations: Dict[str, list] = {}
    
    @classmethod
    def get_instance(cls) -> "Resources":
        if cls._instance is None:
            cls._instance = Resources()
        return cls._instance
    
    @classmethod
    def get_path(cls, resource_key: str) -> str:
        """Get full path for a resource key."""
        if resource_key in cls.SPRITES:
            return os.path.join(cls.ASSET_DIR, cls.SPRITES[resource_key])
        elif resource_key in cls.SOUNDS:
            return os.path.join(cls.ASSET_DIR, cls.SOUNDS[resource_key])
        elif resource_key in cls.FONTS:
            return os.path.join(cls.ASSET_DIR, cls.FONTS[resource_key])
        return resource_key
    
    @classmethod
    def load_image(cls, resource_key: str, scale: float = 1.0) -> Optional[pygame.Surface]:
        """
        Load a single image. Returns None if not found (uses placeholder).
        
        Usage:
            sprite = Resources.load_image("navi_portrait")
        """
        cache_key = f"{resource_key}_{scale}"
        if cache_key in cls._loaded_images:
            return cls._loaded_images[cache_key]
        
        path = cls.get_path(resource_key)
        
        try:
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                if scale != 1.0:
                    new_size = (int(img.get_width() * scale), int(img.get_height() * scale))
                    img = pygame.transform.scale(img, new_size)
                cls._loaded_images[cache_key] = img
                return img
        except Exception as e:
            print(f"Could not load image {path}: {e}")
        
        return None
    
    @classmethod
    def load_animation(cls, resource_key: str, frame_count: int = None, 
                       scale: float = 1.0) -> list:
        """
        Load animation frames from a folder.
        Expects files named: 0.png, 1.png, 2.png, etc. OR frame_0.png, frame_1.png, etc.
        
        Usage:
            frames = Resources.load_animation("navi_idle", frame_count=4)
        """
        cache_key = f"{resource_key}_anim_{scale}"
        if cache_key in cls._loaded_animations:
            return cls._loaded_animations[cache_key]
        
        path = cls.get_path(resource_key)
        frames = []
        
        if os.path.isdir(path):
            # Try to load numbered frames
            i = 0
            while True:
                # Try different naming conventions
                for pattern in [f"{i}.png", f"frame_{i}.png", f"frame{i}.png"]:
                    frame_path = os.path.join(path, pattern)
                    if os.path.exists(frame_path):
                        try:
                            img = pygame.image.load(frame_path).convert_alpha()
                            if scale != 1.0:
                                new_size = (int(img.get_width() * scale), int(img.get_height() * scale))
                                img = pygame.transform.scale(img, new_size)
                            frames.append(img)
                            break
                        except Exception as e:
                            print(f"Could not load frame {frame_path}: {e}")
                            break
                else:
                    # No more frames found
                    break
                
                i += 1
                if frame_count and i >= frame_count:
                    break
        
        cls._loaded_animations[cache_key] = frames
        return frames
    
    @classmethod
    def load_sound(cls, resource_key: str) -> Optional[pygame.mixer.Sound]:
        """
        Load a sound effect.
        
        Usage:
            sound = Resources.load_sound("buster")
            if sound:
                sound.play()
        """
        if resource_key in cls._loaded_sounds:
            return cls._loaded_sounds[resource_key]
        
        path = cls.get_path(resource_key)
        
        try:
            if os.path.exists(path):
                sound = pygame.mixer.Sound(path)
                cls._loaded_sounds[resource_key] = sound
                return sound
        except Exception as e:
            print(f"Could not load sound {path}: {e}")
        
        return None
    
    @classmethod
    def get_sprite_or_placeholder(cls, resource_key: str, width: int, height: int,
                                   color: tuple = (100, 100, 100)) -> pygame.Surface:
        """
        Load sprite or return a colored placeholder if not found.
        
        Usage:
            sprite = Resources.get_sprite_or_placeholder("navi_portrait", 32, 32, (0, 100, 220))
        """
        img = cls.load_image(resource_key)
        if img:
            return img
        
        # Create placeholder
        placeholder = pygame.Surface((width, height), pygame.SRCALPHA)
        placeholder.fill(color)
        return placeholder
    
    @classmethod
    def clear_cache(cls):
        """Clear all loaded resources (for memory management)."""
        cls._loaded_images.clear()
        cls._loaded_sounds.clear()
        cls._loaded_animations.clear()


# Convenience function
def get_sprite(key: str, width: int = 32, height: int = 32, 
               color: tuple = (100, 100, 100)) -> pygame.Surface:
    """Quick sprite loading with placeholder fallback."""
    return Resources.get_sprite_or_placeholder(key, width, height, color)


def get_animation(key: str, frame_count: int = None) -> list:
    """Quick animation loading."""
    return Resources.load_animation(key, frame_count)
