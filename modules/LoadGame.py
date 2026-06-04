import pygame
from pygame.examples.cursors import image
from pygame.sprite import groupcollide, spritecollide
import os

from modules.tool.music import *
from modules.entity.tank import *
from modules.tool.explode import *
from modules.entity.scenes import *
from modules.entity.bullet import *
from modules.onlineConnetion import *
import cfg

class NormalVariables:
    def __init__(self):
        self.total_enemy_tanks = 0
        self.total_created_enemy_tanks = 0
        self.max_enemy_tanks = None
        self.remaining_enemies = self.total_enemy_tanks

        self.enemy_tanks_positions = None
        self.initial_reborn_position = cfg.INITIAL_REBORN
        self.teammate_reborn_position = cfg.INITIAL_REBORN
        self.reborn_interval = cfg.REBORN_INTERVAL

        self.window = None
        self.window_size = (cfg.WIDTH, cfg.HEIGHT)
        self.cell_len = 24

        self.key_order = []
        self.keys_pressed = None
        self.teammate_event = []

        self.game_lose = False
        self.game_win = False

        self.is_multiplayer = False


class TanksEvent:
    def __init__(self, my_tank,teammate_tank, enemy_tanks,my_bullets ,enemy_bullets, walls, all_collision,normal_variables):
        self.normal_variables = normal_variables
        self.all_collision = all_collision

        self.my_tank = my_tank
        self.teammate_tank = teammate_tank

        self.enemy_tanks = enemy_tanks
        self.my_bullets = my_bullets
        self.enemy_bullets = enemy_bullets

        self.walls = walls

        self.is_teammate_move = False
        self.is_teammate_shot = False

        self.allocated_tank_id = 0
        self.allocated_bullet_id = 0

    def tanks_update(self):
        self.random_create_enemy_tanks()
        self.tanks_move()
        self.tanks_shot()

    def render(self):
        nv=self.normal_variables
        #所有坦克的渲染
        if self.my_tank and self.my_tank.live:
            self.my_tank.display_tank()
        elif pygame.time.get_ticks() - self.my_tank.last_dead_time > nv.reborn_interval and self.my_tank.hp > 0:  # 考虑移至更新模块中处理
            self.tank_reborn(self.my_tank)

        if self.normal_variables.is_multiplayer:
            if self.teammate_tank and self.teammate_tank.live:
                self.teammate_tank.display_tank()
            elif pygame.time.get_ticks() - self.teammate_tank.last_dead_time > nv.reborn_interval and self.teammate_tank.hp > 0:
                self.tank_reborn(self.teammate_tank)

        for tank in self.enemy_tanks:
            tank.display_tank()

    def tank_creation(self):
        self.create_my_tank()
        self.allocated_tank_id += 1
        if self.normal_variables.is_multiplayer:
            self.create_teammate_tank()
            self.allocated_tank_id += 1
    
    def create_my_tank(self):
        nv = self.normal_variables
        MainGame.my_tank = MyTank(nv.initial_reborn_position, nv.window, nv.window_size, self.allocated_tank_id)
        self.my_tank = MainGame.my_tank
        self.all_collision.add(MainGame.my_tank)

    def create_teammate_tank(self):
        nv = self.normal_variables
        MainGame.teammate_tank = MyTank(nv.teammate_reborn_position, nv.window, nv.window_size, self.allocated_tank_id)
        self.teammate_tank = MainGame.teammate_tank
        self.all_collision.add(MainGame.teammate_tank)

    #随机创建敌人-更新
    def random_create_enemy_tanks(self):
        nv = self.normal_variables
        if len(self.enemy_tanks) < nv.max_enemy_tanks and nv.total_created_enemy_tanks < nv.total_enemy_tanks:
            position = random.choice(nv.enemy_tanks_positions)
            if not self.create_enemy_tank(position):
                self.allocated_tank_id-=1

    def create_enemy_tank(self, position):
        nv = self.normal_variables

        left, top = position[0], position[1]
        enemy_tank = EnemyTank((left, top), nv.window, nv.window_size, self.allocated_tank_id)
        other_tanks = Group([t for t in self.all_collision if t != enemy_tank])  # 考虑n*n矩阵，空间换时间
        if not pygame.sprite.spritecollideany(enemy_tank, other_tanks):
            nv.total_created_enemy_tanks += 1
            self.enemy_tanks.add(enemy_tank)
            self.all_collision.add(enemy_tank)
            return True
        return False
    def tank_dead(self, tank):
        pass

    #射击-更新
    def tanks_shot(self):
        self.all_players_shot()
        self.enemy_tank_shot()

    def all_players_shot(self):
        nv = self.normal_variables
        if nv.is_multiplayer:
            for event in nv.teammate_event:
                if event == 'c_shot':
                    self.is_teammate_shot = not self.is_teammate_shot

            if self.is_teammate_shot:

                bullet = self.teammate_tank.shot(self.allocated_bullet_id)
                self.allocated_bullet_id += 1
                if bullet:
                    self.my_bullets.add(bullet)

        if nv.keys_pressed:
            if nv.keys_pressed[pygame.K_SPACE] and self.my_tank and self.my_tank.live:
                bullet = self.my_tank.shot(self.allocated_bullet_id)
                self.allocated_bullet_id += 1
                if bullet:
                    self.my_bullets.add(bullet)
                # self.fire_music.play_music()
    def enemy_tank_shot(self):
        for enemy in self.enemy_tanks:

            bullet = enemy.shot(self.allocated_bullet_id)
            self.allocated_bullet_id += 1
            if bullet:
                self.enemy_bullets.add(bullet)

    def tanks_move(self):
        self.all_players_move()
        self.all_enemy_tanks_move()


    def all_players_move(self):
        nv = self.normal_variables
        if nv.key_order and self.my_tank and self.my_tank.live:
            last_direction = nv.key_order[-1]
            self.player_tank_move(self.my_tank, last_direction)

        if nv.is_multiplayer:
            for event in nv.teammate_event:
                if event in ['L', 'R', 'U', 'D']:
                    self.teammate_tank.change_direction(event)
                    self.is_teammate_move = True
                elif event == 's_m':
                    self.is_teammate_move = False

            if self.is_teammate_move:
                self.player_tank_move(self.teammate_tank, self.teammate_tank.direction[0])

    def player_tank_move(self, tank, direction):
        old_rect = tank.rect.copy()
        old_direction = tank.direction

        tank.move(direction)

        if old_direction[0] != direction:
            self.move_check(tank, direction, old_rect)  # 考虑减少耦合的修改

        other_tanks = Group([t for t in MainGame.all_collision if t != tank])  # 考虑n*n矩阵，空间换时间
        if pygame.sprite.spritecollideany(tank, other_tanks):
            tank.rect = old_rect

    def all_enemy_tanks_move(self):
        for enemy in self.enemy_tanks:
            self.enemy_tank_move(enemy)

    def enemy_tank_move(self, tank):
        old_rect = tank.rect.copy()
        old_direction = tank.direction

        tank.rand_move()

        if old_direction[0] != tank.direction:
            self.move_check(tank, tank.direction, old_rect)

        other_tanks = Group([t for t in MainGame.all_collision if t != tank])  # 考虑n*n矩阵，空间换时间
        if pygame.sprite.spritecollideany(tank, other_tanks):
            tank.rect = old_rect

    def move_check(self, tank, direction, old_rect):
        nv = self.normal_variables
        if direction in ['L', 'R']:
            offset = tank.rect.top % nv.cell_len
            if offset < nv.cell_len:
                if offset > nv.cell_len / 2:
                    tank.rect.top -= nv.cell_len - offset
                else:
                    tank.rect.top -= offset
                old_rect.top = tank.rect.top
        elif direction in ['U', 'D']:
            offset = tank.rect.left % nv.cell_len
            if offset < nv.cell_len:
                if offset > nv.cell_len / 2:
                    tank.rect.left -= nv.cell_len - offset
                else:
                    tank.rect.left -= offset
                old_rect.left = tank.rect.left

    def tank_reborn(self, tank):
        nv = self.normal_variables
        if tank == self.my_tank:
            position = nv.initial_reborn_position
        else:
            position = nv.teammate_reborn_position
        
        tank.rect.left, tank.rect.top = position
        tank.direction = 'U1'
        other_tanks = Group([t for t in MainGame.all_collision if t != tank])  # 考虑n*n矩阵，空间换时间
        if not pygame.sprite.spritecollideany(tank, other_tanks):
            self.all_collision.add(tank)
            tank.live = True


