# Seeded Asteroids - Open World Prototype

An Asteroids-inspired, vector-style space survival game with a large wrapping universe, seeded landmarks, and procedural asteroid fields. Fly, shoot, and survive among giant planets and moons while the world persists across sessions.

Built alongside OpenAI Codex as an iterative, collaborative prototype.

## Features
- Large, wrap-around universe with parallax starfield
- Vector-line rendering with color-coded objects
- Procedural planets + moons (seed-based)
- Dense asteroid fields with fragments and giant variants
- Pickups (shield / rapid fire)
- Save/load support
- Gamepad support (NES-style mappings)

## Requirements
- Python 3.10+ (recommended)
- pygame

## Setup
```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
python -m pip install pygame
```

## Run
```powershell
python main.py
```

## Controls
Keyboard:
- Move: Arrow keys / WASD
- Shoot: Space
- Full stop: Q
- Save: F5
- Load: L
- New seed: N

Gamepad (NES-style):
- D-pad: Move
- B (left): Fire
- A (right): Full stop

## Notes
- The universe wraps only for the player ship.
- Collisions with asteroids/planets/moons are fatal.
- Pickups persist until collected.
