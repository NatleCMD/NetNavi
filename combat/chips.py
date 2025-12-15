"""
Chips - Battle chip definitions and folder management.
"""

import random
from dataclasses import dataclass, field
from typing import List


@dataclass
class Chip:
    """A battle chip."""
    name: str
    chip_type: str  # attack, heal, defense, sword, widesword, longsword
    power: int
    code: str
    element: str = "null"
    range_pattern: List[tuple] = field(default_factory=list)  # For melee attacks
    
    def __post_init__(self):
        # Set range patterns for sword types
        if self.chip_type == "sword":
            self.range_pattern = [(1, 0)]  # 1 tile in front
        elif self.chip_type == "widesword":
            self.range_pattern = [(1, -1), (1, 0), (1, 1)]  # 3 tiles (column in front)
        elif self.chip_type == "longsword":
            self.range_pattern = [(1, 0), (2, 0)]  # 2 tiles forward


# Chip database - all possible chips
CHIP_DATABASE = {
    # Buster-type (projectile)
    "Cannon": Chip("Cannon", "attack", 40, "A"),
    "HiCannon": Chip("HiCannon", "attack", 60, "H"),
    "M-Cannon": Chip("M-Cannon", "attack", 80, "M"),
    "Spreader": Chip("Spreader", "attack", 30, "M"),
    "MiniBomb": Chip("MiniBomb", "attack", 50, "B"),
    
    # Sword-type (melee)
    "Sword": Chip("Sword", "sword", 80, "S"),
    "WideSword": Chip("WideSword", "widesword", 80, "W"),
    "LongSword": Chip("LongSword", "longsword", 80, "L"),
    "FireSword": Chip("FireSword", "sword", 100, "F", "fire"),
    "AquaSword": Chip("AquaSword", "sword", 100, "A", "aqua"),
    
    # Heal
    "Recover10": Chip("Recover10", "heal", 10, "R"),
    "Recover30": Chip("Recover30", "heal", 30, "R"),
    "Recover50": Chip("Recover50", "heal", 50, "R"),
    "Recover80": Chip("Recover80", "heal", 80, "R"),
    
    # Defense
    "Barrier": Chip("Barrier", "defense", 10, "B"),
    "Invis": Chip("Invis", "defense", 0, "I"),
}

# Chips that can drop from viruses (with rarity weights)
DROPPABLE_CHIPS = {
    "Cannon": 40,      # Common
    "MiniBomb": 30,
    "Recover10": 25,
    "Sword": 20,
    "HiCannon": 15,    # Uncommon
    "Recover30": 15,
    "WideSword": 10,
    "LongSword": 10,
    "Spreader": 10,
    "M-Cannon": 5,     # Rare
    "Recover50": 5,
    "FireSword": 3,
    "AquaSword": 3,
    "Barrier": 8,
    "Invis": 2,        # Very rare
}


class ChipFolder:
    """Player's battle chip folder."""
    
    def __init__(self, max_size: int = 30):
        self.max_size = max_size
        self.chips: List[Chip] = []
    
    def add_chip(self, chip_name: str) -> bool:
        """Add a chip to the folder by name."""
        if len(self.chips) >= self.max_size:
            return False
        if chip_name in CHIP_DATABASE:
            # Create a copy of the chip
            orig = CHIP_DATABASE[chip_name]
            new_chip = Chip(orig.name, orig.chip_type, orig.power, orig.code, orig.element)
            self.chips.append(new_chip)
            return True
        return False
    
    def remove_chip(self, index: int) -> bool:
        """Remove a chip from the folder."""
        if 0 <= index < len(self.chips):
            self.chips.pop(index)
            return True
        return False
    
    def draw_chips(self, count: int = 5) -> List[Chip]:
        """Draw random chips from folder for custom screen."""
        if not self.chips:
            return []
        available = self.chips.copy()
        random.shuffle(available)
        return available[:min(count, len(available))]
    
    def get_starter_folder():
        """Create a new folder with just starter chips."""
        folder = ChipFolder()
        # Start with just 3 Cannons
        folder.add_chip("Cannon")
        folder.add_chip("Cannon")
        folder.add_chip("Cannon")
        return folder


def roll_chip_drop(enemy_name: str = None) -> str:
    """Roll for a chip drop. Returns chip name or None. 3-5% base drop rate."""
    # Base drop rate: 3-5%
    if random.random() > 0.04:  # 96% chance of no drop
        return None
    
    # Weighted random selection from droppable chips
    total_weight = sum(DROPPABLE_CHIPS.values())
    roll = random.randint(1, total_weight)
    
    cumulative = 0
    for chip_name, weight in DROPPABLE_CHIPS.items():
        cumulative += weight
        if roll <= cumulative:
            return chip_name
    
    return "Cannon"  # Fallback
