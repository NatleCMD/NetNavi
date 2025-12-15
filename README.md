# NetNavi PET - WiFi Dungeon Crawler

A handheld PET game where nearby WiFi networks become explorable cyber dungeons. Your Net Navi explores automatically while you support with Battle Chips!

## 🎮 Features

- **WiFi-as-World**: Real WiFi SSIDs become themed dungeon areas
- **Auto-Exploring Navi**: Your Navi navigates dungeons with AI priorities
- **Chip Override System**: Load Battle Chips during a timed window each turn
- **Procedural Generation**: Same SSID = same dungeon layout (per day)
- **Privacy-First**: Only reads SSID + signal strength, never connects

## 🚀 Quick Start

```bash
# Install dependencies
pip install pygame-ce

# Run the game
python main.py
```

## 🎯 Controls

| Key | Action |
|-----|--------|
| Arrow Keys | Navigate menus |
| Z | Confirm / Load Chip |
| X | Cancel / Skip Chip |
| A/S | Chip scroll (L/R shoulder) |
| Enter | Start / Pause |
| Escape | Quit |

## 📁 Project Structure

```
netnavi-pet/
├── main.py              # Entry point, game loop, scene manager
├── scenes/              # Game screens
│   ├── hub_scene.py     # Main menu with Navi display
│   ├── scan_scene.py    # WiFi scanning & area selection
│   ├── area_scene.py    # Dungeon exploration
│   ├── battle_scene.py  # Turn-based combat
│   ├── folder_scene.py  # Chip folder management
│   └── settings_scene.py
├── combat/
│   └── chips.py         # Chip definitions & folder system
├── wifi/
│   └── scanner.py       # Platform-independent WiFi scanning
├── worldgen/
│   ├── area_gen.py      # WiFi → Area conversion
│   └── dungeon_gen.py   # Node graph dungeon generation
└── storage/
    └── save_manager.py  # Game save/load
```

## 🎨 Adding Your Sprites

The game currently uses colored circles as placeholders. To add your sprites:

1. **Hub Navi**: Edit `hub_scene.py` → `_draw_navi()` method
2. **Battle Sprites**: Edit `battle_scene.py` → `_draw_enemy()` and `_draw_navi()`
3. **Chip Icons**: Edit `battle_scene.py` → `_draw_chips_ui()`

Example sprite loading:
```python
# In your scene's __init__:
self.navi_sprite = pygame.image.load("assets/sprites/navi_idle.png").convert_alpha()

# In draw method:
screen.blit(self.navi_sprite, (x, y))
```

## ⚙️ Configuration

Edit `CONFIG` in `main.py`:

```python
CONFIG = {
    "screen_width": 320,      # Match your display
    "screen_height": 240,
    "fullscreen": False,      # True for Pi deployment
    "fps_hub": 30,
    "fps_battle": 24,
    ...
}
```

## 🔧 Raspberry Pi Setup

1. Install on Pi:
```bash
sudo apt update
sudo apt install python3-pygame
```

2. Enable WiFi scanning without root:
```bash
sudo setcap cap_net_raw+ep $(which python3)
```

3. Run fullscreen:
```python
CONFIG["fullscreen"] = True
```

## 📝 Roadmap

- [ ] Sprite integration
- [ ] Sound effects
- [ ] Daily quests system
- [ ] Navi customizer (passive upgrades)
- [ ] Element weakness chart
- [ ] Chip codes for combos
- [ ] AI speech bubbles (future)

## 🛡️ Privacy

This game is designed with privacy in mind:
- Only reads broadcast SSID names and signal strength
- Never connects to networks
- Never probes devices
- Can anonymize SSIDs in settings
- Hashed SSIDs stored in saves (not raw names)

## License

MIT - Do whatever you want with it!