class BulletsEvent:
    def __init__(self,my_bullets,enemy_bullets,normal_variables):
        self.normal_variables = normal_variables
        self.my_bullets = my_bullets
        self.enemy_bullets = enemy_bullets

    def bullets_update(self):
        self.bullets_move()

    def render(self):
        for bullet in self.my_bullets:
            bullet.display_bullet(self.normal_variables.window)
        for bullet in self.enemy_bullets:
            bullet.display_bullet(self.normal_variables.window)
    def bullets_move(self):
        for bullet in self.my_bullets:
            bullet.move(self.normal_variables.window_size)
        for bullet in self.enemy_bullets:
            bullet.move(self.normal_variables.window_size)

class ScenesEvent:
    def __init__(self, all_collision,walls,normal_variables):
        self.normal_variables = normal_variables

        self.all_collision = all_collision
        self.walls = walls

        self.allocated_scenes_id=0
    def scenes_update(self):
        pass
    def render(self):
        nv = self.normal_variables
        for wall in self.walls:
            wall.display_static_entity(nv.window)
    def scenes_creation(self, scenes_type, position):
        if scenes_type == 'B':
            self.create_brick_wall(position, self.allocated_scenes_id)
            self.allocated_scenes_id+=1
        elif scenes_type == 'I':
            self.create_steel_wall(position, self.allocated_scenes_id)
            self.allocated_scenes_id+=1
        elif scenes_type == 'R':
            self.create_river_wall(position)
        elif scenes_type == 'C':
            self.create_ice_wall(position)
        elif scenes_type == 'T':
            self.create_tree_wall(position)

    def create_steel_wall(self, position, create_id):
        left, top = position[0], position[1]
        wall = SteelWall((left, top), create_id)

        self.walls.add(wall)
        self.all_collision.add(wall)

    def create_brick_wall(self, position, create_id):
        left, top = position[0], position[1]
        wall = BrickWall((left, top), create_id)

        self.walls.add(wall)
        self.all_collision.add(wall)

    def create_river_wall(self, position):
        pass

    def create_ice_wall(self, position):
        pass

    def create_tree_wall(self, position):
        pass

class CollisionEvent:
    def __init__(self, my_tank,teammate_tank, enemy_tanks,my_bullets ,enemy_bullets, walls, explosions, normal_variables):
        self.normal_variables = normal_variables
        self.my_tank = my_tank
        self.teammate_tank = teammate_tank
        self.enemy_tanks = enemy_tanks

        self.my_bullets = my_bullets
        self.enemy_bullets = enemy_bullets

        self.walls = walls
        self.explosions = explosions


        self.default_collided = pygame.sprite.collide_rect_ratio(0.8)

    def collision_update(self):
        self.tank_bullet_collision()
        self.bullet_wall_collision()
        self.tank_move_collision()

    def render(self):
        nv = self.normal_variables
        if self.explosions:
            ready_remove = []
            for explosion in MainGame.explosions:
                if explosion.live:
                    explosion.display_explode(nv.window)
                else:
                    ready_remove.append(explosion)
            for explosion in ready_remove:
                explosion.kill()
    def tank_bullet_collision(self):
        # 子弹和敌方坦克的碰撞

        collision_results = {
            'explosion': []
        }
        hits = groupcollide(self.my_bullets, self.enemy_tanks, True, True, collided=self.default_collided)
        for bullet, tanks in hits.items():

            for tank in tanks:
                tank.hp -= 1
                if tank.hp <= 0:
                    tank.live = False
                    self.normal_variables.remaining_enemies -= 1
                    tank.kill()
                collision_results['explosion'].append(tank)

        #子弹碰撞
        groupcollide(self.enemy_bullets, self.my_bullets, True, True)

        # 我方坦克和子弹的碰撞
        if self.my_tank and self.my_tank.live:
            hits = spritecollide(self.my_tank, self.enemy_bullets, False, collided=self.default_collided)
            if hits:
                self.my_tank.hp -= 1
                self.my_tank.live = False
                self.my_tank.kill()
                collision_results['explosion'].append(self.my_tank)
                self.tank_dead(self.my_tank)
        # 队友坦克和子弹的碰撞
        if self.normal_variables.is_multiplayer and self.teammate_tank and self.teammate_tank.live:
            hits = spritecollide(self.teammate_tank, self.enemy_bullets, True, collided=self.default_collided)
            if hits:
                self.teammate_tank.hp -= 1
                self.teammate_tank.live = False
                self.teammate_tank.kill()
                collision_results['explosion'].append(self.teammate_tank)
                self.tank_dead(self.teammate_tank)
        if collision_results['explosion']:
            print(collision_results)
        for tank in collision_results['explosion']:
            self.create_explosion(tank)

    def tank_dead(self,tank):
        tank.last_dead_time = pygame.time.get_ticks()
    def bullet_wall_collision(self):
        # 子弹与墙的碰撞

        collision_results={
            'explosion':[]
        }

        hits = pygame.sprite.groupcollide(self.my_bullets, self.walls, True, False)
        for bullet, walls in hits.items():
            collision_results['explosion'].append(bullet)
            for wall in walls:
                if wall.type == 'brick':
                    wall.hp -= 1
                if wall.hp <= 0:
                    wall.live = False
                    wall.kill()

        hits = pygame.sprite.groupcollide(self.walls, self.enemy_bullets, False, True)
        for wall, bullets in hits.items():
            collision_results['explosion'].append(wall)
            if wall.type == 'brick':
                wall.hp -= 1
            if wall.hp <= 0:
                wall.live = False
                wall.kill()

        for bullet in collision_results['explosion']:
            self.create_bullet_explosion(bullet)
    def tank_move_collision(self):
        pass

    def create_explosion(self, tank: Tank):
        explode = Explode(tank)
        self.explosions.add(explode)
        # self.hit_music.play_music()

    def create_bullet_explosion(self, bullet):
        explode = BulletExplode(bullet)
        self.explosions.add(explode)
        # self.hit_music.play_music()

