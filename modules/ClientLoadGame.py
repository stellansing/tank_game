import pygame
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
        self.update_variables = {}


class TanksEvent:
    def __init__(self, my_tank, teammate_tank, enemy_tanks, my_bullets, enemy_bullets, walls, all_collision,
                 normal_variables):
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
        self.tanks_move()
        self.tanks_shot()

    def render(self):
        nv = self.normal_variables
        # 所有坦克的渲染
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

    def update_local_variables(self):
        nv = self.normal_variables
        try:
            tanks = self.normal_variables.update_variables['tanks']
        except KeyError:
            return
        is_full_sync = self.normal_variables.update_variables.get('full_sync', False)
        #暴力更新
        if tanks:
            received_tank_ids = set()
            for tank_data in tanks:
                received_tank_ids.add(tank_data['id'])
                is_had = False
                for old_tank in self.enemy_tanks:
                    if old_tank.id == tank_data['id']:
                        if tank_data['live']:
                            old_tank.hp = tank_data['hp']
                            old_tank.live = tank_data['live']
                            old_tank.direction = tank_data['direction'] + old_tank.direction[1] if len(old_tank.direction) > 1 else tank_data['direction'] + '1'
                            old_tank.is_move = tank_data['is_move']
                            old_tank.rect.left, old_tank.rect.top = tank_data['position']
                            is_had = True
                        else:
                            old_tank.kill()
                        break
                if not is_had:
                    if tank_data['id'] == 0:
                        if self.my_tank and self.my_tank.live:
                            self.my_tank.hp = tank_data['hp']
                            self.my_tank.live = tank_data['live']
                            self.my_tank.direction = tank_data['direction'] + '1'
                            self.my_tank.is_move = tank_data['is_move']
                            self.my_tank.rect.left, self.my_tank.rect.top = tank_data['position']
                        else:
                            ClientMainGame.my_tank = MyTank(tank_data['position'], nv.window, nv.window_size, 0)
                            self.my_tank = ClientMainGame.my_tank
                            self.all_collision.add(ClientMainGame.my_tank)
                    elif tank_data['id'] == 1:
                        if self.teammate_tank and self.teammate_tank.live:
                            self.teammate_tank.hp = tank_data['hp']
                            self.teammate_tank.live = tank_data['live']
                            self.teammate_tank.direction = tank_data['direction'] + '1'
                            self.teammate_tank.is_move = tank_data['is_move']
                            self.teammate_tank.rect.left, self.teammate_tank.rect.top = tank_data['position']
                        else:
                            ClientMainGame.teammate_tank = MyTank(tank_data['position'], nv.window, nv.window_size, 1)
                            self.teammate_tank = ClientMainGame.teammate_tank
                            self.all_collision.add(ClientMainGame.teammate_tank)
                    else:
                        enemy_tank = EnemyTank(tank_data['position'], nv.window, nv.window_size, tank_data['id'])
                        enemy_tank.direction = tank_data['direction'] + '1'
                        self.enemy_tanks.add(enemy_tank)
                        self.all_collision.add(enemy_tank)
            # 全量同步时，清理客户端多余的敌方坦克
            if is_full_sync:
                for old_tank in list(self.enemy_tanks):
                    if old_tank.id not in received_tank_ids:
                        old_tank.kill()

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
                if bullet:
                    self.allocated_bullet_id += 1
                    self.my_bullets.add(bullet)

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

        other_tanks = Group([t for t in ClientMainGame.all_collision if t != tank])  # 考虑n*n矩阵，空间换时间
        if pygame.sprite.spritecollideany(tank, other_tanks):
            tank.rect = old_rect

    def all_enemy_tanks_move(self):
        for enemy in self.enemy_tanks:
            self.enemy_tank_move(enemy)

    def predict_remote_tanks_move(self):
        """客户端预测：根据is_move和direction自行移动远程坦克
        在收到服务端权威数据之前先移动，保证帧与帧之间画面平滑
        服务端数据到达后会覆盖预测位置，确保最终一致性"""
        for enemy in self.enemy_tanks:
            if enemy.live and enemy.is_move:
                enemy.move(enemy.direction[0])

    def enemy_tank_move(self, tank):
        old_rect = tank.rect.copy()
        old_direction = tank.direction

        tank.rand_move()

        if old_direction[0] != tank.direction:
            self.move_check(tank, tank.direction, old_rect)

        other_tanks = Group([t for t in ClientMainGame.all_collision if t != tank])  # 考虑n*n矩阵，空间换时间
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

    def tank_reborn(self, tank):
        nv = self.normal_variables
        if tank == self.my_tank:
            position = nv.initial_reborn_position
        else:
            position = nv.teammate_reborn_position

        tank.rect.left, tank.rect.top = position
        tank.direction = 'U1'
        other_tanks = Group([t for t in ClientMainGame.all_collision if t != tank])  # 考虑n*n矩阵，空间换时间
        if not pygame.sprite.spritecollideany(tank, other_tanks):
            self.all_collision.add(tank)
            tank.live = True


