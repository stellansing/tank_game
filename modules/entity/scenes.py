import pygame
from pygame.sprite import Sprite
import random
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
        self.type = "steel"
        self.image = OtherImageCache.get_scene_image("iron")
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = position

        self.hp=1
class BrickWall(StaticEntity):
    def __init__(self,position: tuple,entity_id):
        super().__init__(position,entity_id)
        self.type = "brick"
        self.image = OtherImageCache.get_scene_image("brick")
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = position

        self.hp=1


class Tree(StaticEntity):
    """Grass/tree scene element - 2x2 grid of 4 tree tiles.
    No collision, not destructible, renders on top of other entities for concealment."""
    def __init__(self, position: tuple, entity_id):
        super().__init__(position, entity_id)
        self.type = "tree"
        self.image = OtherImageCache.get_scene_image("tree")
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = position
        self.hp = 1
        self.live = True


class River(StaticEntity):
    """River scene element - 2x2 grid using two different river tiles.
    Tanks cannot pass through, but bullets can."""
    def __init__(self, position: tuple, entity_id, river_variant=0):
        super().__init__(position, entity_id)
        self.type = "river"
        if river_variant == 0:
            self.image = OtherImageCache.get_scene_image("river1")
        else:
            self.image = OtherImageCache.get_scene_image("river2")
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = position
        self.hp = 1
        self.live = True


class Ice(StaticEntity):
    """Ice scene element - tanks on ice move faster and have inertia (sliding)."""
    def __init__(self, position: tuple, entity_id):
        super().__init__(position, entity_id)
        self.type = "ice"
        self.image = OtherImageCache.get_scene_image("ice")
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = position
        self.hp = 1
        self.live = True


class Home(StaticEntity):
    """Home (基地) 元素，被敌人子弹击中后销毁并导致游戏失败。"""
    def __init__(self, position: tuple):
        super().__init__(position, entity_id=-1)
        self.type = "home"
        self.image = OtherImageCache.get_home_image('alive')
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = position
        self.hp = 1
        self.live = True
        self.destroyed = False

    def destroy(self):
        """基地被击毁：切换图片并标记为已销毁。"""
        self.destroyed = True
        self.live = False
        self.image = OtherImageCache.get_home_image('destroyed')