class GameResultEvent:
    def __init__(self, normal_variables,my_tank,teammate_tank,enemy_tanks):
        self.normal_variables = normal_variables
        self.my_tank = my_tank
        self.teammate_tank = teammate_tank
        self.enemy_tanks = enemy_tanks

    def game_result_update(self):
        self.game_win_check()
        self.game_lose_check()
        self.game_result_check()

    def game_lose_check(self):
        if self.normal_variables.is_multiplayer:
            if self.my_tank.hp<=0 and self.teammate_tank.hp<=0:
                self.normal_variables.game_lose = True
        else:
            if self.my_tank.hp<=0:
                self.normal_variables.game_lose = True

    def game_win_check(self):
        if self.normal_variables.remaining_enemies <= 0:
            self.normal_variables.game_win = True
    def game_result_check(self):
        nv = self.normal_variables
        if nv.game_win:
            my_font = pygame.font.Font(cfg.FONTPATH, 50)
            win_text = my_font.render('You Win', True, pygame.Color(255, 0, 0))
            nv.window.blit(win_text, ( nv.window_size[0] / 2 - win_text.get_width() / 2, nv.window_size[1] / 2 - win_text.get_height() / 2))
        elif nv.game_lose:
            # 加载失败图片
            game_over_image = pygame.image.load(cfg.OTHER_IMAGE_PATHS['gameover'])
            logo_width = 300
            logo_height = int(game_over_image.get_height() * (logo_width / game_over_image.get_width()))
            game_over_image = pygame.transform.scale(game_over_image, (logo_width, logo_height))
            nv.window.blit(game_over_image, (nv.window_size[0] / 2 - game_over_image.get_width() / 2,nv.window_size[1] / 2 - game_over_image.get_height() / 2))
