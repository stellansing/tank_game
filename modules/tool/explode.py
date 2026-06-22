from pygame.sprite import Sprite
from modules.tool.time import TimeComputer
from globalCache import OtherImageCache
from modules.tool.sound_manager import SoundManager

class Explode(Sprite):
    def __init__(self, tank,position= None, explode_id=None):
        super().__init__()
        self.id = explode_id if explode_id is not None else id(self)
        self.images= OtherImageCache.get_boom_image()
        self.image = self.images[0]
        self.rect=self.image.get_rect()
        if tank:
            self.rect.center = tank.rect.center
        else:
            self.rect.center = position
        self.step=0

        self.live=True
        self.type='explode'

        self.total_duration = 300  # 爆炸总时长（毫秒）
        self.frame_duration = self.total_duration // len(self.images)  # 每帧持续时间
        self.time_computer = TimeComputer(self.frame_duration)
        SoundManager.play_blast()
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
    def __init__(self, bullet,position= None, explode_id=None):
        super().__init__()
        self.id = explode_id if explode_id is not None else id(self)
        self.images= OtherImageCache.get_boom_image()[0:3]
        self.image = self.images[0]
        self.rect=self.image.get_rect()
        if bullet:
            self.rect.center = bullet.rect.center
        else:
            self.rect.center = position
        self.step=0

        self.live=True
        self.type = 'bullet_explode'

        self.total_duration = 100  # 爆炸总时长（毫秒）
        self.frame_duration = self.total_duration // len(self.images)  # 每帧持续时间
        self.time_computer = TimeComputer(self.frame_duration)
        SoundManager.play_hit()
    def display_explode(self,window):
        if self.step < len(self.images):
            if self.time_computer.set_interval():
                self.image = self.images[self.step]
                self.step += 1
            window.blit(self.image, self.rect)
        else:
            self.step = 0
            self.live = False
