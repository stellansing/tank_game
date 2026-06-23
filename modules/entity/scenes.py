import pygame
from pygame.sprite import Sprite
from globalCache import OtherImageCache


class StaticEntity(Sprite):
    """静态场景实体基类（墙、河流、冰、树、基地）"""

    def __init__(self, position: tuple, entity_id):
        super().__init__()
        self.image = None
        self.rect = None

        self.position = position
        self.id = entity_id
        self.hp = None
        self.live = True

    def display_static_entity(self, window):
        """在窗口中渲染该实体"""
        window.blit(self.image, self.rect)


class SteelWall(StaticEntity):
    """钢墙（不可被子弹摧毁）"""
    def __init__(self, position: tuple, entity_id):
        super().__init__(position, entity_id)
        self.type = "steel"
        self.image = OtherImageCache.get_scene_image("iron")
        if self.image:
            self.rect = self.image.get_rect()
        else:
            self.rect = pygame.Rect(0, 0, 0, 0)
        self.rect.left, self.rect.top = position

        self.hp = 1


class BrickWall(StaticEntity):
    """砖墙（可被子弹摧毁）"""
    def __init__(self, position: tuple, entity_id):
        super().__init__(position, entity_id)
        self.type = "brick"
        self.image = OtherImageCache.get_scene_image("brick")
        if self.image:
            self.rect = self.image.get_rect()
        else:
            self.rect = pygame.Rect(0, 0, 0, 0)
        self.rect.left, self.rect.top = position

        self.hp = 1


class Tree(StaticEntity):
    """树木（不可摧毁，提供视觉遮挡）"""
    def __init__(self, position: tuple, entity_id):
        super().__init__(position, entity_id)
        self.type = "tree"
        self.image = OtherImageCache.get_scene_image("tree")
        if self.image:
            self.rect = self.image.get_rect()
        else:
            self.rect = pygame.Rect(0, 0, 0, 0)
        self.rect.left, self.rect.top = position
        self.hp = 1
        self.live = True


class River(StaticEntity):
    """河流（不可通行）"""
    def __init__(self, position: tuple, entity_id, river_variant=0):
        super().__init__(position, entity_id)
        self.type = "river"
        if river_variant == 0:
            self.image = OtherImageCache.get_scene_image("river1")
        else:
            self.image = OtherImageCache.get_scene_image("river2")
        if self.image:
            self.rect = self.image.get_rect()
        else:
            self.rect = pygame.Rect(0, 0, 0, 0)
        self.rect.left, self.rect.top = position
        self.hp = 1
        self.live = True


class Ice(StaticEntity):
    """冰面（降低坦克摩擦力，产生滑行效果）"""
    def __init__(self, position: tuple, entity_id):
        super().__init__(position, entity_id)
        self.type = "ice"
        self.image = OtherImageCache.get_scene_image("ice")
        if self.image:
            self.rect = self.image.get_rect()
        else:
            self.rect = pygame.Rect(0, 0, 0, 0)
        self.rect.left, self.rect.top = position
        self.hp = 1
        self.live = True


class Home(StaticEntity):
    """基地（被摧毁即游戏失败）"""
    def __init__(self, position: tuple):
        super().__init__(position, entity_id=-1)
        self.type = "home"
        self.image = OtherImageCache.get_home_image('alive')
        if self.image:
            self.rect = self.image.get_rect()
        else:
            self.rect = pygame.Rect(0, 0, 0, 0)
        self.rect.left, self.rect.top = position
        self.hp = 1
        self.live = True
        self.destroyed = False

    def destroy(self):
        """摧毁基地，切换为摧毁贴图"""
        self.destroyed = True
        self.live = False
        destroyed_image = OtherImageCache.get_home_image('destroyed')
        if destroyed_image:
            self.image = destroyed_image
