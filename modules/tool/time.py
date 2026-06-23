import pygame


class TimeComputer:
    """时间间隔计算器，用于控制帧率相关的计时逻辑"""

    def __init__(self, interval):
        self.last_time = pygame.time.get_ticks()
        self.interval = interval

    def set_interval(self):
        """检查是否已达到设定的时间间隔"""
        if self.last_time + self.interval < pygame.time.get_ticks():
            self.last_time = pygame.time.get_ticks()
            return True
        else:
            return False
