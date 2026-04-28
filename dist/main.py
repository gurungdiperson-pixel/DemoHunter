"""Demogorgon Hunter

A Stranger Things-inspired top-down survival shooter built with Pygame.
The player must survive waves of enemies, collect power-ups, and defeat a
final boss (the Mind Flayer) to win.

Architecture overview:
    - The game uses a **world-coordinate system**: every entity stores its
      position as (world_x, world_y) in an infinite 2-D space.  The player
      is always rendered at the centre of the screen; everything else is
      translated relative to the player's world position using the formula::

          screen_x = entity.world_x - player.world_x + WINDOW_WIDTH  // 2
          screen_y = entity.world_y - player.world_y + WINDOW_HEIGHT // 2

    - Game state is controlled by a string stored in ``Game.state``.
      Valid states: "menu", "playing", "paused", "settings",
      "game_over", "victory".

    - Waves 1-3 spawn regular enemies.  Wave 4 skips enemy spawning and
      instead triggers a single boss fight.

    - Power-ups drop on enemy death with a fixed probability.  Timed
      boosts (damage, speed) count down each frame and reset to base
      values when they expire.

Modules used:
    pygame: Rendering, input, sound, and game loop.
    os:     Building cross-platform asset paths.
    math:   Trigonometry for angles, distances, and projectile motion.
    random: Procedural enemy spawning, particle effects, lightning timing.
    upside_down_bg: Custom animated background module (Upside-Down aesthetic).
"""

import pygame, os, math, random
from upside_down_bg import UpsideDownBackground

# Absolute path to the directory that contains this script.
# All asset paths are built relative to this so the game works regardless
# of the working directory from which it is launched.
GAME_PATH = os.path.dirname(os.path.abspath(__file__))

def get_asset_path(filename: str) -> str:
    """Return the absolute path to an asset file inside the assets/ folder.

    Args:
        filename (str): Relative path from the assets/ directory
            (e.g. ``"sprites/player_transparant.png"``).

    Returns:
        str: Absolute filesystem path to the requested asset.
    """
    return os.path.join(GAME_PATH, "assets", filename)

pygame.init()
pygame.mixer.init()

# ---------------------------------------------------------------------------
# Display / timing constants
# ---------------------------------------------------------------------------
GAME_TITTLE = "Demogorgan Hunter!"  # Window title bar caption
WINDOW_WIDTH = 1920   # Default horizontal resolution in pixels
WINDOW_HEIGHT = 1080  # Default vertical resolution in pixels
MAX_FPS = 60          # Frame-rate cap; keeps delta-time consistent

# ---------------------------------------------------------------------------
# Colour palette (RGB tuples)
# ---------------------------------------------------------------------------
WHITE = (255, 255, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
DARK_BLUE = (0, 51, 102)    # Used for UI button fills
GREEN = (0, 255, 0)
DARK_RED = (80, 10, 10)
LIGHT_RED = (180, 40, 40)
PALE_RED = (120, 30, 30)

# ---------------------------------------------------------------------------
# Player constants
# ---------------------------------------------------------------------------
PLAYER_COLOR = YELLOW               # Fallback colour (not used when sprite is loaded)
PLAYER_WIDTH, PLAYER_HEIGHT = 90, 120   # Sprite display size in pixels
PLAYER_SPEED = 400                  # Base movement speed in world-units per second
PLAYER_HEALTH = 100                 # Starting health points
PLAYER_MAX_HEALTH = 100             # Health cap (used to clamp heal pickups)

# ---------------------------------------------------------------------------
# Enemy constants
# ---------------------------------------------------------------------------
ENEMY_SPEED = 300                   # World-units per second the enemy chases the player
ENEMY_WIDTH, ENEMY_HEIGHT = 90, 120  # Sprite display size in pixels
ENEMY_HEALTH = 100                  # Base health (overridden per wave in _setup_wave)
ENEMY_MAX_HEALTH = 100              # Used to calculate health-bar fill ratio

# ---------------------------------------------------------------------------
# Bullet constants
# ---------------------------------------------------------------------------
DAMAGE = 34          # Base damage dealt per bullet hit
BULLET_SPEED = 800   # World-units per second the bullet travels

# ---------------------------------------------------------------------------
# Boss constants
# ---------------------------------------------------------------------------
BOSS_WIDTH, BOSS_HEIGHT = 250, 250   # Mind Flayer sprite display size in pixels
BOSS_SPEED = 135                     # World-units per second the boss chases the player
BOSS_HEALTH = 1500                   # Total boss hit points
BOSS_DAMAGE = 30                     # Melee damage per second when touching the player
BOSS_LASER_SPEED = 900               # World-units per second each laser projectile travels
BOSS_LASER_DAMAGE = 45               # Damage dealt when a laser hits the player
BOSS_LASER_COOLDOWN = 1.5            # Seconds between successive laser shots

# ---------------------------------------------------------------------------
# Power-up constants
# ---------------------------------------------------------------------------
POWERUP_WIDTH, POWERUP_HEIGHT = 40, 40  # Star sprite display size in pixels
POWERUP_DROP_CHANCE = 0.35              # Probability (0-1) that a killed enemy drops a power-up

HEALTH_PACK_AMOUNT = 25        # HP restored when a health pack is collected

DAMAGE_BOOST_AMOUNT = 20       # Extra damage added on top of base DAMAGE during boost
DAMAGE_BOOST_DURATION = 5.0    # Seconds the damage boost lasts

SPEED_BOOST_AMOUNT = 150       # Extra world-units/s added to player speed during boost
SPEED_BOOST_DURATION = 5.0     # Seconds the speed boost lasts


# ---------------------------------------------------------------------------
# Sprite classes
# ---------------------------------------------------------------------------

class Player(pygame.sprite.Sprite):
    """The player character controlled by keyboard (WASD) and mouse.

    The player is always drawn at the centre of the screen.  Movement is
    tracked through ``world_x`` / ``world_y``, which shift the camera so
    the rest of the world scrolls around the player.

    Attributes:
        original_image (pygame.Surface): Un-flipped sprite loaded from disk.
        image (pygame.Surface): Current frame (may be flipped horizontally).
        rect (pygame.Rect): Screen-space bounding rectangle.
        health (int): Current hit points.
        max_health (int): Maximum hit points cap.
        world_x (float): Horizontal position in world coordinates.
        world_y (float): Vertical position in world coordinates.
        speed (float): Movement speed in world-units per second; can be
            temporarily increased by a speed boost power-up.
    """

    def __init__(self):
        """Initialise the player at the centre of the screen with full health."""
        super().__init__()
        self.original_image = pygame.image.load(get_asset_path("sprites/player_transparant.png")).convert_alpha()
        self.original_image = pygame.transform.scale(self.original_image, (PLAYER_WIDTH, PLAYER_HEIGHT))

        self.image = self.original_image
        self.rect = self.image.get_rect()
        # Pin the player sprite to the screen centre; world_x/y do the scrolling
        self.rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)

        self.health = PLAYER_HEALTH
        self.max_health= PLAYER_MAX_HEALTH
        # World-space position starts at the origin
        self.world_x = 0
        self.world_y = 0
        self.speed = PLAYER_SPEED

    def update(self, delta):
        """Handle movement input and sprite facing direction.

        Reads WASD keys each frame and adjusts world_x / world_y by
        ``speed * delta`` so movement is frame-rate independent.
        The sprite is horizontally flipped to face the mouse cursor.

        Args:
            delta (float): Elapsed time since the last frame in seconds.

        Returns:
            bool: ``True`` if the player moved this frame (used by the
            caller to decide whether to play footstep sounds).
        """
        keys = pygame.key.get_pressed()
        moving = False  # Track whether any movement key is held

        # Translate WASD input into world-space displacement
        if keys[pygame.K_w]:
            self.world_y -= self.speed * delta  # Up  → negative Y in screen space
            moving = True
        if keys[pygame.K_s]:
            self.world_y += self.speed * delta  # Down → positive Y
            moving = True
        if keys[pygame.K_a]:
            self.world_x -= self.speed * delta  # Left → negative X
            moving = True
        if keys[pygame.K_d]:
            self.world_x += self.speed * delta  # Right → positive X
            moving = True

        # The rect stays at the screen centre; only world coords move
        self.rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)

        # Determine facing direction from the mouse's horizontal offset
        # relative to the player's screen-centre position
        center_x = WINDOW_WIDTH // 2
        mouse_x, mouse_y = pygame.mouse.get_pos()

        dx = mouse_x - center_x   # Positive dx → mouse is to the right
        facing_left = dx < 0

        # Flip the sprite horizontally so it faces the mouse cursor
        if facing_left:
            self.image = pygame.transform.flip(self.original_image, True, False)
        else:
            self.image = self.original_image

        return moving


