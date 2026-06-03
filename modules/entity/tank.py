import pygame
from pygame.sprite import Sprite,Group
from modules.tool.time import *
from modules.entity.bullet import *
from globalCache import TankImageCache
import random

class Tank(Sprite):


    def __init__(self,position,window,game_window_size:tuple,tank_id)->None:
        super().__init__()
        #在子类中进行具体的实现
        self.owner_window = window
        self.game_window_size = game_window_size

        self.id = tank_id

        self.images = None
        self.direction = None
        self.image = None
        self.rect = None

        self.current_frame = 0
        self.animation_timer = 0
        self.animation_interval = 100

        self.hp=None
        self.live = True

        self.speed = 2
        self.shot_speed = 2000

        self.shot_time_computer = TimeComputer(self.shot_speed)
        self.tank_animation_time_computer = TimeComputer(self.animation_interval)


    def display_tank(self):

        self.image = self.images[self.direction]
        self.owner_window.blit(self.image, self.rect)

    def update_animation(self):
        if self.tank_animation_time_computer.set_interval():
            self.current_frame = 1 - self.current_frame

    def speed_change(self, change_direction,accelerate):
        pass

    def move(self,direction):

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

    def shot(self):
        if self.shot_time_computer.set_interval():
            bullet = Bullet(self)
            return bullet
        return None

class MyTank(Tank):
    def __init__(self,position,window,game_window_size:tuple,tank_id):
        super().__init__(position,window,game_window_size,tank_id)
        self.player_key='player1'
        self.images = TankImageCache.get_player_tank_image(self.player_key,0)
        self.direction = 'U1'
        self.image = self.images[self.direction]
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = position

        self.hp = 3
class EnemyTank(Tank):
    def __init__(self, position, window, game_window_size:tuple, tank_id):
        super().__init__(position, window, game_window_size, tank_id)

        self.enemy_type = '1'
        self.images = TankImageCache.get_enemy_tank_image(self.enemy_type,0)
        self.direction = self.rand_direction()
        self.image = self.images[f"{self.direction}1"]
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = position

        self.hp = 1
        self.step=30
        self.last_position = self.rect.topleft

    def rand_direction(self)->str:
        choice=random.randint(1,4)
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

        if self.rect.topleft != self.last_position:
            self.last_position = self.rect.topleft
        else:
            self.step-= 1

        if self.step <= 0:
            self.step = 50
            self.move(self.rand_direction())
        else:
            self.move(self.direction[0])