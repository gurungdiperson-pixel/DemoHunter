import pygame, os, math, random
from upside_down_bg import UpsideDownBackground

GAME_PATH = os.path.dirname(os.path.abspath(__file__))

def get_asset_path(filename: str) -> str:
    """Returns the path to an asset file, given its filename."""
    return os.path.join(GAME_PATH, "assets", filename)

pygame.init()
pygame.mixer.init()

#Screen Dimension
GAME_TITTLE = "Demogorgan Hunter!"
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080
MAX_FPS = 60

#Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
DARK_BLUE = (0, 51, 102)
GREEN = (0, 255, 0)
DARK_RED = (80, 10, 10)
LIGHT_RED = (180, 40, 40)
PALE_RED = (120, 30, 30)

#Player constants
PLAYER_COLOR = YELLOW
PLAYER_WIDTH, PLAYER_HEIGHT = 90, 120
PLAYER_SPEED = 400
PLAYER_HEALTH = 100
PLAYER_MAX_HEALTH = 100

#Enemy constants 
ENEMY_SPEED = 300
ENEMY_WIDTH, ENEMY_HEIGHT = 90, 120
ENEMY_HEALTH = 100
ENEMY_MAX_HEALTH = 100

#Bullet traits
DAMAGE = 34
BULLET_SPEED = 800

# Boss constants
BOSS_WIDTH, BOSS_HEIGHT = 250, 250
BOSS_SPEED = 135
BOSS_HEALTH = 1500
BOSS_DAMAGE = 30
BOSS_LASER_SPEED = 900
BOSS_LASER_DAMAGE = 45
BOSS_LASER_COOLDOWN = 1.5

# Power-ups constants
POWERUP_WIDTH, POWERUP_HEIGHT = 40, 40
POWERUP_DROP_CHANCE = 0.35

HEALTH_PACK_AMOUNT = 25

DAMAGE_BOOST_AMOUNT = 20
DAMAGE_BOOST_DURATION = 5.0

SPEED_BOOST_AMOUNT = 150
SPEED_BOOST_DURATION = 5.0

#Sprite clasess
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.original_image = pygame.image.load(get_asset_path("sprites/player_transparant.png")).convert_alpha()
        self.original_image = pygame.transform.scale(self.original_image, (PLAYER_WIDTH, PLAYER_HEIGHT))

        
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)

        self.health = PLAYER_HEALTH
        self.max_health= PLAYER_MAX_HEALTH
        self.world_x = 0
        self.world_y = 0
        self.speed = PLAYER_SPEED

    def update(self, delta):
        keys = pygame.key.get_pressed()
        moving = False

        if keys[pygame.K_w]:
            self.world_y -= self.speed * delta
            moving = True
        if keys[pygame.K_s]:
            self.world_y += self.speed * delta
            moving = True
        if keys[pygame.K_a]:
            self.world_x -= self.speed * delta
            moving = True
        if keys[pygame.K_d]:
            self.world_x += self.speed * delta
            moving = True

        self.rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        center_x = WINDOW_WIDTH // 2
        mouse_x, mouse_y = pygame.mouse.get_pos()

        dx = mouse_x - center_x
        facing_left = dx < 0
        
        if facing_left:
            self.image = pygame.transform.flip(self.original_image, True, False)
        else:
            self.image = self.original_image

        return moving

class Bullet(pygame.sprite.Sprite):
    def __init__(self, world_x, world_y, angle, damage):
        super().__init__()
        self.image = pygame.Surface((6, 6), pygame.SRCALPHA)
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=(world_x, world_y))
        self.damage = damage
        self.world_x = world_x
        self.world_y = world_y
        self.angle = angle
        self.speed = BULLET_SPEED

    def update(self, delta):
        self.world_x += math.cos(self.angle) * self.speed * delta
        self.world_y += math.sin(self.angle) * self.speed * delta
        self.rect.center = (self.world_x, self.world_y)

    def draw(self, screen, player_world_x, player_world_y):
        screen_x = self.world_x - player_world_x + WINDOW_WIDTH // 2
        screen_y = self.world_y - player_world_y + WINDOW_HEIGHT // 2

        self.rect.center = (screen_x, screen_y)
        screen.blit(self.image, self.rect)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, health):
        super().__init__()
        self.image = pygame.image.load(get_asset_path("sprites/enemy.png")).convert_alpha()
        self.image = pygame.transform.scale(self.image, (ENEMY_WIDTH, ENEMY_HEIGHT))

        self.rect = self.image.get_rect()

        self.health = health
        self.max_health = health
        self.world_x = x
        self.world_y = y
        self.speed = ENEMY_SPEED

    def update(self, delta, player_world_x, player_world_y):
        dx = player_world_x - self.world_x
        dy = player_world_y - self.world_y

        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance != 0:
            dx /= distance
            dy /= distance

        self.world_x += dx * self.speed * delta
        self.world_y += dy * self.speed * delta

    def draw_health_bar(self, screen, player_world_x, player_world_y):
        screen_x = self.world_x - player_world_x + WINDOW_WIDTH // 2
        screen_y = self.world_y - player_world_y + WINDOW_HEIGHT // 2

        bar_width = 50
        bar_height = 6
        health_ratio = self.health / self.max_health

        bar_x = screen_x - bar_width // 2
        bar_y = screen_y - ENEMY_HEIGHT // 2 - 12

        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, int(bar_width * health_ratio), bar_height))

    def draw(self, screen, player_world_x, player_world_y):
        screen_x = self.world_x - player_world_x + WINDOW_WIDTH // 2
        screen_y = self.world_y - player_world_y + WINDOW_HEIGHT // 2

        self.rect.center = (screen_x, screen_y)
        screen.blit(self.image, self.rect)

class BossLaser(pygame.sprite.Sprite):
    def __init__(self, world_x, world_y, angle):
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
        self.world_x += math.cos(self.angle) * self.speed * delta
        self.world_y += math.sin(self.angle) * self.speed * delta

    def draw(self, screen, player_world_x, player_world_y):
        screen_x = self.world_x - player_world_x + WINDOW_WIDTH // 2
        screen_y = self.world_y - player_world_y + WINDOW_HEIGHT // 2

        rotated = pygame.transform.rotate(self.image, -math.degrees(self.angle))
        self.rect = rotated.get_rect(center=(screen_x, screen_y))
        screen.blit(rotated, self.rect)

class Boss(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()

        self.image = pygame.image.load(get_asset_path("sprites/mind_flayer_final.png")).convert_alpha()
        self.image = pygame.transform.scale(self.image, (BOSS_WIDTH, BOSS_HEIGHT))
        self.rect = self.image.get_rect()

        self.world_x = x
        self.world_y = y
        self.health = BOSS_HEALTH
        self.max_health = BOSS_HEALTH
        self.speed = BOSS_SPEED

        self.laser_timer = 0
        self.laser_cooldown = BOSS_LASER_COOLDOWN

    def update(self, delta, player_world_x, player_world_y):
        dx = player_world_x - self.world_x
        dy = player_world_y - self.world_y

        distance = math.sqrt(dx * dx + dy * dy)

        if distance != 0:
            dx /= distance
            dy /= distance

        self.world_x += dx * self.speed * delta
        self.world_y += dy * self.speed * delta

        self.laser_timer += delta

    def can_shoot(self):
        return self.laser_timer >= self.laser_cooldown
    
    def reset_laser_timer(self):
        self.laser_timer = 0

    def draw(self, screen, player_world_x, player_world_y):
        screen_x = self.world_x - player_world_x + WINDOW_WIDTH // 2
        screen_y = self.world_y - player_world_y + WINDOW_HEIGHT // 2

        self.rect.center = (screen_x, screen_y)
        screen.blit(self.image, self.rect)

    def draw_health_bar(self, screen, player_world_x, player_world_y):
        screen_x = self.world_x - player_world_x + WINDOW_WIDTH // 2
        screen_y = self.world_y - player_world_y + WINDOW_HEIGHT // 2

        bar_width = 180
        bar_height = 12
        health_ratio = self.health / self.max_health

        bar_x = screen_x - bar_width // 2
        bar_y = screen_y - BOSS_HEIGHT // 2 - 18

        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, int(bar_width * health_ratio), bar_height))
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, world_x, world_y, power_type):
        super().__init__()
        self.image = pygame.image.load(get_asset_path("sprites/star_no_bg.png")).convert_alpha()
        self.image = pygame.transform.scale(self.image, (POWERUP_WIDTH, POWERUP_HEIGHT))
        self.rect = self.image.get_rect()

        self.world_x = world_x
        self.world_y = world_y
        self.power_type = power_type

    def draw(self, screen, player_world_x, player_world_y):
        screen_x = self.world_x - player_world_x + WINDOW_WIDTH // 2
        screen_y = self.world_y - player_world_y + WINDOW_HEIGHT // 2

        self.rect.center = (screen_x, screen_y)
        screen.blit(self.image, self.rect)