class Bullet(pygame.sprite.Sprite):
    """A player-fired projectile that travels in a straight line.

    Bullets use world coordinates for physics but are converted to screen
    coordinates each frame when drawn.

    Attributes:
        image (pygame.Surface): Small coloured square representing the bullet.
        rect (pygame.Rect): Bounding rectangle (updated each draw call).
        damage (int): Hit-points removed from the target on impact.
        world_x (float): Horizontal world position.
        world_y (float): Vertical world position.
        angle (float): Travel direction in radians (standard math convention:
            0 = right, π/2 = down).
        speed (float): Travel speed in world-units per second.
    """

    def __init__(self, world_x, world_y, angle, damage):
        """Create a bullet at the given world position aimed along ``angle``.

        Args:
            world_x (float): Spawn position X in world coordinates.
            world_y (float): Spawn position Y in world coordinates.
            angle (float): Direction of travel in radians.
            damage (int): Damage dealt on hit (may include a boost).
        """
        super().__init__()
        # 6×6 yellow square; SRCALPHA allows transparent background
        self.image = pygame.Surface((6, 6), pygame.SRCALPHA)
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=(world_x, world_y))
        self.damage = damage
        self.world_x = world_x
        self.world_y = world_y
        self.angle = angle
        self.speed = BULLET_SPEED

    def update(self, delta):
        """Advance the bullet along its trajectory.

        Uses cos/sin decomposition of the angle to move the bullet in both
        axes simultaneously, producing straight-line travel at a constant
        world-space speed regardless of direction.

        Args:
            delta (float): Elapsed time since the last frame in seconds.
        """
        # cos(angle) gives the X component of the unit direction vector;
        # sin(angle) gives the Y component (positive = downward in screen space)
        self.world_x += math.cos(self.angle) * self.speed * delta
        self.world_y += math.sin(self.angle) * self.speed * delta
        self.rect.center = (self.world_x, self.world_y)

    def draw(self, screen, player_world_x, player_world_y):
        """Blit the bullet onto the screen at its correct screen position.

        Converts world coordinates to screen coordinates using the standard
        camera formula: offset from player world pos, centred on the window.

        Args:
            screen (pygame.Surface): The display surface to draw onto.
            player_world_x (float): Player's current X in world coordinates.
            player_world_y (float): Player's current Y in world coordinates.
        """
        # Translate world position to screen position:
        # Subtract player world coords so the player is at the origin,
        # then add half the window dimensions to centre that origin on screen.
        screen_x = self.world_x - player_world_x + WINDOW_WIDTH // 2
        screen_y = self.world_y - player_world_y + WINDOW_HEIGHT // 2

        self.rect.center = (screen_x, screen_y)
        screen.blit(self.image, self.rect)


class Enemy(pygame.sprite.Sprite):
    """A basic melee enemy that chases the player in a straight line.

    Enemies use world coordinates and are drawn relative to the player's
    camera position.  They deal contact damage when they reach the player.

    Attributes:
        image (pygame.Surface): Scaled enemy sprite.
        rect (pygame.Rect): Bounding rectangle (updated each draw call).
        health (int): Remaining hit points.
        max_health (int): Starting hit points; used for health-bar ratio.
        world_x (float): Horizontal world position.
        world_y (float): Vertical world position.
        speed (float): Chase speed in world-units per second.
    """

    def __init__(self, x, y, health):
        """Spawn an enemy at the given world position with the specified health.

        Args:
            x (float): Initial world X position.
            y (float): Initial world Y position.
            health (int): Starting health (varies per wave).
        """
        super().__init__()
        self.image = pygame.image.load(get_asset_path("sprites/enemy.png")).convert_alpha()
        self.image = pygame.transform.scale(self.image, (ENEMY_WIDTH, ENEMY_HEIGHT))

        self.rect = self.image.get_rect()

        self.health = health
        self.max_health = health   # Store original for health-bar proportion
        self.world_x = x
        self.world_y = y
        self.speed = ENEMY_SPEED

    def update(self, delta, player_world_x, player_world_y):
        """Move the enemy directly toward the player's current world position.

        The direction vector is normalised so the enemy always moves at a
        constant speed regardless of distance from the player.

        Args:
            delta (float): Elapsed time since the last frame in seconds.
            player_world_x (float): Player's current X in world coordinates.
            player_world_y (float): Player's current Y in world coordinates.
        """
        # Vector from this enemy to the player
        dx = player_world_x - self.world_x
        dy = player_world_y - self.world_y

        # Euclidean distance used to normalise the direction vector
        distance = math.sqrt(dx * dx + dy * dy)

        # Avoid division by zero if the enemy is exactly on top of the player
        if distance != 0:
            dx /= distance   # Normalised X component (unit vector)
            dy /= distance   # Normalised Y component (unit vector)

        # Advance the enemy toward the player at a constant speed
        self.world_x += dx * self.speed * delta
        self.world_y += dy * self.speed * delta

    def draw_health_bar(self, screen, player_world_x, player_world_y):
        """Draw a red/green health bar above the enemy sprite.

        Args:
            screen (pygame.Surface): The display surface to draw onto.
            player_world_x (float): Player's current X in world coordinates.
            player_world_y (float): Player's current Y in world coordinates.
        """
        # Convert world position to screen position (same camera formula as draw)
        screen_x = self.world_x - player_world_x + WINDOW_WIDTH // 2
        screen_y = self.world_y - player_world_y + WINDOW_HEIGHT // 2

        bar_width = 50
        bar_height = 6
        # Fraction of health remaining (0.0 – 1.0)
        health_ratio = self.health / self.max_health

        # Position the bar horizontally centred above the sprite
        bar_x = screen_x - bar_width // 2
        bar_y = screen_y - ENEMY_HEIGHT // 2 - 12  # 12px gap above sprite top

        # Red background represents the missing health
        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
        # Green foreground scales with remaining health
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, int(bar_width * health_ratio), bar_height))

    def draw(self, screen, player_world_x, player_world_y):
        """Blit the enemy sprite at its camera-relative screen position.

        Args:
            screen (pygame.Surface): The display surface to draw onto.
            player_world_x (float): Player's current X in world coordinates.
            player_world_y (float): Player's current Y in world coordinates.
        """
        # Translate from world space to screen space
        screen_x = self.world_x - player_world_x + WINDOW_WIDTH // 2
        screen_y = self.world_y - player_world_y + WINDOW_HEIGHT // 2

        self.rect.center = (screen_x, screen_y)
        screen.blit(self.image, self.rect)


class BossLaser(pygame.sprite.Sprite):
    """A projectile fired by the boss toward the player's position.

    Each laser travels in a straight line at a fixed angle determined at
    the moment of firing.  It rotates its sprite to align with that angle
    when drawn.

    Attributes:
        image (pygame.Surface): Base laser sprite (will be rotated on draw).
        rect (pygame.Rect): Bounding rectangle; updated each draw call.
        world_x (float): Horizontal world position.
        world_y (float): Vertical world position.
        angle (float): Travel direction in radians.
        speed (float): Travel speed in world-units per second.
        damage (int): Hit-points removed from the player on impact.
    """

    def __init__(self, world_x, world_y, angle):
        """Create a boss laser at the given world position aimed along ``angle``.

        Args:
            world_x (float): Spawn position X in world coordinates.
            world_y (float): Spawn position Y in world coordinates.
            angle (float): Direction of travel in radians (aimed at the
                player's world position at the time of firing).
        """
        super().__init__()

        # Replace this with your laser sprite later if needed
        self.image = pygame.image.load(get_asset_path("sprites/preview.gif")).convert_alpha()
        self.image = pygame.transform.scale(self.image, ((40, 40)))
        self.rect = self.image.get_rect()
        self.world_x = world_x
        self.world_y = world_y
        self.angle = angle
        self.speed = BOSS_LASER_SPEED
        self.damage = BOSS_LASER_DAMAGE

    def update(self, delta):
        """Advance the laser along its fixed travel direction.

        Args:
            delta (float): Elapsed time since the last frame in seconds.
        """
        # Decompose angle into X and Y velocity components, same as Bullet.update
        self.world_x += math.cos(self.angle) * self.speed * delta
        self.world_y += math.sin(self.angle) * self.speed * delta

    def draw(self, screen, player_world_x, player_world_y):
        """Blit the laser sprite, rotated to face its direction of travel.

        The sprite is rotated each frame to visually align with the
        projectile's angle rather than always facing right.

        Args:
            screen (pygame.Surface): The display surface to draw onto.
            player_world_x (float): Player's current X in world coordinates.
            player_world_y (float): Player's current Y in world coordinates.
        """
        # Convert world position to screen position
        screen_x = self.world_x - player_world_x + WINDOW_WIDTH // 2
        screen_y = self.world_y - player_world_y + WINDOW_HEIGHT // 2

        # pygame.transform.rotate uses counter-clockwise degrees, but math.atan2
        # returns clockwise radians in screen space.  Negate and convert to
        # degrees to align the sprite with the bullet's travel direction.
        rotated = pygame.transform.rotate(self.image, -math.degrees(self.angle))
        # Recalculate rect after rotation since the surface size changes
        self.rect = rotated.get_rect(center=(screen_x, screen_y))
        screen.blit(rotated, self.rect)


