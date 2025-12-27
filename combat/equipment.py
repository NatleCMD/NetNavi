"""
Equipment System - Replaces NaviCust grid system.
Simple list-based equipment with CP costs.
"""

# Equipment Database
EQUIPMENT_DB = {
    # Common Equipment (60% drop rate)
    "ATK+1": {
        "name": "ATK+1",
        "cost": 2,
        "stat": "attack",
        "value": 1,
        "rarity": "common",
        "description": "Buster Attack +1"
    },
    "HP+50": {
        "name": "HP+50",
        "cost": 3,
        "stat": "max_hp",
        "value": 50,
        "rarity": "common",
        "description": "Maximum HP +50"
    },
    "Speed+1": {
        "name": "Speed+1",
        "cost": 2,
        "stat": "buster_speed",
        "value": 1,
        "rarity": "common",
        "description": "Buster Speed +1"
    },
    
    # Uncommon Equipment (30% drop rate)
    "Charge+1": {
        "name": "Charge+1",
        "cost": 3,
        "stat": "charge_speed",
        "value": 1,
        "rarity": "uncommon",
        "description": "Charge Speed +1"
    },
    "Custom+1": {
        "name": "Custom+1",
        "cost": 3,
        "stat": "custom_gauge",
        "value": 1,
        "rarity": "uncommon",
        "description": "Custom Gauge fills faster"
    },
    "Shield": {
        "name": "Shield",
        "cost": 4,
        "stat": "defense",
        "value": 2,
        "rarity": "uncommon",
        "description": "Defense +2"
    },
    
    # Rare Equipment (10% drop rate)
    "Float": {
        "name": "Float",
        "cost": 5,
        "stat": "movement",
        "value": "float",
        "rarity": "rare",
        "description": "Ignore panel effects"
    },
    "SuperArmor": {
        "name": "SuperArmor",
        "cost": 6,
        "stat": "armor",
        "value": "no_flinch",
        "rarity": "rare",
        "description": "No flinching from attacks"
    },
    "BusterPack": {
        "name": "BusterPack",
        "cost": 5,
        "stat": "attack",
        "value": 3,
        "rarity": "rare",
        "description": "Buster Attack +3"
    }
}


class Equipment:
    """Manages equipment system - owned items, equipped items, CP limits."""
    
    def __init__(self, max_cp: int = 10):
        self.owned = {}  # {item_name: quantity}
        self.equipped = []  # [item_name, item_name, ...]
        self.max_cp = max_cp
    
    def add_item(self, item_name: str):
        """Add item to owned inventory."""
        if item_name not in EQUIPMENT_DB:
            return False
        
        if item_name in self.owned:
            self.owned[item_name] += 1
        else:
            self.owned[item_name] = 1
        return True
    
    def can_equip(self, item_name: str) -> bool:
        """Check if item can be equipped (has CP and owns it)."""
        if item_name not in self.owned or self.owned[item_name] <= 0:
            return False
        
        if item_name in self.equipped:
            return False  # Already equipped
        
        item_cost = EQUIPMENT_DB[item_name]["cost"]
        used_cp = self.get_used_cp()
        
        return (used_cp + item_cost) <= self.max_cp
    
    def equip(self, item_name: str) -> bool:
        """Equip an item if possible."""
        if not self.can_equip(item_name):
            return False
        
        self.equipped.append(item_name)
        return True
    
    def unequip(self, item_name: str) -> bool:
        """Unequip an item."""
        if item_name in self.equipped:
            self.equipped.remove(item_name)
            return True
        return False
    
    def is_equipped(self, item_name: str) -> bool:
        """Check if item is currently equipped."""
        return item_name in self.equipped
    
    def get_used_cp(self) -> int:
        """Calculate total CP used by equipped items."""
        total = 0
        for item_name in self.equipped:
            if item_name in EQUIPMENT_DB:
                total += EQUIPMENT_DB[item_name]["cost"]
        return total
    
    def get_stat_bonuses(self) -> dict:
        """
        Calculate all stat bonuses from equipped items.
        Returns dict like: {"attack": 2, "max_hp": 50, "defense": 1, ...}
        """
        bonuses = {}
        
        for item_name in self.equipped:
            if item_name not in EQUIPMENT_DB:
                continue
            
            item = EQUIPMENT_DB[item_name]
            stat = item["stat"]
            value = item["value"]
            
            # For numeric bonuses, accumulate
            if isinstance(value, (int, float)):
                if stat in bonuses:
                    bonuses[stat] += value
                else:
                    bonuses[stat] = value
            else:
                # For special effects (like "float"), store as-is
                bonuses[stat] = value
        
        return bonuses
    
    def get_all_owned_items(self) -> list:
        """Return list of all owned item names (for UI display)."""
        return list(self.owned.keys())
    
    def to_dict(self) -> dict:
        """Serialize to dictionary for saving."""
        return {
            "owned": self.owned.copy(),
            "equipped": self.equipped.copy(),
            "max_cp": self.max_cp
        }
    
    @staticmethod
    def from_dict(data: dict) -> "Equipment":
        """Deserialize from dictionary."""
        equipment = Equipment(max_cp=data.get("max_cp", 10))
        equipment.owned = data.get("owned", {})
        equipment.equipped = data.get("equipped", [])
        return equipment
    
    @staticmethod
    def _get_starter_equipment() -> "Equipment":
        """Create starter equipment for new game."""
        equipment = Equipment(max_cp=10)
        # Give player 2 ATK+1 to start
        equipment.owned = {"ATK+1": 2, "HP+50": 1}
        equipment.equipped = ["ATK+1"]  # One equipped
        return equipment


def roll_equipment_drop() -> str | None:
    """
    Roll for equipment drop after battle.
    3% chance overall.
    Returns item name or None.
    """
    import random
    
    # 3% chance for any drop
    if random.random() >= 0.03:
        return None
    
    # Weighted rarity selection
    rarity_roll = random.random()
    
    if rarity_roll < 0.60:  # 60% common
        pool = [name for name, data in EQUIPMENT_DB.items() if data["rarity"] == "common"]
    elif rarity_roll < 0.90:  # 30% uncommon
        pool = [name for name, data in EQUIPMENT_DB.items() if data["rarity"] == "uncommon"]
    else:  # 10% rare
        pool = [name for name, data in EQUIPMENT_DB.items() if data["rarity"] == "rare"]
    
    if not pool:
        return None
    
    return random.choice(pool)