class BulletsEvent:
    def __init__(self, my_bullets, enemy_bullets, normal_variables):
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

    def update_local_variables(self):
        nv = self.normal_variables
        try:
            bullets = self.normal_variables.update_variables['bullets']
        except KeyError:
            return
        is_full_sync = self.normal_variables.update_variables.get('full_sync', False)
        # 暴力更新
        if bullets:
            received_bullet_ids = set()
            for bullet_data in bullets:
                received_bullet_ids.add(bullet_data['id'])
                is_had = False
                for old_bullet in list(self.my_bullets) + list(self.enemy_bullets):
                    if old_bullet.id == bullet_data['id']:
                        if bullet_data.get('live', True):
                            old_bullet.live = bullet_data['live']
                            old_bullet.rect.left, old_bullet.rect.top = bullet_data['position']
                            old_bullet.direction = bullet_data['direction']
                        else:
                            old_bullet.live = False
                            old_bullet.kill()
                        is_had = True
                        break
                if not is_had and bullet_data.get('live', True):
                    new_bullet = Bullet(None, bullet_data['id'], position=bullet_data['position'], direction=bullet_data['direction'])
                    if bullet_data.get('owner_type') == 'enemy' or bullet_data['id'] > 1:
                        self.enemy_bullets.add(new_bullet)
                    else:
                        self.my_bullets.add(new_bullet)
            # 全量同步时，清理客户端多余子弹
            if is_full_sync:
                for old_bullet in list(self.my_bullets) + list(self.enemy_bullets):
                    if old_bullet.id not in received_bullet_ids:
                        old_bullet.kill()

    def bullets_move(self):
        for bullet in self.my_bullets:
            bullet.move(self.normal_variables.window_size)
        for bullet in self.enemy_bullets:
            bullet.move(self.normal_variables.window_size)


