"""
Save Manager - Handles game save/load with chip folder and recovery system.
"""

import json
import os
import time
from pathlib import Path


class SaveManager:
    """Manages saving and loading game state."""
    
    def __init__(self, save_dir: str = None):
        if save_dir is None:
            save_dir = Path.home() / ".netnavi-pet"
        self.save_dir = Path(save_dir)
        self.save_file = self.save_dir / "save.json"
        self._ensure_dir()
    
    def _ensure_dir(self):
        self.save_dir.mkdir(parents=True, exist_ok=True)
    
    def save(self, game_state: dict) -> bool:
        """Save game state to file."""
        try:
            save_data = self._serialize(game_state)
            with open(self.save_file, "w") as f:
                json.dump(save_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Save failed: {e}")
            return False
    
    def load(self) -> dict:
        """Load game state from file."""
        try:
            if self.save_file.exists():
                with open(self.save_file, "r") as f:
                    data = json.load(f)
                return self._deserialize(data)
        except Exception as e:
            print(f"Load failed: {e}")
        return None
    
    def exists(self) -> bool:
        return self.save_file.exists()
    
    def delete(self) -> bool:
        try:
            if self.save_file.exists():
                self.save_file.unlink()
            return True
        except Exception as e:
            print(f"Delete failed: {e}")
            return False
    
    def _serialize(self, game_state: dict) -> dict:
        """Convert game state to JSON-serializable format."""
        data = {
            "navi": game_state["navi"].copy(),
            "zenny": game_state["zenny"],
            "day": game_state["day"],
            "settings": game_state["settings"].copy(),
            "explored_areas": game_state.get("explored_areas", []),
            "last_save_time": time.time(),
            "deleted_time": game_state.get("deleted_time", 0),
            "last_hp_regen_time": game_state.get("last_hp_regen_time", time.time()),
        }
        
        # Serialize chip folder
        folder = game_state.get("chip_folder")
        if folder:
            data["chips"] = [chip.name for chip in folder.chips]
        
        return data
    
    def _deserialize(self, data: dict) -> dict:
        """Convert saved data back to game state format."""
        from combat.chips import ChipFolder
        
        game_state = {
            "navi": data.get("navi", {}),
            "zenny": data.get("zenny", 0),
            "day": data.get("day", 1),
            "settings": data.get("settings", {}),
            "explored_areas": data.get("explored_areas", []),
            "current_area": None,
            "daily_quests": [],
            "deleted_time": data.get("deleted_time", 0),
            "last_hp_regen_time": data.get("last_hp_regen_time", time.time()),
        }
        
        # Deserialize chip folder
        folder = ChipFolder()
        folder.chips = []
        for chip_name in data.get("chips", []):
            folder.add_chip(chip_name)
        
        # If no chips saved, give starter chip
        if not folder.chips:
            folder.add_chip("Cannon")
            folder.add_chip("Cannon")
            folder.add_chip("Cannon")
        
        game_state["chip_folder"] = folder
        
        # Handle HP regeneration (2 HP per 5 minutes)
        current_time = time.time()
        last_regen = data.get("last_hp_regen_time", current_time)
        minutes_passed = (current_time - last_regen) / 60
        regen_ticks = int(minutes_passed / 5)  # 5 minute intervals
        
        if regen_ticks > 0:
            navi = game_state["navi"]
            regen_amount = regen_ticks * 2
            navi["hp"] = min(navi["max_hp"], navi["hp"] + regen_amount)
            game_state["last_hp_regen_time"] = current_time
        
        # Handle deletion recovery (1 hour wait)
        deleted_time = data.get("deleted_time", 0)
        if deleted_time > 0:
            hours_since_deletion = (current_time - deleted_time) / 3600
            if hours_since_deletion >= 1.0:
                # Navi recovered!
                game_state["navi"]["hp"] = game_state["navi"]["max_hp"]
                game_state["deleted_time"] = 0
        
        return game_state
