"""
Navi Sprite Manager - Load and manage Navi battle animations.
Complete animation system with idle, hurt, movement, attacks, sword, and throwing.
"""

import pygame
import os
from typing import Dict, List, Optional
from pathlib import Path


class NaviSpriteManager:
    """Manages Navi sprite loading and animation playback."""
    
    def __init__(self, sprite_base_path: str = "assets/sprites/navi"):
        """
        Initialize sprite manager.
        
        Args:
            sprite_base_path: Base directory containing navi sprites
        """
        self.base_path = Path(sprite_base_path)
        
        print(f"[NAVI SPRITES] Loading from: {self.base_path.absolute()}")
        
        # Animation states
        self.animations: Dict[str, List[pygame.Surface]] = {}
        self.current_animation = "idle"
        self.frame_index = 0
        self.frame_timer = 0.0
        self.frame_duration = 0.1  # seconds per frame
        
        # Load animations
        self._load_animations()
    
    def _load_animations(self):
        """Load all animation frames from directories."""
        # Define animation sources (name -> animation_id, frame_count)
        animation_sources = {
            "idle": (0, 1),           # Static pose
            "hurt": (1, 7),           # Hurt/flinch reaction
            "move": (3, 4),           # Movement/walking
            "sword": (5, 4),          # Sword attack
            "throw": (6, 4),          # Throwing/lob animation
            "buster": (8, 8),         # Buster/projectile attack
        }
        
        for anim_name, (anim_num, frame_count) in animation_sources.items():
            frames = []
            print(f"\n[NAVI SPRITES] Loading {anim_name}...")
            
            for frame_num in range(frame_count):
                # Generate filename variants to try
                possible_names = [
                    f"animation_{anim_num}_frame_{frame_num}.png",
                    f"animation_{anim_num}_frame_{frame_num}.webp",
                ]
                
                loaded = False
                
                # Try root directory first
                for filename in possible_names:
                    path = self.base_path / filename
                    
                    if path.exists():
                        try:
                            img = pygame.image.load(str(path)).convert_alpha()
                            frames.append(img)
                            loaded = True
                            print(f"  ✓ Frame {frame_num}: {filename} ({img.get_width()}x{img.get_height()})")
                            break
                        except Exception as e:
                            print(f"  ✗ Failed to load {filename}: {e}")
                            continue
                
                # Try palette1 subdirectory
                if not loaded:
                    for filename in possible_names:
                        path = self.base_path / "palette1" / filename
                        
                        if path.exists():
                            try:
                                img = pygame.image.load(str(path)).convert_alpha()
                                frames.append(img)
                                loaded = True
                                print(f"  ✓ Frame {frame_num}: palette1/{filename} ({img.get_width()}x{img.get_height()})")
                                break
                            except Exception as e:
                                print(f"  ✗ Failed to load palette1/{filename}: {e}")
                                continue
                
                if not loaded:
                    # Create placeholder if file not found
                    placeholder = pygame.Surface((84, 84), pygame.SRCALPHA)
                    placeholder.fill((255, 0, 255, 128))  # Magenta = missing
                    frames.append(placeholder)
                    print(f"  ✗ MISSING: Frame {frame_num} (no file found)")
            
            if frames:
                self.animations[anim_name] = frames
                print(f"  [{anim_name}] Loaded {len(frames)} frames")
    
    def update(self, dt: float):
        """Update animation frame. Call this every game frame."""
        if self.current_animation not in self.animations:
            return
        
        frames = self.animations[self.current_animation]
        if not frames:
            return
        
        self.frame_timer += dt
        
        # Advance frame when timer exceeds duration
        if self.frame_timer >= self.frame_duration:
            self.frame_timer = 0.0
            self.frame_index += 1
            
            # Loop animation
            if self.frame_index >= len(frames):
                self.frame_index = 0
    
    def set_animation(self, animation_name: str, loop: bool = True):
        """
        Switch to a different animation.
        
        Args:
            animation_name: Name of animation (e.g., "idle", "hurt", "buster")
            loop: Whether animation should loop
        """
        if animation_name in self.animations:
            if self.current_animation != animation_name:
                print(f"[NAVI SPRITES] Switching to: {animation_name}")
            self.current_animation = animation_name
            self.frame_index = 0
            self.frame_timer = 0.0
    
    # Animation shortcuts
    def play_idle(self):
        """Return to idle animation."""
        self.set_animation("idle")
    
    def play_hurt(self):
        """Trigger hurt/flinch animation."""
        self.set_animation("hurt")
    
    def play_move(self):
        """Trigger movement animation."""
        self.set_animation("move")
    
    def play_sword(self):
        """Trigger sword attack animation."""
        self.set_animation("sword")
    
    def play_throw(self):
        """Trigger throwing/lob animation."""
        self.set_animation("throw")
    
    def play_buster(self):
        """Trigger buster/projectile attack animation."""
        self.set_animation("buster")
    
    def get_current_frame(self) -> Optional[pygame.Surface]:
        """Get the current frame surface for rendering."""
        if self.current_animation not in self.animations:
            return None
        
        frames = self.animations[self.current_animation]
        if not frames or self.frame_index >= len(frames):
            return None
        
        return frames[self.frame_index]
    
    def draw(self, screen: pygame.Surface, x: int, y: int, 
             scale: float = 1.0, center: bool = True):
        """
        Draw current animation frame.
        
        Args:
            screen: Pygame surface to draw on
            x, y: Position
            scale: Scale multiplier (e.g., 2.0 for 2x size)
            center: If True, position is center; if False, top-left
        """
        frame = self.get_current_frame()
        if frame is None:
            return
        
        # Scale if needed
        if scale != 1.0:
            new_size = (int(frame.get_width() * scale), int(frame.get_height() * scale))
            frame = pygame.transform.scale(frame, new_size)
        
        # Position
        if center:
            rect = frame.get_rect(center=(x, y))
        else:
            rect = frame.get_rect(topleft=(x, y))
        
        screen.blit(frame, rect)


# Convenience function for lazy loading
_navi_sprite_manager: Optional[NaviSpriteManager] = None

def get_navi_sprites(sprite_path: str = "assets/sprites/navi") -> NaviSpriteManager:
    """Get or create the global Navi sprite manager."""
    global _navi_sprite_manager
    if _navi_sprite_manager is None:
        _navi_sprite_manager = NaviSpriteManager(sprite_path)
    return _navi_sprite_manager
