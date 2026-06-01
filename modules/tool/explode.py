from pygame.sprite import Sprite
from modules.tool.time import *
from globalCache import *

class Explode(Sprite):
    def __init__(self, tank):
        super().__init__()
        self.images= OtherImageCache.get_boom_image()
        self.image = self.images[0]
        self.rect=self.image.get_rect()
        self.rect.center = tank.rect.center
        self.step=0

        self.live=True

        self.total_duration = 300  # 爆炸总时长（毫秒）
        self.frame_duration = self.total_duration // len(self.images)  # 每帧持续时间
        self.time_computer = TimeComputer(self.frame_duration)
    def display_explode(self,window):
        if self.step < len(self.images):
            if self.time_computer.set_interval():
                self.image = self.images[self.step]
                self.step += 1
            window.blit(self.image, self.rect)
        else:
            self.step = 0
            self.live = False
class BulletExplode(Sprite):
    def __init__(self, tank):
        super().__init__()
        self.images= OtherImageCache.get_boom_image()[0:3]
        self.image = self.images[0]
        self.rect=self.image.get_rect()
        self.rect.center = tank.rect.center
        self.step=0

        self.live=True

        self.total_duration = 100  # 爆炸总时长（毫秒）
        self.frame_duration = self.total_duration // len(self.images)  # 每帧持续时间
        self.time_computer = TimeComputer(self.frame_duration)
    def display_explode(self,window):
        if self.step < len(self.images):
            if self.time_computer.set_interval():
                self.image = self.images[self.step]
                self.step += 1
            window.blit(self.image, self.rect)
        else:
            self.step = 0
            self.live = False