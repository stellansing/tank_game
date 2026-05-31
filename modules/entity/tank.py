class Tank(Sprite):


    def __init__(self,left,top)->None:
        super().__init__()
        self.images = None
        self.direction = None
        self.image = None
        self.rect = None

        self.blood=1000
        self.live = True

        self.speed = 2
        self.shot_speed = 500

        self.time_computer = TimeComputer(self.shot_speed)

    def display_tank(self):
        self.image = self.images[self.direction]
        MainGame.window.blit(self.image, self.rect)

    def speed_change(self, change_direction,accelerate):
        pass

    def move(self,direction):
        old_rect = self.rect.copy()

        self.direction = direction
        if self.direction == 'L':
            if self.rect.left > 0:
                self.rect = self.rect.move(-self.speed, 0)
        elif self.direction == 'R':
            if self.rect.right < MainGame.window.get_rect().right:
                self.rect = self.rect.move(self.speed, 0)
        elif self.direction == 'U':
            if self.rect.top > 0:
                self.rect = self.rect.move(0, -self.speed)
        elif self.direction == 'D':
            if self.rect.bottom < MainGame.window.get_rect().bottom:
                self.rect = self.rect.move(0, self.speed)

        other_tanks = Group([t for t in MainGame.all_collision if t != self])#考虑n*n矩阵，空间换时间
        if pygame.sprite.spritecollideany(self,other_tanks):
            # 发生碰撞，恢复位置和方向
            self.rect = old_rect
            return False
        return True

    def shot(self):
        if not self.time_computer.set_interval():
            return None
        bullet = Bullet(self)
        bullet.bullet_initial_position()
        return bullet

class MyTank(Tank):
    def __init__(self,left,top):
        super().__init__(left,top)
        self.images = {
            'U': pygame.image.load('img/p1tankU.gif'),
            'D': pygame.image.load('img/p1tankD.gif'),
            'L': pygame.image.load('img/p1tankL.gif'),
            'R': pygame.image.load('img/p1tankR.gif')
        }
        self.direction = 'U'
        self.image = self.images[self.direction]
        self.rect = self.image.get_rect()
        self.rect.center = [left, top]
class EnemyTank(Tank):
    def __init__(self, left,top):
        super().__init__(left,top)
        self.images = {
            'U': pygame.image.load('img/enemy1U.gif'),
            'D': pygame.image.load('img/enemy1D.gif'),
            'L': pygame.image.load('img/enemy1L.gif'),
            'R': pygame.image.load('img/enemy1R.gif')
        }
        self.direction = self.rand_direction()
        self.image = self.images[self.direction]
        self.rect = self.image.get_rect()
        self.rect.center = [left, top]

        self.step=50

    def rand_direction(self)->str:
        choice=random.randint(1,4)
        if choice == 1:
            return 'L'
        elif choice == 2:
            return 'R'
        elif choice == 3:
            return 'U'
        elif choice == 4:
            return 'D'

    def rand_move(self):
        if self.step <= 0:
            self.step = 50
            self.direction = self.rand_direction()
        else:
            self.move(self.direction)
            self.step -= 1