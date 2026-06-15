import pygame
from pygame.sprite import Sprite
import cfg
from globalCache import OtherImageCache

class StaticEntity(Sprite):
    def __init__(self, position: tuple, entity_id):
        super().__init__()
        self.image = None
        self.rect = None

        self.position = position
        self.id = entity_id
        self.hp = None
        self.live = True

    def display_static_entity(self, window):
        window.blit(self.image, self.rect)

class SteelWall(StaticEntity):
    def __init__(self,position: tuple,entity_id):
        super().__init__(position,entity_id)
        self.type = 'steel'
        self.image = OtherImageCache.get_scene_image('iron')
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = position

        self.hp=1
class BrickWall(StaticEntity):
    def __init__(self,position: tuple,entity_id):
        super().__init__(position,entity_id)
        self.type = 'brick'
        self.image = OtherImageCache.get_scene_image('brick')
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = position

        self.hp=1
