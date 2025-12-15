"""
Area Generator - Converts WiFi networks to game Areas.
"""

import hashlib
import random
from datetime import date


class AreaGenerator:
    """Generates game Areas from WiFi network data."""
    
    THEMES = ["digital", "fire", "aqua", "forest", "electric", "dark"]
    
    def generate_area(self, network: dict) -> dict:
        """Convert a WiFi network into a game Area."""
        ssid = network.get("ssid", "Unknown")
        signal = network.get("signal", 50)
        security = network.get("security", "Open")
        
        # Create deterministic seed from SSID + date
        seed_str = f"{ssid}_{date.today().isoformat()}"
        seed = int(hashlib.sha256(seed_str.encode()).hexdigest()[:8], 16)
        
        # Use seed for deterministic generation
        rng = random.Random(seed)
        
        # Theme based on SSID characteristics
        theme = self._determine_theme(ssid, rng)
        
        # Difficulty based on signal (stronger = harder boss area)
        base_level = max(1, 10 - signal // 12)  # 1-10 range roughly
        level_variance = rng.randint(-1, 2)
        recommended_level = max(1, base_level + level_variance)
        
        # Display name (can be anonymized based on settings)
        display_name = ssid
        
        return {
            "ssid": ssid,
            "display_name": display_name,
            "seed": seed,
            "signal": signal,
            "security": security,
            "theme": theme,
            "recommended_level": recommended_level,
            "is_boss_area": False,  # Set by scan scene for strongest signal
            "node_count": rng.randint(5, 10),
            "loot_quality": min(5, recommended_level // 2 + 1),
        }
    
    def _determine_theme(self, ssid: str, rng: random.Random) -> str:
        """Pick a theme based on SSID keywords or randomly."""
        ssid_lower = ssid.lower()
        
        # Keyword matching
        if any(w in ssid_lower for w in ["fire", "hot", "flame", "sun"]):
            return "fire"
        if any(w in ssid_lower for w in ["aqua", "water", "ocean", "pool", "fish"]):
            return "aqua"
        if any(w in ssid_lower for w in ["forest", "tree", "green", "garden", "plant"]):
            return "forest"
        if any(w in ssid_lower for w in ["electric", "power", "volt", "thunder", "storm"]):
            return "electric"
        if any(w in ssid_lower for w in ["dark", "shadow", "night", "black", "void"]):
            return "dark"
        if any(w in ssid_lower for w in ["net", "wifi", "router", "link", "web"]):
            return "digital"
        
        # Random otherwise
        return rng.choice(self.THEMES)
