"""
WiFi Scanner - Scans for nearby networks.
Uses OS-level tools, returns SSID + signal strength only.
"""

import subprocess
import platform
import random
import hashlib


class WiFiScanner:
    """Platform-independent WiFi scanner."""
    
    def __init__(self):
        self.system = platform.system()
    
    def scan(self) -> list:
        """Scan for WiFi networks. Returns list of dicts with ssid, signal, security."""
        try:
            if self.system == "Linux":
                return self._scan_linux()
            elif self.system == "Darwin":  # macOS
                return self._scan_macos()
            elif self.system == "Windows":
                return self._scan_windows()
        except Exception as e:
            print(f"WiFi scan failed: {e}")
        
        # Fallback to fake networks for testing
        return self._fake_networks()
    
    def _scan_linux(self) -> list:
        """Scan using nmcli or iwlist on Linux/Pi."""
        networks = []
        try:
            # Try nmcli first (works on most modern Linux)
            result = subprocess.run(
                ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "device", "wifi", "list"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line:
                        parts = line.split(":")
                        if len(parts) >= 2 and parts[0]:
                            networks.append({
                                "ssid": parts[0],
                                "signal": int(parts[1]) if parts[1].isdigit() else 50,
                                "security": parts[2] if len(parts) > 2 else "Open"
                            })
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return networks if networks else self._fake_networks()
    
    def _scan_macos(self) -> list:
        """Scan using airport on macOS."""
        networks = []
        try:
            result = subprocess.run(
                ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-s"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")[1:]  # Skip header
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 2:
                        ssid = parts[0]
                        signal = abs(int(parts[1])) if parts[1].lstrip("-").isdigit() else 50
                        signal = min(100, max(0, 100 + int(parts[1])))  # Convert dBm to %
                        networks.append({
                            "ssid": ssid,
                            "signal": signal,
                            "security": "WPA2" if len(parts) > 6 else "Open"
                        })
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return networks if networks else self._fake_networks()
    
    def _scan_windows(self) -> list:
        """Scan using netsh on Windows."""
        networks = []
        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "networks", "mode=Bssid"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                current_ssid = None
                current_signal = 50
                for line in result.stdout.split("\n"):
                    line = line.strip()
                    if line.startswith("SSID") and ":" in line:
                        if current_ssid:
                            networks.append({
                                "ssid": current_ssid,
                                "signal": current_signal,
                                "security": "WPA2"
                            })
                        current_ssid = line.split(":", 1)[1].strip()
                        current_signal = 50
                    elif "Signal" in line and ":" in line:
                        sig_str = line.split(":")[1].strip().replace("%", "")
                        current_signal = int(sig_str) if sig_str.isdigit() else 50
                
                if current_ssid:
                    networks.append({
                        "ssid": current_ssid,
                        "signal": current_signal,
                        "security": "WPA2"
                    })
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return networks if networks else self._fake_networks()
    
    def _fake_networks(self) -> list:
        """Generate fake networks for testing."""
        fake_names = [
            "NETGEAR-5G", "xfinitywifi", "HOME-WIFI-2.4", "Linksys00042",
            "ATT-WIFI-8821", "DIRECT-roku-123", "HP-Print-42-LaserJet",
            "CoffeeShop_Guest", "Library-Public", "ASUS_5G_Gaming",
            "FBI-Surveillance-Van", "Pretty_Fly_WiFi", "The_LAN_Before_Time"
        ]
        
        # Use time-based seed for variety but consistency within short period
        import time
        seed = int(time.time() // 300)  # Changes every 5 minutes
        random.seed(seed)
        
        count = random.randint(4, 8)
        networks = []
        used = set()
        
        for _ in range(count):
            name = random.choice([n for n in fake_names if n not in used])
            used.add(name)
            networks.append({
                "ssid": name,
                "signal": random.randint(20, 95),
                "security": random.choice(["WPA2", "WPA3", "WEP", "Open"])
            })
        
        random.seed()  # Reset seed
        return networks


def hash_ssid(ssid: str) -> str:
    """Create a privacy-safe hash of an SSID."""
    return hashlib.sha256(ssid.encode()).hexdigest()[:12]


def anonymize_ssid(ssid: str) -> str:
    """Convert SSID to anonymous display name."""
    h = hash_ssid(ssid)
    prefixes = ["Cyber", "Net", "Data", "Node", "Grid", "Link", "Core", "Hub"]
    suffixes = ["Zone", "Sector", "Block", "Area", "Field", "Space", "Point"]
    
    # Deterministic selection based on hash
    p_idx = int(h[:4], 16) % len(prefixes)
    s_idx = int(h[4:8], 16) % len(suffixes)
    num = int(h[8:], 16) % 100
    
    return f"{prefixes[p_idx]}{suffixes[s_idx]}-{num:02d}"