class ScenesEvent:
    def __init__(self, all_collision, walls, normal_variables):
        self.normal_variables = normal_variables

        self.all_collision = all_collision
        self.walls = walls

        self.allocated_scenes_id = 0

    def scenes_update(self):
        pass

    def render(self):
        nv = self.normal_variables
        for wall in self.walls:
            wall.display_static_entity(nv.window)

    def update_local_variables(self):
        nv = self.normal_variables
        try:
            scenes = self.normal_variables.update_variables['scenes']
        except KeyError:
            return
        is_full_sync = self.normal_variables.update_variables.get('full_sync', False)
        # 暴力更新
        if scenes:
            received_scene_ids = set()
            for scene in scenes:
                received_scene_ids.add(scene['id'])
                is_had = False
                for old_scene in self.walls:
                    if old_scene.id == scene['id']:
                        if scene.get('live', True):
                            old_scene.live = scene['live']
                            old_scene.hp = scene.get('hp', old_scene.hp)
                        else:
                            old_scene.live = False
                            old_scene.kill()
                        is_had = True
                        break
                if not is_had and scene.get('live', True):
                    if scene['type'] == 'brick':
                        self.create_brick_wall(scene['position'], scene['id'])
                    elif scene['type'] == 'steel':
                        self.create_steel_wall(scene['position'], scene['id'])
            # 全量同步时，清理客户端多余墙壁
            if is_full_sync:
                for old_scene in list(self.walls):
                    if old_scene.id not in received_scene_ids:
                        old_scene.kill()

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
    def __init__(self, my_tank, teammate_tank, enemy_tanks, my_bullets, enemy_bullets, walls, explosions,
                 normal_variables):
        self.normal_variables = normal_variables
        self.my_tank = my_tank
        self.teammate_tank = teammate_tank
        self.enemy_tanks = enemy_tanks

        self.my_bullets = my_bullets
        self.enemy_bullets = enemy_bullets

        self.walls = walls
        self.explosions = explosions

        self.default_collided = pygame.sprite.collide_rect_ratio(0.8)
        self._explosion_id_counter = 0

    def collision_update(self):
        self.tank_bullet_collision()
        self.bullet_wall_collision()
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

    def update_local_variables(self):
        nv = self.normal_variables
        try:
            explosions = self.normal_variables.update_variables['explosions']
        except KeyError:
            return
        is_full_sync = self.normal_variables.update_variables.get('full_sync', False)
        # 暴力更新
        if explosions:
            received_explosion_ids = set()
            for explosion in explosions:
                received_explosion_ids.add(explosion['id'])
                is_had = False
                for old_explosion in self.explosions:
                    if old_explosion.id == explosion['id']:
                        if explosion.get('live', True):
                            old_explosion.rect.center = explosion['position']
                        else:
                            old_explosion.live = False
                            old_explosion.kill()
                        is_had = True
                        break
                if not is_had and explosion.get('live', True):
                    # 根据类型判断创建哪种爆炸
                    ex = None
                    if explosion.get('type') == 'explode':
                        ex = Explode(None,explosion['position'])
                    elif explosion.get('type') == 'bullet_explode':
                        ex = BulletExplode(None,explosion['position'])
                    if ex:
                        self.explosions.add(ex)
            # 全量同步时，清理客户端多余爆炸
            if is_full_sync:
                for old_explosion in list(self.explosions):
                    if old_explosion.id not in received_explosion_ids:
                        old_explosion.kill()

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

        # 子弹碰撞
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

    def tank_dead(self, tank):
        tank.last_dead_time = pygame.time.get_ticks()

    def bullet_wall_collision(self):
        # 子弹与墙的碰撞

        collision_results = {
            'explosion': []
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
        explode = Explode(tank, explode_id=self._explosion_id_counter)
        self._explosion_id_counter += 1
        self.explosions.add(explode)
        # self.hit_music.play_music()

    def create_bullet_explosion(self, bullet):
        explode = BulletExplode(bullet, explode_id=self._explosion_id_counter)
        self._explosion_id_counter += 1
        self.explosions.add(explode)
        # self.hit_music.play_music()


class GameResultEvent:
    def __init__(self, normal_variables, my_tank, teammate_tank, enemy_tanks):
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
            if (self.my_tank and self.my_tank.hp <= 0) and (self.teammate_tank and self.teammate_tank.hp <= 0):
                self.normal_variables.game_lose = True
        else:
            if self.my_tank and self.my_tank.hp <= 0:
                self.normal_variables.game_lose = True

    def game_win_check(self):
        if self.normal_variables.remaining_enemies <= 0:
            self.normal_variables.game_win = True

    def game_result_check(self):
        nv = self.normal_variables
        if nv.game_win:
            my_font = pygame.font.Font(cfg.FONTPATH, 50)
            win_text = my_font.render('You Win', True, pygame.Color(255, 0, 0))
            nv.window.blit(win_text, (
            nv.window_size[0] / 2 - win_text.get_width() / 2, nv.window_size[1] / 2 - win_text.get_height() / 2))
        elif nv.game_lose:
            # 加载失败图片
            game_over_image = pygame.image.load(cfg.OTHER_IMAGE_PATHS['gameover'])
            logo_width = 300
            logo_height = int(game_over_image.get_height() * (logo_width / game_over_image.get_width()))
            game_over_image = pygame.transform.scale(game_over_image, (logo_width, logo_height))
            nv.window.blit(game_over_image, (nv.window_size[0] / 2 - game_over_image.get_width() / 2,
                                             nv.window_size[1] / 2 - game_over_image.get_height() / 2))


class RemoteEvent:
    def __init__(self, network_handler, my_tank, enemy_tanks, teammate_tank, my_bullets, enemy_bullets, walls,
                 explosions, normal_variables):
        self.normal_variables = normal_variables
        self.explosions = explosions
        self.walls = walls
        self.my_bullets = my_bullets
        self.enemy_bullets = enemy_bullets
        self.network_handler = network_handler
        self.my_tank = my_tank
        self.enemy_tanks = enemy_tanks
        self.teammate_tank = teammate_tank

        self.old_attributes = {}
        self.change_attributes = {}
        self._data_check_counter = 0
        self._data_check_interval = 60  # 每60帧（约1秒）发送一次数据校验

    def send_all_events(self):
        self.network_handler.send_entity_data(self.change_attributes)

    def get_remote_tank_event(self):
        events = self.network_handler.run()
        if events:
            self.normal_variables.teammate_event = events
        # events=['U','D','L','R','s_m','c_shot']

    def collect_all_current_data(self):
        """收集客户端当前所有实体数据（格式与服务端entity_update一致）"""
        data = {
            'tanks': [],
            'bullets': [],
            'scenes': [],
            'explosions': []
        }

        all_tanks = [self.my_tank, self.teammate_tank] + list(self.enemy_tanks)
        for tank in all_tanks:
            if tank:
                data['tanks'].append({
                    'id': tank.id,
                    'position': tank.rect.topleft,
                    'direction': tank.direction[0] if isinstance(tank.direction, str) and len(tank.direction) > 0 else 'U',
                    'live': tank.live,
                    'hp': tank.hp,
                    'is_move': tank.is_move
                })

        all_bullets = list(self.my_bullets) + list(self.enemy_bullets)
        for bullet in all_bullets:
            data['bullets'].append({
                'id': bullet.id,
                'position': bullet.rect.topleft,
                'direction': bullet.direction,
                'live': bullet.live,
                'speed': bullet.speed,
                'is_move': bullet.is_move
            })

        for wall in self.walls:
            data['scenes'].append({
                'id': wall.id,
                'position': wall.rect.topleft,
                'type': wall.type,
                'live': wall.live,
                'hp': wall.hp
            })

        for explosion in self.explosions:
            data['explosions'].append({
                'id': explosion.id,
                'position': explosion.rect.topleft,
                'type': getattr(explosion, 'type', 'explode')
            })

        return data

    def periodic_data_check(self):
        """周期性发送数据校验给主机"""
        self._data_check_counter += 1
        if self._data_check_counter >= self._data_check_interval:
            self._data_check_counter = 0
            all_data = self.collect_all_current_data()
            self.network_handler.send_data_check(all_data)

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
                })