class RemoteEvent:
    def __init__(self,network_handler,my_tank,enemy_tanks,teammate_tank,my_bullets,enemy_bullets, walls,explosions,normal_variables):
        self.normal_variables = normal_variables
        self.explosions = explosions
        self.walls = walls
        self.my_bullets = my_bullets
        self.enemy_bullets = enemy_bullets
        self.network_handler = network_handler
        self.my_tank = my_tank
        self.enemy_tanks = enemy_tanks
        self.teammate_tank = teammate_tank


        self.init_attributes= {}
        self.old_attributes = {}
        self.change_attributes = {}

    def send_all_events(self):
        self.network_handler.send_entity_data(self.change_attributes)

    def send_init_attributes(self):
        self.network_handler.send_entity_data(self.init_attributes)
    def get_remote_tank_event(self):
        events=self.network_handler.run()
        self.normal_variables.teammate_event = events
        #events=['U','D','L','R','s_m','c_shot']
    def record_attributes(self):
        self.old_attributes['tanks'] = {}
        self.old_attributes['bullets'] = {}
        self.old_attributes['walls'] = {}
        self.old_attributes['explosions'] = {}

        # 修正：需将 enemy_tanks (Group) 转为 list 合并遍历
        all_tanks = [self.my_tank, self.teammate_tank] + list(self.enemy_tanks)
        for tank in all_tanks:
            if tank:
                self.old_attributes['tanks'][tank.id] = {
                    'position': tank.rect.topleft,
                    'direction': tank.direction[0],
                    'live': tank.live,
                    'hp': tank.hp,
                    'is_move': tank.is_move
                }

        # 修正：需将两个 Group 合并遍历
        all_bullets = list(self.my_bullets) + list(self.enemy_bullets)
        for bullet in all_bullets:
            self.old_attributes['bullets'][bullet.id] = {
                'position': bullet.rect.topleft,
                'direction': bullet.direction,
                'live': bullet.live,
                'speed': bullet.speed,
                'is_move': bullet.is_move
            }

        for wall in self.walls:
            self.old_attributes['walls'][wall.id] = {
                'position': wall.rect.topleft,
                'type': wall.type,
                'live': wall.live,
                'hp': wall.hp
            }

        for explosion in self.explosions:
            self.old_attributes['explosions'][explosion.id] = {
                'position': explosion.rect.topleft,
            }

    def record_change(self):
        self.change_attributes['tanks'] = []
        self.change_attributes['bullets'] = []
        self.change_attributes['walls'] = []
        self.change_attributes['explosions'] = []

        all_tanks = [self.my_tank, self.teammate_tank] + list(self.enemy_tanks)
        for tank in all_tanks:
            if not tank:
                continue

            old_tank = self.old_attributes['tanks'].get(tank.id)
            is_move = tank.rect.topleft != old_tank['position'] if old_tank else False
            tank.is_move = is_move

            # 判断是否产生变化：新实体 或 属性发生改变
            changed = (not old_tank or
                       tank.direction[0] != old_tank['direction'] or
                       is_move != old_tank['is_move'] or
                       tank.live != old_tank['live'])

            if changed:
                self.change_attributes['tanks'].append({
                    'id': tank.id,
                    'position': tank.rect.topleft,
                    'direction': tank.direction[0],
                    'live': tank.live,
                    'hp': tank.hp,
                    'is_move': is_move
                })

        all_bullets = list(self.my_bullets) + list(self.enemy_bullets)
        for bullet in all_bullets:
            old_bullet = self.old_attributes['bullets'].get(bullet.id)
            # 判断子弹状态是否变化：新实体 或 生存状态改变
            if not old_bullet or bullet.live != old_bullet['live']:
                self.change_attributes['bullets'].append({
                    'id': bullet.id,
                    'position': bullet.rect.topleft,
                    'direction': bullet.direction,
                    'live': bullet.live,
                    'speed': bullet.speed,
                    'is_move': bullet.is_move
                })

        for wall in self.walls:
            old_wall = self.old_attributes['walls'].get(wall.id)
            # 检测墙状态是否变化：新实体 或 生存状态改变
            if not old_wall or wall.live != old_wall['live']:
                self.change_attributes['walls'].append({
                    'id': wall.id,
                    'position': wall.rect.topleft,
                    'type': wall.type,
                    'live': wall.live,
                    'hp': wall.hp
                })

        for explosion in self.explosions:
            old_explosion = self.old_attributes['explosions'].get(explosion.id)
            # 检测爆炸状态是否变化：新实体 或 生存状态改变
            if not old_explosion:
                self.change_attributes['explosions'].append({
                    'id': explosion.id,
                    'position': explosion.rect.topleft,
                    'type': explosion.type
                })
    #初始化游戏数据后，将所有实体记录
    def record_all_attributes(self):
        self.change_attributes['tanks'] = []
        self.change_attributes['walls'] = []

        all_tanks = [self.my_tank, self.teammate_tank] + list(self.enemy_tanks)
        for tank in all_tanks:
            self.change_attributes['tanks'].append({
                'id': tank.id,
                'position': tank.rect.topleft,
                'direction': tank.direction[0],
                'live': tank.live,
                'hp': tank.hp,
                'is_move': False
            })


        for wall in self.walls:
            self.change_attributes['walls'].append({
                'id': wall.id,
                'position': wall.rect.topleft,
                'type': wall.type,
                'live': wall.live,
                'hp': wall.hp
            })

