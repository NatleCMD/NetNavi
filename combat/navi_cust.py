"""
Navi Customizer - Grid-based program system for stat boosts and abilities.
Based on MMBN3+ NaviCust system.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
import json


@dataclass
class NCProgram:
    """A Navi Customizer Program."""
    name: str
    color: str  # pink, yellow, white, blue, red, green
    shape: List[Tuple[int, int]]  # List of (x, y) offsets from origin
    is_solid: bool  # Solid must touch command line, Plus must NOT touch
    effect: str  # Effect type
    value: int  # Effect value
    description: str
    
    def get_bounds(self) -> Tuple[int, int]:
        """Get width and height of shape."""
        if not self.shape:
            return (1, 1)
        max_x = max(s[0] for s in self.shape) + 1
        max_y = max(s[1] for s in self.shape) + 1
        return (max_x, max_y)


# Program database
NCP_DATABASE = {
    # Buster stat programs (solid - must touch command line)
    "Attack+1": NCProgram(
        "Attack+1", "pink", [(0, 0), (1, 0)], True,
        "buster_attack", 1, "Buster Attack +1"
    ),
    "Speed+1": NCProgram(
        "Speed+1", "yellow", [(0, 0), (0, 1)], True,
        "buster_speed", 1, "Buster Speed +1"
    ),
    "Charge+1": NCProgram(
        "Charge+1", "white", [(0, 0), (1, 0), (0, 1)], True,
        "buster_charge", 1, "Charge Time -1"
    ),
    
    # HP programs
    "HP+50": NCProgram(
        "HP+50", "pink", [(0, 0), (1, 0), (2, 0)], True,
        "max_hp", 50, "Max HP +50"
    ),
    "HP+100": NCProgram(
        "HP+100", "white", [(0, 0), (1, 0), (0, 1), (1, 1)], True,
        "max_hp", 100, "Max HP +100"
    ),
    
    # Custom gauge programs
    "Custom+1": NCProgram(
        "Custom+1", "yellow", [(0, 0), (1, 0), (1, 1)], True,
        "custom_size", 1, "Draw +1 chip in Custom"
    ),
    "FstGauge": NCProgram(
        "FstGauge", "pink", [(0, 0), (1, 0), (2, 0), (1, 1)], True,
        "gauge_speed", 2, "Custom gauge fills 2x faster"
    ),
    
    # Utility programs (plus parts - must NOT touch command line)
    "UnderSht": NCProgram(
        "UnderSht", "white", [(0, 0)], False,
        "undershirt", 1, "Survive fatal hit with 1 HP"
    ),
    "SneakRun": NCProgram(
        "SneakRun", "pink", [(0, 0), (1, 0)], False,
        "sneak_run", 1, "Reduce encounter rate"
    ),
    "Collect": NCProgram(
        "Collect", "yellow", [(0, 0), (0, 1)], False,
        "collect", 1, "Better item drops"
    ),
    "FloatShoe": NCProgram(
        "FloatShoe", "white", [(0, 0), (1, 0), (0, 1)], False,
        "float_shoes", 1, "Ignore panel effects"
    ),
    
    # Defense programs
    "Barrier": NCProgram(
        "Barrier", "blue", [(0, 0), (1, 0)], True,
        "start_barrier", 10, "Start battle with 10HP barrier"
    ),
    "SuperArmr": NCProgram(
        "SuperArmr", "white", [(0, 0), (1, 0), (2, 0), (1, 1)], True,
        "super_armor", 1, "No flinching from hits"
    ),
}


class NaviCustomizer:
    """The Navi Customizer grid system."""
    
    def __init__(self, grid_size: int = 4):
        self.grid_size = grid_size  # 4x4 default, can expand to 5x5
        self.grid = [[None for _ in range(grid_size)] for _ in range(grid_size)]
        self.command_line = grid_size // 2  # Middle row is command line
        
        # Installed programs with their positions
        self.installed = []  # List of (program_name, x, y, rotation)
        
        # Owned programs with quantities: {"Attack+1": 2, "Speed+1": 1}
        self.owned_programs = {"Attack+1": 1, "Speed+1": 1}  # Start with 1 of each
        
        # Computed stats from installed programs - initialize with defaults
        self.computed_stats = self._default_stats()
        
        # Last run status
        self.last_run_ok = True
        self.last_run_bugs = []
    
    def _default_stats(self) -> dict:
        """Return default stats dictionary."""
        return {
            "buster_attack": 0,
            "buster_speed": 0,
            "buster_charge": 0,
            "max_hp": 0,
            "custom_size": 0,
            "gauge_speed": 1.0,
            "undershirt": False,
            "sneak_run": False,
            "collect": False,
            "float_shoes": False,
            "start_barrier": 0,
            "super_armor": False,
        }
        
    def expand_grid(self):
        """Expand grid from 4x4 to 5x5."""
        if self.grid_size >= 5:
            return False
        
        self.grid_size = 5
        self.grid = [[None for _ in range(5)] for _ in range(5)]
        self.command_line = 2  # Still middle row
        
        # Re-install programs
        self._rebuild_grid()
        return True
    
    def _rebuild_grid(self):
        """Rebuild grid from installed programs list."""
        self.grid = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        for prog_name, x, y, rotation in self.installed:
            if prog_name in NCP_DATABASE:
                self._place_on_grid(prog_name, x, y, rotation)
    
    def _place_on_grid(self, prog_name: str, x: int, y: int, rotation: int = 0):
        """Place program shape on grid."""
        prog = NCP_DATABASE.get(prog_name)
        if not prog:
            return False
        
        shape = self._rotate_shape(prog.shape, rotation)
        for dx, dy in shape:
            gx, gy = x + dx, y + dy
            if 0 <= gx < self.grid_size and 0 <= gy < self.grid_size:
                self.grid[gy][gx] = prog_name
    
    def _rotate_shape(self, shape: List[Tuple[int, int]], rotation: int) -> List[Tuple[int, int]]:
        """Rotate shape 0, 90, 180, or 270 degrees."""
        rotated = shape
        for _ in range(rotation % 4):
            rotated = [(-y, x) for x, y in rotated]
            # Normalize to positive coordinates
            min_x = min(p[0] for p in rotated)
            min_y = min(p[1] for p in rotated)
            rotated = [(x - min_x, y - min_y) for x, y in rotated]
        return rotated
    
    def can_install(self, prog_name: str, x: int, y: int, rotation: int = 0) -> Tuple[bool, str]:
        """Check if program can be installed at position."""
        prog = NCP_DATABASE.get(prog_name)
        if not prog:
            return False, "Unknown program"
        
        # Check if we own this program
        owned_count = self.owned_programs.get(prog_name, 0)
        if owned_count <= 0:
            return False, "Program not owned"
        
        # Check how many are already installed
        installed_count = sum(1 for name, _, _, _ in self.installed if name == prog_name)
        if installed_count >= owned_count:
            return False, "All copies already installed"
        
        shape = self._rotate_shape(prog.shape, rotation)
        
        # Check bounds and overlap
        for dx, dy in shape:
            gx, gy = x + dx, y + dy
            if gx < 0 or gx >= self.grid_size or gy < 0 or gy >= self.grid_size:
                return False, "Out of bounds"
            if self.grid[gy][gx] is not None:
                return False, "Overlaps existing program"
        
        # Check same-color touching (not allowed)
        for dx, dy in shape:
            gx, gy = x + dx, y + dy
            for nx, ny in [(gx-1, gy), (gx+1, gy), (gx, gy-1), (gx, gy+1)]:
                if 0 <= nx < self.grid_size and 0 <= ny < self.grid_size:
                    neighbor = self.grid[ny][nx]
                    if neighbor and neighbor != prog_name:
                        neighbor_prog = NCP_DATABASE.get(neighbor)
                        if neighbor_prog and neighbor_prog.color == prog.color:
                            return False, "Same color programs cannot touch"
        
        return True, "OK"
    
    def install(self, prog_name: str, x: int, y: int, rotation: int = 0) -> Tuple[bool, str]:
        """Install a program at position."""
        can, msg = self.can_install(prog_name, x, y, rotation)
        if not can:
            return False, msg
        
        self._place_on_grid(prog_name, x, y, rotation)
        self.installed.append((prog_name, x, y, rotation))
        self._compute_stats()
        return True, "Installed"
    
    def uninstall(self, prog_name: str) -> bool:
        """Remove a program from the grid."""
        for i, (name, x, y, rot) in enumerate(self.installed):
            if name == prog_name:
                self.installed.pop(i)
                self._rebuild_grid()
                self._compute_stats()
                return True
        return False
    
    def check_bugs(self) -> List[str]:
        """Check for rule violations (bugs)."""
        bugs = []
        
        for prog_name, x, y, rotation in self.installed:
            prog = NCP_DATABASE.get(prog_name)
            if not prog:
                continue
            
            shape = self._rotate_shape(prog.shape, rotation)
            touches_command = any(y + dy == self.command_line for _, dy in shape)
            
            if prog.is_solid and not touches_command:
                bugs.append(f"{prog_name}: Solid program must touch command line")
            elif not prog.is_solid and touches_command:
                bugs.append(f"{prog_name}: Plus program must NOT touch command line")
        
        return bugs
    
    def _compute_stats(self):
        """Compute stat bonuses from installed programs."""
        stats = {
            "buster_attack": 0,
            "buster_speed": 0,
            "buster_charge": 0,
            "max_hp": 0,
            "custom_size": 0,
            "gauge_speed": 1.0,
            "undershirt": False,
            "sneak_run": False,
            "collect": False,
            "float_shoes": False,
            "start_barrier": 0,
            "super_armor": False,
        }
        
        bugs = self.check_bugs()
        
        for prog_name, x, y, rotation in self.installed:
            prog = NCP_DATABASE.get(prog_name)
            if not prog:
                continue
            
            # Check if this program is bugged
            is_bugged = any(prog_name in bug for bug in bugs)
            if is_bugged:
                continue  # Bugged programs don't provide effects
            
            # Apply effect
            effect = prog.effect
            if effect in ["buster_attack", "buster_speed", "buster_charge", "max_hp", "custom_size", "start_barrier"]:
                stats[effect] += prog.value
            elif effect == "gauge_speed":
                stats[effect] *= prog.value
            elif effect in ["undershirt", "sneak_run", "collect", "float_shoes", "super_armor"]:
                stats[effect] = True
        
        # Cap buster stats at 5
        stats["buster_attack"] = min(5, stats["buster_attack"])
        stats["buster_speed"] = min(5, stats["buster_speed"])
        stats["buster_charge"] = min(5, stats["buster_charge"])
        
        self.computed_stats = stats
    
    def add_program(self, prog_name: str, count: int = 1) -> bool:
        """Add program(s) to owned inventory."""
        if prog_name in NCP_DATABASE:
            current = self.owned_programs.get(prog_name, 0)
            self.owned_programs[prog_name] = current + count
            return True
        return False
    
    def get_owned_list(self) -> list:
        """Get list of owned program names (with duplicates for quantities)."""
        result = []
        for name, count in self.owned_programs.items():
            for _ in range(count):
                result.append(name)
        return result
    
    def get_available_to_install(self) -> list:
        """Get programs that can still be installed (have remaining copies)."""
        available = []
        for name, count in self.owned_programs.items():
            installed_count = sum(1 for n, _, _, _ in self.installed if n == name)
            remaining = count - installed_count
            if remaining > 0:
                available.append((name, remaining))
        return available
    
    def run_programs(self) -> Tuple[bool, str]:
        """
        Run the NaviCust configuration.
        Returns (success, message) for dialog display.
        """
        self._compute_stats()
        bugs = self.check_bugs()
        
        self.last_run_bugs = bugs
        self.last_run_ok = len(bugs) == 0
        
        if self.last_run_ok:
            return True, "All systems\nnormal!\nI knew it, Lan!"
        else:
            return False, "Feels a little\nodd, but...\nI'm all right!"
    
    def to_dict(self) -> dict:
        """Serialize for saving."""
        return {
            "grid_size": self.grid_size,
            "installed": self.installed,
            "owned": self.owned_programs,  # Now a dict with quantities
            "last_run_ok": self.last_run_ok,
        }
    
    @staticmethod
    def from_dict(data: dict) -> "NaviCustomizer":
        """Deserialize from save data."""
        nc = NaviCustomizer(data.get("grid_size", 4))
        
        # Handle both old (list) and new (dict) format for owned programs
        owned = data.get("owned", {"Attack+1": 1, "Speed+1": 1})
        if isinstance(owned, list):
            # Convert old list format to dict
            nc.owned_programs = {}
            for name in owned:
                nc.owned_programs[name] = nc.owned_programs.get(name, 0) + 1
        else:
            nc.owned_programs = owned
        
        nc.installed = data.get("installed", [])
        nc.last_run_ok = data.get("last_run_ok", True)
        nc._rebuild_grid()
        nc._compute_stats()
        return nc
