# Nyumba-quest
## Game Overview

Nyumba Quest is a 2D adventure game developed using Python and Pygame. Navigate through a mysterious house, collect treasures and health items, and evade AI-controlled enemies to achieve victory.

## Features

- Dynamic AI Enemies
- Item Collection
- Realistic Collision Detection
- Pseudo-3D Rendering
- Interactive Menus
- Immersive Sound Effects
- Responsive Controls

## Prerequisites

- Python 3.7+
- Pygame library

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/clairewachira/Nyumba-quest
   cd nyumba-quest
   ```

2. Create and activate a virtual environment (optional if you have a global pygame installation):
   ```bash
   python -m venv venv
   # Activate:
   # Windows: venv\Scripts\activate
   # macOS/Linux: source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   # Or manually: pip install pygame
   ```

## Controls

- Move Forward: Up Arrow
- Move Backward: Down Arrow
- Rotate Left: Left Arrow
- Rotate Right: Right Arrow
- Pause Menu: Escape
- Select Menu Options: Mouse Click

## Objectives

- Collect All Treasures
- Maintain Health
- Evade Enemies
- Explore the House

## Running the Game

```bash
python main.py
```

## Project Structure

```
nyumba-quest/
├── audio/
│   ├── bg.mp3
│   ├── item.wav
│   ├── win.wav
│   └── button.mp3
├── images/
│   ├── enemy.png
│   ├── treasure.png
│   ├── health.png
│   ├── player_sprite.png
├── main.py
├── requirements.txt
└── README.md
```

## Troubleshooting

- Ensure Pygame is installed
- Check asset file locations
- Verify Python version

## Contributing

Contributions are welcome! Fork the repository, create a branch, commit changes, and open a pull request.

## License

Distributed under the MIT License.

## Acknowledgements

- Pygame
- OpenGameArt.org
- Python Community

---
*Embark on your quest and uncover the secrets that await within the house of mysteries!*
