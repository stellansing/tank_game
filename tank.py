# -*- coding: utf-8 -*-
import pygame
import random
from pygame.sprite import collide_rect,Sprite,Group,groupcollide,spritecollide

window_color=pygame.Color(255, 255, 255)
INITIAL_REBORN=(300, 500)

class TimeComputer:
    def __init__(self,interval):
        self.last_time = pygame.time.get_ticks()
        self.interval = interval
    def set_interval(self):
        if self.last_time + self.interval < pygame.time.get_ticks():
            self.last_time = pygame.time.get_ticks()
            return True
        else:
            return False
class Tank(Sprite):


    def __init__(self,left,top)->None:
        super().__init__()
        self.images = None
        self.direction = None
        self.image = None
        self.rect = None

        self.blood=1000
        self.live = True

        self.speed = 3
        self.shot_speed = 500

        self.time_computer = TimeComputer(self.shot_speed)

    def display_tank(self):
        self.image = self.images[self.direction]
        MainGame.window.blit(self.image, self.rect)

    def speed_change(self, change_direction,accelerate):
        pass

    def move(self,direction):
        old_rect = self.rect.copy()
        old_direction = self.direction

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
            self.direction = old_direction
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


class Bullet(Sprite):
    def __init__(self,tank):
        super().__init__()
        self.owner_tank = tank
        self.img = pygame.image.load('img/enemymissile.gif')
        self.direction=tank.direction
        self.rect = self.img.get_rect()
        self.speed = 8
        self.live=True

    def bullet_initial_position(self):
        if self.direction == 'U':
            self.rect.left=self.owner_tank.rect.left + self.owner_tank.rect.width / 2-self.rect.width / 2
            self.rect.top = self.owner_tank.rect.top-self.rect.height
        elif self.direction == 'D':
            self.rect.left=self.owner_tank.rect.left + self.owner_tank.rect.width / 2-self.rect.width / 2
            self.rect.top = self.owner_tank.rect.top + self.owner_tank.rect.height

        elif self.direction == 'L':
            self.rect.left = self.owner_tank.rect.left-self.rect.width
            self.rect.top=self.owner_tank.rect.top + self.owner_tank.rect.height / 2-self.rect.height / 2
        elif self.direction == 'R':
            self.rect.left = self.owner_tank.rect.left + self.owner_tank.rect.width
            self.rect.top=self.owner_tank.rect.top + self.owner_tank.rect.height / 2-self.rect.height / 2



    def display_bullet(self, window):
        window.blit(self.img, self.rect)

    def move(self, window):
        if self.direction == 'U':
            if self.rect.top > 0:
                self.rect = self.rect.move(0, -self.speed)
            else:
                self.live=False
        elif self.direction == 'D':
            if self.rect.bottom < window.get_rect().bottom:
                self.rect = self.rect.move(0, self.speed)
            else:
                self.live=False
        elif self.direction == 'L':
            if self.rect.left > 0:
                self.rect = self.rect.move(-self.speed, 0)
            else :
                self.live=False
        elif self.direction == 'R':
            if self.rect.right < window.get_rect().right:
                self.rect = self.rect.move(self.speed, 0)
            else:
                self.live=False

class Wall:
    def __init__(self):
        pass
    def display_wall(self):
        pass
class Explode(Sprite):
    def __init__(self, tank):
        super().__init__()
        self.images=[
            pygame.image.load('img/blast0.gif'),
            pygame.image.load('img/blast1.gif'),
            pygame.image.load('img/blast2.gif'),
            pygame.image.load('img/blast3.gif'),
            pygame.image.load('img/blast4.gif'),
        ]
        self.image = self.images[0]
        self.rect=self.image.get_rect()
        self.rect.center = tank.rect.center
        self.step=0

        self.live=True

        self.total_duration = 300  # 爆炸总时长（毫秒）
        self.frame_duration = self.total_duration // len(self.images)  # 每帧持续时间
        self.time_computer = TimeComputer(self.frame_duration)
    def display_explode(self):
        if self.step < len(self.images):
            if self.time_computer.set_interval():
                self.image = self.images[self.step]
                self.step += 1
            MainGame.window.blit(self.image, self.rect)
        else:
            self.step = 0
            self.live = False

class Music:
    def __init__(self):
        pass
    def play(self):
        pass

