import pygame
from pygame.sprite import Sprite
from modules.tool.time import TimeComputer
from modules.entity.bullet import Bullet
from globalCache import TankImageCache
import random


class Tank(Sprite):
    """坦克基类，提供移动、射击、动画等通用功能"""

    def __init__(self, position, window, game_window_size: tuple,
                 tank_id) -> None:
        super().__init__()
        # 在子类中进行具体的实现
        self.owner_window = window
        self.game_window_size = game_window_size

        self.images = None
        self.image = None

        self.current_frame = 0
        self.animation_timer = 0
        self.animation_interval = 100

        self.rect = None
        self.id = tank_id
        self.hp = 3
        self.live = True
        self.is_move = False
        self.direction = None

        self.last_dead_time = 0

        self.speed = 2
        self.normal_speed = 2
        self.ice_speed = 4
        self.on_ice = False
        self.ice_inertia_direction = None
        self.shot_speed = 300
        self.bullet_live = False

        self.shot_time_computer = TimeComputer(self.shot_speed)
        self.tank_animation_time_computer = \
            TimeComputer(self.animation_interval)

        # 击杀计数器
        self.kills = 0

    def display_tank(self):
        """在窗口中渲染坦克"""
        if self.images and self.direction in self.images:
            self.image = self.images[self.direction]
            if self.image:
                self.owner_window.blit(self.image, self.rect)

    def update_animation(self):
        """更新坦克动画帧"""
        if self.tank_animation_time_computer.set_interval():
            self.current_frame = 1 - self.current_frame

    def change_direction(self, direction):
        """改变坦克方向（保留当前帧编号）"""
        self.direction = str(direction) + self.direction[1]

    def move(self, direction):
        """按指定方向移动坦克"""
        if direction == 'L':
            if self.rect.left > 0:
                self.rect = self.rect.move(-self.speed, 0)
        elif direction == 'R':
            if self.rect.right < self.game_window_size[0]:
                self.rect = self.rect.move(self.speed, 0)
        elif direction == 'U':
            if self.rect.top > 0:
                self.rect = self.rect.move(0, -self.speed)
        elif direction == 'D':
            if self.rect.bottom < self.game_window_size[1]:
                self.rect = self.rect.move(0, self.speed)

        self.direction = f"{direction}{self.current_frame + 1}"
        self.update_animation()

    def shot(self, bullet_id):
        """发射子弹，返回Bullet实例；cd中则返回None"""
        if not self.bullet_live and self.shot_time_computer.set_interval():
            bullet = Bullet(self, bullet_id)
            self.bullet_live = True
            return bullet
        return None


class MyTank(Tank):
    """玩家坦克类"""
    def __init__(self, position, window, game_window_size: tuple,
                 tank_id, player_key='player1'):
        super().__init__(position, window, game_window_size, tank_id)
        self.player_key = player_key
        self.images = TankImageCache.get_player_tank_image(self.player_key, 0)
        self.direction = 'U1'
        self.image = self.images[self.direction] if self.images and self.direction in self.images else None
        self.rect = self.image.get_rect() if self.image else pygame.Rect(position[0], position[1], 0, 0)
        self.rect.left, self.rect.top = position


class EnemyTank(Tank):
    """敌方坦克类，具备随机移动逻辑"""
    def __init__(self, position, window, game_window_size: tuple,
                 tank_id):
        super().__init__(position, window, game_window_size, tank_id)

        self.enemy_type = '1'
        self.images = TankImageCache.get_enemy_tank_image(self.enemy_type, 0)
        self.direction = self.rand_direction() + '1'
        self.image = self.images[self.direction] if self.images and self.direction in self.images else None
        self.rect = self.image.get_rect() if self.image else pygame.Rect(position[0], position[1], 0, 0)
        self.rect.left, self.rect.top = position

        self.hp = 1
        self.step = 30
        self.last_position = self.rect.topleft

    def rand_direction(self) -> str:
        """随机返回一个方向字符(L/R/U/D)"""
        choice = random.randint(1, 4)
        rand_direction = None
        if choice == 1:
            rand_direction = 'L'
        elif choice == 2:
            rand_direction = 'R'
        elif choice == 3:
            rand_direction = 'U'
        elif choice == 4:
            rand_direction = 'D'
        return rand_direction

    def rand_move(self):
        """敌方坦克随机移动逻辑：卡住时改变方向"""
        if self.rect.topleft != self.last_position:
            self.last_position = self.rect.topleft
        else:
            self.step -= 1

        if self.step <= 0:
            self.step = 50
            self.move(self.rand_direction())
        else:
            self.move(self.direction[0])
