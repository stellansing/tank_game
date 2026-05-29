# -*- coding: utf-8 -*-
import pygame
import random
from pygame.sprite import collide_rect,Sprite,Group,groupcollide,spritecollide

window_color=pygame.Color(255, 255, 255)

class TimeComputer:
    def __init__(self,interval):
        self.last_time = pygame.time.get_ticks()
        self.interval = interval
    def set_interval(self):
        if self.last_time + self.interval < pygame.time.get_ticks():
            self.last_time = pygame.time.get_ticks()
            return True
        else:
            return False
class Tank(Sprite):


    def __init__(self,left,top)->None:
        super().__init__()
        self.images = None
        self.direction = None
        self.img = None
        self.rect = None
        self.live = True

        self.speed = 5
        self.shot_speed = 500

        self.time_computer = TimeComputer(self.shot_speed)

    def display_tank(self):
        self.img = self.images[self.direction]
        MainGame.window.blit(self.img, self.rect)

    def speed_change(self, change_direction,accelerate):
        pass

    def move(self,direction):
        self.direction = direction
        if self.direction == 'L':
            if self.rect.left > 0:
                self.rect = self.rect.move(-self.speed, 0)
        elif self.direction == 'R':
            if self.rect.right < MainGame.window.get_rect().right:
                self.rect = self.rect.move(self.speed, 0)
        elif self.direction == 'U':
            if self.rect.top > 0:
                self.rect = self.rect.move(0, -self.speed)
        elif self.direction == 'D':
            if self.rect.bottom < MainGame.window.get_rect().bottom:
                self.rect = self.rect.move(0, self.speed)

    def shot(self):
        if not self.time_computer.set_interval():
            return None
        bullet = Bullet(self)
        bullet.bullet_initial_position()
        return bullet

class MyTank(Tank):
    def __init__(self,left,top):
        super().__init__(left,top)
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
    def __init__(self, left,top):
        super().__init__(left,top)
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

        self.step=50

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

    def rand_move(self):
        if self.step <= 0:
            self.step = 50
            self.direction = self.rand_direction()
        else:
            self.move(self.direction)
            self.step -= 1


class Bullet(Sprite):
    def __init__(self,tank):
        super().__init__()
        self.owner_tank = tank
        self.img = pygame.image.load('img/enemymissile.gif')
        self.direction=tank.direction
        self.rect = self.img.get_rect()
        self.speed = 8
        self.live=True

    def bullet_initial_position(self):
        if self.direction == 'U':
            self.rect.left=self.owner_tank.rect.left + self.owner_tank.rect.width / 2-self.rect.width / 2
            self.rect.top = self.owner_tank.rect.top-self.rect.height
        elif self.direction == 'D':
            self.rect.left=self.owner_tank.rect.left + self.owner_tank.rect.width / 2-self.rect.width / 2
            self.rect.top = self.owner_tank.rect.top + self.owner_tank.rect.height

        elif self.direction == 'L':
            self.rect.left = self.owner_tank.rect.left-self.rect.width
            self.rect.top=self.owner_tank.rect.top + self.owner_tank.rect.height / 2-self.rect.height / 2
        elif self.direction == 'R':
            self.rect.left = self.owner_tank.rect.left + self.owner_tank.rect.width
            self.rect.top=self.owner_tank.rect.top + self.owner_tank.rect.height / 2-self.rect.height / 2



    def display_bullet(self, window):
        window.blit(self.img, self.rect)

    def move(self, window):
        if self.direction == 'U':
            if self.rect.top > 0:
                self.rect = self.rect.move(0, -self.speed)
            else:
                self.live=False
        elif self.direction == 'D':
            if self.rect.bottom < window.get_rect().bottom:
                self.rect = self.rect.move(0, self.speed)
            else:
                self.live=False
        elif self.direction == 'L':
            if self.rect.left > 0:
                self.rect = self.rect.move(-self.speed, 0)
            else :
                self.live=False
        elif self.direction == 'R':
            if self.rect.right < window.get_rect().right:
                self.rect = self.rect.move(self.speed, 0)
            else:
                self.live=False

    def is_hit(self,tank):

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
    enemy_tanks = Group()
    my_bullets = Group()
    enemy_bullets = Group()
    enemy_tanks_count = 6
    clock = None

    def __init__(self):
        self.key_order = []
        self.bullets = []
    def start_game(self,window_size):
        pygame.display.init()
        MainGame.window = pygame.display.set_mode(window_size)
        pygame.font.init()
        pygame.display.set_caption("Tank War")

        MainGame.clock = pygame.time.Clock()

        self.create_my_tank(350,500)
        self.create_enemy_tank()

        while True:
            MainGame.clock.tick(60)
            MainGame.window.fill(window_color)

            num=100
            text=self.get_text_surface(f"血量{num}")
            MainGame.window.blit(text,(10,10))

            self.get_event()

            self.my_tank.display_tank()
            self.display_enemy_tank()
            self.display_bullet()

            pygame.display.update()

    def create_my_tank(self,left,top):
        self.my_tank = MyTank(left,top)

    def create_enemy_tank(self):
        for i in range(self.enemy_tanks_count):
            enemy_tank = EnemyTank(random.randint(0, 700), random.randint(0, 500))
            self.enemy_tanks.append(enemy_tank)

    def display_enemy_tank(self):
        for enemy_tank in self.enemy_tanks:
            enemy_tank.display_tank()
            enemy_tank.rand_move()
            bullet = enemy_tank.shot()
            if bullet:
                self.bullets.append(bullet)

    def display_bullet(self):
        for bullet in self.bullets:
            if bullet.live:
                bullet.display_bullet(MainGame.window)
                bullet.move(MainGame.window)
            else:
                self.bullets.remove(bullet)


    def get_text_surface(self, text):

        my_font = pygame.font.Font("ttf/MSYH.ttf", 25)
        text_surface = my_font.render(text, True, pygame.Color(255, 0, 0))
        return text_surface

    def get_event(self):
        event_list = pygame.event.get()
        for event in event_list:
            if event.type == pygame.QUIT:
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
        if keys_pressed[pygame.K_SPACE]:
            bullet = self.my_tank.shot()
            if bullet:
                self.bullets.append(bullet)

        self.tank_move_envent()


    def tank_move_envent(self):

        if self.key_order:
            last_direction = self.key_order[-1]
            self.my_tank.move(last_direction)

    def end_game(self):
        print("退出游戏")
        pygame.quit()
        exit()


if __name__ == '__main__':
    MainGame().start_game((800,600))