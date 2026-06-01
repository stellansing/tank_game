# -*- coding: utf-8 -*-
import pygame
from pygame.sprite import groupcollide,spritecollide

from modules.tool.music import *
from modules.entity.tank import *
from modules.tool.explode import *
from modules.entity.scenes import *
from modules.entity.bullet import *
import cfg
from modules.LoadGame import *

# class MainGame:
#     window = None
#     my_tank = None
#
#     enemy_tanks = Group()
#     all_collision = Group()
#
#     my_bullets = Group()
#     enemy_bullets = Group()
#
#     walls = Group()
#
#     explosions = Group()
#
#     enemy_tanks_count = 3
#     clock = None
#
#
#
#     def __init__(self):
#         pygame.display.init()
#         self.init_image_size()
#
#         self.key_order = []
#         self.my_tank_dead_time=0
#
#         self.reborn_interval=cfg.REBORN_INTERVAL
#
#         self.fire_music = Sound(cfg.AUDIO_PATHS['fire'])
#         self.hit_music = Sound(cfg.AUDIO_PATHS['hit'])
#
#
#     def init_image_size(self):
#         scene_sizes = {}
#         for key, path in cfg.SCENE_IMAGE_PATHS.items():
#             img = pygame.image.load(path)
#             scene_sizes[key] = img.get_size()
#         cfg.SCENES_SIZE = scene_sizes
#
#     def start_game(self, window_size):
#         MainGame.window = pygame.display.set_mode(window_size)
#         pygame.font.init()
#         pygame.display.set_caption(cfg.TITLE)
#
#         TankImageCache.initialize(cfg)
#         OtherImageCache.initialize(cfg)
#
#         MainGame.clock = pygame.time.Clock()
#
#         self.create_my_tank(cfg.INITIAL_REBORN)
#         self.create_enemy_tank()
#         self.create_steel_wall()
#         self.create_brick_wall()
#
#         Music(cfg.AUDIO_PATHS['start']).play_music()
#
#         while True:
#             MainGame.clock.tick(cfg.INITIAL_TICK)
#
#             num=100
#             text=self.get_text_surface(f"血量{num}")
#             MainGame.window.blit(text,(10,10))
#
#             self.get_event()
#
#             self.update()
#             self.render()
#
#             pygame.display.update()
#
#     def check_collision(self):
#         # 子弹和敌方坦克的碰撞
#         self.my_bullets.add(self.my_bullets)
#         default_collided = pygame.sprite.collide_rect_ratio(0.8)
#
#         hits=groupcollide(self.my_bullets,self.enemy_tanks,True,False,collided=default_collided)
#         for bullet,tanks in hits.items():
#             for tank in tanks:
#                 tank.hp-=1
#                 if tank.hp <= 0:
#                     tank.live = False
#                     tank.kill()
#                 self.create_explosion(tank)
#
#         groupcollide(self.enemy_bullets,self.my_bullets,True,True)
#
#         #我方坦克和子弹的碰撞
#         if self.my_tank and self.my_tank.live:
#             hits = spritecollide(self.my_tank, self.enemy_bullets, False,collided=default_collided)
#             if hits:
#                 self.my_tank.hp-=1
#                 self.my_tank.live = False
#                 self.create_explosion(self.my_tank)
#                 self.my_tank_dead_time=pygame.time.get_ticks()
#
#         #子弹与墙的碰撞
#         hits=pygame.sprite.groupcollide(self.walls, self.my_bullets, False, True)
#         for wall, bullets in hits.items():
#             self.create_bullet_explosion(wall)
#             if wall.type=='brick':
#                 wall.hp-=1
#             if wall.hp<=0:
#                 wall.live=False
#                 wall.kill()
#
#         hits = pygame.sprite.groupcollide(self.walls, self.enemy_bullets, False, True)
#         for wall, bullets in hits.items():
#             self.create_bullet_explosion(wall)
#             if wall.type=='brick':
#                 wall.hp-=1
#             if wall.hp<=0:
#                 wall.live=False
#                 wall.kill()
#
#
#
#
#
#     def update(self):
#         # 移动所有子弹
#         for bullet in self.my_bullets:
#             bullet.move(self.window)
#         for bullet in self.enemy_bullets:
#             bullet.move(self.window)
#
#         # 敌方坦克移动和射击
#         self.enemy_tank_event()
#
#         # 我的坦克移动
#         self.my_tank_envent()
#
#         # 碰撞检测（关键步骤）
#         self.check_collision()
#
#
#     def render(self):
#         """渲染所有元素"""
#         self.window.fill(cfg.WINDOW_COLOR)
#
#         if self.my_tank and self.my_tank.live:
#             self.my_tank.display_tank()
#         elif pygame.time.get_ticks()-self.my_tank_dead_time>self.reborn_interval and self.my_tank.hp>=0:#考虑移至更新模块中处理
#             self.reborn_tank(self.my_tank,cfg.INITIAL_REBORN)
#
#         for enemy in self.enemy_tanks:
#             enemy.display_tank()
#
#         for bullet in self.my_bullets:
#             bullet.display_bullet(self.window)
#         for bullet in self.enemy_bullets:
#             bullet.display_bullet(self.window)
#
#         #加载墙壁
#         for wall in self.walls:
#             wall.display_static_entity(self.window)
#
#         if MainGame.explosions:
#             ready_remove = []
#             for explosion in MainGame.explosions:
#                 if explosion.live:
#                     explosion.display_explode(self.window)
#                 else:
#                     ready_remove.append(explosion)
#             MainGame.explosions = Group([e for e in MainGame.explosions if e not in ready_remove])
#
#         # 显示血量等UI
#         text = self.get_text_surface(f"敌人数: {len(self.enemy_tanks)}")
#         self.window.blit(text, (10, 10))
#
#         pygame.display.update()
#
#
#     def create_explosion(self,tank:Tank):
#         explode = Explode(tank)
#         MainGame.explosions.add(explode)
#         self.hit_music.play_music()
#
#     def create_bullet_explosion(self,wall):
#         explode = BulletExplode(wall)
#         MainGame.explosions.add(explode)
#         self.hit_music.play_music()
#
#     def create_my_tank(self,initial_reborn):
#         self.my_tank = MyTank((initial_reborn[0],initial_reborn[1]),self.window)
#         MainGame.all_collision.add(self.my_tank)
#
#     def create_enemy_tank(self):
#         for i in range(self.enemy_tanks_count):
#             enemy_tank = EnemyTank((i*120, 300),self.window )
#             self.enemy_tanks.add(enemy_tank)
#             MainGame.all_collision.add(enemy_tank)
#
#     def create_steel_wall(self):
#         for i in range(10):
#             steel = WallGroup((i * 120, 400), 'iron')
#             steel.add_to(MainGame.walls)
#             steel.add_to(MainGame.all_collision)
#
#     def create_brick_wall(self):
#         for i in range(10):
#             wall = WallGroup((i * 120, 200), 'brick')
#             wall.add_to(MainGame.walls)
#             wall.add_to(MainGame.all_collision)
#
#     def reborn_tank(self,tank,position):
#         tank.rect.left, tank.rect.top = position
#         tank.direction = 'U1'
#         other_tanks = Group([t for t in MainGame.all_collision if t != tank])  # 考虑n*n矩阵，空间换时间
#         if not pygame.sprite.spritecollideany(tank, other_tanks):
#             tank.live= True
#
#     def my_tank_move(self,tank,direction):
#         old_rect = tank.rect.copy()
#         tank.move(direction)
#
#         other_tanks = Group([t for t in MainGame.all_collision if t != tank])  # 考虑n*n矩阵，空间换时间
#         if pygame.sprite.spritecollideany(tank, other_tanks):
#             tank.rect = old_rect
#
#     def enemy_tank_move(self,tank):
#         old_rect = tank.rect.copy()
#         tank.rand_move()
#
#         other_tanks = Group([t for t in MainGame.all_collision if t != tank])  # 考虑n*n矩阵，空间换时间
#         if pygame.sprite.spritecollideany(tank, other_tanks):
#             tank.rect = old_rect
#
#     def enemy_tank_event(self):
#         for enemy in self.enemy_tanks:
#             self.enemy_tank_move(enemy)
#             bullet = enemy.shot()
#             if bullet:
#                 # print("敌方发射子弹")
#                 self.enemy_bullets.add(bullet)
#
#     def my_tank_envent(self):
#
#         if self.key_order and self.my_tank and self.my_tank.live:
#             last_direction = self.key_order[-1]
#             self.my_tank_move(self.my_tank, last_direction)
#
#     def get_text_surface(self, text):
#
#         my_font = pygame.font.Font(cfg.FONTPATH, 25)
#         text_surface = my_font.render(text, True, pygame.Color(255, 0, 0))
#         return text_surface
#
#     def get_event(self):
#         event_list = pygame.event.get()
#         for event in event_list:
#             if event.type == pygame.QUIT:
#                 self.end_game()
#             if event.type == pygame.KEYDOWN:
#                 if event.key == pygame.K_LEFT and 'L' not in self.key_order:
#                     self.key_order.append('L')
#                 elif event.key == pygame.K_RIGHT and 'R' not in self.key_order:
#                     self.key_order.append('R')
#                 elif event.key == pygame.K_UP and 'U' not in self.key_order:
#                     self.key_order.append('U')
#                 elif event.key == pygame.K_DOWN and 'D' not in self.key_order:
#                     self.key_order.append('D')
#
#             if event.type == pygame.KEYUP:
#                 if event.key == pygame.K_LEFT and 'L' in self.key_order:
#                     self.key_order.remove('L')
#                 elif event.key == pygame.K_RIGHT and 'R' in self.key_order:
#                     self.key_order.remove('R')
#                 elif event.key == pygame.K_UP and 'U' in self.key_order:
#                     self.key_order.remove('U')
#                 elif event.key == pygame.K_DOWN and 'D' in self.key_order:
#                     self.key_order.remove('D')
#         keys_pressed = pygame.key.get_pressed()
#         if keys_pressed[pygame.K_SPACE] and self.my_tank and self.my_tank.live:
#             bullet = self.my_tank.shot()
#             if bullet:
#                 self.my_bullets.add(bullet)
#
#                 self.fire_music.play_music()
#
#
#     def end_game(self):
#         print("退出游戏")
#         pygame.quit()
#         exit()


if __name__ == '__main__':
    MainGame().start_game()