class Game():
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

        self.bg = UpsideDownBackground(seed=42)

        self.lightning_timer = random.uniform(4, 8)
        self.lightning_flash_time = 0

        self.ash_particles = []
        for _ in range(120):
            self.ash_particles.append([
                random.randint(-2000, 2000),   # world x
                random.randint(-2000, 2000),   # world y
                random.uniform(10, 25),        # fall speed
                random.randint(1, 3),          # size
                random.randint(80, 180)        # alpha
            ])

        pygame.display.set_caption(GAME_TITTLE)
        self.state = "menu"
        self.previous_state = "menu"
        self.last_state = self.state

        # Sound effects
        self.shoot_sound = pygame.mixer.Sound(get_asset_path("sounds/gunshot.mp3"))
        self.footstep_sound = pygame.mixer.Sound(get_asset_path("sounds/footsteps.mp3"))
        self.laser_sound = pygame.mixer.Sound(get_asset_path("sounds/laser_sound.mp3"))
        self.enemy_death_sound = pygame.mixer.Sound(get_asset_path("sounds/enemy_death.mp3"))
        self.player_hurt_sound = pygame.mixer.Sound(get_asset_path("sounds/player_hurt.mp3"))
        self.game_over_sound = pygame.mixer.Sound(get_asset_path("sounds/game_over.mp3"))
        self.menu_click_sound = pygame.mixer.Sound(get_asset_path("sounds/menu_click.mp3"))
        self.victory_sound = pygame.mixer.Sound(get_asset_path("sounds/victory.mp3"))
        self.lightning_sound = pygame.mixer.Sound(get_asset_path("sounds/lightning.mp3"))

        # Volumes
        self.shoot_sound.set_volume(0.35)
        self.footstep_sound.set_volume(0.2)
        self.laser_sound.set_volume(0.35)
        self.enemy_death_sound.set_volume(0.35)
        self.player_hurt_sound.set_volume(0.4)
        self.game_over_sound.set_volume(0.4)
        self.menu_click_sound.set_volume(0.35)
        self.victory_sound.set_volume(0.45)
        self.lightning_sound.set_volume(0.3)

        # Footstep timing
        self.footstep_timer = 0
        self.footstep_delay = 0.35

        # Music state tracking
        self.current_music = None

        self.play_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 400, 200, 60)
        self.settings_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 500, 200, 60)
        self.back_button = pygame.Rect(50, 50, 150, 50)
        self.pause_button = pygame.Rect(WINDOW_WIDTH // 2 - 25, 20, 50, 50)
        self.continue_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 350, 200, 60)
        self.pause_settings_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 450, 200, 60)
        self.quit_menu_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 550, 200, 60)

        self.wave = 1
        self.wave_in_progress = True
        self.enemies_spawned = 0
        self.enemies_to_spawn = 5

        self.play_again_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 450, 200, 60)
        self.game_over_menu_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 550, 200, 60)

        self.res_1920_button = pygame.Rect(WINDOW_WIDTH // 2 - 150, 320, 300, 50)
        self.res_1280_button = pygame.Rect(WINDOW_WIDTH // 2 - 150, 390, 300, 50)
        self.res_800_button = pygame.Rect(WINDOW_WIDTH // 2 - 150, 460, 300, 50)
        
        self.running = True
        self.clock = pygame.time.Clock()
        self.score = 0
        self.font = pygame.font.SysFont(None, 48)
        self.all_sprites = pygame.sprite.Group()

        self.player = Player()
        self.all_sprites.add(self.player)

        self.enemies = pygame.sprite.Group()
        self.enemy_spawn_timer = 0
        self.enemy_spawn_delay = 1.0 #later on I will decrease this with stage or wave to make it harder. I will also introduce different types of enemies 

        self.bullets = pygame.sprite.Group()

        self.boss = None
        self.boss_lasers = pygame.sprite.Group()
        self.boss_spawned = False

        self.powerups = pygame.sprite.Group()

        self.damage_boost_timer = 0
        self.speed_boost_timer = 0

        self.current_bullet_damage = DAMAGE
        self.current_player_speed = PLAYER_SPEED

        self.gun_image = pygame.image.load(get_asset_path("sprites/gun.png")).convert_alpha()
        self.gun_image = pygame.transform.scale(self.gun_image, ((120, 40)))

        self._play_music(get_asset_path("sounds/final_boss_main_menu.mp3"))

    def _update_overlay_effects(self, delta):
        self.lightning_timer -= delta

        if self.lightning_timer <= 0:
            self.lightning_flash_time = 0.22
            self.lightning_timer = random.uniform(3, 6)
            self.lightning_sound.play()

        if self.lightning_flash_time > 0:
            self.lightning_flash_time -= delta

        for particle in self.ash_particles:
            particle[1] += particle[2] * delta
            particle[0] += random.uniform(-6, 6) * delta

            if particle[1] > self.player.world_y + WINDOW_HEIGHT:
                particle[0] = self.player.world_x + random.randint(-WINDOW_WIDTH, WINDOW_WIDTH)
                particle[1] = self.player.world_y - random.randint(WINDOW_HEIGHT, WINDOW_HEIGHT + 300)

    def _draw_atmosphere_overlay(self):
        # faint red tint over whole screen
        red_overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        red_overlay.fill((60, 0, 0, 25))
        self.screen.blit(red_overlay, (0, 0))


        # white floating ash / spores
        for x, y, speed, size, alpha in self.ash_particles:
            screen_x = x - self.player.world_x + WINDOW_WIDTH // 2
            screen_y = y - self.player.world_y + WINDOW_HEIGHT // 2

            if -20 <= screen_x <= WINDOW_WIDTH + 20 and -20 <= screen_y <= WINDOW_HEIGHT + 20:
                particle_surf = pygame.Surface((size * 2 + 2, size * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    particle_surf,
                    (230, 230, 230, alpha),
                    (size + 1, size + 1),
                    size
                )
                self.screen.blit(particle_surf, (screen_x, screen_y))

        # lightning flash
        if self.lightning_flash_time > 0:
            flash = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            flash.fill((235, 235, 255, 75))
            self.screen.blit(flash, (0, 0))

    def _play_music(self, music_file):
        if self.current_music != music_file:
            pygame.mixer.music.load(music_file)
            pygame.mixer.music.set_volume(0.35)
            pygame.mixer.music.play(-1)
            self.current_music = music_file

    def _setup_wave(self):
        self.enemies_spawned = 0
        self.wave_in_progress = True

        if self.wave == 1:
            self.enemies_to_spawn = 5
            self.enemy_spawn_delay = 1.2
            self.current_enemy_health = 60

        elif self.wave == 2:
            self.enemies_to_spawn = 8
            self.enemy_spawn_delay = 0.9
            self.current_enemy_health = 90

        elif self.wave == 3:
            self.enemies_to_spawn = 12
            self.enemy_spawn_delay = 0.7
            self.current_enemy_health = 120

        elif self.wave == 4:
            self.enemies_to_spawn = 0
            self.enemy_spawn_delay = 999
            self.current_enemy_health = 0

    def _reset_game(self):
        self.score = 0
        self.player = Player()
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.player)

        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()

        self.enemy_spawn_timer = 0
    
        self.wave = 1
        self.wave_in_progress = True
        self.enemies_spawned = 0
        self.enemies_to_spawn = 5
        self.current_enemy_health = 60

        self.boss = None
        self.boss_lasers = pygame.sprite.Group()
        self.boss_spawned = False

        self.powerups = pygame.sprite.Group()

        self.damage_boost_timer = 0
        self.speed_boost_timer = 0

        self.current_bullet_damage = DAMAGE
        self.current_player_speed = PLAYER_SPEED

        self.player.speed = PLAYER_SPEED

        self._setup_wave()


    def _handle_events(self):
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
                        self.previous_state = "menu"
                        self.state = "settings"

                elif self.state == "settings":
                    if self.back_button.collidepoint(mouse_pos):
                        self.menu_click_sound.play()
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
                        self._shoot()

                elif self.state == "paused":
                    if self.continue_button.collidepoint(mouse_pos):
                        self.menu_click_sound.play()
                        self.state = "playing"
                    elif self.pause_settings_button.collidepoint(mouse_pos):
                        self.menu_click_sound.play()
                        self.previous_state = "paused"
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
        global WINDOW_WIDTH, WINDOW_HEIGHT

        WINDOW_WIDTH = width
        WINDOW_HEIGHT = height

        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

        self.play_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 400, 200, 60)
        self.settings_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 500, 200, 60)

        self.continue_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 350, 200, 60)
        self.pause_settings_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 450, 200, 60)
        self.quit_menu_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 550, 200, 60)

        self.play_again_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 450, 200, 60)
        self.game_over_menu_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 550, 200, 60)

        self.res_1920_button = pygame.Rect(WINDOW_WIDTH // 2 - 150, 320, 300, 50)
        self.res_1280_button = pygame.Rect(WINDOW_WIDTH // 2 - 150, 390, 300, 50)
        self.res_800_button = pygame.Rect(WINDOW_WIDTH // 2 - 150, 460, 300, 50)

        self.pause_button = pygame.Rect(WINDOW_WIDTH // 2 - 25, 20, 50, 50)

    def _update(self, delta):
        

        if self.state != "playing":
            return
        self._update_overlay_effects(delta)

        if self.state == "playing":
            if self.wave == 4:
                self._play_music(get_asset_path("sounds/final_boss_main_menu.mp3"))
            else:
                self._play_music(get_asset_path("sounds/ingame_background.mp3"))

        moving = self.player.update(delta)
        if moving:
            self.footstep_timer -= delta
            if self.footstep_timer <= 0:
                self.footstep_sound.play()
                self.footstep_timer = self.footstep_delay
        else:
            self.footstep_timer = 0

        self.bullets.update(delta)

        for enemy in self.enemies:
            enemy.update(delta, self.player.world_x, self.player.world_y)

        for bullet in self.bullets.copy():
            for enemy in self.enemies.copy():
                dx = bullet.world_x - enemy.world_x
                dy = bullet.world_y - enemy.world_y
                distance = math.sqrt(dx * dx + dy * dy)

                if distance < 50:
                    enemy.health -= bullet.damage
                    bullet.kill()

                    if enemy.health <= 0:
                        drop_x = enemy.world_x
                        drop_y = enemy.world_y

                        enemy.kill()
                        self.score += 1
                        self.enemy_death_sound.play()

                        if random.random() < POWERUP_DROP_CHANCE:
                            power_type = random.choice(["health", "health", "damage", "speed"])
                            powerup = PowerUp(drop_x, drop_y, power_type)
                            self.powerups.add(powerup)
                    break

        for powerup in self.powerups.copy():
            dx = powerup.world_x - self.player.world_x
            dy = powerup.world_y - self.player.world_y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance < 50:
                if powerup.power_type == "health":
                    self.player.health = min(self.player.max_health, self.player.health + HEALTH_PACK_AMOUNT)

                elif powerup.power_type == "damage":
                    self.current_bullet_damage = DAMAGE + DAMAGE_BOOST_AMOUNT
                    self.damage_boost_timer = DAMAGE_BOOST_DURATION

                elif powerup.power_type == "speed":
                    self.player.speed = PLAYER_SPEED + SPEED_BOOST_AMOUNT
                    self.speed_boost_timer = SPEED_BOOST_DURATION

                powerup.kill()   

        if self.damage_boost_timer > 0:
            self.damage_boost_timer -= delta
            if self.damage_boost_timer <= 0:
                self.current_bullet_damage = DAMAGE

        if self.speed_boost_timer > 0:
            self.speed_boost_timer -= delta
            if self.speed_boost_timer <= 0:
                self.player.speed = PLAYER_SPEED

        if self.boss is not None:
            for bullet in self.bullets.copy():
                dx = bullet.world_x - self.boss.world_x
                dy = bullet.world_y - self.boss.world_y
                distance = math.sqrt(dx * dx + dy * dy)

                if distance < 120:   # bigger hitbox for boss
                    self.boss.health -= bullet.damage
                    bullet.kill()

                    if self.boss.health <= 0:
                        self.boss = None
                        self.state = "victory"

                    break

        for enemy in self.enemies.copy():
            dx = enemy.world_x - self.player.world_x
            dy = enemy.world_y - self.player.world_y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance < 60:
                self.player.health -= 20
                enemy.kill()
                self.player_hurt_sound.play()
                
                if self.player.health <= 0:
                    self.state = "game_over"

        self.boss_lasers.update(delta)
        
        for laser in self.boss_lasers.copy():
            dx = laser.world_x - self.player.world_x
            dy = laser.world_y - self.player.world_y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance < 50:
                self.player.health -= laser.damage
                laser.kill()
                self.player_hurt_sound.play()

                if self.player.health <= 0:
                    self.state = "game_over"

        if self.wave_in_progress and self.wave <= 3 and self.enemies_spawned < self.enemies_to_spawn:
            self.enemy_spawn_timer += delta
            if self.enemy_spawn_timer >= self.enemy_spawn_delay:
                self._spawn_enemy()
                self.enemy_spawn_timer = 0

        if self.wave == 4:
            if not self.boss_spawned:
                self._spawn_boss()

            if self.boss is not None:
                self.boss.update(delta, self.player.world_x, self.player.world_y)

                if self.boss.can_shoot():
                    self._boss_shoot()
                    self.boss.reset_laser_timer()

        if self.wave_in_progress:
            if self.wave <= 3 and self.enemies_spawned >= self.enemies_to_spawn and len(self.enemies) == 0:
                self.wave += 1

                if self.wave <= 4:
                    self._setup_wave()

        if self.boss is not None:
            dx = self.boss.world_x - self.player.world_x
            dy = self.boss.world_y - self.player.world_y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance < 100:
                self.player.health -= BOSS_DAMAGE * delta

                if self.player.health <= 0:
                    self.state = "game_over"

        if self.state != self.last_state:
            if self.state == "game_over":
                pygame.mixer.music.stop()
                self.game_over_sound.play()

            elif self.state == "victory":
                pygame.mixer.music.stop()
                self.enemy_death_sound.play()
                pygame.time.delay(150)
                self.victory_sound.play()

            elif self.state == "menu":
                self._play_music(get_asset_path("sounds/final_boss_main_menu.mp3"))

            self.last_state = self.state

        
    def _draw_wave(self):
        wave_text = self.font.render(f"Wave: {self.wave}", True, WHITE)
        self.screen.blit(wave_text, (20, 70))

    def _draw_pause_button(self):
        pygame.draw.rect(self.screen, DARK_BLUE, self.pause_button)

        bar_width = 8
        bar_height = 24
        gap = 8

        x = self.pause_button.x + 12
        y = self.pause_button.y + 13

        pygame.draw.rect(self.screen, WHITE, (x, y, bar_width, bar_height))
        pygame.draw.rect(self.screen, WHITE, (x + bar_width + gap, y, bar_width, bar_height))

    def _draw_paused(self):
        self._draw_game()

        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        title_font = pygame.font.SysFont(None, 90)
        button_font = pygame.font.SysFont(None, 45)

        title_text = title_font.render("Paused", True, WHITE)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 220))
        self.screen.blit(title_text, title_rect)

        pygame.draw.rect(self.screen, DARK_BLUE, self.continue_button)
        pygame.draw.rect(self.screen, DARK_BLUE, self.pause_settings_button)
        pygame.draw.rect(self.screen, DARK_BLUE, self.quit_menu_button)

        continue_text = button_font.render("Continue", True, WHITE)
        settings_text = button_font.render("Settings", True, WHITE)
        quit_text = button_font.render("Main Menu", True, WHITE)

        self.screen.blit(continue_text, continue_text.get_rect(center=self.continue_button.center))
        self.screen.blit(settings_text, settings_text.get_rect(center=self.pause_settings_button.center))
        self.screen.blit(quit_text, quit_text.get_rect(center=self.quit_menu_button.center))

    def _draw_player_health(self):
        bar_width = 300
        bar_height = 20

        health_ratio = self.player.health / self.player.max_health

        bar_x = WINDOW_WIDTH - bar_width - 20
        bar_y = 20

        pygame.draw.rect(self.screen, RED, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(
            self.screen,
            GREEN,
            (bar_x, bar_y, int(bar_width * health_ratio), bar_height)
        )
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)


    def _draw_score(self):
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (20, 20))

    def _draw_grid(self):
        grid_size = 100

        start_x = - (self.player.world_x % grid_size)
        start_y = - (self.player.world_y % grid_size)

        for x in range(int(start_x), WINDOW_WIDTH, grid_size):
            pygame.draw.line(self.screen, DARK_BLUE, (x, 0), (x, WINDOW_HEIGHT))

        for y in range(int(start_y), WINDOW_HEIGHT, grid_size):
            pygame.draw.line(self.screen, DARK_BLUE, (0, y), (WINDOW_WIDTH, y))

    def _draw_gun(self):
        center_x = WINDOW_WIDTH // 2
        center_y = WINDOW_HEIGHT // 2
        mouse_x, mouse_y = pygame.mouse.get_pos()

        dx = mouse_x - center_x
        dy = mouse_y - center_y

        angle = math.atan2(dy, dx)

        angle_degrees = -math.degrees(angle)

        facing_right = dx > 0

        gun_to_draw = self.gun_image

        if facing_right:
            gun_to_draw = pygame.transform.flip(self.gun_image, True, False)
        else:
            angle_degrees = -math.degrees(angle) + 180

        rotated_gun = pygame.transform.rotate(gun_to_draw, angle_degrees)

        gun_distance = 28
        gun_x = center_x + math.cos(angle) * gun_distance
        gun_y = center_y + math.sin(angle) * gun_distance

        gun_rect = rotated_gun.get_rect(center=(gun_x, gun_y))
        self.screen.blit(rotated_gun, gun_rect)

    def _shoot(self):
        center_x = WINDOW_WIDTH // 2
        center_y = WINDOW_HEIGHT // 2
        mouse_x, mouse_y = pygame.mouse.get_pos()

        dx = mouse_x - center_x
        dy = mouse_y - center_y
        angle = math.atan2(dy, dx)

        gun_distance = 40
        bullet_x = self.player.world_x + math.cos(angle) * gun_distance
        bullet_y = self.player.world_y + math.sin(angle) * gun_distance

        bullet = Bullet(bullet_x, bullet_y, angle, self.current_bullet_damage)
        self.bullets.add(bullet)
        self.shoot_sound.play()

    def _spawn_enemy(self):
        side = random.choice(["top","bottom","left","right"])
        margin = 200

        if side == "top":
            x = random.randint(-WINDOW_WIDTH, WINDOW_WIDTH)
            y = self.player.world_y - WINDOW_HEIGHT // 2 - margin
        elif side == "bottom":
            x = random.randint(-WINDOW_WIDTH, WINDOW_WIDTH)
            y = self.player.world_y + WINDOW_HEIGHT // 2 + margin
        elif side == "left":
            x = self.player.world_x - WINDOW_WIDTH // 2 - margin
            y = random.randint(-WINDOW_HEIGHT, WINDOW_HEIGHT)
        else:
            x = self.player.world_x + WINDOW_WIDTH // 2 + margin
            y = random.randint(-WINDOW_HEIGHT, WINDOW_HEIGHT)

        enemy = Enemy(x, y, self.current_enemy_health)
        self.enemies.add(enemy)
        self.enemies_spawned += 1

    def _spawn_boss(self):
        boss_x = self.player.world_x
        boss_y = self.player.world_y - WINDOW_HEIGHT // 2 - 300

        self.boss = Boss(boss_x, boss_y)
        self.boss_spawned = True

    def _boss_shoot(self):
        if self.boss is None:
            return

        dx = self.player.world_x - self.boss.world_x
        dy = self.player.world_y - self.boss.world_y
        angle = math.atan2(dy, dx)

        laser_x = self.boss.world_x + math.cos(angle) * 40
        laser_y = self.boss.world_y + math.sin(angle) * 40

        laser = BossLaser(laser_x, laser_y, angle)
        self.boss_lasers.add(laser)
        self.laser_sound.play()

    def _draw_powerup_status(self):
        y = 110

        if self.damage_boost_timer > 0:
            text = self.font.render(f"Damage Boost: {self.damage_boost_timer:.1f}s", True, WHITE)
            self.screen.blit(text, (20, y))
            y += 35

        if self.speed_boost_timer > 0:
            text = self.font.render(f"Speed Boost: {self.speed_boost_timer:.1f}s", True, WHITE)
            self.screen.blit(text, (20, y))

    def _draw_menu(self):
        title_font = pygame.font.SysFont(None, 100)
        button_font = pygame.font.SysFont(None, 50)

        title_text = title_font.render("Demogorgon Hunter", True, WHITE)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 200))
        self.screen.blit(title_text, title_rect)

        pygame.draw.rect(self.screen, DARK_BLUE, self.play_button)
        pygame.draw.rect(self.screen, DARK_BLUE, self.settings_button)

        play_text = button_font.render("Play", True, WHITE)
        settings_text = button_font.render("Settings", True, WHITE)

        play_rect = play_text.get_rect(center=self.play_button.center)
        settings_rect = settings_text.get_rect(center=self.settings_button.center)

        self.screen.blit(play_text, play_rect)
        self.screen.blit(settings_text, settings_rect)

    def _draw_settings(self):
        title_font = pygame.font.SysFont(None, 80)
        button_font = pygame.font.SysFont(None, 40)

        title_text = title_font.render("Settings", True, WHITE)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 180))
        self.screen.blit(title_text, title_rect)

        res_text = button_font.render("Resolution", True, WHITE)
        res_rect = res_text.get_rect(center=(WINDOW_WIDTH // 2, 260))
        self.screen.blit(res_text, res_rect)

        pygame.draw.rect(self.screen, DARK_BLUE, self.res_1920_button)
        pygame.draw.rect(self.screen, DARK_BLUE, self.res_1280_button)
        pygame.draw.rect(self.screen, DARK_BLUE, self.res_800_button)
        pygame.draw.rect(self.screen, DARK_BLUE, self.back_button)

        text_1920 = button_font.render("1920 x 1080", True, WHITE)
        text_1280 = button_font.render("1280 x 720", True, WHITE)
        text_800 = button_font.render("800 x 600", True, WHITE)
        back_text = button_font.render("Back", True, WHITE)

        self.screen.blit(text_1920, text_1920.get_rect(center=self.res_1920_button.center))
        self.screen.blit(text_1280, text_1280.get_rect(center=self.res_1280_button.center))
        self.screen.blit(text_800, text_800.get_rect(center=self.res_800_button.center))
        self.screen.blit(back_text, back_text.get_rect(center=self.back_button.center))

    def _draw_victory(self):
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
        self.screen.fill(BLACK)

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

        pygame.display.flip()

    def _draw_game(self):
        self.bg.draw(self.screen, self.player.world_x, self.player.world_y)

        self.all_sprites.draw(self.screen)
        self._draw_gun()

        for bullet in self.bullets:
            bullet.draw(self.screen, self.player.world_x, self.player.world_y)

        if self.boss is not None:
            self.boss.draw(self.screen, self.player.world_x, self.player.world_y)
            self.boss.draw_health_bar(self.screen, self.player.world_x, self.player.world_y)

        for laser in self.boss_lasers:
            laser.draw(self.screen, self.player.world_x, self.player.world_y)

        for enemy in self.enemies:
            enemy.draw(self.screen, self.player.world_x, self.player.world_y)
            enemy.draw_health_bar(self.screen, self.player.world_x, self.player.world_y)

        for powerup in self.powerups:
            powerup.draw(self.screen, self.player.world_x, self.player.world_y)

        self._draw_powerup_status()

        self._draw_atmosphere_overlay()
        
        self._draw_wave()
        self._draw_player_health()
        self._draw_score()
        self._draw_pause_button()

    def run(self):
        while self.running:
            delta = self.clock.tick(MAX_FPS) / 1000.0
            self._handle_events()
            self._update(delta)
            self._draw()
        
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
