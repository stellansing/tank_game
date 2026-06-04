import pygame
from pygame.sprite import Sprite

import cfg


class Bullet(Sprite):
    def __init__(self,tank,bullet_id,position=None,direction=None):
        super().__init__()
        self.images = {
            'U': pygame.image.load(cfg.BULLET_IMAGE_PATHS['U']),
            'D': pygame.image.load(cfg.BULLET_IMAGE_PATHS['D']),
            'L': pygame.image.load(cfg.BULLET_IMAGE_PATHS['L']),
            'R': pygame.image.load(cfg.BULLET_IMAGE_PATHS['R'])
        }
        self.speed = 8
        self.id = bullet_id
        self.live = True
        self.is_move = False
        if tank:
            self.owner_tank = tank
            self.img = self.images[self.owner_tank.direction[0]]
            self.direction = self.owner_tank.direction[0]
            self.rect = self.img.get_rect()
            self.bullet_initial_position()
        else:
            self.img = self.images[direction]
            self.direction = direction
            self.rect = self.img.get_rect()
            self.rect.left, self.rect.top = position







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

    def move(self,game_window_size):
        if self.direction == 'U':
            if self.rect.top > 0:
                self.rect = self.rect.move(0, -self.speed)
            else:
                self.kill()
        elif self.direction == 'D':
            if self.rect.bottom < game_window_size[1]:
                self.rect = self.rect.move(0, self.speed)
            else:
                self.kill()
        elif self.direction == 'L':
            if self.rect.left > 0:
                self.rect = self.rect.move(-self.speed, 0)
            else :
                self.kill()
        elif self.direction == 'R':
            if self.rect.right < game_window_size[0]:
                self.rect = self.rect.move(self.speed, 0)
            else:
                self.kill()

    def dead(self):
        self.live=False