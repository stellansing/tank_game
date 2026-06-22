import pygame
from pygame._sprite import Group
from pygame.sprite import groupcollide, spritecollide
import os
import time

from modules.tool.sound_manager import SoundManager
from modules.entity.tank import *
from modules.tool.explode import *
from modules.entity.scenes import *
from modules.entity.bullet import *
from modules.network import HostNetwork, ClientNetwork
from modules.network.protocol import GameStateSnapshot, NetworkMessage, InputData
from modules.user_manager import UserManager
from globalCache import OtherImageCache
import cfg


class NormalVariables:
    def __init__(self):
        self.teammate_reborn_position = None
        self.total_enemy_tanks = 0
        self.total_created_enemy_tanks = 0
        self.max_enemy_tanks = None
        self.remaining_enemies = self.total_enemy_tanks

        self.enemy_tanks_positions = None
        self.initial_reborn_position = cfg.INITIAL_REBORN
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

        self.home = None

        self.current_level = 1
        self.level_transition = False


class TanksEvent:
    def __init__(self, my_tank, enemy_tanks, my_bullets,
                 enemy_bullets, walls, all_collision, ices,
                 normal_variables):
        self.normal_variables = normal_variables
        self.all_collision = all_collision

        self.my_tank = my_tank

        self.enemy_tanks = enemy_tanks
        self.my_bullets = my_bullets
        self.ices = ices
        self.enemy_bullets = enemy_bullets

        self.walls = walls

        self.allocated_tank_id = 0
        self.allocated_bullet_id = 0

    def tanks_update(self):
        self.random_create_enemy_tanks()
        self.tanks_move()
        self.tanks_shot()

    def render(self):
        nv = self.normal_variables
        # 所有坦克的渲染
        if self.my_tank and self.my_tank.live:
            self.my_tank.display_tank()
        elif pygame.time.get_ticks() - self.my_tank.last_dead_time > nv.reborn_interval and self.my_tank.hp > 0:  # 考虑移至更新模块中处理
            self.tank_reborn(self.my_tank)

        for tank in self.enemy_tanks:
            tank.display_tank()

    def tank_creation(self):
        self.create_my_tank()
        self.allocated_tank_id += 1

    def create_my_tank(self):
        nv = self.normal_variables
        MainGame.my_tank = MyTank(nv.initial_reborn_position, nv.window, nv.window_size, self.allocated_tank_id)
        self.my_tank = MainGame.my_tank
        self.all_collision.add(MainGame.my_tank)

    # 随机创建敌人-更新
    def random_create_enemy_tanks(self):
        nv = self.normal_variables
        if len(self.enemy_tanks) < nv.max_enemy_tanks and nv.total_created_enemy_tanks < nv.total_enemy_tanks:
            position = random.choice(nv.enemy_tanks_positions)
            if not self.create_enemy_tank(position):
                self.allocated_tank_id -= 1

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
    # 射击-更新

    def tanks_shot(self):
        self.all_players_shot()
        self.enemy_tank_shot()

    def all_players_shot(self):
        nv = self.normal_variables
        if nv.keys_pressed:
            if nv.keys_pressed[pygame.K_SPACE] and self.my_tank and self.my_tank.live:
                bullet = self.my_tank.shot(self.allocated_bullet_id)
                if bullet:
                    self.allocated_bullet_id += 1
                    self.my_bullets.add(bullet)
                # self.fire_music.play_music()

    def enemy_tank_shot(self):
        for enemy in self.enemy_tanks:

            bullet = enemy.shot(self.allocated_bullet_id)
            if bullet:
                self.allocated_bullet_id += 1
                self.enemy_bullets.add(bullet)

    def tanks_move(self):
        self.all_players_move()
        self.all_enemy_tanks_move()

    def all_players_move(self):
        nv = self.normal_variables
        if self.my_tank and self.my_tank.live:
            if nv.key_order:
                last_direction = nv.key_order[-1]
                self.my_tank.ice_inertia_direction = last_direction
                self.player_tank_move(self.my_tank, last_direction)
            elif self.my_tank.on_ice and self.my_tank.ice_inertia_direction:
                self.player_tank_move(self.my_tank, self.my_tank.ice_inertia_direction)

    def player_tank_move(self, tank, direction):
        old_rect = tank.rect.copy()
        old_direction = tank.direction

        self.apply_ice_effect(tank)
        tank.move(direction)

        if old_direction[0] != direction:
            self.move_check(tank, direction, old_rect)  # 考虑减少耦合的修改

        other_tanks = Group([t for t in MainGame.all_collision if t != tank])  # 考虑n*n矩阵，空间换时间
        if pygame.sprite.spritecollideany(tank, other_tanks):
            tank.rect = old_rect

    def apply_ice_effect(self, tank):
        tank.on_ice = False
        for ice in self.ices:
            if tank.rect.colliderect(ice.rect):
                tank.on_ice = True
                tank.speed = tank.ice_speed
                break
        if not tank.on_ice:
            tank.speed = tank.normal_speed
            tank.ice_inertia_direction = None

    def all_enemy_tanks_move(self):
        for enemy in self.enemy_tanks:
            self.enemy_tank_move(enemy)

    def enemy_tank_move(self, tank):
        old_rect = tank.rect.copy()
        old_direction = tank.direction

        self.apply_ice_effect(tank)
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
            if offset > nv.cell_len / 2:
                tank.rect.top += nv.cell_len - offset
            elif offset > 0:
                tank.rect.top -= offset
            old_rect.top = tank.rect.top
        elif direction in ['U', 'D']:
            offset = tank.rect.left % nv.cell_len
            if offset > nv.cell_len / 2:
                tank.rect.left += nv.cell_len - offset
            elif offset > 0:
                tank.rect.left -= offset
            old_rect.left = tank.rect.left

    def tank_reborn(self, tank, position=None):
        nv = self.normal_variables
        if not position:
            position = nv.initial_reborn_position
        tank.rect.left, tank.rect.top = position
        tank.direction = 'U1'
        other_tanks = Group([t for t in MainGame.all_collision if t != tank])  # 考虑n*n矩阵，空间换时间
        if not pygame.sprite.spritecollideany(tank, other_tanks):
            self.all_collision.add(tank)
            tank.live = True


class BulletsEvent:
    def __init__(self, my_bullets, enemy_bullets,
                 normal_variables):
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
    def __init__(self, all_collision, walls, rivers, trees, ices,
                 normal_variables):
        self.normal_variables = normal_variables

        self.all_collision = all_collision
        self.walls = walls
        self.rivers = rivers
        self.trees = trees
        self.ices = ices

        self.allocated_scenes_id = 0
        self._river_variant_counter = 0

    def scenes_update(self):
        pass

    def render(self):
        nv = self.normal_variables
        for wall in self.walls:
            wall.display_static_entity(nv.window)
        for river in self.rivers:
            river.display_static_entity(nv.window)

    def render_ices(self):
        nv = self.normal_variables
        for ice in self.ices:
            ice.display_static_entity(nv.window)

    def render_trees(self):
        nv = self.normal_variables
        for tree in self.trees:
            tree.display_static_entity(nv.window)

    def scenes_creation(self, scenes_type, position):
        if scenes_type == 'B':
            self.create_brick_wall(position, self.allocated_scenes_id)
            self.allocated_scenes_id += 1
        elif scenes_type == 'I':
            self.create_steel_wall(position, self.allocated_scenes_id)
            self.allocated_scenes_id += 1
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
        left, top = position[0], position[1]
        variant = self._river_variant_counter % 2
        self._river_variant_counter += 1
        river = River((left, top), self.allocated_scenes_id, river_variant=variant)
        self.allocated_scenes_id += 1
        self.rivers.add(river)
        self.all_collision.add(river)

    def create_ice_wall(self, position):
        left, top = position[0], position[1]
        ice = Ice((left, top), self.allocated_scenes_id)
        self.allocated_scenes_id += 1
        self.ices.add(ice)

    def create_tree_wall(self, position):
        left, top = position[0], position[1]
        tree = Tree((left, top), self.allocated_scenes_id)
        self.allocated_scenes_id += 1
        self.trees.add(tree)


class CollisionEvent:
    def __init__(self, my_tank, enemy_tanks, my_bullets,
                 enemy_bullets, walls, rivers, explosions,
                 normal_variables, teammate_tank=None, home=None):
        self.normal_variables = normal_variables
        self.my_tank = my_tank
        self.teammate_tank = teammate_tank
        self.enemy_tanks = enemy_tanks

        self.my_bullets = my_bullets
        self.enemy_bullets = enemy_bullets

        self.walls = walls
        self.rivers = rivers
        self.explosions = explosions
        self.home = home

        self.default_collided = pygame.sprite.collide_rect_ratio(0.8)
        self._explosion_id_counter = 0

    def collision_update(self):
        self.tank_bullet_collision()
        self.bullet_wall_collision()
        self.bullet_home_collision()
        self.tank_move_collision()

    def render(self):
        nv = self.normal_variables
        if self.explosions:
            ready_remove = []
            for explosion in self.explosions:
                if explosion.live:
                    explosion.display_explode(nv.window)
                else:
                    ready_remove.append(explosion)
            for explosion in ready_remove:
                explosion.kill()

    def tank_bullet_collision(self):
        collision_results = {
            'explosion': []
        }

        # 子弹和敌方坦克的碰撞
        hits = groupcollide(self.my_bullets, self.enemy_tanks, True, True, collided=self.default_collided)
        for bullet, tanks in hits.items():
            if bullet.owner_tank:
                bullet.owner_tank.bullet_live = False
            for tank in tanks:
                tank.hp -= 1
                if tank.hp <= 0:
                    tank.live = False
                    self.normal_variables.remaining_enemies -= 1
                    tank.kill()
                    # 击杀计数：子弹所属坦克击杀数+1
                    if bullet.owner_tank:
                        bullet.owner_tank.kills += 1
                collision_results['explosion'].append(tank)

        # 子弹碰撞
        hits = groupcollide(self.enemy_bullets, self.my_bullets, True, True)
        for enemy_bullet, my_bullets in hits.items():
            if enemy_bullet.owner_tank:
                enemy_bullet.owner_tank.bullet_live = False
            for my_bullet in my_bullets:
                if my_bullet.owner_tank:
                    my_bullet.owner_tank.bullet_live = False

        # 我方坦克和子弹的碰撞
        if self.my_tank and self.my_tank.live:
            hits = spritecollide(self.my_tank, self.enemy_bullets, False, collided=self.default_collided)
            if hits:
                self.my_tank.hp -= 1
                self.my_tank.live = False
                self.my_tank.kill()
                collision_results['explosion'].append(self.my_tank)
                self.tank_dead(self.my_tank)

                for bullet in hits:
                    if bullet.owner_tank:
                        bullet.owner_tank.bullet_live = False

        # 队友坦克和子弹的碰撞
        if self.teammate_tank and self.teammate_tank.live:
            hits = spritecollide(self.teammate_tank, self.enemy_bullets, False, collided=self.default_collided)
            if hits:
                self.teammate_tank.hp -= 1
                self.teammate_tank.live = False
                self.teammate_tank.kill()
                collision_results['explosion'].append(self.teammate_tank)
                self.tank_dead(self.teammate_tank)

                for bullet in hits:
                    if bullet.owner_tank:
                        bullet.owner_tank.bullet_live = False

        for tank in collision_results['explosion']:
            self.create_explosion(tank)

    def tank_dead(self, tank):
        tank.last_dead_time = pygame.time.get_ticks()

    def bullet_wall_collision(self):
        # 子弹与墙的碰撞

        collision_results = {
            'explosion': []
        }

        hits = pygame.sprite.groupcollide(self.my_bullets, self.walls, True, False)
        for bullet, walls in hits.items():
            if bullet.owner_tank:
                bullet.owner_tank.bullet_live = False
            collision_results['explosion'].append(bullet)

            for wall in walls:
                if wall.type == 'brick':
                    wall.hp -= 1
                if wall.hp <= 0:
                    wall.live = False
                    wall.kill()

        hits = pygame.sprite.groupcollide(self.walls, self.enemy_bullets, False, True)
        for wall, bullets in hits.items():
            for bullet in bullets:
                if bullet.owner_tank:
                    bullet.owner_tank.bullet_live = False
                collision_results['explosion'].append(bullet)

            if wall.type == 'brick':
                wall.hp -= 1
            if wall.hp <= 0:
                wall.live = False
                wall.kill()

        for bullet in collision_results['explosion']:
            self.create_bullet_explosion(bullet)

    def bullet_home_collision(self):
        if self.home and self.home.live:
            hits = spritecollide(self.home, self.enemy_bullets, True)
            if hits:
                self.home.destroy()
                for bullet in hits:
                    if bullet.owner_tank:
                        bullet.owner_tank.bullet_live = False
                self.create_explosion_on_home()

    def create_explosion_on_home(self):
        explode = Explode(self.home, explode_id=self._explosion_id_counter)
        self._explosion_id_counter += 1
        self.explosions.add(explode)

    def tank_move_collision(self):
        pass

    def create_explosion(self, tank: Tank):
        explode = Explode(tank, explode_id=self._explosion_id_counter)
        self._explosion_id_counter += 1
        self.explosions.add(explode)

    def create_bullet_explosion(self, bullet):
        explode = BulletExplode(bullet, explode_id=self._explosion_id_counter)
        self._explosion_id_counter += 1
        self.explosions.add(explode)