class Boss(pygame.sprite.Sprite):
    """The final boss (Mind Flayer) that appears in wave 4.

    The boss chases the player like a regular enemy but also fires lasers
    at regular intervals and deals continuous melee damage on contact.

    Attributes:
        image (pygame.Surface): Scaled boss sprite.
        rect (pygame.Rect): Bounding rectangle; updated each draw call.
        world_x (float): Horizontal world position.
        world_y (float): Vertical world position.
        health (int): Remaining hit points.
        max_health (int): Starting hit points; used for health-bar ratio.
        speed (float): Chase speed in world-units per second.
        laser_timer (float): Accumulated seconds since the last laser shot.
        laser_cooldown (float): Minimum seconds required between shots.
    """

    def __init__(self, x, y):
        """Spawn the boss at the given world position with full health.

        Args:
            x (float): Initial world X position.
            y (float): Initial world Y position.
        """
        super().__init__()

        self.image = pygame.image.load(get_asset_path("sprites/mind_flayer_final.png")).convert_alpha()
        self.image = pygame.transform.scale(self.image, (BOSS_WIDTH, BOSS_HEIGHT))
        self.rect = self.image.get_rect()

        self.world_x = x
        self.world_y = y
        self.health = BOSS_HEALTH
        self.max_health = BOSS_HEALTH
        self.speed = BOSS_SPEED

        # Laser cooldown tracking: timer accumulates delta each frame
        self.laser_timer = 0
        self.laser_cooldown = BOSS_LASER_COOLDOWN

    def update(self, delta, player_world_x, player_world_y):
        """Chase the player and advance the laser cooldown timer.

        Movement logic mirrors Enemy.update: normalise the direction
        vector and step toward the player each frame.

        Args:
            delta (float): Elapsed time since the last frame in seconds.
            player_world_x (float): Player's current X in world coordinates.
            player_world_y (float): Player's current Y in world coordinates.
        """
        # Vector from boss to player
        dx = player_world_x - self.world_x
        dy = player_world_y - self.world_y

        # Distance used to normalise the direction vector
        distance = math.sqrt(dx * dx + dy * dy)

        if distance != 0:
            dx /= distance   # Normalised X component
            dy /= distance   # Normalised Y component

        # Advance toward the player
        self.world_x += dx * self.speed * delta
        self.world_y += dy * self.speed * delta

        # Accumulate time since the last shot so can_shoot() can gate firing
        self.laser_timer += delta

    def can_shoot(self):
        """Check whether enough time has elapsed to fire another laser.

        Returns:
            bool: ``True`` if ``laser_timer`` has reached ``laser_cooldown``.
        """
        return self.laser_timer >= self.laser_cooldown

    def reset_laser_timer(self):
        """Reset the laser cooldown timer to zero after a shot is fired."""
        self.laser_timer = 0

    def draw(self, screen, player_world_x, player_world_y):
        """Blit the boss sprite at its camera-relative screen position.

        Args:
            screen (pygame.Surface): The display surface to draw onto.
            player_world_x (float): Player's current X in world coordinates.
            player_world_y (float): Player's current Y in world coordinates.
        """
        # Translate world position to screen position
        screen_x = self.world_x - player_world_x + WINDOW_WIDTH // 2
        screen_y = self.world_y - player_world_y + WINDOW_HEIGHT // 2

        self.rect.center = (screen_x, screen_y)
        screen.blit(self.image, self.rect)

    def draw_health_bar(self, screen, player_world_x, player_world_y):
        """Draw a large red/green health bar with a white border above the boss.

        Args:
            screen (pygame.Surface): The display surface to draw onto.
            player_world_x (float): Player's current X in world coordinates.
            player_world_y (float): Player's current Y in world coordinates.
        """
        # Convert world position to screen position
        screen_x = self.world_x - player_world_x + WINDOW_WIDTH // 2
        screen_y = self.world_y - player_world_y + WINDOW_HEIGHT // 2

        # Boss health bar is wider and taller than the standard enemy bar
        bar_width = 180
        bar_height = 12
        # Fraction of health remaining (0.0 – 1.0)
        health_ratio = self.health / self.max_health

        # Centre horizontally above the sprite
        bar_x = screen_x - bar_width // 2
        bar_y = screen_y - BOSS_HEIGHT // 2 - 18  # 18px gap above sprite top

        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, int(bar_width * health_ratio), bar_height))
        # White border to make the bar stand out against the background
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)


class PowerUp(pygame.sprite.Sprite):
    """A collectible item dropped by enemies on death.

    The player picks up a power-up by walking over it (proximity check).
    Three types are available: "health" (instant heal), "damage" (timed
    bullet damage increase), and "speed" (timed movement speed increase).

    Attributes:
        image (pygame.Surface): Star sprite displayed on the ground.
        rect (pygame.Rect): Bounding rectangle; updated each draw call.
        world_x (float): Horizontal world position (fixed at drop location).
        world_y (float): Vertical world position (fixed at drop location).
        power_type (str): One of ``"health"``, ``"damage"``, or ``"speed"``.
    """

    def __init__(self, world_x, world_y, power_type):
        """Create a power-up at the given world position.

        Args:
            world_x (float): World X coordinate where the enemy died.
            world_y (float): World Y coordinate where the enemy died.
            power_type (str): Effect type: ``"health"``, ``"damage"``,
                or ``"speed"``.
        """
        super().__init__()
        self.image = pygame.image.load(get_asset_path("sprites/star_no_bg.png")).convert_alpha()
        self.image = pygame.transform.scale(self.image, (POWERUP_WIDTH, POWERUP_HEIGHT))
        self.rect = self.image.get_rect()

        # Power-ups don't move; these stay at the drop location
        self.world_x = world_x
        self.world_y = world_y
        self.power_type = power_type

    def draw(self, screen, player_world_x, player_world_y):
        """Blit the power-up sprite at its camera-relative screen position.

        Args:
            screen (pygame.Surface): The display surface to draw onto.
            player_world_x (float): Player's current X in world coordinates.
            player_world_y (float): Player's current Y in world coordinates.
        """
        # Translate world position to screen position
        screen_x = self.world_x - player_world_x + WINDOW_WIDTH // 2
        screen_y = self.world_y - player_world_y + WINDOW_HEIGHT // 2

        self.rect.center = (screen_x, screen_y)
        screen.blit(self.image, self.rect)


