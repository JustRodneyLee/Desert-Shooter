import sys, os
import pygame as pg
import json
from pygame.locals import *  # import pygame constants
from pygame.math import *
import random

# game constants
gameWidth = 512
gameHeight = 608
fly_Speed = 60  # background speed (per second)
player_speed = 8
bullet_Speed = 12
anim_fr = 12  # animation frame rate
FPS = 60
bgm_vol = 0.25

# Directions +X -Y
LEFT = Vector2(-1, 0)
RIGHT = Vector2(1, 0)
UP = Vector2(0, -1)
DOWN = Vector2(0, 1)

# Colors
TRANSPARENT = (0, 0, 0, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CORNFLOWER_BLUE = (100, 149, 237)

# Game Events
EVENT_SPAWN_ENEMY = pg.USEREVENT + 1

pg.mixer.pre_init(44100, -16, 2, 512)
pg.init()  # pygame initialize
os.environ['SDL_VIDEO_CENTERED'] = '1'  # center window at startup
screen = pg.display.set_mode((gameWidth, gameHeight))  # create window and set window resolution
# game content
sfx_shoot = pg.mixer.Sound(os.path.join('assets', 'shoot.ogg'))
sfx_explosion = pg.mixer.Sound(os.path.join('assets', 'explosion.ogg'))
bkgd_tex = pg.transform.scale2x(pg.image.load(os.path.join('assets', 'desert-background-looped.png')).convert())
clouds_tex = pg.transform.scale2x(pg.image.load(os.path.join('assets', 'clouds-transparent.png')).convert_alpha())
bkgd_pos = Vector2(0, -bkgd_tex.get_height() / 2)
enemy_large_tex = pg.transform.scale2x(pg.image.load(os.path.join('assets', 'enemy-big.png')).convert_alpha())
enemy_medium_tex = pg.transform.scale2x(pg.image.load(os.path.join('assets', 'enemy-medium.png')).convert_alpha())
enemy_small_tex = pg.transform.scale2x(pg.image.load(os.path.join('assets', 'enemy-small.png')).convert_alpha())
shoot_tex = pg.transform.scale2x(pg.image.load(os.path.join('assets', 'laser-bolts.png')).convert_alpha())
power_up_tex = pg.transform.scale2x(pg.image.load(os.path.join('assets', 'power-up.png')).convert_alpha())
explosion_tex = pg.transform.scale2x(pg.image.load(os.path.join('assets', 'explosion.png')).convert_alpha())
# load anim data via json parsing
anim_data = {}
anim_data_raw = {}
with open(os.path.join('assets', 'data.json')) as f:
    anim_data_raw = json.load(f)['animations']

# preprocess animation data
for animation in anim_data_raw:
    temp_data = []
    for data in anim_data_raw[animation]:
        rect_data = str.split(data, ',')
        temp_data.append(
            Rect(int(rect_data[0]) * 2, int(rect_data[1]) * 2, int(rect_data[2]) * 2, int(rect_data[3]) * 2))
    anim_data[animation] = temp_data

# print(anim_data)

pg.display.set_caption('Desert Shooter')  # set window title
pg.display.set_icon(pg.image.load("assets/icon.png"))
clock = pg.time.Clock()  # create clock
# define game elements
font = pg.font.Font(os.path.join('assets', 'arial.ttf'), 24)
pg.mixer_music.load(os.path.join('assets', 'fight_looped.ogg'))


# initialize player
class Player(pg.sprite.Sprite):
    def __init__(self, init_pos, init_hp):
        super(Player, self).__init__()
        self.hp = init_hp
        self.pos = init_pos
        self.tex = pg.transform.scale2x(pg.image.load(os.path.join('assets', 'ship.png')).convert_alpha())
        self.image = pg.transform.scale2x(pg.image.load(os.path.join('assets', 'ship.png')).convert_alpha())
        self.ss = 'player'
        self.size = (32, 48)
        self.score = 0
        self.frame = 2
        self.anim = 'n'
        self.rect = Rect((int(self.pos.x - self.size[0] / 2), int(self.pos.y)), self.size)
        self.invulnerable = False
        self.invTimer = 0  # invulnerability time
        self.invTime = 2 # default invulnerability time
        self.shooting = False
        self.animTimer = 0
        self.dmg = 1
        self.exploding = False
        self.died = False

    def update(self, *args):
        if not self.died:
            if self.invulnerable:
                self.invTimer += 1 / FPS
                if self.invTimer >= self.invTime:
                    self.invulnerable = False
                    self.image = self.tex
                    self.invTimer = 0
                    self.invTime = 2
            # check for left and right presses

            if not self.exploding:
                if pressed_keys[K_RIGHT]:
                    self.pos += RIGHT * player_speed
                    self.rect = Rect((int(self.pos.x - self.size[0] / 2), int(self.pos.y)), self.size)
                    self.anim = 'r'
                elif pressed_keys[K_LEFT]:
                    self.pos += LEFT * player_speed
                    self.rect = Rect((int(self.pos.x - self.size[0] / 2), int(self.pos.y)), self.size)
                    self.anim = 'l'
                else:
                    if self.anim == 'l':
                        self.anim = 'ln'
                    elif self.anim == 'r':
                        self.anim = 'rn'
                    # check for up and down presses
                if pressed_keys[K_UP]:
                    self.pos += UP * player_speed
                    self.rect = Rect((int(self.pos.x - self.size[0] / 2), int(self.pos.y)), self.size)
                elif pressed_keys[K_DOWN]:
                    self.pos += DOWN * player_speed
                    self.rect = Rect((int(self.pos.x - self.size[0] / 2), int(self.pos.y)), self.size)
                    # shooting
                if pressed_keys[K_LCTRL]:
                    if not self.shooting:
                        sfx_shoot.play()
                        player_projectiles.append(
                            Projectile(Vector2(self.pos.x, self.pos.y), Vector2(0, -bullet_Speed), self.dmg))
                        self.shooting = True
                else:
                    self.shooting = False
            # boundary check
            # vertical check
            if self.pos.y <= 0:
                self.pos = Vector2(self.pos.x, 0)
            elif self.pos.y >= gameHeight - player.rect.height:
                self.pos = Vector2(self.pos.x, gameHeight - player.rect.height)
            # horizontal check
            if self.pos.x <= self.rect.width / 2:
                self.pos = Vector2(self.rect.width / 2, self.pos.y)
            elif self.pos.x >= gameWidth - self.rect.width / 2:
                self.pos = Vector2(gameWidth - self.rect.width / 2, self.pos.y)

            # player animation update
            self.animTimer += 1 / FPS
            if self.animTimer >= 1 / anim_fr:
                if self.anim == 'l':
                    if self.frame != 0 and self.frame != 5:
                        self.frame -= 1
                elif self.anim == 'r':
                    if self.frame != 4 and self.frame != 9:
                        self.frame += 1
                elif self.anim == "ln":
                    if self.frame != 2 and self.frame != 7:
                        self.frame += 1
                    else:
                        self.anim = 'n'
                elif self.anim == "rn":
                    if self.frame != 2 and self.frame != 7:
                        self.frame -= 1
                    else:
                        self.anim = 'n'
                elif self.anim == 'b':
                    self.frame += 1
                    if self.frame >= len(anim_data['explosion']):
                        self.frame = 0
                        self.exploding = False
                        self.died = True
                else:
                    if self.frame <= 4:
                        self.frame += 5
                    else:
                        self.frame -= 5
                self.animTimer = 0

    def get_hurt(self):
        if not self.invulnerable:
            self.hp -= 1
            self.image = tintRed(self.image)
            self.invulnerable = True

    def buff(self, buff_type):
        if buff_type=="xtra_hp": #extra hp
            self.hp+=1
        elif buff_type == "inv": #invulnerability
            self.invulnerable = True

    def explode(self):
        if not self.exploding:
            self.exploding = True
            self.frame = 0
            self.image = explosion_tex
            self.ss = 'explosion'
            self.anim = 'b'
            self.hp = 0
            sfx_explosion.play()


player = Player(Vector2(gameWidth / 2, gameHeight * 0.85), 3)
last_score = 0
player_projectiles = []
flashTimer = 0
flashes = 0
difficulty = 0

class Projectile():
    def __init__(self, init_pos, direction, dmg):  # initial position, direction and damage
        self.pos = init_pos
        self.dmg = dmg
        self.vel = direction
        self.frame = 0
        self.animTimer = 0
        self.collision = Rect(int(self.pos.x - 5), int(self.pos.y), 10, 10)

    def update(self):
        self.pos += self.vel
        self.animTimer += 1 / FPS
        self.collision = Rect(int(self.pos.x - 5), int(self.pos.y), 10, 10)
        if self.animTimer >= 2.5 / anim_fr:
            self.frame += 1
            if self.frame > 1:
                self.frame = 0
            self.animTimer = 0


class EnemyShip(pg.sprite.Sprite):
    def __init__(self, init_pos, type, spd):  # initial position & health
        super(EnemyShip, self).__init__()
        self.type = type
        self.pos = init_pos
        self.vel = spd
        self.animTimer = 0
        self.hurtTimer = 0
        self.shootTimer = 0
        self.frame = 0
        self.died = False
        self.type = type
        if self.type == 'enemy_small':
            self.hp = 1
            self.tex = enemy_small_tex
            self.image = enemy_small_tex
            self.rect = anim_data['enemy_small'][0]
        elif self.type == 'enemy_medium':
            self.hp = 3
            self.tex = enemy_medium_tex
            self.image = enemy_medium_tex
            self.rect = anim_data['enemy_medium'][0]
        elif self.type == 'enemy_big':
            self.hp = 7
            self.tex = enemy_large_tex
            self.image = enemy_large_tex
            self.rect = anim_data['enemy_big'][0]
        self.collision = Rect(int(self.pos.x - self.rect.width / 2), int(self.pos.y), self.rect.width,
                              self.rect.height)  # set collision
        self.shoot()

    def update(self):
        if self.hurtTimer != 0:
            self.hurtTimer += 1 / FPS
            if self.hurtTimer >= 1 + 2 / anim_fr:
                self.image = self.tex
                self.hurtTimer = 0
        self.pos += Vector2(0, self.vel)
        self.animTimer += 1 / FPS
        self.shootTimer += 1 / FPS
        self.collision = Rect(int(self.pos.x - self.rect.width / 2), int(self.pos.y), self.rect.width,
                              self.rect.height)  # set collision
        self.rect = anim_data[self.type][self.frame]  # update animation
        if self.hp <= 0:
            self.image = explosion_tex
            self.type = 'explosion'
            if self.animTimer >= 1 / anim_fr:  # animator
                self.frame += 1
                if self.frame >= len(anim_data['explosion']):
                    sfx_explosion.play()
                    self.died = True
        else:
            if self.animTimer >= 1 / anim_fr:  # animator
                if self.frame == 0:
                    self.frame = 1
                else:
                    self.frame = 0
                self.animTimer = 0  # reset timer
            if self.shootTimer >= 1 / difficulty ** 2 + 1:
                self.shoot()
                self.shootTimer = 0

    def get_hurt(self):
        self.hp -= 1
        if self.hp > 0:
            self.image = tintRed(self.image)
            self.hurtTimer += 1

    def shoot(self):
        if self.type == 'enemy_small':
            enemy_projectiles.append(
                Projectile(Vector2(self.pos.x, self.pos.y + self.tex.get_height()), Vector2(0, self.vel * 1.5), 1))
        elif self.type == 'enemy_medium':  # shoots 2 projectiles
            enemy_projectiles.append(
                Projectile(Vector2(self.pos.x - self.tex.get_width() / 6, self.pos.y + self.tex.get_height()),
                           Vector2(0, self.vel * 1.5), 1))
            enemy_projectiles.append(
                Projectile(Vector2(self.pos.x + self.tex.get_width() / 6, self.pos.y + self.tex.get_height()),
                           Vector2(0, self.vel * 1.5), 1))
        elif self.type == 'enemy_big':
            enemy_projectiles.append(Projectile(Vector2(self.pos.x, self.pos.y + self.tex.get_height()), Vector2(0, self.vel * 1.5), 1))
            enemy_projectiles.append(
                Projectile(Vector2(self.pos.x - self.tex.get_width() / 3, self.pos.y + self.tex.get_height()),
                           Vector2(-1, self.vel * 1.5), 1))
            enemy_projectiles.append(
                Projectile(Vector2(self.pos.x + self.tex.get_width() / 3, self.pos.y + self.tex.get_height()),
                           Vector2(1, self.vel * 1.5), 1))


def spawnEnemy():
    enemy_ships = []
    pos = random.randint(int(gameWidth * 0.25), int(gameWidth * 0.75))
    margin = 5
    if difficulty <= 0.5:
        choice = 'enemy_small'
        formation = random.choice(['-', '--'])
        ship_maxlen = anim_data['enemy_small'][0].width
    elif difficulty <= 6:
        choice = random.choice(['enemy_small','enemy_medium'])
        formation = random.choice(['-', '--', 'v'])
        ship_maxlen = anim_data['enemy_medium'][0].width
    else:
        choice = random.choice(['enemy_small','enemy_medium','enemy_big'])
        formation = random.choice(['-', '--', 'v', 'x'])
        ship_maxlen = anim_data['enemy_big'][0].width

    if formation == '-':
        enemy_ships.append(EnemyShip(Vector2(pos, -40), choice,
                                 2))
    elif formation == '--':
        enemy_ships.append(EnemyShip(Vector2(pos, -40), choice,
                                     2))
        enemy_ships.append(EnemyShip(Vector2(pos + ship_maxlen + margin, -40), choice,
                                     2))
    elif formation == 'v':
        enemy_ships.append(EnemyShip(Vector2(pos, -40), choice, # leading ship
                                     2))
        enemy_ships.append(EnemyShip(Vector2(pos + ship_maxlen + margin, -80), 'enemy_small',
                                     2))
        enemy_ships.append(EnemyShip(Vector2(pos - ship_maxlen - margin, -80), 'enemy_small',
                                     2))
    elif formation == 'x':
        enemy_ships.append(EnemyShip(Vector2(pos, -100), choice,  # leading ship
                                     2))
        enemy_ships.append(EnemyShip(Vector2(pos + ship_maxlen + margin, -120), 'enemy_small',
                                     2))
        enemy_ships.append(EnemyShip(Vector2(pos - ship_maxlen - margin, -120), 'enemy_small',
                                     2))
        enemy_ships.append(EnemyShip(Vector2(pos + ship_maxlen + margin, -40), 'enemy_small',
                                     2))
        enemy_ships.append(EnemyShip(Vector2(pos - ship_maxlen - margin, -40), 'enemy_small',
                                     2))
    for ship in enemy_ships:
        enemies.append(ship)

class PowerUp():
    def __init__(self, type):
        self.pos = Vector2(random.randint(int(gameWidth * 0.1), int(gameWidth * 0.9)), -40) # random generation
        self.collision = Rect(int(self.pos.x), int(self.pos.y), 32, 32) # hard coding... not a good habit
        self.animTimer = 0
        self.frame = 0
        self.buff = type

    def update(self):
        self.pos += Vector2(0, fly_Speed / FPS)
        self.collision = Rect(int(self.pos.x), int(self.pos.y), 32, 32)  # hard coding... not a good habit
        self.animTimer += 1 / FPS
        if self.animTimer >= 2 / anim_fr:
            self.frame += 1
            if self.frame > 1:
                self.frame = 0
            self.animTimer = 0

def spawnPowerUp():
    powerup = random.randint(0, 100)
    if powerup >= 95:
        powerups.append(PowerUp('inv'))
    else:
        powerups.append(PowerUp('xtra_hp'))

def tintRed(surf):
    surf = surf.copy()
    surf.fill(RED + (125,), None, pg.BLEND_RGBA_MULT)
    return surf


enemies = []
lastPressed = []
enemySpawnTime = 2 / (difficulty + 1)
enemySpawnTimer = 0
enemy_projectiles = []
clouds = []
cloudTimer = 0
powerups = []
powerUpTimer = 0

gameOver = False
pressingMute = False
muteAudio = False

# HUD
fpsText = font.render(str(int(clock.get_fps())), True, WHITE)
scoreText = font.render(str(player.score), True, WHITE)
healthText = font.render('HP:' + str(player.hp), True, WHITE)
gameOverText = font.render('Game Over', True, WHITE)

pg.mixer_music.set_volume(bgm_vol)
pg.mixer_music.play(-1) # plays bgm
while True:
    screen.fill(CORNFLOWER_BLUE)  # clear screen

    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.quit()
            sys.exit()

    clock.tick(FPS)
    pressed_keys = pg.key.get_pressed()

    if gameOver:
        flashTimer += 1 / FPS
        if flashTimer <= 0.5:
            gameOverText = font.render('Game Over', True, WHITE)
        elif flashTimer <= 1:
            gameOverText = font.render('', True, WHITE)
        else:
            flashTimer = 0
    else:
        player.score += 0.25

    # Check for game over conditions
    if not gameOver:
        # difficulty change
        difficulty += 0.1 / FPS
        if player.hp == 0:
            fly_Speed = 60
            gameOver = True
            player.explode()
        elif player.score < 0:
            player.score = 0
            player.explode()
            gameOver = True
        elif player.score == 99999:
            difficulty = -1
            gameOver = True

    player.update()
    
    if pressed_keys[K_m]:
        if not pressingMute:
            muteAudio = not muteAudio
            if muteAudio:
                pg.mixer_music.set_volume(bgm_vol)
            else:
                pg.mixer_music.set_volume(0)

    if pressed_keys[K_ESCAPE]:
        pg.quit()
        sys.exit()

    # Spawning objects
    # spawn enemies
    enemySpawnTimer += 1 / FPS  # inaccurate but OK
    if enemySpawnTimer >= enemySpawnTime:
        spawnEnemy()
        enemySpawnTimer = 0
    # spawn powerups
    powerUpTimer += 1 / FPS
    if powerUpTimer >= random.randint(int(14 - difficulty), 20):
        spawnPowerUp()
        powerUpTimer = 0

    # update enemies
    for enemy in enemies:
        enemy.update()
        if enemy.died:
            enemies.remove(enemy)
        else:
            if enemy.pos.y >= gameHeight:
                if not gameOver:
                    if enemy.type == 'enemy_big':
                        player.score -= 500
                    elif enemy.type == 'enemy_medium':
                        player.score -= 250
                    elif enemy.type == 'enemy_small':
                        player.score -= 100
                enemies.remove(enemy)
                pass
            if not player.died:
                if player.rect.colliderect(enemy.collision) and not enemy.died:  # player ship hits enemy ship
                    enemy.get_hurt()
                    player.get_hurt()
            for projectile in player_projectiles:
                if projectile.collision.colliderect(enemy.collision):
                    enemy.get_hurt()
                    player_projectiles.remove(projectile)

    for projectile in player_projectiles:
        projectile.update()
        if projectile.pos.y <= -20:  # clipping out projectiles
            player_projectiles.remove(projectile)

    for powerup in powerups:
        powerup.update()
        if powerup.pos.y >= gameHeight:
            powerups.remove(powerup)
        if powerup.collision.colliderect(player.rect):
            player.buff(powerup.buff)
            powerups.remove(powerup)

    # Projectile Update
    for projectile in enemy_projectiles:
        projectile.update()
        if projectile.pos.y <= -20 or projectile.pos.y >= gameHeight or projectile.pos.x <= -20 or projectile.pos.x >= gameWidth + 20:  # clipping out projectiles
            enemy_projectiles.remove(projectile)
        if projectile.collision.colliderect(player.rect):
            player.get_hurt()
            enemy_projectiles.remove(projectile)

    # background update
    bkgd_pos += Vector2(0, fly_Speed / FPS)
    if bkgd_pos.y >= 0:
        bkgd_pos = Vector2(0, -bkgd_tex.get_height() / 2)

    # cloud spawn update
    for cloud in clouds:
        cloud.move_ip(0, fly_Speed * 3 / FPS)
        if cloud.y >= gameHeight:
            clouds.remove(cloud)
    cloudTimer += 1 / FPS
    if cloudTimer >= random.randint(8, 20 - int(difficulty)):
        clouds.append(Rect(0, -clouds_tex.get_height(), clouds_tex.get_width(), clouds_tex.get_height()))
        cloudTimer = 0

    # Here we draw our game
    fpsText = font.render('FPS:' + str(int(clock.get_fps())), True, WHITE)  # buffer fps text
    scoreText = font.render('Score:' + str(int(player.score)).zfill(5), True, WHITE)  # buffer score text
    healthText = font.render('HP:' + str(player.hp), True, WHITE)

    # draw looping background
    screen.blit(bkgd_tex, (int(bkgd_pos.x), int(bkgd_pos.y)))

    # draw projectiles
    # projectiles_spriteBatch.draw(screen)
    for projectile in player_projectiles:
        screen.blit(shoot_tex, projectile.collision, anim_data['projectile'][projectile.frame])
    for projectile in enemy_projectiles:
        screen.blit(shoot_tex, projectile.collision, anim_data['enemy_projectile'][projectile.frame])

    # draw power-ups
    for powerup in powerups:
        screen.blit(power_up_tex, powerup.collision, anim_data[powerup.buff][powerup.frame])

    # draw enemy ships
    for enemy in enemies:
        screen.blit(enemy.image, enemy.collision, enemy.rect)

    # draw player
    if not player.died:
        screen.blit(player.image, player.rect, anim_data[player.ss][player.frame])

    # draw clouds
    for cloud in clouds:
        screen.blit(clouds_tex, cloud)

    # draw HUD
    screen.blit(healthText, (int(gameWidth * 0.5 - healthText.get_width() / 2), int(gameWidth * 0.01)))
    screen.blit(fpsText, (int(gameWidth * 0.83), int(gameWidth * 0.01)))
    screen.blit(scoreText, (int(gameWidth * 0.01), int(gameWidth * 0.01)))
    if gameOver:
        screen.blit(gameOverText, (
        int(gameWidth * 0.5 - gameOverText.get_width() / 2), int(gameHeight * 0.5 - gameOverText.get_height() / 2)))

    pressingMute = pressed_keys[K_m]

    pg.display.update((0, 0, gameWidth, gameHeight))    
    # Debug Info
    # print(self.pos)
