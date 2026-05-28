# -*- coding: utf-8 -*-
import pygame
from time import sleep
import random

window_color=pygame.Color(255, 255, 255)
class Tank:


    def __init__(self,left,top,window)->None:
        self.window = window

        self.images = None
        self.direction = None
        self.img = None

        self.rect = None

        self.speed = 5



    def display_tank(self):
        self.img = self.images[self.direction]
        self.window.blit(self.img, self.rect)

    def speed_change(self, change_direction,accelerate):
        pass

    def move(self,direction):
        self.direction = direction
        if self.direction == 'L':
            if self.rect.left > 0:
                self.rect = self.rect.move(-self.speed, 0)
        elif self.direction == 'R':
            if self.rect.right < self.window.get_rect().right:
                self.rect = self.rect.move(self.speed, 0)
        elif self.direction == 'U':
            if self.rect.top > 0:
                self.rect = self.rect.move(0, -self.speed)
        elif self.direction == 'D':
            if self.rect.bottom < self.window.get_rect().bottom:
                self.rect = self.rect.move(0, self.speed)

    def shot(self):
        pass

class MyTank(Tank):
    def __init__(self,left,top,window):
        super().__init__(left,top,window)
        self.images = {
            'U': pygame.image.load('img/p1tankU.gif'),
            'D': pygame.image.load('img/p1tankD.gif'),
            'L': pygame.image.load('img/p1tankL.gif'),
            'R': pygame.image.load('img/p1tankR.gif')
        }
        self.direction = 'U'
        self.img = self.images[self.direction]
        self.rect = self.img.get_rect()
        self.rect.center = [left, top]
class EnemyTank(Tank):
    def __init__(self, left,top,window):
        super().__init__(left,top,window)
        self.images = {
            'U': pygame.image.load('img/enemy1U.gif'),
            'D': pygame.image.load('img/enemy1D.gif'),
            'L': pygame.image.load('img/enemy1L.gif'),
            'R': pygame.image.load('img/enemy1R.gif')
        }
        self.direction = self.rand_direction()
        self.img = self.images[self.direction]
        self.rect = self.img.get_rect()
        self.rect.center = [left, top]

    def rand_direction(self)->str:
        choice=random.randint(1,4)
        if choice == 1:
            return 'L'
        elif choice == 2:
            return 'R'
        elif choice == 3:
            return 'U'
        elif choice == 4:
            return 'D'
class Bullet:
    def __init__(self):
        pass
    def display_bullet(self):
        pass
    def move(self):
        pass
class Wall:
    def __init__(self):
        pass
    def display_wall(self):
        pass
class Explode:
    def __init__(self):
        pass
    def display_explode(self):
        pass
class Music:
    def __init__(self):
        pass
    def play(self):
        pass

class MainGame:
    window = None
    my_tank = None
    enemy_tanks = []
    enemy_tanks_count = 6

    def __init__(self):
        self.key_order = []
    def start_game(self,window_size):
        pygame.display.init()
        self.window = pygame.display.set_mode(window_size)
        pygame.font.init()
        pygame.display.set_caption("Tank War")

        self.create_my_tank(350,500)
        self.create_enemy_tank()

        while True:
            sleep(0.02)
            self.window.fill(window_color)

            num=100
            text=self.get_text_surface(f"血量{num}")
            self.window.blit(text,(10,10))

            self.get_event()

            self.my_tank.display_tank()
            self.display_enemy_tank()

            pygame.display.update()

    def create_my_tank(self,left,top):
        self.my_tank = MyTank(left,top,self.window)

    def create_enemy_tank(self):
        for i in range(self.enemy_tanks_count):
            enemy_tank = EnemyTank(random.randint(0, 700), random.randint(0, 500),self.window)
            self.enemy_tanks.append(enemy_tank)

    def display_enemy_tank(self):
        for enemy_tank in self.enemy_tanks:
            enemy_tank.display_tank()

    def get_text_surface(self, text):

        my_font = pygame.font.Font("ttf/MSYH.ttf", 25)
        text_surface = my_font.render(text, True, pygame.Color(255, 0, 0))
        return text_surface

    def get_event(self):
        event_list = pygame.event.get()
        for event in event_list:
            if event.type == pygame.QUIT:
                print("退出游戏")
                pygame.quit()
                self.end_game()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and 'L' not in self.key_order:
                    self.key_order.append('L')
                elif event.key == pygame.K_RIGHT and 'R' not in self.key_order:
                    self.key_order.append('R')
                elif event.key == pygame.K_UP and 'U' not in self.key_order:
                    self.key_order.append('U')
                elif event.key == pygame.K_DOWN and 'D' not in self.key_order:
                    self.key_order.append('D')

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT and 'L' in self.key_order:
                    self.key_order.remove('L')
                elif event.key == pygame.K_RIGHT and 'R' in self.key_order:
                    self.key_order.remove('R')
                elif event.key == pygame.K_UP and 'U' in self.key_order:
                    self.key_order.remove('U')
                elif event.key == pygame.K_DOWN and 'D' in self.key_order:
                    self.key_order.remove('D')
        keys_pressed = pygame.key.get_pressed()
        self.tank_move_envent()


    def tank_move_envent(self):
        if self.key_order:
            last_direction = self.key_order[-1]
            self.my_tank.move(last_direction)

    def end_game(self):
        exit()


if __name__ == '__main__':
    MainGame().start_game((800,600))