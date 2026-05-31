class StaticEntity(Sprite):
    def __init__(self,position: tuple):
        super().__init__()
        self.image = None
        self.rect = None
        self.position = position
        self.live = True

    def display_static_entity(self):
        MainGame.window.blit(self.image, self.rect)
class SteelWall(StaticEntity):
    def __init__(self,position: tuple):
        super().__init__(position)
        self.image = pygame.image.load('img/redWall.gif')
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = position