import pygame


class TimeComputer:

    def __init__(self, interval):
        self.last_time = pygame.time.get_ticks()
        self.interval = interval

    def set_interval(self):
        if self.last_time + self.interval < pygame.time.get_ticks():
            self.last_time = pygame.time.get_ticks()
            return True
        else:
            return False