class MainGame:
    window = None

    my_tank = None
    teammate_tank = None
    enemy_tanks = Group()

    all_collision = Group()

    my_bullets = Group()
    enemy_bullets = Group()

    walls = Group()

    explosions = Group()

    clock = None

    def __init__(self):

        self.normal_variables = NormalVariables()

        self.panel_x = None
        self.level_config = None

        self.game_result_event = None
        self.remote_event = None
        self.scenes_event = None
        self.collision_event = None
        self.tanks_event = None
        self.bullet_event = None


        self.network_handler = None
        self.network_mode = None  # 'host' or 'join'

        self.fire_music = Sound(cfg.AUDIO_PATHS['fire'])
        self.hit_music = Sound(cfg.AUDIO_PATHS['hit'])

    def start_game(self, level='1'):
        """启动游戏，可指定关卡"""
        MainGame.window = pygame.display.set_mode((cfg.WIDTH + cfg.PANEL_WIDTH, cfg.HEIGHT))
        pygame.font.init()
        pygame.display.set_caption(cfg.TITLE)

        TankImageCache.initialize(cfg)
        OtherImageCache.initialize(cfg)

        MainGame.clock = pygame.time.Clock()

        nv = self.normal_variables
        nv.window = MainGame.window
        self.scenes_event = ScenesEvent(self.all_collision, self.walls, nv)
        # 加载指定关卡
        self.load_lvl(str(level))
        # Music(cfg.AUDIO_PATHS['start']).play_music()

        
        self.tanks_event=TanksEvent(self.my_tank,self.teammate_tank, self.enemy_tanks,self.my_bullets ,self.enemy_bullets, self.walls, self.all_collision, nv)
        self.tanks_event.tank_creation()

        self.remote_event=RemoteEvent(self.network_handler,self.my_tank,self.enemy_tanks,self.teammate_tank,self.my_bullets,self.enemy_bullets, self.walls,self.explosions,nv)
        self.game_result_event=GameResultEvent(nv,self.my_tank,self.teammate_tank,self.enemy_tanks)
        self.collision_event=CollisionEvent(self.my_tank,self.teammate_tank, self.enemy_tanks,self.my_bullets ,self.enemy_bullets, self.walls, self.explosions, nv)

        self.bullet_event=BulletsEvent(self.my_bullets,self.enemy_bullets,self.normal_variables)



        while True:
            MainGame.clock.tick(cfg.INITIAL_TICK)

            self.get_event()

            self.update()
            self.render()

            pygame.display.update()

    def start_multiplayer_game(self, mode='host', level='1'):
        self.network_mode = mode
        self.is_multiplayer = True

        # 初始化网络
        self.network_handler = ServerHandler(level, port=12345)
        while not self.network_handler.is_connected:
            time.sleep(1)

        # 启动游戏窗口
        MainGame.window = pygame.display.set_mode((cfg.WIDTH + cfg.PANEL_WIDTH, cfg.HEIGHT))
        pygame.font.init()
        pygame.display.set_caption(cfg.TITLE + " - 多人游戏")

        TankImageCache.initialize(cfg)
        OtherImageCache.initialize(cfg)

        MainGame.clock = pygame.time.Clock()

        nv = self.normal_variables
        nv.window = MainGame.window
        self.scenes_event = ScenesEvent(self.all_collision, self.walls, nv)
        # 加载指定关卡
        self.load_lvl(str(level))
        # Music(cfg.AUDIO_PATHS['start']).play_music()

        self.tanks_event = TanksEvent(self.my_tank, self.teammate_tank, self.enemy_tanks, self.my_bullets,
                                      self.enemy_bullets, self.walls, self.all_collision, nv)
        self.tanks_event.tank_creation()
        self.remote_event = RemoteEvent(self.network_handler, self.my_tank, self.enemy_tanks, self.teammate_tank,
                                        self.my_bullets, self.enemy_bullets, self.walls, self.explosions, nv)
        self.game_result_event = GameResultEvent(nv, self.my_tank, self.teammate_tank, self.enemy_tanks)
        self.collision_event = CollisionEvent(self.my_tank, self.teammate_tank, self.enemy_tanks, self.my_bullets,
                                              self.enemy_bullets, self.walls, self.explosions, nv)

        self.bullet_event = BulletsEvent(self.my_bullets, self.enemy_bullets, self.normal_variables)
        # 发送初始化数据
        self.remote_event.send_init_attributes()
        # 游戏主循环
        try:
            while True:
                MainGame.clock.tick(cfg.INITIAL_TICK)

                self.get_event()

                self.update()
                self.render()

                pygame.display.update()
        finally:
            # 清理网络资源
            if self.network_handler:
                self.network_handler.disconnect()

    def load_lvl(self, level):
        """加载关卡文件"""
        nv=self.normal_variables

        path = cfg.LEVELFILEDIR + '/' + str(level) + '.lvl'

        # 检查文件是否存在
        if not os.path.exists(path):
            print(f"关卡文件不存在: {path}，使用默认关卡1")
            path = cfg.LEVELFILEDIR + '/1.lvl'

        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 清除现有对象（重新加载关卡时）
        MainGame.walls.empty()
        MainGame.enemy_tanks.empty()
        MainGame.all_collision.empty()
        MainGame.my_bullets.empty()
        MainGame.enemy_bullets.empty()
        MainGame.explosions.empty()

        # 解析配置参数
        config = {}
        num_row = 0

        for i, line in enumerate(lines):
            line = line.strip()

            if line.startswith('%TOTALENEMYNUM:'):
                config['total_enemy_num'] = int(line.split(':')[1])
            elif line.startswith('%MAXENEMYNUM:'):
                config['max_enemy_num'] = int(line.split(':')[1])
            elif line.startswith('%HOMEPOS:'):
                pos_str = line.split(':')[1]
                x, y = map(int, pos_str.split(','))
                config['home_pos'] = (x, y)
            elif line.startswith('%HOMEAROUNDPOS:'):
                pos_str = line.split(':')[1]
                positions = []
                for pos in pos_str.split():
                    x, y = map(int, pos.split(','))
                    positions.append((x, y))
                config['home_around_pos'] = positions
            elif line.startswith('%PLAYERTANKPOS:'):
                pos_str = line.split(':')[1]
                positions = []
                for pos in pos_str.split():
                    x, y = map(int, pos.split(','))
                    positions.append((x, y))
                config['player_tank_pos'] = positions
            elif line.startswith('%ENEMYTANKPOS:'):
                pos_str = line.split(':')[1]
                positions = []
                for pos in pos_str.split():
                    x, y = map(int, pos.split(','))
                    positions.append((x * self.normal_variables.cell_len, y * self.normal_variables.cell_len))
                config['enemy_tank_pos'] = positions
            elif line and not line.startswith('#') and not line.startswith('%'):
                for row_i, elem in enumerate(line.split(' ')):
                    self.scenes_event.scenes_creation(elem,(row_i * self.normal_variables.cell_len, num_row * self.normal_variables.cell_len))
                num_row += 1

        # 保存关卡配置
        self.level_config = config
        print(f"成功加载关卡 {level}")
        print(config)

        # 更新敌方坦克数量
        nv.max_enemy_tanks = config.get('max_enemy_num', 6)
        nv.total_enemy_tanks = config.get('total_enemy_num', 12)
        nv.remaining_enemies = nv.total_enemy_tanks
        player_positions = config.get('player_tank_pos', [(8, 24), (16, 24)])
        nv.initial_reborn_position = (player_positions[0][0] * nv.cell_len, player_positions[0][1] * nv.cell_len)
        nv.teammate_reborn_position = (player_positions[1][0] * nv.cell_len, player_positions[1][1] * nv.cell_len)
        nv.enemy_tanks_positions = config.get('enemy_tank_pos', [(0, 0), (288, 0), (576, 0)])



    def update(self):

        self.tanks_event.tanks_update()
        self.bullet_event.bullets_update()
        self.collision_event.collision_update()

        # 更新菜单
        self.menu()

        # # 更新远程玩家
        # if self.is_multiplayer:
        #     self.get_remote_tank_event()
        #     self.teammate_tank_event()

        # 碰撞检测（关键步骤）

    def render(self):
        """渲染所有元素"""
        self.window.fill((0, 0, 0))
        # 加载并显示背景图片
        background_image = pygame.image.load(cfg.OTHER_IMAGE_PATHS['background'])
        self.window.blit(background_image, (0, 0))

        self.tanks_event.render()

        self.bullet_event.render()
        self.scenes_event.render()

        self.game_result_event.game_result_update()

        self.collision_event.render()

        enemy_text = self.get_text_surface(f"敌人: {self.normal_variables.remaining_enemies}", 20)
        self.window.blit(enemy_text, (self.panel_x, 10))

        if self.my_tank:
            hp_text = self.get_text_surface(f"血量: {self.my_tank.hp}", 20)
            self.window.blit(hp_text, (self.panel_x, 50))


        pygame.display.update()

    def menu(self):
        # 显示右侧信息面板
        self.panel_x = cfg.WIDTH + 10

    def get_text_surface(self, text, size=25):

        my_font = pygame.font.Font(cfg.FONTPATH, size)
        text_surface = my_font.render(text, True, pygame.Color(255, 0, 0))
        return text_surface

    def get_event(self):
        nv=self.normal_variables
        event_list = pygame.event.get()
        for event in event_list:
            if event.type == pygame.QUIT:
                self.end_game()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and 'L' not in nv.key_order:
                    nv.key_order.append('L')
                elif event.key == pygame.K_RIGHT and 'R' not in nv.key_order:
                    nv.key_order.append('R')
                elif event.key == pygame.K_UP and 'U' not in nv.key_order:
                    nv.key_order.append('U')
                elif event.key == pygame.K_DOWN and 'D' not in nv.key_order:
                    nv.key_order.append('D')

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT and 'L' in nv.key_order:
                    nv.key_order.remove('L')
                elif event.key == pygame.K_RIGHT and 'R' in nv.key_order:
                    nv.key_order.remove('R')
                elif event.key == pygame.K_UP and 'U' in nv.key_order:
                    nv.key_order.remove('U')
                elif event.key == pygame.K_DOWN and 'D' in nv.key_order:
                    nv.key_order.remove('D')
        nv.keys_pressed = pygame.key.get_pressed()



    def end_game(self):
        # 清理网络资源
        if self.network_handler:
            self.network_handler.disconnect()
        print("退出游戏")
        pygame.quit()
        exit()
