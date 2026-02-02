# Seeded Asteroids - Open World Prototype

An Asteroids-inspired, vector-style space survival game with a large wrapping universe, seeded landmarks, and procedural asteroid fields. Fly, shoot, and survive among giant planets and moons while the world persists across sessions.

Built alongside OpenAI Codex as an iterative, collaborative prototype.

## Features
- Large, wrap-around universe with parallax starfield
- Vector-line rendering with color-coded objects
- Procedural planets + moons (seed-based) and roaming freighters
- Asteroids that fragment into smaller chunks
- Enemies (including elite variants)
- Pickups: shield, boost, spread, mines, and shootable boost canisters
- Objectives screen with per-seed checklist tracking
- Save/load support and seeded world resets
- Gamepad support (DualShock-style mappings via pygame)

## Requirements
- Python 3.10+ (recommended)
- pygame

## Setup
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install pygame
```

## How To Run
1) Open PowerShell in this folder.
2) (First time only) Create and activate the virtual environment:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
3) Install dependencies (first time only):
```powershell
python -m pip install pygame
```
4) Start the game:
```powershell
python main.py
```

## Controls
Keyboard:
- Move/turn: Arrow keys / WASD
- Strafe: Q / E
- Shoot: Space
- Brake/stop: LShift
- Map: M
- Objectives: O
- New seed: N
- Save: F5
- Load: F6
- Powerups: 1 Shield, 2 Boost, 3 Spread, 4 Mine
- Toggle debug HUD: F1

Gamepad (DualShock-style via pygame):
- Left stick or D-pad: Turn/rotate
- R1: Thrust
- L1: Brake/stop
- X: Fire
- Triangle/Circle/Square/L3: Powerups (see debug HUD for actual button IDs)

## Notes
- The universe wraps only for the player ship (currently blocked by the red bounds debug overlay).
- Collisions with asteroids/planets/moons are fatal.
- Pickups persist until collected.
- Mines expire after 60 seconds if not triggered.
- Explosion sounds are distance-attenuated so off-screen events are quieter.