class MainGame:
    window = None
    my_tank = None

    enemy_tanks = Group()
    all_collision = Group()

    my_bullets = Group()
    enemy_bullets = Group()

    explosions = Group()

    enemy_tanks_count = 3
    clock = None

    def __init__(self):
        self.key_order = []
        self.my_tank_dead_time=0
        self.reborn_interval=300
    def start_game(self,window_size):
        pygame.display.init()
        MainGame.window = pygame.display.set_mode(window_size)
        pygame.font.init()
        pygame.display.set_caption("Tank War")

        MainGame.clock = pygame.time.Clock()

        self.create_my_tank(INITIAL_REBORN)
        self.create_enemy_tank()

        while True:
            MainGame.clock.tick(60)
            MainGame.window.fill(window_color)

            num=100
            text=self.get_text_surface(f"血量{num}")
            MainGame.window.blit(text,(10,10))

            self.get_event()

            self.update()
            self.render()

            pygame.display.update()

    def check_collision(self):
        # 子弹和敌方坦克的碰撞
        default_collided = pygame.sprite.collide_rect_ratio(0.8)
        hits=groupcollide(self.my_bullets,self.enemy_tanks,True,True,collided=default_collided)
        for bullet,tanks in hits.items():
            for tank in tanks:
                self.create_explosion(tank)

        #我方坦克和子弹的碰撞
        if self.my_tank and self.my_tank.live:
            hits = spritecollide(self.my_tank, self.enemy_bullets, True,collided=default_collided)
            if hits:
                self.my_tank.live = False
                self.create_explosion(self.my_tank)
                self.my_tank_dead_time=pygame.time.get_ticks()



    def update(self):
        # 移动所有子弹
        for bullet in self.my_bullets:
            bullet.move(self.window)
        for bullet in self.enemy_bullets:
            bullet.move(self.window)

        # 敌方坦克移动和射击
        self.enemy_tank_event()

        # 我的坦克移动
        self.my_tank_envent()

        # 碰撞检测（关键步骤）
        self.check_collision()

        # 移除超出边界的子弹
        self.cleanup_bullets()

    def render(self):
        """渲染所有元素"""
        self.window.fill(window_color)

        if self.my_tank and self.my_tank.live:
            self.my_tank.display_tank()
        elif pygame.time.get_ticks()-self.my_tank_dead_time>self.reborn_interval:
            self.reborn_tank(self.my_tank,INITIAL_REBORN)

        for enemy in self.enemy_tanks:
            enemy.display_tank()

        for bullet in self.my_bullets:
            bullet.display_bullet(self.window)
        for bullet in self.enemy_bullets:
            bullet.display_bullet(self.window)

        if MainGame.explosions:
            for explosion in MainGame.explosions:
                if explosion.live:
                    explosion.display_explode()
                else:
                    MainGame.explosions.remove(explosion)
        # 显示血量等UI
        text = self.get_text_surface(f"敌人数: {len(self.enemy_tanks)}")
        self.window.blit(text, (10, 10))

        pygame.display.update()

    def cleanup_bullets(self):
        for bullet in list(self.my_bullets):
            if not bullet.live:
                self.my_bullets.remove(bullet)
        for bullet in list(self.enemy_bullets):
            if not bullet.live:
                self.enemy_bullets.remove(bullet)

    def create_explosion(self,tank:Tank):
        explode = Explode(tank)
        MainGame.explosions.add(explode)

    def create_my_tank(self,initial_reborn):
        self.my_tank = MyTank(initial_reborn[0],initial_reborn[1])
        MainGame.all_collision.add(self.my_tank)

    def create_enemy_tank(self):
        for i in range(self.enemy_tanks_count):
            enemy_tank = EnemyTank(random.randint(0, 700), 300 )
            self.enemy_tanks.add(enemy_tank)
            MainGame.all_collision.add(enemy_tank)

    def reborn_tank(self,tank,position):
        tank.live= True
        tank.rect.left, tank.rect.top = position
        tank.direction = 'U'

    def enemy_tank_event(self):
        for enemy in self.enemy_tanks:
            enemy.rand_move()
            bullet = enemy.shot()
            if bullet:
                self.enemy_bullets.add(bullet)

    def my_tank_envent(self):

        if self.key_order and self.my_tank and self.my_tank.live:
            last_direction = self.key_order[-1]
            self.my_tank.move(last_direction)

    def get_text_surface(self, text):

        my_font = pygame.font.Font("ttf/MSYH.ttf", 25)
        text_surface = my_font.render(text, True, pygame.Color(255, 0, 0))
        return text_surface

    def get_event(self):
        event_list = pygame.event.get()
        for event in event_list:
            if event.type == pygame.QUIT:
                self.end_game()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and 'L' not in self.key_order:
                    self.key_order.append('L')
                elif event.key == pygame.K_RIGHT and 'R' not in self.key_order:
                    self.key_order.append('R')
                elif event.key == pygame.K_UP and 'U' not in self.key_order:
                    self.key_order.append('U')
                elif event.key == pygame.K_DOWN and 'D' not in self.key_order:
                    self.key_order.append('D')

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT and 'L' in self.key_order:
                    self.key_order.remove('L')
                elif event.key == pygame.K_RIGHT and 'R' in self.key_order:
                    self.key_order.remove('R')
                elif event.key == pygame.K_UP and 'U' in self.key_order:
                    self.key_order.remove('U')
                elif event.key == pygame.K_DOWN and 'D' in self.key_order:
                    self.key_order.remove('D')
        keys_pressed = pygame.key.get_pressed()
        if keys_pressed[pygame.K_SPACE]:
            bullet = self.my_tank.shot()
            if bullet:
                self.my_bullets.add(bullet)

        self.my_tank_envent()



    def end_game(self):
        print("退出游戏")
        pygame.quit()
        exit()


if __name__ == '__main__':
    MainGame().start_game((800,600))