class ClientMainGame:
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

    def start_multiplayer_game(self, mode='join'):
        self.network_mode = mode
        self.normal_variables.is_multiplayer = True

        # 初始化网络 - ClientHandler 会通过UDP广播查找主机并加入
        self.network_handler = ClientHandler(port=12345)
        while not self.network_handler.is_connected:
            pygame.time.delay(500)

        print(f"已连接到主机，关卡: {self.network_handler.get_level()}")
        # 启动游戏窗口
        ClientMainGame.window = pygame.display.set_mode((cfg.WIDTH + cfg.PANEL_WIDTH, cfg.HEIGHT))
        pygame.font.init()
        pygame.display.set_caption(cfg.TITLE + " - 多人游戏(客户端)")

        TankImageCache.initialize(cfg)
        OtherImageCache.initialize(cfg)

        ClientMainGame.clock = pygame.time.Clock()

        nv = self.normal_variables
        nv.window = ClientMainGame.window
        self.scenes_event = ScenesEvent(self.all_collision, self.walls, nv)

        self.tanks_event = TanksEvent(self.my_tank, self.teammate_tank, self.enemy_tanks, self.my_bullets,
                                      self.enemy_bullets, self.walls, self.all_collision, nv)
        self.remote_event = RemoteEvent(self.network_handler, self.my_tank, self.enemy_tanks, self.teammate_tank,
                                        self.my_bullets, self.enemy_bullets, self.walls, self.explosions, nv)
        self.game_result_event = GameResultEvent(nv, self.my_tank, self.teammate_tank, self.enemy_tanks)
        self.collision_event = CollisionEvent(self.my_tank, self.teammate_tank, self.enemy_tanks, self.my_bullets,
                                              self.enemy_bullets, self.walls, self.explosions, nv)

        self.bullet_event = BulletsEvent(self.my_bullets, self.enemy_bullets, self.normal_variables)
        self.panel_x = cfg.WIDTH + 10

        # 等待接收服务器初始实体数据（包含坦克、墙壁等完整场景）
        print("等待主机发送初始数据...")
        while True:
            data = self.network_handler.run()
            if data:
                nv.update_variables = data
                self.tanks_event.update_local_variables()
                self.bullet_event.update_local_variables()
                self.scenes_event.update_local_variables()
                self.collision_event.update_local_variables()
                nv.update_variables = {}
                break
            pygame.time.delay(100)

        print("初始数据已加载，通知主机...")
        self.network_handler.send_load_complete()
        print("开始游戏...")
        # 游戏主循环
        try:
            while True:
                ClientMainGame.clock.tick(cfg.INITIAL_TICK)

                self.get_event()

                self.update()
                self.render()

                pygame.display.update()
        finally:
            # 清理网络资源
            if self.network_handler:
                self.network_handler.disconnect()

    def update(self):
        if self.normal_variables.is_multiplayer:
            # 客户端预测：在接收服务端数据之前先按方向自行移动坦克，保证帧间平滑
            self.tanks_event.predict_remote_tanks_move()
            # 联机模式: 发送键盘事件给主机, 接收实体状态更新
            self._send_keyboard_events_to_host()
            self._receive_entity_updates()
            if self.normal_variables.update_variables:
                data = self.normal_variables.update_variables
                print(data)
                # 分别分发各类型数据到对应的事件处理器
                if data:
                    self.tanks_event.update_local_variables()
                    self.bullet_event.update_local_variables()
                    self.scenes_event.update_local_variables()
                    self.collision_event.update_local_variables()
                self.normal_variables.update_variables = {}
            # 周期性发送全量数据校验给主机
            self.remote_event.periodic_data_check()
        else:
            self.tanks_event.tanks_update()
            self.bullet_event.bullets_update()
            self.collision_event.collision_update()

        # 更新菜单
        self.menu()

    def _send_keyboard_events_to_host(self):
        """将本地键盘事件发送给主机"""
        nv = self.normal_variables
        events = []
        # 移动方向
        if nv.key_order:
            events.append(nv.key_order[-1])  # 最后按下的方向键
        else:
            events.append('s_m')  # 停止移动
        # 射击（空格键按下时发送c_shot切换事件）
        if nv.keys_pressed and nv.keys_pressed[pygame.K_SPACE]:
            events.append('c_shot')

        if events and self.network_handler:
            self.network_handler.send_keyboard_event(events)

    def _receive_entity_updates(self):
        """从主机接收实体状态更新"""
        if not self.network_handler:
            return
        data = self.network_handler.run()
        if data:
            self.normal_variables.update_variables = data

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

    def menu(self):
        # 显示右侧信息面板
        self.panel_x = cfg.WIDTH + 10

    def get_text_surface(self, text, size=25):

        my_font = pygame.font.Font(cfg.FONTPATH, size)
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
        if self.network_handler:
            self.network_handler.disconnect()
        print("退出游戏")
        pygame.quit()
        exit()
