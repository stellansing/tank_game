import pygame
from pygame.sprite import Sprite
from globalCache import OtherImageCache

import cfg


class Bullet(Sprite):
    def __init__(self, tank, bullet_id, position=None, direction=None):
        super().__init__()
        self.images = OtherImageCache.get_bullet_images()
        self.speed = 8
        self.id = bullet_id
        self.live = True
        self.is_move = False

        self.owner_tank=None
        if tank:
            #根据坦克位置和朝向确定位置
            self.owner_tank = tank
            self.img = self.images[self.owner_tank.direction[0]]
            self.direction = self.owner_tank.direction[0]
            self.rect = self.img.get_rect()
            self.bullet_initial_position()
        else:
            #直接给出位置
            self.img = self.images[direction]
            self.direction = direction
            self.rect = self.img.get_rect()
            self.rect.left, self.rect.top = position

    def bullet_initial_position(self):
        if self.direction == 'U':
            self.rect.left = self.owner_tank.rect.left + self.owner_tank.rect.width / 2 - self.rect.width / 2
            self.rect.top = self.owner_tank.rect.top - self.rect.height
        elif self.direction == 'D':
            self.rect.left = self.owner_tank.rect.left + self.owner_tank.rect.width / 2 - self.rect.width / 2
            self.rect.top = self.owner_tank.rect.top + self.owner_tank.rect.height
        elif self.direction == 'L':
            self.rect.left = self.owner_tank.rect.left - self.rect.width
            self.rect.top = self.owner_tank.rect.top + self.owner_tank.rect.height / 2 - self.rect.height / 2
        elif self.direction == 'R':
            self.rect.left = self.owner_tank.rect.left + self.owner_tank.rect.width
            self.rect.top = self.owner_tank.rect.top + self.owner_tank.rect.height / 2 - self.rect.height / 2

    def display_bullet(self, window):
        window.blit(self.img, self.rect)

    def move(self, game_window_size):
        if self.direction == 'U':
            if self.rect.top > 0:
                self.rect = self.rect.move(0, -self.speed)
            else:
                if self.owner_tank:
                    self.owner_tank.bullet_live = False
                self.kill()
        elif self.direction == 'D':
            if self.rect.bottom < game_window_size[1]:
                self.rect = self.rect.move(0, self.speed)
            else:
                if self.owner_tank:
                    self.owner_tank.bullet_live = False
                self.kill()
        elif self.direction == 'L':
            if self.rect.left > 0:
                self.rect = self.rect.move(-self.speed, 0)
            else:
                if self.owner_tank:
                    self.owner_tank.bullet_live = False
                self.kill()
        elif self.direction == 'R':
            if self.rect.right < game_window_size[0]:
                self.rect = self.rect.move(self.speed, 0)
            else:
                if self.owner_tank:
                    self.owner_tank.bullet_live = False
                self.kill()
