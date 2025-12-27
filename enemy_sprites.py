"""
Enemy Sprite Manager - Load and manage enemy animations.
Handles Metaur and other virus sprites with their attacks.
"""

import pygame
import os
from typing import Dict, List, Optional
from pathlib import Path


class EnemySpriteManager:
    """Manages enemy sprite loading and animation playback."""
    
    def __init__(self, enemy_type: str = "metaur", sprite_base_path: str = "assets/sprites/enemies"):
        """
        Initialize sprite manager.
        
        Args:
            enemy_type: Type of enemy (metaur, spikey, bunny, etc.)
            sprite_base_path: Base directory containing enemy sprites
        """
        self.enemy_type = enemy_type
        self.base_path = Path(sprite_base_path) / enemy_type
        
        print(f"[ENEMY SPRITES] Loading {enemy_type} from: {self.base_path.absolute()}")
        
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
        if self.enemy_type == "metaur":
            self._load_metaur()
        else:
            self._load_generic()
    
    def _load_metaur(self):
        """Load Metaur-specific animations."""
        print("[ENEMY SPRITES] Loading Metaur animations...")
        
        # Idle animation (animation_0_frame_0 only)
        idle_frame = self._load_frame("animation_0_frame_0")
        if idle_frame:
            self.animations["idle"] = [idle_frame]
            print(f"  [idle] Loaded 1 frame")
        else:
            print("  [idle] WARNING: Could not load idle frame!")
        
        # Attack animation (animation_1_frame_1 to animation_1_frame_19)
        attack_frames = []
        for i in range(1, 20):  # frames 1-19
            frame = self._load_frame(f"animation_1_frame_{i}")
            if frame:
                attack_frames.append(frame)
        
        if attack_frames:
            self.animations["attack"] = attack_frames
            print(f"  [attack] Loaded {len(attack_frames)} frames")
        else:
            print("  [attack] WARNING: No attack frames loaded!")
        
        # If no animations loaded, create placeholder
        if not self.animations:
            print("  [FALLBACK] Creating placeholder animations")
            placeholder = pygame.Surface((32, 32), pygame.SRCALPHA)
            placeholder.fill((180, 140, 60, 200))
            self.animations["idle"] = [placeholder]
            self.animations["attack"] = [placeholder]
    
    def _load_generic(self):
        """Load generic enemy animations (placeholder)."""
        # For other enemies, create simple placeholder
        placeholder = pygame.Surface((32, 32), pygame.SRCALPHA)
        placeholder.fill((180, 140, 60, 200))
        self.animations["idle"] = [placeholder]
        self.animations["attack"] = [placeholder]
    
    def _load_frame(self, frame_name: str) -> Optional[pygame.Surface]:
        """Load a single frame by name."""
        extensions = [".png", ".webp"]
        
        # For Metaur: sprites are in palette1 subfolder
        # Try palette1 subdirectory FIRST for Metaur
        for ext in extensions:
            path = self.base_path / "palette1" / f"{frame_name}{ext}"
            print(f"    Trying: {path}")
            if path.exists():
                try:
                    img = pygame.image.load(str(path)).convert_alpha()
                    print(f"    ✓ Loaded: palette1/{frame_name}{ext} ({img.get_width()}x{img.get_height()})")
                    return img
                except Exception as e:
                    print(f"    ✗ Failed to load {path}: {e}")
            else:
                print(f"    ✗ Not found: {path}")
        
        # Fallback: Try root directory
        for ext in extensions:
            path = self.base_path / f"{frame_name}{ext}"
            print(f"    Trying: {path}")
            if path.exists():
                try:
                    img = pygame.image.load(str(path)).convert_alpha()
                    print(f"    ✓ Loaded: {path} ({img.get_width()}x{img.get_height()})")
                    return img
                except Exception as e:
                    print(f"    ✗ Failed to load {path}: {e}")
            else:
                print(f"    ✗ Not found: {path}")
        
        return None
    
    def update(self, dt: float):
        """Update animation frame."""
        if self.current_animation not in self.animations:
            return
        
        frames = self.animations[self.current_animation]
        if not frames or len(frames) == 1:
            return
        
        self.frame_timer += dt
        
        # Advance frame
        if self.frame_timer >= self.frame_duration:
            self.frame_timer = 0.0
            self.frame_index = (self.frame_index + 1) % len(frames)
    
    def set_animation(self, animation_name: str):
        """Switch to a different animation."""
        if animation_name in self.animations:
            self.current_animation = animation_name
            self.frame_index = 0
            self.frame_timer = 0.0
    
    def play_idle(self):
        """Return to idle animation."""
        self.set_animation("idle")
    
    def play_attack(self):
        """Trigger attack animation."""
        self.set_animation("attack")
    
    def get_current_frame(self) -> Optional[pygame.Surface]:
        """Get the current frame surface for rendering."""
        if self.current_animation not in self.animations:
            return None
        
        frames = self.animations[self.current_animation]
        if not frames:
            return None
        
        return frames[self.frame_index]
    
    def draw(self, screen: pygame.Surface, x: int, y: int, 
             scale: float = 1.0, center: bool = True):
        """
        Draw current animation frame.
        
        Args:
            screen: Pygame surface to draw on
            x, y: Position
            scale: Scale multiplier
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


class WaveAttack:
    """Wave attack projectile for Metaur."""
    
    def __init__(self, x: float, y: float, dx: int, damage: int, 
                 sprite_path: str = "assets/sprites/enemies/metaur/attack"):
        """
        Initialize wave attack.
        
        Args:
            x, y: Starting position
            dx: Direction (-1 for left, 1 for right)
            damage: Damage value
            sprite_path: Path to wave animation frames
        """
        self.x = x
        self.y = y
        self.dx = dx
        self.damage = damage
        self.alive = True
        self.from_enemy = True
        self.speed = 8.0  # Fast speed to match original projectile
        self.hit_radius = 0.6
        
        # Load wave animation frames (animation_0_frame_0 to animation_0_frame_5)
        self.frames: List[pygame.Surface] = []
        self.frame_index = 0
        self.frame_timer = 0.0
        self.frame_duration = 0.06  # Slowed down 2x (was 0.03)
        
        self._load_frames(sprite_path)
    
    def _load_frames(self, sprite_path: str):
        """Load wave animation frames."""
        base_path = Path(sprite_path)
        
        for i in range(6):  # frames 0-5
            loaded = False
            
            # Attack folder has frames in ROOT (not palette1)
            # Try root attack directory
            for ext in [".png", ".webp"]:
                path = base_path / f"animation_0_frame_{i}{ext}"
                if path.exists():
                    try:
                        img = pygame.image.load(str(path)).convert_alpha()
                        self.frames.append(img)
                        loaded = True
                        print(f"    ✓ Loaded wave frame {i}: {path}")
                        break
                    except Exception as e:
                        print(f"Failed to load wave frame {i}: {e}")
            
            if not loaded:
                # Create placeholder
                placeholder = pygame.Surface((16, 16), pygame.SRCALPHA)
                placeholder.fill((100, 200, 255, 200))
                self.frames.append(placeholder)
                print(f"    ✗ Wave frame {i} not found at {base_path}, using placeholder")
    
    def update(self, dt: float):
        """Update wave position and animation."""
        # Move
        self.x += self.dx * self.speed * dt
        
        # Animate
        self.frame_timer += dt
        if self.frame_timer >= self.frame_duration:
            self.frame_timer = 0.0
            self.frame_index = (self.frame_index + 1) % len(self.frames)
    
    def draw(self, screen: pygame.Surface, grid_x: int, grid_y: int, 
             cell_width: int, cell_height: int, shake_x: int = 0):
        """Draw the wave attack."""
        if not self.frames:
            return
        
        sx = grid_x + int(self.x * cell_width) + shake_x
        sy = grid_y + int(self.y * cell_height) + cell_height // 2
        
        frame = self.frames[self.frame_index]
        
        # Scale to fit grid (smaller than cell)
        scale = 0.6
        scaled = pygame.transform.scale(
            frame, 
            (int(frame.get_width() * scale), int(frame.get_height() * scale))
        )
        
        # ALWAYS flip horizontally so wave faces left (toward Navi)
        scaled = pygame.transform.flip(scaled, True, False)
        
        rect = scaled.get_rect(center=(sx, sy))
        screen.blit(scaled, rect)


# Global cache for enemy sprite managers
_enemy_managers: Dict[str, EnemySpriteManager] = {}

def get_enemy_sprites(enemy_type: str) -> EnemySpriteManager:
    """Get or create enemy sprite manager for the given type."""
    if enemy_type not in _enemy_managers:
        _enemy_managers[enemy_type] = EnemySpriteManager(enemy_type)
    return _enemy_managers[enemy_type]
