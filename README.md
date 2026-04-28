# Demogorgon Hunter

A Stranger Things-inspired top-down survival shooter built with Python and Pygame.

## Features
- 4-wave progression system
- enemy combat with health bars
- final boss battle with laser attack
- power-up drops: health, damage boost, speed boost
- pause menu, settings menu, game over and victory screens
- dynamic background, atmosphere effects, and sound

## Controls
- W A S D = move
- Mouse = aim
- Left Click = shoot
- Pause button at top center = pause menu

## How to Run
Run:

python dist/main.py

## File Structure

```
/ (Root)
├── README.md           # Project documentation (this file)
├── DEMO.mp4            # Gameplay demo video (under 30 seconds)
├── src/                # Development environment — raw, in-progress code (may have bugs, minimal comments)
│   ├── main.py         # Main game file (game loop, wave logic, player, enemies, bullets, UI)
│   ├── upside_down_bg.py  # Procedurally generated Upside Down background (vines, ground, atmosphere)
│   └── assets/
│       ├── sounds/     # All sound effects and music used in the game
│       └── sprites/    # All sprite images used in the game
└── dist/               # Production version — stable, fully commented and documented code (this is what gets graded)
    ├── main.py         # Stable version of the main game file
    ├── upside_down_bg.py  # Stable version of the background module
    └── assets/
        ├── sounds/     # Verified copies of all sounds
        └── sprites/    # Verified copies of all sprites
```

## OOP Breakdown

The game is structured around several classes defined in `main.py` and `upside_down_bg.py`:

| Class | Description |
|---|---|
| `Player` | Represents the player character. Handles movement (WASD), gun rotation toward the mouse, shooting, health, and power-up application. |
| `Enemy` | Represents a standard Demogorgon enemy. Handles pathfinding toward the player, health, damage, and health bar rendering. |
| `Boss` | Extends enemy behavior for the final wave. Includes a laser attack mechanic and increased aggression/health scaling. |
| `Bullet` | Represents a projectile fired by the player. Handles directional movement based on mouse-aim angle math. |
| `PowerUp` | Represents a dropped power-up (health, damage boost, or speed boost). Handles drop logic and collision with the player. |
| `UpsideDownBackground` | Manages the procedurally generated background — draws vines, ground, and atmospheric overlays that always fit the screen. |

## Assets & Sources

### Sprites
- **Gun sprite:** [Pixel Art Guns with Firing Animations](https://gg-undroid-games.itch.io/pixel-art-guns-with-firing-animations-2) (itch.io — gg-undroid-games)
- **Enemy sprite (Demogorgon):** [Stranger Things Demogorgon Pixel Art](https://dinopixel.com/stranger-things-demogorgon-pixel-art-44185) (dinopixel.com)
- **Boss sprite (Mind Flayer):** [Mind Flayer](https://www.deviantart.com/gojilion91/art/Mind-Flayer-766307237) (DeviantArt — gojilion91)
- **Player sprite:** [Stranger Things Pixel Art](https://www.pinterest.com/pin/stranger-things-pixel-art-pattern--6896205672256546/) (Pinterest)
- **Laser sprite:** [Warped Shooting FX](https://ansimuz.itch.io/warped-shooting-fx) (itch.io — ansimuz)

### Sounds
All sound effects and music were sourced from YouTube.

## AI Usage

AI was a significant part of my development process, both as a learning tool and as a practical assistant. Here's a breakdown of where and how I used it:

### What AI Helped With

**Color Selection**
I used AI to look up and suggest hex color codes throughout the game. This saved a lot of time compared to manually hunting for the right shades using a color picker.

**Procedural Background Generation**
The game's background is procedurally drawn using code rather than an image file. I originally tried using a static image, but it kept getting cropped or stretched depending on the window size. I asked AI to help me generate the background programmatically so it would always fit the screen correctly.

**Player vs. World Perspective**
Pygame handles screen coordinates differently from how you might intuitively think about a "world" the player moves through. I used AI to understand and implement the distinction between player-space and world-space so the game camera and movement felt correct.

**Mouse Input in Pygame**
I had no prior experience with mouse-based controls in Pygame. AI explained how to read mouse position and button events so I could implement aiming and shooting with the mouse.

**Drawing Health Bars**
Every time I tried to draw the health bar myself, the red (damage) bar would render on top of the green (health) bar. AI helped me understand the correct draw order and layering logic to get it displaying properly.

**Bullet and Gun Angle Math**
I used AI to help with the trigonometry behind aiming — specifically calculating the angle a gun needs to rotate and the direction a bullet needs to travel based on where the mouse is pointing.

**Audio with Pygame Mixer**
I had no prior experience with `pygame.mixer`. AI walked me through how to load, play, and manage sound effects and music in the game.

**Particle Effects and Visual Overlays**
I used AI to help implement particle systems and screen overlays (like atmosphere/lighting effects) that play during gameplay.

**Menu State Management**
AI helped me understand how to structure a state machine for my menus — separating the main menu, settings, pause menu, game over screen, and victory screen into distinct states. This was a turning point for the project because it gave the whole game a clear organizational backbone.

**Docstrings and Code Comments**
All docstrings and inline comments throughout the codebase were written with AI assistance.

**General Debugging and Placement**
Whenever I was stuck — whether it was enemy pathfinding, bullets disappearing after one shot, or figuring out where to place a piece of logic so it would actually work — I consulted AI to talk through the problem. This was one of the most valuable uses throughout the project and helped me develop better instincts for code structure.

---

### What I Figured Out Without AI

**Gun Flipping Based on Mouse Position**
AI repeatedly gave me incorrect or overcomplicated solutions for flipping the gun sprite depending on which side of the player the mouse was on. I ended up solving this one myself by working through the logic manually.

**Git and GitHub**
AI was not helpful here either. Getting my repository set up, understanding what `get_asset_path()` was doing, renaming files correctly, and finally pushing everything — none of that came from AI. A senior CS major at my university walked me through it in person, and that's what actually got it working.
