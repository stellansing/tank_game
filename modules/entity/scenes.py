import pygame
from pygame.sprite import Sprite
import cfg

class StaticEntity(Sprite):
    def __init__(self,position: tuple,entity_id):
        super().__init__()
        self.image = None
        self.rect = None

        self.position = position
        self.id=entity_id
        self.hp = None
        self.live = True

    def display_static_entity(self,window):
        window.blit(self.image, self.rect)

    def dead(self):
        self.live = False

    def move(self):
        pass
class SteelWall(StaticEntity):
    def __init__(self,position: tuple,entity_id):
        super().__init__(position,entity_id)
        self.type = 'steel'
        self.image = pygame.image.load(cfg.SCENE_IMAGE_PATHS['iron'])
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = position

        self.hp=1
class BrickWall(StaticEntity):
    def __init__(self,position: tuple,entity_id):
        super().__init__(position,entity_id)
        self.type = 'brick'
        self.image = pygame.image.load(cfg.SCENE_IMAGE_PATHS['brick'])
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = position

        self.hp=1
class WallGroup:
    def __init__(self,positions: tuple,wall_class:str):
        self.left, self.top = positions

        self.steel_wall_group = pygame.sprite.Group()
        self.wall_classes = {
            'iron': SteelWall,
            'brick': BrickWall,
        }

        self.wall=self.wall_classes[wall_class]
        self.wall_width, self.wall_height = cfg.SCENES_SIZE[wall_class]


        self.steel_wall_group.add(self.wall((self.left,self.top)))
        self.steel_wall_group.add(self.wall((self.left+self.wall_width,self.top)))
        self.steel_wall_group.add(self.wall((self.left,self.top+self.wall_height)))
        self.steel_wall_group.add(self.wall((self.left+self.wall_width,self.top+self.wall_height)))

    def display_wall(self,window):
        for wall in self.steel_wall_group:
            wall.display_static_entity(window)

    def add_to(self,group):
        for wall in self.steel_wall_group:
            group.add(wall)