class Game():
    """Top-level game controller that owns all subsystems and the main loop.

    Manages the state machine (menu → playing → paused / game_over / victory),
    all sprite groups, wave progression, sound playback, and rendering.

    Attributes:
        screen (pygame.Surface): The main display surface.
        bg (UpsideDownBackground): Scrolling parallax background.
        lightning_timer (float): Seconds until the next lightning flash.
        lightning_flash_time (float): Remaining seconds for the current flash.
        ash_particles (list[list]): Particle data rows
            ``[world_x, world_y, fall_speed, size, alpha]`` for falling spores.
        state (str): Current game state string.
        previous_state (str): State before entering settings (used for back).
        last_state (str): Previous state; used to detect state transitions.
        shoot_sound (pygame.mixer.Sound): Gunshot audio clip.
        footstep_sound (pygame.mixer.Sound): Footstep audio clip.
        laser_sound (pygame.mixer.Sound): Boss laser audio clip.
        enemy_death_sound (pygame.mixer.Sound): Enemy death audio clip.
        player_hurt_sound (pygame.mixer.Sound): Player hurt audio clip.
        game_over_sound (pygame.mixer.Sound): Game over sting.
        menu_click_sound (pygame.mixer.Sound): UI button click sound.
        victory_sound (pygame.mixer.Sound): Victory fanfare.
        lightning_sound (pygame.mixer.Sound): Thunder crack audio clip.
        footstep_timer (float): Seconds elapsed since the last footstep sound.
        footstep_delay (float): Minimum seconds between footstep sounds.
        current_music (str | None): Path of the currently loaded music track.
        wave (int): Current wave number (1-4).
        wave_in_progress (bool): Whether enemies are still being spawned/alive.
        enemies_spawned (int): How many enemies have been spawned this wave.
        enemies_to_spawn (int): Total enemies to spawn for this wave.
        running (bool): Main loop flag; set to False to quit.
        clock (pygame.time.Clock): Tracks elapsed time for delta calculation.
        score (int): Number of enemies killed.
        font (pygame.font.Font): Default UI font.
        all_sprites (pygame.sprite.Group): Group containing only the player.
        player (Player): The player sprite instance.
        enemies (pygame.sprite.Group): Active enemy sprites.
        enemy_spawn_timer (float): Accumulated seconds since the last enemy spawn.
        enemy_spawn_delay (float): Seconds between individual enemy spawns.
        bullets (pygame.sprite.Group): Active player bullet sprites.
        boss (Boss | None): The boss instance, or None before wave 4.
        boss_lasers (pygame.sprite.Group): Active boss laser sprites.
        boss_spawned (bool): Whether the boss has been created this run.
        powerups (pygame.sprite.Group): Active power-up sprites on the ground.
        damage_boost_timer (float): Remaining seconds of the damage boost.
        speed_boost_timer (float): Remaining seconds of the speed boost.
        current_bullet_damage (int): Effective damage per bullet (base or boosted).
        current_player_speed (int): Effective player speed (base or boosted).
        gun_image (pygame.Surface): Gun sprite used in _draw_gun().
        current_enemy_health (int): Health value for enemies in the current wave.
    """

    def __init__(self):
        """Initialise all game subsystems and create the first wave."""

        # --- Display setup ---
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

        # Scrolling Upside-Down themed background; seed ensures reproducibility
        self.bg = UpsideDownBackground(seed=42)

        # --- Atmospheric lightning effect ---
        # Timer counts down; when it hits 0 a flash is triggered and reset
        self.lightning_timer = random.uniform(4, 8)
        self.lightning_flash_time = 0   # Remaining seconds of the current flash

        # --- Falling ash / spore particles ---
        # Each entry: [world_x, world_y, fall_speed, size_px, alpha]
        self.ash_particles = []
        for _ in range(120):   # 120 particles gives a dense but subtle effect
            self.ash_particles.append([
                random.randint(-2000, 2000),   # world x — scattered across the map
                random.randint(-2000, 2000),   # world y
                random.uniform(10, 25),        # fall speed (world-units per second)
                random.randint(1, 3),          # radius in pixels
                random.randint(80, 180)        # opacity (0 = transparent, 255 = opaque)
            ])

        pygame.display.set_caption(GAME_TITTLE)

        # --- Game state machine ---
        self.state = "menu"            # Active state
        self.previous_state = "menu"   # Used when navigating back from settings
        self.last_state = self.state   # Compared each frame to detect transitions

        # --- Sound effects ---
        self.shoot_sound = pygame.mixer.Sound(get_asset_path("sounds/gunshot.mp3"))
        self.footstep_sound = pygame.mixer.Sound(get_asset_path("sounds/footsteps.mp3"))
        self.laser_sound = pygame.mixer.Sound(get_asset_path("sounds/laser_sound.mp3"))
        self.enemy_death_sound = pygame.mixer.Sound(get_asset_path("sounds/enemy_death.mp3"))
        self.player_hurt_sound = pygame.mixer.Sound(get_asset_path("sounds/player_hurt.mp3"))
        self.game_over_sound = pygame.mixer.Sound(get_asset_path("sounds/game_over.mp3"))
        self.menu_click_sound = pygame.mixer.Sound(get_asset_path("sounds/menu_click.mp3"))
        self.victory_sound = pygame.mixer.Sound(get_asset_path("sounds/victory.mp3"))
        self.lightning_sound = pygame.mixer.Sound(get_asset_path("sounds/lightning.mp3"))

        # --- Per-sound volume levels (0.0 – 1.0) ---
        self.shoot_sound.set_volume(0.35)
        self.footstep_sound.set_volume(0.2)
        self.laser_sound.set_volume(0.35)
        self.enemy_death_sound.set_volume(0.35)
        self.player_hurt_sound.set_volume(0.4)
        self.game_over_sound.set_volume(0.4)
        self.menu_click_sound.set_volume(0.35)
        self.victory_sound.set_volume(0.45)
        self.lightning_sound.set_volume(0.3)

        # --- Footstep cadence ---
        self.footstep_timer = 0           # Counts up while moving
        self.footstep_delay = 0.35        # Play a step every 0.35 s of movement

        # Tracks the currently loaded music file so _play_music can skip
        # re-loading if the correct track is already playing
        self.current_music = None

        # --- UI button rectangles (screen-space, repositioned on resolution change) ---
        self.play_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 400, 200, 60)
        self.settings_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 500, 200, 60)
        self.back_button = pygame.Rect(50, 50, 150, 50)
        self.pause_button = pygame.Rect(WINDOW_WIDTH // 2 - 25, 20, 50, 50)
        self.continue_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 350, 200, 60)
        self.pause_settings_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 450, 200, 60)
        self.quit_menu_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 550, 200, 60)

        # --- Wave state ---
        self.wave = 1                 # Waves 1-3 are enemy waves; wave 4 is the boss
        self.wave_in_progress = True
        self.enemies_spawned = 0      # Running count of enemies spawned this wave
        self.enemies_to_spawn = 5     # Total enemies for wave 1 (adjusted by _setup_wave)

        # Post-game screen buttons (shared by game_over and victory)
        self.play_again_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 450, 200, 60)
        self.game_over_menu_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 550, 200, 60)

        # --- Settings screen resolution buttons ---
        self.res_1920_button = pygame.Rect(WINDOW_WIDTH // 2 - 150, 320, 300, 50)
        self.res_1280_button = pygame.Rect(WINDOW_WIDTH // 2 - 150, 390, 300, 50)
        self.res_800_button = pygame.Rect(WINDOW_WIDTH // 2 - 150, 460, 300, 50)

        # --- Core game loop objects ---
        self.running = True
        self.clock = pygame.time.Clock()
        self.score = 0
        self.font = pygame.font.SysFont(None, 48)
        self.all_sprites = pygame.sprite.Group()

        # --- Player ---
        self.player = Player()
        self.all_sprites.add(self.player)

        # --- Enemy spawning ---
        self.enemies = pygame.sprite.Group()
        self.enemy_spawn_timer = 0
        self.enemy_spawn_delay = 1.0 #later on I will decrease this with stage or wave to make it harder. I will also introduce different types of enemies

        # --- Bullets ---
        self.bullets = pygame.sprite.Group()

        # --- Boss ---
        self.boss = None                             # Created when wave 4 starts
        self.boss_lasers = pygame.sprite.Group()
        self.boss_spawned = False                    # Prevents spawning the boss twice

        # --- Power-ups ---
        self.powerups = pygame.sprite.Group()

        # --- Timed power-up countdowns ---
        self.damage_boost_timer = 0   # Counts down in seconds; 0 = no active boost
        self.speed_boost_timer = 0    # Counts down in seconds; 0 = no active boost

        # Effective per-bullet damage and player speed (start at base values)
        self.current_bullet_damage = DAMAGE
        self.current_player_speed = PLAYER_SPEED

        # --- Gun sprite (drawn over the player, rotated toward the mouse) ---
        self.gun_image = pygame.image.load(get_asset_path("sprites/gun.png")).convert_alpha()
        self.gun_image = pygame.transform.scale(self.gun_image, ((120, 40)))

        # Start playing the main menu / boss music immediately
        self._play_music(get_asset_path("sounds/final_boss_main_menu.mp3"))

    def _update_overlay_effects(self, delta):
        """Advance the lightning flash timer and the ash particle simulation.

        Lightning:
            ``lightning_timer`` counts down each frame.  When it reaches zero,
            a flash is triggered (``lightning_flash_time`` is set to 0.22 s),
            the sound plays, and the timer resets to a new random interval.

        Ash particles:
            Each particle falls downward and drifts horizontally.  When a
            particle drops below the bottom of the visible area, it is
            recycled to a position just above the top of the screen.

        Args:
            delta (float): Elapsed time since the last frame in seconds.
        """
        # Count down to the next lightning flash
        self.lightning_timer -= delta

        if self.lightning_timer <= 0:
            # Trigger a 0.22-second bright flash
            self.lightning_flash_time = 0.22
            # Schedule the next flash with a random interval
            self.lightning_timer = random.uniform(3, 6)
            self.lightning_sound.play()

        # Fade out the current flash over time
        if self.lightning_flash_time > 0:
            self.lightning_flash_time -= delta

        # Update each ash / spore particle
        for particle in self.ash_particles:
            # particle[1] = world_y; particle[2] = fall speed (world-units/s)
            particle[1] += particle[2] * delta
            # Slight random horizontal drift per frame
            particle[0] += random.uniform(-6, 6) * delta

            # Recycle particle when it falls below the bottom of the viewport
            if particle[1] > self.player.world_y + WINDOW_HEIGHT:
                # Respawn at a random X near the player, above the top of the screen
                particle[0] = self.player.world_x + random.randint(-WINDOW_WIDTH, WINDOW_WIDTH)
                particle[1] = self.player.world_y - random.randint(WINDOW_HEIGHT, WINDOW_HEIGHT + 300)

    def _draw_atmosphere_overlay(self):
        """Draw post-process atmosphere effects over the game scene.

        Three layers are composited in order:
        1. A semi-transparent red tint to give a menacing Upside-Down feel.
        2. Floating white ash / spore particles (drawn only if on-screen).
        3. A brief blue-white lightning flash when triggered.
        """
        # --- Layer 1: faint red tint over whole screen ---
        red_overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        red_overlay.fill((60, 0, 0, 25))   # Alpha 25 keeps the tint very subtle
        self.screen.blit(red_overlay, (0, 0))

        # --- Layer 2: white floating ash / spores ---
        for x, y, speed, size, alpha in self.ash_particles:
            # Convert each particle's world position to screen position
            screen_x = x - self.player.world_x + WINDOW_WIDTH // 2
            screen_y = y - self.player.world_y + WINDOW_HEIGHT // 2

            # Skip particles that are outside the visible window (off-screen cull)
            if -20 <= screen_x <= WINDOW_WIDTH + 20 and -20 <= screen_y <= WINDOW_HEIGHT + 20:
                # Draw each spore as a small filled circle with its own alpha
                particle_surf = pygame.Surface((size * 2 + 2, size * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    particle_surf,
                    (230, 230, 230, alpha),   # Off-white with variable transparency
                    (size + 1, size + 1),     # Centre within the small surface
                    size                      # Radius in pixels
                )
                self.screen.blit(particle_surf, (screen_x, screen_y))

        # --- Layer 3: lightning flash ---
        if self.lightning_flash_time > 0:
            flash = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            flash.fill((235, 235, 255, 75))   # Blue-tinted white, semi-transparent
            self.screen.blit(flash, (0, 0))

    def _play_music(self, music_file):
        """Load and loop a music track, skipping if it is already playing.

        Avoids restarting the same track by comparing the requested file path
        with the currently loaded one.

        Args:
            music_file (str): Absolute path to the music file to play.
        """
        if self.current_music != music_file or not pygame.mixer.music.get_busy():
            pygame.mixer.music.load(music_file)
            pygame.mixer.music.set_volume(0.35)
            pygame.mixer.music.play(-1)   # -1 = loop indefinitely
            self.current_music = music_file

    def _setup_wave(self):
        """Configure spawn parameters for the current wave number.

        Resets the spawn counter and sets wave-specific values for:
        - ``enemies_to_spawn``: total enemies in the wave.
        - ``enemy_spawn_delay``: seconds between spawns (decreases each wave).
        - ``current_enemy_health``: hit points each enemy starts with.

        Wave 4 sets enemy counts to zero because it uses the boss instead.
        """
        self.enemies_spawned = 0
        self.wave_in_progress = True

        if self.wave == 1:
            # Wave 1 — gentle introduction: few weak enemies, slow spawn rate
            self.enemies_to_spawn = 5
            self.enemy_spawn_delay = 1.2
            self.current_enemy_health = 60

        elif self.wave == 2:
            # Wave 2 — moderate difficulty: more enemies with slightly more HP
            self.enemies_to_spawn = 8
            self.enemy_spawn_delay = 0.9
            self.current_enemy_health = 90

        elif self.wave == 3:
            # Wave 3 — hardest regular wave: many tanky enemies, fast spawns
            self.enemies_to_spawn = 12
            self.enemy_spawn_delay = 0.7
            self.current_enemy_health = 120

        elif self.wave == 4:
            # Wave 4 — boss fight: no regular enemies; boss is spawned separately
            self.enemies_to_spawn = 0
            self.enemy_spawn_delay = 999   # Effectively disabled
            self.current_enemy_health = 0

    def _reset_game(self):
        """Reset all game state to start a fresh run from wave 1.

        Called when the player presses Play from the menu or Play Again after
        game over / victory.  Re-creates the player, clears all sprite groups,
        and re-initialises wave variables and power-up timers.
        """
        # Reset score and re-create the player sprite
        self.score = 0
        self.player = Player()
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.player)

        # Clear all in-flight objects from the previous run
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()

        self.enemy_spawn_timer = 0

        # Reset wave state back to the beginning
        self.wave = 1
        self.wave_in_progress = True
        self.enemies_spawned = 0
        self.enemies_to_spawn = 5
        self.current_enemy_health = 60

        # Clear boss state
        self.boss = None
        self.boss_lasers = pygame.sprite.Group()
        self.boss_spawned = False

        # Clear dropped power-ups
        self.powerups = pygame.sprite.Group()

        # Reset active boost timers (no boosts active at start)
        self.damage_boost_timer = 0
        self.speed_boost_timer = 0

        # Reset effective stats to base constants
        self.current_bullet_damage = DAMAGE
        self.current_player_speed = PLAYER_SPEED

        # Ensure player speed matches base (in case a boost was active)
        self.player.speed = PLAYER_SPEED

        # Apply wave 1 configuration
        self._setup_wave()

    def _handle_events(self):
        """Process all queued Pygame events for the current frame.

        Handles window-close events, and routes left mouse-button clicks to
        the appropriate UI button handler based on the current game state.
        In the "playing" state, clicks outside the pause button fire a bullet.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()

                if self.state == "menu":
                    if self.play_button.collidepoint(mouse_pos):
                        self.menu_click_sound.play()
                        self._reset_game()
                        self.state = "playing"

                    elif self.settings_button.collidepoint(mouse_pos):
                        self.menu_click_sound.play()
                        self.previous_state = "menu"   # So Back returns to the menu
                        self.state = "settings"

                elif self.state == "settings":
                    if self.back_button.collidepoint(mouse_pos):
                        self.menu_click_sound.play()
                        # Return to wherever the player came from (menu or pause)
                        self.state = self.previous_state

                    elif self.res_1920_button.collidepoint(mouse_pos):
                        self.menu_click_sound.play()
                        self._change_resolution(1920, 1080)

                    elif self.res_1280_button.collidepoint(mouse_pos):
                        self.menu_click_sound.play()
                        self._change_resolution(1280, 720)

                    elif self.res_800_button.collidepoint(mouse_pos):
                        self.menu_click_sound.play()
                        self._change_resolution(800, 600)

                elif self.state == "playing":
                    if self.pause_button.collidepoint(mouse_pos):
                        self.menu_click_sound.play()
                        self.state = "paused"
                    else:
                        # Any click outside the pause button fires a bullet
                        self._shoot()

                elif self.state == "paused":
                    if self.continue_button.collidepoint(mouse_pos):
                        self.menu_click_sound.play()
                        self.state = "playing"
                    elif self.pause_settings_button.collidepoint(mouse_pos):
                        self.menu_click_sound.play()
                        self.previous_state = "paused"   # Back returns to pause screen
                        self.state = "settings"
                    elif self.quit_menu_button.collidepoint(mouse_pos):
                        self.menu_click_sound.play()
                        self.state = "menu"
                        self._play_music(get_asset_path("sounds/final_boss_main_menu.mp3"))

                elif self.state == "game_over":
                    if self.play_again_button.collidepoint(mouse_pos):
                        self.menu_click_sound.play()
                        self._reset_game()
                        self.state = "playing"
                    elif self.game_over_menu_button.collidepoint(mouse_pos):
                        self.menu_click_sound.play()
                        self.state = "menu"
                        self._play_music(get_asset_path("sounds/final_boss_main_menu.mp3"))

                elif self.state == "victory":
                    if self.play_again_button.collidepoint(mouse_pos):
                        self.menu_click_sound.play()
                        self._reset_game()
                        self.state = "playing"
                    elif self.game_over_menu_button.collidepoint(mouse_pos):
                        self.menu_click_sound.play()
                        self.state = "menu"
                        self._play_music(get_asset_path("sounds/final_boss_main_menu.mp3"))

    def _change_resolution(self, width, height):
        """Resize the display window and reposition all UI button rects.

        Updates the global ``WINDOW_WIDTH`` / ``WINDOW_HEIGHT`` constants so
        that the coordinate conversion formula used throughout the game adapts
        to the new dimensions, then re-creates every button rect centred on
        the new window size.

        Args:
            width (int): New window width in pixels.
            height (int): New window height in pixels.
        """
        global WINDOW_WIDTH, WINDOW_HEIGHT

        WINDOW_WIDTH = width
        WINDOW_HEIGHT = height

        # Recreate the display surface at the new resolution
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

        # Recentre all button rects for the main menu and pause screen
        self.play_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 400, 200, 60)
        self.settings_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 500, 200, 60)

        self.continue_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 350, 200, 60)
        self.pause_settings_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 450, 200, 60)
        self.quit_menu_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 550, 200, 60)

        # Post-game screen buttons
        self.play_again_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 450, 200, 60)
        self.game_over_menu_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 550, 200, 60)

        # Settings screen buttons
        self.res_1920_button = pygame.Rect(WINDOW_WIDTH // 2 - 150, 320, 300, 50)
        self.res_1280_button = pygame.Rect(WINDOW_WIDTH // 2 - 150, 390, 300, 50)
        self.res_800_button = pygame.Rect(WINDOW_WIDTH // 2 - 150, 460, 300, 50)

        # Pause button (top-centre of the screen during gameplay)
        self.pause_button = pygame.Rect(WINDOW_WIDTH // 2 - 25, 20, 50, 50)

    def _update(self, delta):
        """Advance all game logic by one frame.

        Only runs when ``state == "playing"``.  Processes (in order):
        1. Atmospheric overlay effects (lightning, particles).
        2. Music switching based on the current wave.
        3. Player movement and footstep sounds.
        4. Bullet physics.
        5. Enemy AI movement.
        6. Bullet–enemy collision detection and power-up drops.
        7. Player–power-up proximity pickup and timed boost countdowns.
        8. Bullet–boss collision detection.
        9. Player–enemy contact damage.
        10. Boss laser physics and player collision.
        11. Enemy wave spawning and wave-completion checks.
        12. Boss spawn, AI, and laser firing (wave 4).
        13. Boss melee damage (continuous while touching the player).
        14. Game-state transition sound effects.

        Args:
            delta (float): Elapsed time since the last frame in seconds.
        """
        # Early-out: nothing to update if not actively playing
        if self.state != "playing":
            return
        self._update_overlay_effects(delta)

        # --- Music: switch track when the boss wave begins ---
        if self.state == "playing":
            if self.wave == 4:
                # Re-use the main menu track as the boss battle theme
                self._play_music(get_asset_path("sounds/final_boss_main_menu.mp3"))
            else:
                self._play_music(get_asset_path("sounds/ingame_background.mp3"))

        # --- Player movement and footstep audio ---
        moving = self.player.update(delta)
        if moving:
            # Count down toward the next footstep sound
            self.footstep_timer -= delta
            if self.footstep_timer <= 0:
                self.footstep_sound.play()
                # Reset the timer so the next step plays after the delay
                self.footstep_timer = self.footstep_delay
        else:
            # Reset immediately when the player stops so the next move
            # plays a step right away (no silent gap at movement start)
            self.footstep_timer = 0

        # --- Advance all bullet positions ---
        self.bullets.update(delta)

        # --- Chase the player for every active enemy ---
        for enemy in self.enemies:
            enemy.update(delta, self.player.world_x, self.player.world_y)

        # --- Bullet vs. enemy collision (world-space circle check) ---
        for bullet in self.bullets.copy():
            for enemy in self.enemies.copy():
                # Euclidean distance between bullet and enemy world centres
                dx = bullet.world_x - enemy.world_x
                dy = bullet.world_y - enemy.world_y
                distance = math.sqrt(dx * dx + dy * dy)

                # 50-unit radius is the combined hit threshold for this size of sprite
                if distance < 50:
                    enemy.health -= bullet.damage
                    bullet.kill()   # One bullet can only hit one enemy

                    if enemy.health <= 0:
                        # Store drop position before removing the enemy
                        drop_x = enemy.world_x
                        drop_y = enemy.world_y

                        enemy.kill()
                        self.score += 1
                        self.enemy_death_sound.play()

                        # Roll to see if this enemy drops a power-up
                        if random.random() < POWERUP_DROP_CHANCE:
                            # "health" appears twice in the list to make it
                            # twice as likely to drop as damage or speed
                            power_type = random.choice(["health", "health", "damage", "speed"])
                            powerup = PowerUp(drop_x, drop_y, power_type)
                            self.powerups.add(powerup)
                    break   # Bullet is already dead; stop checking other enemies

        # --- Player vs. power-up pickup (world-space proximity check) ---
        for powerup in self.powerups.copy():
            dx = powerup.world_x - self.player.world_x
            dy = powerup.world_y - self.player.world_y
            distance = math.sqrt(dx * dx + dy * dy)

            # Collect the power-up when the player walks within 50 world-units
            if distance < 50:
                if powerup.power_type == "health":
                    # Instant heal — clamp to max health so the bar never overfills
                    self.player.health = min(self.player.max_health, self.player.health + HEALTH_PACK_AMOUNT)

                elif powerup.power_type == "damage":
                    # Temporarily increase bullet damage and start the countdown
                    self.current_bullet_damage = DAMAGE + DAMAGE_BOOST_AMOUNT
                    self.damage_boost_timer = DAMAGE_BOOST_DURATION

                elif powerup.power_type == "speed":
                    # Temporarily increase player move speed and start the countdown
                    self.player.speed = PLAYER_SPEED + SPEED_BOOST_AMOUNT
                    self.speed_boost_timer = SPEED_BOOST_DURATION

                powerup.kill()   # Remove the pickup from the world

        # --- Damage boost countdown ---
        if self.damage_boost_timer > 0:
            self.damage_boost_timer -= delta
            if self.damage_boost_timer <= 0:
                # Boost has expired — revert bullet damage to base value
                self.current_bullet_damage = DAMAGE

        # --- Speed boost countdown ---
        if self.speed_boost_timer > 0:
            self.speed_boost_timer -= delta
            if self.speed_boost_timer <= 0:
                # Boost has expired — revert player speed to base value
                self.player.speed = PLAYER_SPEED

        # --- Bullet vs. boss collision (larger hit threshold for boss size) ---
        if self.boss is not None:
            for bullet in self.bullets.copy():
                dx = bullet.world_x - self.boss.world_x
                dy = bullet.world_y - self.boss.world_y
                distance = math.sqrt(dx * dx + dy * dy)

                if distance < 120:   # bigger hitbox for boss
                    self.boss.health -= bullet.damage
                    bullet.kill()

                    if self.boss.health <= 0:
                        # Boss is dead — trigger victory
                        self.boss = None
                        self.state = "victory"

                    break   # Bullet consumed; stop checking

        # --- Player vs. enemy melee contact ---
        for enemy in self.enemies.copy():
            dx = enemy.world_x - self.player.world_x
            dy = enemy.world_y - self.player.world_y
            distance = math.sqrt(dx * dx + dy * dy)

            # If the enemy overlaps the player, deal fixed damage and remove it
            if distance < 60:
                self.player.health -= 20
                enemy.kill()   # Enemy is consumed on contact (one-hit melee)
                self.player_hurt_sound.play()

                if self.player.health <= 0:
                    self.state = "game_over"

        # --- Boss laser projectile movement ---
        self.boss_lasers.update(delta)

        # --- Boss laser vs. player collision ---
        for laser in self.boss_lasers.copy():
            dx = laser.world_x - self.player.world_x
            dy = laser.world_y - self.player.world_y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance < 50:
                self.player.health -= laser.damage
                laser.kill()   # Laser is consumed on hit
                self.player_hurt_sound.play()

                if self.player.health <= 0:
                    self.state = "game_over"

        # --- Regular enemy wave: spawn enemies one at a time on a timer ---
        if self.wave_in_progress and self.wave <= 3 and self.enemies_spawned < self.enemies_to_spawn:
            self.enemy_spawn_timer += delta
            if self.enemy_spawn_timer >= self.enemy_spawn_delay:
                self._spawn_enemy()
                self.enemy_spawn_timer = 0   # Reset so the next spawn waits the full delay

        # --- Wave 4: boss fight ---
        if self.wave == 4:
            if not self.boss_spawned:
                # Spawn the boss exactly once
                self._spawn_boss()

            if self.boss is not None:
                # Let the boss chase and accumulate its laser cooldown
                self.boss.update(delta, self.player.world_x, self.player.world_y)

                # Fire a laser whenever the cooldown has elapsed
                if self.boss.can_shoot():
                    self._boss_shoot()
                    self.boss.reset_laser_timer()

        # --- Wave progression: advance to the next wave when all enemies are cleared ---
        if self.wave_in_progress:
            # Condition: all enemies for this wave have been spawned AND none remain alive
            if self.wave <= 3 and self.enemies_spawned >= self.enemies_to_spawn and len(self.enemies) == 0:
                self.wave += 1   # Advance to the next wave number

                # Configure the new wave (wave 4 sets boss parameters)
                if self.wave <= 4:
                    self._setup_wave()

        # --- Boss continuous melee damage (scales with delta for frame-rate independence) ---
        if self.boss is not None:
            dx = self.boss.world_x - self.player.world_x
            dy = self.boss.world_y - self.player.world_y
            distance = math.sqrt(dx * dx + dy * dy)

            # Within 100 world-units the boss continuously drains HP
            if distance < 100:
                self.player.health -= BOSS_DAMAGE * delta   # Per-second damage × frame time

                if self.player.health <= 0:
                    self.state = "game_over"

        # --- State transition sound effects ---
        # Runs only on the frame that the state changes
        if self.state != self.last_state:
            if self.state == "game_over":
                pygame.mixer.music.stop()
                self.current_music = None
                self.game_over_sound.play()

            elif self.state == "victory":
                pygame.mixer.music.stop()
                self.current_music = None
                pygame.mixer.stop()  # Clear all active sound channels so the fanfare gets one
                self.victory_sound.play()

            elif self.state == "menu":
                self._play_music(get_asset_path("sounds/final_boss_main_menu.mp3"))

            # Update last_state so this block only fires once per transition
            self.last_state = self.state

    def _draw_wave(self):
        """Render the current wave number in the top-left corner of the screen."""
        wave_text = self.font.render(f"Wave: {self.wave}", True, WHITE)
        self.screen.blit(wave_text, (20, 70))

    def _draw_pause_button(self):
        """Draw a standard two-bar pause icon centred in the pause button rect."""
        pygame.draw.rect(self.screen, DARK_BLUE, self.pause_button)

        # Dimensions and spacing of the two vertical bars
        bar_width = 8
        bar_height = 24
        gap = 8   # Horizontal space between the two bars

        # Top-left origin of the first (left) bar, inset from the button edge
        x = self.pause_button.x + 12
        y = self.pause_button.y + 13

        # Left bar
        pygame.draw.rect(self.screen, WHITE, (x, y, bar_width, bar_height))
        # Right bar — offset by bar_width + gap from the left bar
        pygame.draw.rect(self.screen, WHITE, (x + bar_width + gap, y, bar_width, bar_height))

    def _draw_paused(self):
        """Draw the pause overlay on top of the frozen game scene.

        Renders the game world first (so it is visible behind the overlay),
        then draws a semi-transparent black overlay and the pause menu buttons.
        """
        # Show the game world dimly behind the pause menu
        self._draw_game()

        # Semi-transparent dark overlay to de-emphasise the background
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))   # Black at ~70% opacity
        self.screen.blit(overlay, (0, 0))

        title_font = pygame.font.SysFont(None, 90)
        button_font = pygame.font.SysFont(None, 45)

        title_text = title_font.render("Paused", True, WHITE)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 220))
        self.screen.blit(title_text, title_rect)

        # Draw pause menu buttons
        pygame.draw.rect(self.screen, DARK_BLUE, self.continue_button)
        pygame.draw.rect(self.screen, DARK_BLUE, self.pause_settings_button)
        pygame.draw.rect(self.screen, DARK_BLUE, self.quit_menu_button)

        continue_text = button_font.render("Continue", True, WHITE)
        settings_text = button_font.render("Settings", True, WHITE)
        quit_text = button_font.render("Main Menu", True, WHITE)

        # Centre each label within its button rectangle
        self.screen.blit(continue_text, continue_text.get_rect(center=self.continue_button.center))
        self.screen.blit(settings_text, settings_text.get_rect(center=self.pause_settings_button.center))
        self.screen.blit(quit_text, quit_text.get_rect(center=self.quit_menu_button.center))

    def _draw_player_health(self):
        """Draw the player health bar in the top-right corner of the screen.

        The bar is a full-width red background with a green foreground scaled
        by the player's current health fraction, bordered in white.
        """
        bar_width = 300
        bar_height = 20

        # health_ratio is 0.0 (empty) to 1.0 (full)
        health_ratio = self.player.health / self.player.max_health

        # Anchor to the right edge of the screen with a 20px margin
        bar_x = WINDOW_WIDTH - bar_width - 20
        bar_y = 20

        # Red background (represents total missing health)
        pygame.draw.rect(self.screen, RED, (bar_x, bar_y, bar_width, bar_height))
        # Green foreground (represents remaining health)
        pygame.draw.rect(
            self.screen,
            GREEN,
            (bar_x, bar_y, int(bar_width * health_ratio), bar_height)
        )
        # White outline for visibility against any background
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)

    def _draw_score(self):
        """Render the player's kill score in the top-left corner."""
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (20, 20))

    def _draw_grid(self):
        """Draw a faint grid that scrolls with the camera to convey world movement.

        The grid is aligned to 100-unit world-space cells.  The offset is
        computed using modulo arithmetic so the lines tile seamlessly as the
        player moves, creating the illusion of infinite scrolling ground.
        """
        grid_size = 100   # World-units between grid lines

        # Compute the sub-cell screen offset so lines appear to slide smoothly.
        # Negating the modulo aligns the first visible line to the left/top edge.
        start_x = - (self.player.world_x % grid_size)
        start_y = - (self.player.world_y % grid_size)

        # Draw vertical lines across the full window height
        for x in range(int(start_x), WINDOW_WIDTH, grid_size):
            pygame.draw.line(self.screen, DARK_BLUE, (x, 0), (x, WINDOW_HEIGHT))

        # Draw horizontal lines across the full window width
        for y in range(int(start_y), WINDOW_HEIGHT, grid_size):
            pygame.draw.line(self.screen, DARK_BLUE, (0, y), (WINDOW_WIDTH, y))

    def _draw_gun(self):
        """Draw the gun sprite rotated to aim toward the mouse cursor.

        The gun is always rendered at the player's screen-centre position,
        offset slightly in the direction of the cursor so it appears to
        extend from the player's hand.

        Angle and flip logic:
            ``math.atan2(dy, dx)`` returns an angle in radians where 0 points
            right and positive values rotate clockwise (screen-space Y is
            inverted vs. maths convention).

            ``pygame.transform.rotate`` uses counter-clockwise degrees, so
            the sign must be negated: ``angle_degrees = -math.degrees(angle)``
            points the sprite in the correct direction when facing right.

            When the cursor is to the left (``dx < 0``), the sprite is
            horizontally flipped first, then its angle adjusted by +180° to
            compensate for the flip so the barrel still points at the cursor.
        """
        # The player is always at the screen centre
        center_x = WINDOW_WIDTH // 2
        center_y = WINDOW_HEIGHT // 2
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # Direction vector from player screen position to the mouse cursor
        dx = mouse_x - center_x
        dy = mouse_y - center_y

        # Compute the aim angle in radians
        # atan2 returns values in [-π, π]; 0 = right, π/2 = down (screen coords)
        angle = math.atan2(dy, dx)

        # Convert to degrees for pygame.transform.rotate (which uses CCW degrees)
        # Negate because screen Y increases downward, opposite to maths convention
        angle_degrees = -math.degrees(angle)

        facing_right = dx > 0

        gun_to_draw = self.gun_image

        if facing_right:
            # Flip the gun sprite horizontally so it points to the right by default
            gun_to_draw = pygame.transform.flip(self.gun_image, True, False)
        else:
            # When aiming left the sprite is NOT flipped, but the angle must be
            # rotated 180° so the barrel still faces the cursor after the base
            # "right-facing" sprite is used unflipped
            angle_degrees = -math.degrees(angle) + 180

        # Rotate the chosen sprite to align with the aim direction
        rotated_gun = pygame.transform.rotate(gun_to_draw, angle_degrees)

        # Place the gun a fixed pixel distance from the player centre along the aim vector
        gun_distance = 28   # Pixels from player centre to gun centre
        gun_x = center_x + math.cos(angle) * gun_distance
        gun_y = center_y + math.sin(angle) * gun_distance

        gun_rect = rotated_gun.get_rect(center=(gun_x, gun_y))
        self.screen.blit(rotated_gun, gun_rect)

    def _shoot(self):
        """Create a bullet aimed from the player toward the mouse cursor.

        The bullet spawns at the player's world position offset slightly in
        the aim direction (so it clears the player sprite) and inherits the
        current effective bullet damage (which may be boosted).
        """
        # Player is always rendered at the screen centre
        center_x = WINDOW_WIDTH // 2
        center_y = WINDOW_HEIGHT // 2
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # Direction vector from player to mouse in screen space
        dx = mouse_x - center_x
        dy = mouse_y - center_y
        # Convert to a travel angle in radians
        angle = math.atan2(dy, dx)

        # Offset the spawn point 40 world-units along the aim direction
        # so the bullet doesn't collide with the player immediately
        gun_distance = 40
        bullet_x = self.player.world_x + math.cos(angle) * gun_distance
        bullet_y = self.player.world_y + math.sin(angle) * gun_distance

        # Use current_bullet_damage (may be boosted above base DAMAGE)
        bullet = Bullet(bullet_x, bullet_y, angle, self.current_bullet_damage)
        self.bullets.add(bullet)
        self.shoot_sound.play()

    def _spawn_enemy(self):
        """Spawn a single enemy just outside the visible screen boundary.

        Picks a random screen edge (top/bottom/left/right) and places the
        enemy 200 world-units beyond the corresponding viewport edge so it
        is never visible at the moment of creation.

        The spawn position is relative to the player's current world
        position so enemies always appear off-screen regardless of where
        the player has moved.
        """
        side = random.choice(["top", "bottom", "left", "right"])
        margin = 200   # Extra buffer beyond the viewport edge in world-units

        if side == "top":
            x = random.randint(-WINDOW_WIDTH, WINDOW_WIDTH)
            # Place above the top edge of the current viewport
            y = self.player.world_y - WINDOW_HEIGHT // 2 - margin
        elif side == "bottom":
            x = random.randint(-WINDOW_WIDTH, WINDOW_WIDTH)
            # Place below the bottom edge of the current viewport
            y = self.player.world_y + WINDOW_HEIGHT // 2 + margin
        elif side == "left":
            # Place to the left of the left edge of the current viewport
            x = self.player.world_x - WINDOW_WIDTH // 2 - margin
            y = random.randint(-WINDOW_HEIGHT, WINDOW_HEIGHT)
        else:
            # Place to the right of the right edge of the current viewport
            x = self.player.world_x + WINDOW_WIDTH // 2 + margin
            y = random.randint(-WINDOW_HEIGHT, WINDOW_HEIGHT)

        enemy = Enemy(x, y, self.current_enemy_health)
        self.enemies.add(enemy)
        self.enemies_spawned += 1   # Track how many have been created this wave

    def _spawn_boss(self):
        """Spawn the boss centred above the player's current position.

        The boss appears 300 world-units above the top of the viewport
        (off-screen) and immediately begins chasing the player.
        The ``boss_spawned`` flag is set to prevent a second spawn.
        """
        # Position the boss directly above the player, just off the top of the screen
        boss_x = self.player.world_x
        boss_y = self.player.world_y - WINDOW_HEIGHT // 2 - 300

        self.boss = Boss(boss_x, boss_y)
        self.boss_spawned = True

    def _boss_shoot(self):
        """Fire a laser from the boss directly toward the player's world position.

        Computes the angle from the boss to the player using ``atan2``, then
        spawns a ``BossLaser`` offset 40 world-units along that angle so the
        projectile clears the boss sprite on creation.
        """
        if self.boss is None:
            return   # Safety guard — should not be called when boss is dead

        # Direction vector from boss to player
        dx = self.player.world_x - self.boss.world_x
        dy = self.player.world_y - self.boss.world_y
        # Travel angle in radians: 0 = right, positive = clockwise (screen space)
        angle = math.atan2(dy, dx)

        # Offset the laser's spawn point so it doesn't overlap the boss sprite
        laser_x = self.boss.world_x + math.cos(angle) * 40
        laser_y = self.boss.world_y + math.sin(angle) * 40

        laser = BossLaser(laser_x, laser_y, angle)
        self.boss_lasers.add(laser)
        self.laser_sound.play()

    def _draw_powerup_status(self):
        """Display active power-up timers as countdown text in the top-left HUD.

        Shows one line per active timed boost, each with the remaining
        seconds formatted to one decimal place.  Lines stack vertically,
        starting at y=110 (below the score and wave counters).
        """
        y = 110   # Starting Y position; shifts down for each active boost line

        if self.damage_boost_timer > 0:
            text = self.font.render(f"Damage Boost: {self.damage_boost_timer:.1f}s", True, WHITE)
            self.screen.blit(text, (20, y))
            y += 35   # Move down for the next line

        if self.speed_boost_timer > 0:
            text = self.font.render(f"Speed Boost: {self.speed_boost_timer:.1f}s", True, WHITE)
            self.screen.blit(text, (20, y))

    def _draw_menu(self):
        """Render the main menu screen with the game title and Play/Settings buttons."""
        title_font = pygame.font.SysFont(None, 100)
        button_font = pygame.font.SysFont(None, 50)

        title_text = title_font.render("Demogorgon Hunter", True, WHITE)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 200))
        self.screen.blit(title_text, title_rect)

        pygame.draw.rect(self.screen, DARK_BLUE, self.play_button)
        pygame.draw.rect(self.screen, DARK_BLUE, self.settings_button)

        play_text = button_font.render("Play", True, WHITE)
        settings_text = button_font.render("Settings", True, WHITE)

        # Centre each label within its button rectangle
        play_rect = play_text.get_rect(center=self.play_button.center)
        settings_rect = settings_text.get_rect(center=self.settings_button.center)

        self.screen.blit(play_text, play_rect)
        self.screen.blit(settings_text, settings_rect)

    def _draw_settings(self):
        """Render the settings screen with resolution selection buttons and a Back button."""
        title_font = pygame.font.SysFont(None, 80)
        button_font = pygame.font.SysFont(None, 40)

        title_text = title_font.render("Settings", True, WHITE)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 180))
        self.screen.blit(title_text, title_rect)

        res_text = button_font.render("Resolution", True, WHITE)
        res_rect = res_text.get_rect(center=(WINDOW_WIDTH // 2, 260))
        self.screen.blit(res_text, res_rect)

        # Draw all three resolution option buttons and the back button
        pygame.draw.rect(self.screen, DARK_BLUE, self.res_1920_button)
        pygame.draw.rect(self.screen, DARK_BLUE, self.res_1280_button)
        pygame.draw.rect(self.screen, DARK_BLUE, self.res_800_button)
        pygame.draw.rect(self.screen, DARK_BLUE, self.back_button)

        text_1920 = button_font.render("1920 x 1080", True, WHITE)
        text_1280 = button_font.render("1280 x 720", True, WHITE)
        text_800 = button_font.render("800 x 600", True, WHITE)
        back_text = button_font.render("Back", True, WHITE)

        # Centre each label within its corresponding button
        self.screen.blit(text_1920, text_1920.get_rect(center=self.res_1920_button.center))
        self.screen.blit(text_1280, text_1280.get_rect(center=self.res_1280_button.center))
        self.screen.blit(text_800, text_800.get_rect(center=self.res_800_button.center))
        self.screen.blit(back_text, back_text.get_rect(center=self.back_button.center))

    def _draw_victory(self):
        """Render the victory screen with a You Win message and post-game buttons."""
        title_font = pygame.font.SysFont(None, 100)
        button_font = pygame.font.SysFont(None, 45)

        text = title_font.render("You Win!", True, GREEN)
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, 250))
        self.screen.blit(text, text_rect)

        pygame.draw.rect(self.screen, DARK_BLUE, self.play_again_button)
        pygame.draw.rect(self.screen, DARK_BLUE, self.game_over_menu_button)

        play_again_text = button_font.render("Play Again", True, WHITE)
        menu_text = button_font.render("Main Menu", True, WHITE)

        self.screen.blit(play_again_text, play_again_text.get_rect(center=self.play_again_button.center))
        self.screen.blit(menu_text, menu_text.get_rect(center=self.game_over_menu_button.center))

    def _draw_game_over(self):
        """Render the game-over screen with a Game Over message and post-game buttons."""
        title_font = pygame.font.SysFont(None, 100)
        button_font = pygame.font.SysFont(None, 45)

        text = title_font.render("Game Over", True, RED)
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, 250))
        self.screen.blit(text, text_rect)

        pygame.draw.rect(self.screen, DARK_BLUE, self.play_again_button)
        pygame.draw.rect(self.screen, DARK_BLUE, self.game_over_menu_button)

        play_again_text = button_font.render("Play Again", True, WHITE)
        menu_text = button_font.render("Main Menu", True, WHITE)

        self.screen.blit(play_again_text, play_again_text.get_rect(center=self.play_again_button.center))
        self.screen.blit(menu_text, menu_text.get_rect(center=self.game_over_menu_button.center))

    def _draw(self):
        """Clear the screen and delegate rendering to the active state's draw method.

        Acts as the top-level draw dispatcher: fills the background black,
        calls the correct ``_draw_*`` method based on ``self.state``, and
        finally flips the display buffer to show the completed frame.
        """
        self.screen.fill(BLACK)   # Clear previous frame

        if self.state == "menu":
            self._draw_menu()

        elif self.state == "settings":
            self._draw_settings()

        elif self.state == "playing":
            self._draw_game()

        elif self.state == "paused":
            self._draw_paused()

        elif self.state == "game_over":
            self._draw_game_over()

        elif self.state == "victory":
            self._draw_victory()

        # Present the completed frame to the monitor
        pygame.display.flip()

    def _draw_game(self):
        """Render the full in-game scene for the current frame.

        Draw order (back to front):
        1. Scrolling background.
        2. Player sprite (via all_sprites group).
        3. Gun sprite rotated toward the mouse.
        4. Player bullets.
        5. Boss sprite and health bar (if alive).
        6. Boss laser projectiles.
        7. Enemy sprites and health bars.
        8. Power-up pickups.
        9. Active power-up HUD timers.
        10. Atmosphere overlay (red tint, particles, lightning flash).
        11. Wave counter, player health bar, score, and pause button.
        """
        # Background layer (tiles/scrolls with the camera)
        self.bg.draw(self.screen, self.player.world_x, self.player.world_y)

        # Player sprite (always at screen centre)
        self.all_sprites.draw(self.screen)
        # Gun drawn over the player sprite, aimed at the mouse
        self._draw_gun()

        # Player bullets (use world-to-screen conversion inside draw())
        for bullet in self.bullets:
            bullet.draw(self.screen, self.player.world_x, self.player.world_y)

        # Boss and its health bar (only when boss is alive)
        if self.boss is not None:
            self.boss.draw(self.screen, self.player.world_x, self.player.world_y)
            self.boss.draw_health_bar(self.screen, self.player.world_x, self.player.world_y)

        # Boss laser projectiles
        for laser in self.boss_lasers:
            laser.draw(self.screen, self.player.world_x, self.player.world_y)

        # Enemies and their individual health bars
        for enemy in self.enemies:
            enemy.draw(self.screen, self.player.world_x, self.player.world_y)
            enemy.draw_health_bar(self.screen, self.player.world_x, self.player.world_y)

        # Power-up pickups lying on the ground
        for powerup in self.powerups:
            powerup.draw(self.screen, self.player.world_x, self.player.world_y)

        # HUD: boost countdown timers
        self._draw_powerup_status()

        # Post-process atmosphere effects drawn over the world
        self._draw_atmosphere_overlay()

        # HUD elements drawn last so they appear over everything
        self._draw_wave()
        self._draw_player_health()
        self._draw_score()
        self._draw_pause_button()

    def run(self):
        """Run the main game loop until the player closes the window.

        Each iteration:
        1. Compute ``delta`` (seconds since the last frame) from the clock.
        2. Process input events via ``_handle_events``.
        3. Advance game logic via ``_update``.
        4. Render the frame via ``_draw``.

        ``MAX_FPS`` caps the frame rate to prevent the CPU running at 100%.
        After the loop exits, ``pygame.quit()`` tears down all Pygame modules.
        """
        while self.running:
            # Limit to MAX_FPS and get elapsed milliseconds; convert to seconds
            delta = self.clock.tick(MAX_FPS) / 1000.0
            self._handle_events()
            self._update(delta)
            self._draw()

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