class GameResultEvent:
    def __init__(self, normal_variables, my_tank, enemy_tanks,
                 teammate_tank=None):
        self.normal_variables = normal_variables
        self.my_tank = my_tank
        self.teammate_tank = teammate_tank
        self.enemy_tanks = enemy_tanks

    def game_result_update(self):
        self.game_win_check()
        self.game_lose_check()
        self.game_result_check()

    def check_game_state(self):
        self.game_win_check()
        self.game_lose_check()

    def render_game_result(self):
        self.game_result_check()

    def game_lose_check(self):
        # home 被击毁直接判负
        if self.normal_variables.home and self.normal_variables.home.destroyed:
            self.normal_variables.game_lose = True
            return
        # 双人模式：所有玩家都死亡才算输
        if self.my_tank and self.my_tank.hp <= 0:
            if self.teammate_tank is None or self.teammate_tank.hp <= 0:
                self.normal_variables.game_lose = True

    def game_win_check(self):
        if self.normal_variables.remaining_enemies <= 0:
            self.normal_variables.game_win = True

    def game_result_check(self):
        nv = self.normal_variables
        if nv.game_win:
            my_font = pygame.font.Font(cfg.FONT_PATH, 50)
            win_text = my_font.render('You Win', True, pygame.Color(255, 0, 0))
            nv.window.blit(win_text, (nv.window_size[0] / 2 - win_text.get_width() / 2, nv.window_size[1] / 2 - win_text.get_height() / 2))
            return True
        elif nv.game_lose:
            # 加载失败图片
            game_over_image = OtherImageCache.get_other_image('gameover')
            logo_width = 300
            logo_height = int(game_over_image.get_height() * (logo_width / game_over_image.get_width()))
            game_over_image = pygame.transform.scale(game_over_image, (logo_width, logo_height))
            nv.window.blit(game_over_image, (nv.window_size[0] / 2 - game_over_image.get_width() / 2, nv.window_size[1] / 2 - game_over_image.get_height() / 2))
            return True
        return False


class MainGame:
    window = None

    my_tank = None
    enemy_tanks = Group()

    all_collision = Group()

    my_bullets = Group()
    enemy_bullets = Group()

    walls = Group()

    explosions = Group()
    rivers = Group()
    trees = Group()
    ices = Group()

    clock = None

    TRANSITION_DELAY = 3000

    def __init__(self, username=None):

        self.username = username
        self.normal_variables = NormalVariables()

        self.panel_x = None
        self.level_config = None

        self.game_result_event = None
        self.scenes_event = None
        self.collision_event = None
        self.tanks_event = None
        self.bullet_event = None

        # 关卡切换相关
        self._transition_timer = 0
        self._last_level_kills = 0  # 上一关的击杀数

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
        self.scenes_event = ScenesEvent(self.all_collision, self.walls, self.rivers, self.trees, self.ices, nv)
        # 加载指定关卡
        self.load_lvl(str(level))

        self.tanks_event = TanksEvent(self.my_tank, self.enemy_tanks,
                                      self.my_bullets, self.enemy_bullets,
                                      self.walls, self.all_collision,
                                      self.ices, nv)
        self.tanks_event.tank_creation()

        self.game_result_event = GameResultEvent(nv, self.my_tank, self.enemy_tanks)
        self.collision_event = CollisionEvent(self.my_tank, self.enemy_tanks,
                                              self.my_bullets,
                                              self.enemy_bullets, self.walls,
                                              self.rivers, self.explosions, nv,
                                              home=nv.home)

        self.bullet_event = BulletsEvent(self.my_bullets, self.enemy_bullets,
                                         self.normal_variables)
        self.panel_x = cfg.WIDTH + 10
        SoundManager.play_start()

        self._transition_timer = 0
        while True:
            MainGame.clock.tick(cfg.INITIAL_TICK)

            self.get_event()

            nv = self.normal_variables

            # 处理关卡胜利/失败过渡
            if nv.game_win or nv.game_lose:
                # 过渡初始化
                if self._transition_timer == 0:
                    self._transition_timer = pygame.time.get_ticks()
                    # 首次进入过渡时保存击杀数
                    if nv.game_win and self.my_tank:
                        self._last_level_kills = self.my_tank.kills

                self.render()
                if nv.game_win:
                    self._render_transition_kills()
                pygame.display.update()

                if pygame.time.get_ticks() - self._transition_timer > self.TRANSITION_DELAY:
                    if nv.game_win:
                        # 记录本关胜利数据
                        if self.username:
                            UserManager.save_game_record(
                                self.username, nv.current_level,
                                is_win=True, kills=self._last_level_kills
                            )
                        next_level = nv.current_level + 1
                        if self.level_exists(next_level):
                            self._reset_and_load_level(next_level)
                            self._transition_timer = 0
                            continue
                        # 全部通关，返回主菜单
                        pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT))
                        return
                    # 失败，记录并返回主菜单
                    if self.username:
                        lose_kills = self.my_tank.kills if self.my_tank else 0
                        UserManager.save_game_record(
                            self.username, nv.current_level,
                            is_win=False, kills=lose_kills
                        )
                    # 将窗口恢复为原始大小
                    pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT))
                    return
                # 过渡中
                continue

            # 主游戏逻辑
            self.update()
            self.render()

            pygame.display.update()

    def load_lvl(self, level):
        """加载关卡文件"""
        nv = self.normal_variables

        path = cfg.LEVEL_FILE_DIR + '/' + str(level) + '.lvl'

        # 检查文件是否存在
        if not os.path.exists(path):
            print(f"关卡文件不存在: {path}，使用默认关卡1")
            path = cfg.LEVEL_FILE_DIR + '/1.lvl'

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
                    self.scenes_event.scenes_creation(elem, (row_i * self.normal_variables.cell_len, num_row * self.normal_variables.cell_len))
                num_row += 1

        # 创建 home
        home_pos = config.get('home_pos')
        if home_pos:
            pixel_pos = (home_pos[0] * nv.cell_len, home_pos[1] * nv.cell_len)
            nv.home = Home(pixel_pos)

        # 保存关卡配置
        nv.current_level = int(str(level))
        self.level_config = config
        print(f"成功加载关卡 {level}")

        # 更新敌方坦克数量
        nv.max_enemy_tanks = config.get('max_enemy_num', 6)
        nv.total_enemy_tanks = config.get('total_enemy_num', 12)
        nv.remaining_enemies = nv.total_enemy_tanks
        player_positions = config.get('player_tank_pos', [(8, 24), (16, 24)])
        nv.initial_reborn_position = (player_positions[0][0] * nv.cell_len, player_positions[0][1] * nv.cell_len)
        if len(player_positions) > 1:
            nv.teammate_reborn_position = (player_positions[1][0] * nv.cell_len, player_positions[1][1] * nv.cell_len)
        else:
            nv.teammate_reborn_position = nv.initial_reborn_position
        nv.enemy_tanks_positions = config.get('enemy_tank_pos', [(0, 0), (288, 0), (576, 0)])

    def update(self):

        self.tanks_event.tanks_update()
        self.bullet_event.bullets_update()
        self.collision_event.collision_update()

        # 更新菜单
        self.menu()

    def render(self):
        """渲染所有元素"""
        nv = self.normal_variables

        self.window.fill((0, 0, 0))
        # 加载并显示背景图片
        background_image = OtherImageCache.get_other_image('background')
        self.window.blit(background_image, (0, 0))

        # 先检查游戏状态（不渲染）
        self.game_result_event.check_game_state()

        # 渲染场景（墙壁、河流）
        self.scenes_event.render()
        # 冰场景渲染在坦克下面
        self.scenes_event.render_ices()

        self.tanks_event.render()
        self.bullet_event.render()

        # 渲染 home
        if nv.home:
            nv.home.display_static_entity(nv.window)

        self.scenes_event.render_trees()

        self.collision_event.render()
        # 游戏结果渲染在所有图层之上
        self.game_result_event.render_game_result()

        self.render_panel()

    def menu(self):
        # 显示右侧信息面板
        self.panel_x = cfg.WIDTH + 10

    def render_panel(self):
        """渲染信息面板"""
        enemy_text = self.get_text_surface(f"敌人: {self.normal_variables.remaining_enemies}", 20)
        self.window.blit(enemy_text, (self.panel_x, 10))

        if self.my_tank:
            hp_text = self.get_text_surface(f"血量: {self.my_tank.hp}", 20)
            self.window.blit(hp_text, (self.panel_x, 50))

    def get_text_surface(self, text, size=25):

        my_font = pygame.font.Font(cfg.FONT_PATH, size)
        text_surface = my_font.render(text, True, pygame.Color(255, 0, 0))
        return text_surface

    def get_event(self):
        nv = self.normal_variables
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
        print("退出游戏")
        pygame.quit()
        exit()

    @staticmethod
    def level_exists(level):
        """检查关卡文件是否存在"""
        path = os.path.join(cfg.LEVEL_FILE_DIR, f'{level}.lvl')
        return os.path.exists(path)

    def _reset_and_load_level(self, level):
        """重置游戏状态并加载新关卡"""

        # 清空所有精灵组
        MainGame.walls.empty()
        MainGame.enemy_tanks.empty()
        MainGame.all_collision.empty()
        MainGame.my_bullets.empty()
        MainGame.enemy_bullets.empty()
        MainGame.explosions.empty()
        MainGame.rivers.empty()
        MainGame.trees.empty()
        MainGame.ices.empty()

        nv = self.normal_variables
        nv.game_win = False
        nv.game_lose = False
        nv.key_order = []
        nv.keys_pressed = None
        nv.home = None
        nv.total_created_enemy_tanks = 0

        # 加载新关卡
        self.load_lvl(str(level))

        # 重建坦克（保留累计击杀数由_tanks_event管理）
        self.tanks_event.allocated_tank_id = 0
        self.tanks_event.allocated_bullet_id = 0
        self.tanks_event.tank_creation()
        if self.my_tank:
            self.my_tank.kills = 0  # 每关击杀数清零

        # 重建事件处理器
        self.game_result_event = GameResultEvent(nv, self.my_tank, self.enemy_tanks)
        self.collision_event = CollisionEvent(
            self.my_tank, self.enemy_tanks, self.my_bullets, self.enemy_bullets,
            self.walls, self.rivers, self.explosions, nv, home=nv.home
        )
        self.bullet_event = BulletsEvent(self.my_bullets, self.enemy_bullets, nv)

    def _render_transition_kills(self):
        """在关卡切换时渲染击杀统计"""
        nv = self.normal_variables
        my_font = pygame.font.Font(cfg.FONT_PATH, 36)
        kills = self._last_level_kills
        kills_text = my_font.render(f'击杀: {kills}', True, pygame.Color(255, 255, 0))
        text_x = nv.window_size[0] / 2 - kills_text.get_width() / 2
        text_y = nv.window_size[1] / 2 + 40
        nv.window.blit(kills_text, (text_x, text_y))


class MultiplayerGame:
    TRANSITION_DELAY = 3000  # 关卡切换显示时间（毫秒）

    def __init__(self, host_network=None, host_ip=None, username=None):
        # 主机则传入network对象并依据此判断标记
        self._host_network = host_network
        self._host_ip = host_ip
        self._client_network = None
        self._is_host = host_network is not None

        self.username = username

        # 游戏变量
        self._window = None
        self._clock = None
        self._running = False
        self._panel_x = None

        # Host端：队友坦克（客户端控制的坦克）
        self._teammate_tank = None
        self.last_teammate_direction = None
        self.last_is_teammate_shot = True

        # Client端：渲染用的精灵组
        self._render_tanks = pygame.sprite.Group()
        self._render_bullets = pygame.sprite.Group()
        self._render_walls = pygame.sprite.Group()
        self._render_ices = pygame.sprite.Group()
        self._render_trees = pygame.sprite.Group()
        self._render_explosions = pygame.sprite.Group()
        self._client_home = None

        # 关卡数据（Client端从Host接收）
        self._level_config = None
        self._walls_data = None
        self._game_started = False

        # 主机端使用的MainGame实例
        self._main_game = None

        # 关卡切换相关
        self._transition_timer = 0
        self._last_p1_kills = 0
        self._last_p2_kills = 0
        self._game_over_sent = False

    def start_game(self, level='1', is_host=True):
        if is_host:
            self._start_as_host(level)
        else:
            self._start_as_client()

    # ==================== Host端 ====================

    def _start_as_host(self, level):
        # 初始化游戏
        MainGame.window = pygame.display.set_mode((cfg.WIDTH + cfg.PANEL_WIDTH, cfg.HEIGHT))
        pygame.font.init()
        pygame.display.set_caption(cfg.TITLE + " - Host")

        TankImageCache.initialize(cfg)
        OtherImageCache.initialize(cfg)

        MainGame.clock = pygame.time.Clock()
        self._window = MainGame.window

        # 创建NormalVariables
        self.nv = NormalVariables()
        self.nv.window = self._window
        self.nv.is_multiplayer = True

        # 创建SceneEvent并加载关卡
        self._scenes_event = ScenesEvent(
            MainGame.all_collision, MainGame.walls,
            MainGame.rivers, MainGame.trees, MainGame.ices, self.nv
        )
        self._load_level_for_host(level)

        # 发送关卡数据给客户端
        self._send_level_data_to_client()

        # 创建Host玩家的坦克
        player_pos = self.nv.initial_reborn_position
        teammate_pos = self.nv.teammate_reborn_position

        # 先创建Host坦克（TanksEvent需要引用）
        self._create_host_tank(player_pos)

        # 创建TanksEvent
        self._tanks_event = TanksEvent(
            self._my_tank, MainGame.enemy_tanks,
            MainGame.my_bullets, MainGame.enemy_bullets,
            MainGame.walls, MainGame.all_collision, MainGame.ices, self.nv
        )

        # 创建队友坦克（客户端控制）
        self._create_teammate_tank(teammate_pos)

        # 设置已分配的ID以避免冲突
        self._tanks_event.allocated_tank_id = 2
        self._tanks_event.allocated_bullet_id = 0

        # 初始化其他事件
        self._game_result_event = GameResultEvent(
            self.nv, self._my_tank, MainGame.enemy_tanks,
            teammate_tank=self._teammate_tank
        )
        self._collision_event = CollisionEvent(
            self._my_tank, MainGame.enemy_tanks,
            MainGame.my_bullets, MainGame.enemy_bullets,
            MainGame.walls, MainGame.rivers, MainGame.explosions, self.nv,
            teammate_tank=self._teammate_tank,
            home=self.nv.home
        )
        self._bullet_event = BulletsEvent(
            MainGame.my_bullets, MainGame.enemy_bullets, self.nv
        )
        self._panel_x = cfg.WIDTH + 10
        SoundManager.play_start()

        # 通知客户端游戏开始
        self._host_network.send_game_start()
        self._game_started = True

        # 主游戏循环
        self._running = True
        self._transition_timer = 0
        while self._running:
            MainGame.clock.tick(cfg.INITIAL_TICK)

            self._get_host_events()

            nv = self.nv

            # 处理关卡胜利/失败过渡
            if nv.game_win or nv.game_lose:
                if self._transition_timer == 0:
                    self._transition_timer = pygame.time.get_ticks()
                    # 保存击杀数用于过渡显示
                    if nv.game_win:
                        self._last_p1_kills = self._my_tank.kills if self._my_tank else 0
                        self._last_p2_kills = self._teammate_tank.kills if self._teammate_tank else 0

                self._render_host()
                if nv.game_win:
                    self._render_multiplayer_transition_kills()

                # 网络更新
                self._host_network.update()
                # 同步状态到客户端
                self._sync_to_client()
                pygame.display.update()

                if pygame.time.get_ticks() - self._transition_timer > self.TRANSITION_DELAY:
                    if nv.game_win:
                        # 记录本关胜利数据
                        if self.username:
                            p1_kills = self._my_tank.kills if self._my_tank else 0
                            UserManager.save_game_record(
                                self.username, nv.current_level,
                                is_win=True, kills=p1_kills,
                                is_multiplayer=True, teammate="队友"
                            )
                        next_level = nv.current_level + 1
                        if MainGame.level_exists(next_level):
                            self._reset_host_level(next_level)
                            self._transition_timer = 0
                            self._game_over_sent = False
                            continue
                    # 全部通关或失败，退出
                    else:
                        # 记录失败数据
                        if self.username:
                            p1_kills = self._my_tank.kills if self._my_tank else 0
                            UserManager.save_game_record(
                                self.username, nv.current_level,
                                is_win=False, kills=p1_kills,
                                is_multiplayer=True, teammate="队友"
                            )
                        # 将窗口恢复为原始大小
                        pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT))
                        self._running = False
                continue

            self._update_host()
            self._render_host()

            # 网络更新
            self._host_network.update()

            # 同步状态到客户端
            self._sync_to_client()

            pygame.display.update()

        self._host_network.close()

    def _load_level_for_host(self, level):
        """Host端加载关卡（复用MainGame的load_lvl逻辑）"""
        nv = self.nv
        path = os.path.join(cfg.LEVEL_FILE_DIR, f'{level}.lvl')
        if not os.path.exists(path):
            path = os.path.join(cfg.LEVEL_FILE_DIR, '1.lvl')

        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 清除现有对象
        MainGame.walls.empty()
        MainGame.enemy_tanks.empty()
        MainGame.all_collision.empty()
        MainGame.my_bullets.empty()
        MainGame.enemy_bullets.empty()
        MainGame.explosions.empty()
        MainGame.rivers.empty()
        MainGame.trees.empty()
        MainGame.ices.empty()

        config = {}
        num_row = 0
        walls_list = []

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
                    positions.append((x * nv.cell_len, y * nv.cell_len))
                config['enemy_tank_pos'] = positions
            elif line and not line.startswith('#') and not line.startswith('%'):
                for row_i, elem in enumerate(line.split(' ')):
                    pos = (row_i * nv.cell_len, num_row * nv.cell_len)
                    self._scenes_event.scenes_creation(elem, pos)
                    # 捕获Host端分配的场景ID，确保Client端ID一致
                    scene_id = self._scenes_event.allocated_scenes_id - 1
                    walls_list.append({'type': elem, 'x': pos[0], 'y': pos[1], 'id': scene_id})
                num_row += 1

        self._level_config = config
        self._walls_data = walls_list

        nv.current_level = int(str(level))
        nv.max_enemy_tanks = config.get('max_enemy_num', 6)
        nv.total_enemy_tanks = config.get('total_enemy_num', 12)
        nv.remaining_enemies = nv.total_enemy_tanks
        player_positions = config.get('player_tank_pos', [(8, 24), (16, 24)])
        nv.initial_reborn_position = (player_positions[0][0] * nv.cell_len, player_positions[0][1] * nv.cell_len)
        if len(player_positions) > 1:
            nv.teammate_reborn_position = (player_positions[1][0] * nv.cell_len, player_positions[1][1] * nv.cell_len)
        else:
            nv.teammate_reborn_position = nv.initial_reborn_position
        nv.enemy_tanks_positions = config.get('enemy_tank_pos', [(0, 0), (288, 0), (576, 0)])

        # 创建 home
        home_pos = config.get('home_pos')
        if home_pos:
            pixel_pos = (home_pos[0] * nv.cell_len, home_pos[1] * nv.cell_len)
            nv.home = Home(pixel_pos)

    def _send_level_data_to_client(self):
        level_config_for_client = {
            'cell_len': self.nv.cell_len,
            'window_size': self.nv.window_size,
            'total_enemy_num': self.nv.total_enemy_tanks,
            'remaining_enemies': self.nv.remaining_enemies,
            'home_pos': self._level_config.get('home_pos'),
        }
        self._host_network.send_level_data(level_config_for_client, self._walls_data)
        # 等待一小段时间确保客户端收到
        time.sleep(0.1)

    def _create_host_tank(self, position):
        tank_id = 0
        self._my_tank = MyTank(
            position, self._window, self.nv.window_size,
            tank_id, player_key='player1'
        )
        MainGame.all_collision.add(self._my_tank)
        MainGame.my_tank = self._my_tank

    def _create_teammate_tank(self, position):
        self._teammate_tank = MyTank(
            position, self._window, self.nv.window_size,
            1, player_key='player2'
        )
        MainGame.all_collision.add(self._teammate_tank)

    def _get_host_events(self):
        nv = self.nv
        event_list = pygame.event.get()
        for event in event_list:
            if event.type == pygame.QUIT:
                self._running = False
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

        # 处理客户端输入
        client_input = self._host_network.latest_input
        if self._teammate_tank and self._teammate_tank.live:
            if client_input:
                self._process_client_input(client_input)
            else:
                self._continue_client_input()

    def _continue_client_input(self):
        # 移动队友坦克
        if self.last_teammate_direction:
            self._teammate_move(self.last_teammate_direction)

        # 射击
        if self.last_is_teammate_shot:
            bullet = self._teammate_tank.shot(
                self._tanks_event.allocated_bullet_id
            )
            if bullet:
                self._tanks_event.allocated_bullet_id += 1
                MainGame.my_bullets.add(bullet)

    def _process_client_input(self, input_data):

        # 移动队友坦克
        if input_data.key_order:
            direction = input_data.key_order[-1]
            self.last_teammate_direction = direction
            self._teammate_move(direction)
        else:
            self.last_teammate_direction = None

        # 射击
        if input_data.space_pressed:
            self.last_is_teammate_shot = True
            bullet = self._teammate_tank.shot(
                self._tanks_event.allocated_bullet_id
            )
            if bullet:
                self._tanks_event.allocated_bullet_id += 1
                MainGame.my_bullets.add(bullet)
        else:
            self.last_is_teammate_shot = False

    def _teammate_move(self, direction):
        if not self._teammate_tank or not self._teammate_tank.live:
            return

        old_rect = self._teammate_tank.rect.copy()
        old_direction = self._teammate_tank.direction

        self._tanks_event.apply_ice_effect(self._teammate_tank)

        self._teammate_tank.move(direction)

        if old_direction[0] != direction:
            self._tanks_event.move_check(self._teammate_tank, direction, old_rect)

        other_tanks = pygame.sprite.Group([t for t in MainGame.all_collision if t != self._teammate_tank])
        if pygame.sprite.spritecollideany(self._teammate_tank, other_tanks):
            self._teammate_tank.rect = old_rect

    def _update_host(self):
        self._tanks_event.tanks_update()
        self._bullet_event.bullets_update()
        self._collision_event.collision_update()

        # 队友坦克复活检查
        if self._teammate_tank and not self._teammate_tank.live:
            if pygame.time.get_ticks() - self._teammate_tank.last_dead_time > self.nv.reborn_interval:
                if self._teammate_tank.hp > 0:
                    self._tanks_event.tank_reborn(self._teammate_tank, self.nv.teammate_reborn_position)

        # 菜单
        self._panel_x = cfg.WIDTH + 10

    def _render_host(self):
        self._window.fill((0, 0, 0))
        background_image = OtherImageCache.get_other_image('background')
        self._window.blit(background_image, (0, 0))

        # 先检查游戏状态（不渲染）
        self._game_result_event.check_game_state()

        # 渲染场景（墙壁、河流）
        self._scenes_event.render()
        # 冰场景渲染在坦克下面
        self._scenes_event.render_ices()

        self._tanks_event.render()
        self._bullet_event.render()

        # 渲染队友坦克
        if self._teammate_tank and self._teammate_tank.live:
            self._teammate_tank.display_tank()

        self._collision_event.render()

        # 渲染 home
        if self.nv.home:
            self.nv.home.display_static_entity(self._window)

        # 渲染树木（最顶层，用于隐蔽效果）
        self._scenes_event.render_trees()

        # 检查游戏是否结束，通知客户端（只发送一次）
        # _game_over_sent 仅仅使用一次
        if not getattr(self, '_game_over_sent', False):
            if self.nv.game_win:
                self._host_network.send_game_over('win')
                self._game_over_sent = True
            elif self.nv.game_lose:
                self._host_network.send_game_over('lose')
                self._game_over_sent = True

        # 游戏结果渲染在所有图层之上
        self._game_result_event.render_game_result()

        # 信息面板
        enemy_text = self.get_text_surface(f"敌人: {self.nv.remaining_enemies}", 20)
        self._window.blit(enemy_text, (self._panel_x, 10))

        font = pygame.font.Font(cfg.FONT_PATH, 20)
        if self._my_tank:
            hp_text = font.render(f"P1血量: {self._my_tank.hp}", True, pygame.Color(255, 0, 0))
            self._window.blit(hp_text, (self._panel_x, 50))
        if self._teammate_tank:
            hp_text = font.render(f"P2血量: {self._teammate_tank.hp}", True, pygame.Color(0, 255, 0))
            self._window.blit(hp_text, (self._panel_x, 80))

    def _sync_to_client(self):
        snapshot = GameStateSnapshot()

        # 收集坦克数据
        if self._my_tank:
            snapshot.tanks.append(
                NetworkMessage.tank_to_data(self._my_tank, 'player1')
            )
        if self._teammate_tank:
            snapshot.tanks.append(
                NetworkMessage.tank_to_data(self._teammate_tank, 'player2')
            )
        for enemy in MainGame.enemy_tanks:
            snapshot.tanks.append(
                NetworkMessage.tank_to_data(enemy, 'enemy')
            )

        # 收集子弹数据
        for bullet in MainGame.my_bullets:
            snapshot.bullets.append(
                NetworkMessage.bullet_to_data(bullet)
            )
        for bullet in MainGame.enemy_bullets:
            snapshot.bullets.append(
                NetworkMessage.bullet_to_data(bullet)
            )

        # 收集墙体数据
        for wall in MainGame.walls:
            snapshot.walls.append(NetworkMessage.wall_to_data(wall))
        for river in MainGame.rivers:
            snapshot.walls.append(NetworkMessage.wall_to_data(river))

        # 收集爆炸数据
        for explosion in MainGame.explosions:
            snapshot.explosions.append(NetworkMessage.explosion_to_data(explosion))

        # home 数据
        if self.nv.home:
            snapshot.home = NetworkMessage.home_to_data(self.nv.home)

        # 游戏信息
        snapshot.game_info = NetworkMessage.game_info_to_data(
            self.nv, self._my_tank, self._teammate_tank
        )

        self._host_network.send_state(snapshot)

    # ==================== Client端 ====================

    def _reset_host_level(self, level):
        """Host端重置游戏状态并加载新关卡，同步到客户端"""
        nv = self.nv
        # 保存击杀数（用于过渡显示）
        self._last_p1_kills = self._my_tank.kills if self._my_tank else 0
        self._last_p2_kills = self._teammate_tank.kills if self._teammate_tank else 0

        # 清空所有精灵组
        MainGame.walls.empty()
        MainGame.enemy_tanks.empty()
        MainGame.all_collision.empty()
        MainGame.my_bullets.empty()
        MainGame.enemy_bullets.empty()
        MainGame.explosions.empty()
        MainGame.rivers.empty()
        MainGame.trees.empty()
        MainGame.ices.empty()

        nv.game_win = False
        nv.game_lose = False
        nv.key_order = []
        nv.keys_pressed = None
        nv.home = None
        nv.total_created_enemy_tanks = 0

        # 重建ScenesEvent（关键：让墙体ID从0重新开始，与Client端匹配）
        self._scenes_event = ScenesEvent(
            MainGame.all_collision, MainGame.walls,
            MainGame.rivers, MainGame.trees, MainGame.ices, nv
        )

        # 加载新关卡
        self._load_level_for_host(level)

        # 重建坦克
        player_pos = nv.initial_reborn_position
        teammate_pos = nv.teammate_reborn_position

        self._create_host_tank(player_pos)
        self._my_tank.kills = 0

        self._create_teammate_tank(teammate_pos)
        self._teammate_tank.kills = 0

        # 重建TanksEvent
        self._tanks_event = TanksEvent(
            self._my_tank, MainGame.enemy_tanks,
            MainGame.my_bullets, MainGame.enemy_bullets,
            MainGame.walls, MainGame.all_collision, MainGame.ices, nv
        )
        self._tanks_event.allocated_tank_id = 2
        self._tanks_event.allocated_bullet_id = 0

        # 重建事件处理器
        self._game_result_event = GameResultEvent(
            nv, self._my_tank, MainGame.enemy_tanks,
            teammate_tank=self._teammate_tank
        )
        self._collision_event = CollisionEvent(
            self._my_tank, MainGame.enemy_tanks,
            MainGame.my_bullets, MainGame.enemy_bullets,
            MainGame.walls, MainGame.rivers, MainGame.explosions, nv,
            teammate_tank=self._teammate_tank,
            home=nv.home
        )
        self._bullet_event = BulletsEvent(
            MainGame.my_bullets, MainGame.enemy_bullets, nv
        )

        # 同步新关卡数据到客户端
        self._send_level_data_to_client()
        self._host_network.send_game_start()

    def _render_multiplayer_transition_kills(self):
        """在联机关卡切换时渲染双方击杀统计"""
        nv = self.nv
        my_font = pygame.font.Font(cfg.FONT_PATH, 36)
        p1_text = my_font.render(f'P1击杀: {self._last_p1_kills}', True, pygame.Color(255, 255, 0))
        p2_text = my_font.render(f'P2击杀: {self._last_p2_kills}', True, pygame.Color(0, 255, 0))
        text_x = nv.window_size[0] / 2 - p1_text.get_width() / 2
        text_y = nv.window_size[1] / 2 + 40
        nv.window.blit(p1_text, (text_x, text_y))
        p2_x = nv.window_size[0] / 2 - p2_text.get_width() / 2
        p2_y = text_y + 45
        nv.window.blit(p2_text, (p2_x, p2_y))

    def _start_as_client(self):
        # 初始化窗口
        self._window = pygame.display.set_mode((cfg.WIDTH + cfg.PANEL_WIDTH, cfg.HEIGHT))
        pygame.font.init()
        pygame.display.set_caption(cfg.TITLE + " - Client")

        TankImageCache.initialize(cfg)
        OtherImageCache.initialize(cfg)

        self._clock = pygame.time.Clock()

        # 初始化客户端网络
        self._client_network = ClientNetwork()
        self._client_network.connect(self._host_ip)

        if not self._client_network.try_connect_handshake():
            print("[Client] 无法连接到Host")
            return

        # 等待接收关卡数据
        print("[Client] 等待接收关卡数据...")
        self._wait_for_level_data()

        if not self._level_config:
            print("[Client] 未收到关卡数据")
            self._client_network.close()
            return

        # 创建初始墙体
        self._create_walls_from_data()

        # 等待游戏开始信号
        print("[Client] 等待游戏开始...")
        self._wait_for_game_start()

        self._panel_x = cfg.WIDTH + 10
        self._running = True
        SoundManager.play_start()
        self._transition_timer = 0

        # Client主循环
        while self._running:
            self._clock.tick(cfg.INITIAL_TICK)

            self._get_client_events()
            self._client_network.update()

            if not self._client_network.is_connected:
                print("[Client] 与Host断开连接")
                self._running = False
                break

            # 处理关卡切换
            if self._client_network.pending_level_reset:
                print("[Client] 收到新关卡数据，重置场景...")
                self._level_config = self._client_network.level_config
                self._walls_data = self._client_network.walls_data
                self._render_tanks.empty()
                self._render_bullets.empty()
                self._render_ices.empty()
                self._render_trees.empty()
                self._render_explosions.empty()
                self._create_walls_from_data()
                self._game_started = False
                self._snapshot_game_info = {}
                self._transition_timer = 0
                # 跳过本帧的状态处理，等待下一帧Host的新快照
                self._render_client()
                pygame.display.update()
                continue

            # 处理接收到的状态（每帧都处理，包括过渡期间）
            self._process_received_state()

            # 检查游戏胜负并处理过渡
            game_info = getattr(self, '_snapshot_game_info', {})
            if game_info.get('game_win') or game_info.get('game_lose'):
                if self._transition_timer == 0:
                    self._transition_timer = pygame.time.get_ticks()

                self._render_client()
                if game_info.get('game_win'):
                    self._render_client_transition_kills(game_info)
                pygame.display.update()

                elapsed = pygame.time.get_ticks() - self._transition_timer
                if elapsed > self.TRANSITION_DELAY:
                    # 记录客户端游戏数据
                    if self.username and game_info:
                        is_win = game_info.get('game_win', False)
                        level = game_info.get('current_level', 1)
                        kills = game_info.get('player2_kills', 0)
                        UserManager.save_game_record(
                            self.username, level, is_win=is_win, kills=kills,
                            is_multiplayer=True, teammate="房主"
                        )
                    # Host会发送新关卡数据，等待接收
                    self._transition_timer = 0
            else:
                # 正常渲染
                self._render_client()
                pygame.display.update()

        # 将窗口恢复为原始大小
        pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT))
        self._client_network.close()

    def _wait_for_level_data(self, timeout=30.0):
        start = time.time()
        while time.time() - start < timeout:
            self._client_network.update()
            # 处理pygame事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return

            if self._client_network.level_config is not None:
                self._level_config = self._client_network.level_config
                self._walls_data = self._client_network.walls_data
                print(f"[Client] 收到关卡数据")
                return
            time.sleep(0.01)

    def _wait_for_game_start(self, timeout=30.0):
        start = time.time()
        while time.time() - start < timeout:
            self._client_network.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return

            if self._client_network.game_started:
                self._game_started = True
                print("[Client] 游戏开始!")
                return
            time.sleep(0.01)

    def _create_walls_from_data(self):
        self._render_walls.empty()
        if not self._walls_data:
            return

        for wall_data in self._walls_data:
            wall_type = wall_data['type']
            pos = (wall_data['x'], wall_data['y'])
            wall_id = wall_data.get('id', 0)  # 使用Host端分配的场景ID

            if wall_type == 'B':
                wall = BrickWall(pos, wall_id)
                self._render_walls.add(wall)
            elif wall_type == 'I':
                wall = SteelWall(pos, wall_id)
                self._render_walls.add(wall)
            elif wall_type == 'R':
                wall = River(pos, wall_id, river_variant=wall_id % 2)
                self._render_walls.add(wall)
            elif wall_type == 'C':
                wall = Ice(pos, wall_id)
                self._render_ices.add(wall)
            elif wall_type == 'T':
                wall = Tree(pos, wall_id)
                self._render_trees.add(wall)

        # 创建 Home
        if self._level_config and self._level_config.get('home_pos'):
            home_pos = self._level_config['home_pos']
            cell_len = self._level_config.get('cell_len', 24)
            pixel_pos = (home_pos[0] * cell_len, home_pos[1] * cell_len)
            self._client_home = Home(pixel_pos)
        else:
            self._client_home = None

    def _get_client_events(self):
        event_list = pygame.event.get()
        for event in event_list:
            if event.type == pygame.QUIT:
                self._running = False

        # 获取当前按键状态并发送
        keys = pygame.key.get_pressed()
        key_order = []
        if keys[pygame.K_LEFT]:
            key_order.append('L')
        if keys[pygame.K_RIGHT]:
            key_order.append('R')
        if keys[pygame.K_UP]:
            key_order.append('U')
        if keys[pygame.K_DOWN]:
            key_order.append('D')

        space_pressed = keys[pygame.K_SPACE]

        self._client_network.send_input(key_order, space_pressed)

    def _process_received_state(self):
        snapshot = self._client_network.latest_snapshot
        if snapshot is None:
            return

        # 更新坦克
        self._render_tanks.empty()
        for tank_snap in snapshot.tanks:
            if not tank_snap.get('live', True):
                continue
            tank_type = tank_snap.get('tank_type', 'enemy')
            pos = (tank_snap['x'], tank_snap['y'])

            if tank_type in ('player1', 'player2'):
                player_key = tank_type
                tank = MyTank(pos, self._window, (cfg.WIDTH, cfg.HEIGHT),
                              tank_snap['id'], player_key=player_key)
                tank.direction = tank_snap.get('direction', 'U1')
                tank.hp = tank_snap.get('hp', 3)
                tank.live = tank_snap.get('live', True)
                tank.image = tank.images[tank.direction]
                self._render_tanks.add(tank)
            else:
                tank = EnemyTank(pos, self._window, (cfg.WIDTH, cfg.HEIGHT),
                                 tank_snap['id'])
                tank.direction = tank_snap.get('direction', 'D1')
                tank.hp = tank_snap.get('hp', 1)
                tank.live = tank_snap.get('live', True)
                tank.image = tank.images[tank.direction]
                self._render_tanks.add(tank)

        # 更新子弹
        self._render_bullets.empty()
        for bullet_snap in snapshot.bullets:
            bullet = Bullet(None, bullet_snap['id'],
                            position=(bullet_snap['x'], bullet_snap['y']),
                            direction=bullet_snap['direction'])
            self._render_bullets.add(bullet)

        # 更新墙体（只在初始加载时创建，后续只更新状态）
        if snapshot.walls:
            wall_dict = {wd['id']: wd for wd in snapshot.walls}
            for wall in list(self._render_walls):
                wd = wall_dict.get(wall.id)
                if wd:
                    wall.hp = wd.get('hp', 1)
                    wall.live = wd.get('live', True)
                    if not wall.live:
                        wall.kill()
                else:
                    wall.kill()

            # 创建快照中有但本地缺失的新墙体
            existing_ids = {w.id for w in self._render_walls}
            for wd in snapshot.walls:
                wall_id = wd['id']
                if wall_id not in existing_ids:
                    wall_type = wd.get('wall_type', 'brick')
                    pos = (wd['x'], wd['y'])
                    if wall_type == 'steel':
                        wall = SteelWall(pos, wall_id)
                    else:
                        wall = BrickWall(pos, wall_id)
                    wall.hp = wd.get('hp', 1)
                    wall.live = wd.get('live', True)
                    if not wall.live:
                        wall.kill()
                    self._render_walls.add(wall)

        # 更新爆炸
        self._render_explosions.empty()
        for ed in snapshot.explosions:
            explode_type = ed.get('explode_type', 'explode')
            if explode_type == 'explode':
                exp = Explode(None, position=(ed['x'], ed['y']),
                              explode_id=ed['id'])
            else:
                exp = BulletExplode(None, position=(ed['x'], ed['y']),
                                    explode_id=ed['id'])
            exp.step = ed.get('step', 0)
            if exp.step < len(exp.images):
                exp.image = exp.images[exp.step]
            self._render_explosions.add(exp)

        # 更新 home 状态

        home_data = snapshot.home
        if home_data and self._client_home:
            self._client_home.live = home_data.get('live', True)
            self._client_home.destroyed = home_data.get('destroyed', False)
            if not self._client_home.live or self._client_home.destroyed:
                self._client_home.image = OtherImageCache.get_home_image('destroyed')

        # 检查游戏结束
        game_info = snapshot.game_info or {}
        if game_info.get('game_win'):
            print("[Client] 游戏胜利!")
        elif game_info.get('game_lose'):
            print("[Client] 游戏失败!")

        self._snapshot_game_info = game_info

    def _render_client(self):
        self._window.fill((0, 0, 0))
        background_image = OtherImageCache.get_other_image('background')
        self._window.blit(background_image, (0, 0))

        # 渲染墙体
        for wall in self._render_walls:
            if wall.live:
                wall.display_static_entity(self._window)

        # 冰场景渲染在坦克下面
        for ice in self._render_ices:
            ice.display_static_entity(self._window)

        # 渲染坦克
        for tank in self._render_tanks:
            tank.display_tank()

        # 渲染子弹
        for bullet in self._render_bullets:
            bullet.display_bullet(self._window)

        # 渲染 home
        if self._client_home:
            self._client_home.display_static_entity(self._window)

        # 渲染树木（最顶层，用于隐蔽效果）
        for tree in self._render_trees:
            tree.display_static_entity(self._window)

        # 渲染爆炸
        for explosion in self._render_explosions:
            if explosion.live:
                explosion.display_explode(self._window)

        # 信息面板
        game_info = getattr(self, '_snapshot_game_info', {})
        font = pygame.font.Font(cfg.FONT_PATH, 20)

        remaining = game_info.get('remaining_enemies', 0)
        enemy_text = font.render(f"敌人: {remaining}", True, pygame.Color(255, 0, 0))
        self._window.blit(enemy_text, (self._panel_x, 10))

        p1_hp = game_info.get('player1_hp', 0)
        hp_text = font.render(f"P1血量: {p1_hp}", True, pygame.Color(255, 0, 0))
        self._window.blit(hp_text, (self._panel_x, 50))

        p2_hp = game_info.get('player2_hp', 0)
        hp_text2 = font.render(f"P2血量: {p2_hp}", True, pygame.Color(0, 255, 0))
        self._window.blit(hp_text2, (self._panel_x, 80))

        # 游戏结束提示（在所有图层之上）
        if game_info.get('game_win'):
            my_font = pygame.font.Font(cfg.FONT_PATH, 50)
            win_text = my_font.render('You Win', True, pygame.Color(255, 0, 0))
            self._window.blit(win_text, (
                cfg.WIDTH / 2 - win_text.get_width() / 2,
                cfg.HEIGHT / 2 - win_text.get_height() / 2
            ))
        elif game_info.get('game_lose'):
            game_over_image = OtherImageCache.get_other_image('gameover')
            logo_width = 300
            logo_height = int(game_over_image.get_height() * (logo_width / game_over_image.get_width()))
            game_over_image = pygame.transform.scale(game_over_image, (logo_width, logo_height))
            self._window.blit(game_over_image, (
                cfg.WIDTH / 2 - game_over_image.get_width() / 2,
                cfg.HEIGHT / 2 - game_over_image.get_height() / 2
            ))

    def _render_client_transition_kills(self, game_info):
        """Client端渲染关卡切换时的击杀统计"""
        my_font = pygame.font.Font(cfg.FONT_PATH, 36)
        p1_kills = game_info.get('player1_kills', 0)
        p2_kills = game_info.get('player2_kills', 0)
        p1_text = my_font.render(f'P1击杀: {p1_kills}', True, pygame.Color(255, 255, 0))
        p2_text = my_font.render(f'P2击杀: {p2_kills}', True, pygame.Color(0, 255, 0))
        text_x = cfg.WIDTH / 2 - p1_text.get_width() / 2
        text_y = cfg.HEIGHT / 2 + 40
        self._window.blit(p1_text, (text_x, text_y))
        p2_x = cfg.WIDTH / 2 - p2_text.get_width() / 2
        p2_y = text_y + 45
        self._window.blit(p2_text, (p2_x, p2_y))

    def get_text_surface(self, text, size=25):
        my_font = pygame.font.Font(cfg.FONT_PATH, size)
        text_surface = my_font.render(text, True, pygame.Color(255, 0, 0))
        return text_surface
