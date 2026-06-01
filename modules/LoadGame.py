import pygame
from pygame.sprite import groupcollide,spritecollide

from modules.tool.music import *
from modules.entity.tank import *
from modules.tool.explode import *
from modules.entity.scenes import *
from modules.entity.bullet import *
import cfg

class MainGame:
    window = None

    my_tank = None
    enemy_tanks = Group()
    all_collision = Group()

    my_bullets = Group()
    enemy_bullets = Group()

    walls = Group()

    explosions = Group()

    clock = None



    def __init__(self):
        self.total_enemy_tanks = None
        self.level_config = None
        self.max_enemy_tanks = None
        self.enemy_tanks_positions = None
        self.reborn_position = cfg.INITIAL_REBORN


        pygame.display.init()
        self.init_image_size()

        self.key_order = []
        self.my_tank_dead_time=0
        self.total_created_enemy_tanks = 0

        self.reborn_interval=cfg.REBORN_INTERVAL

        self.fire_music = Sound(cfg.AUDIO_PATHS['fire'])
        self.hit_music = Sound(cfg.AUDIO_PATHS['hit'])

        self.cell_len=24

        self.window_size = (cfg.WIDTH, cfg.HEIGHT)

    def init_image_size(self):
        scene_sizes = {}
        for key, path in cfg.SCENE_IMAGE_PATHS.items():
            img = pygame.image.load(path)
            scene_sizes[key] = img.get_size()
        cfg.SCENES_SIZE = scene_sizes

    def start_game(self):
        MainGame.window = pygame.display.set_mode((cfg.WIDTH+cfg.PANEL_WIDTH, cfg.HEIGHT))
        pygame.font.init()
        pygame.display.set_caption(cfg.TITLE)

        TankImageCache.initialize(cfg)
        OtherImageCache.initialize(cfg)

        MainGame.clock = pygame.time.Clock()

        self.load_lvl('1')
        Music(cfg.AUDIO_PATHS['start']).play_music()
        self.create_all_players()

        while True:
            MainGame.clock.tick(cfg.INITIAL_TICK)

            self.get_event()

            self.update()
            self.render()

            pygame.display.update()

    def load_lvl(self, level):
        path = cfg.LEVELFILEDIR + '/' + level + '.lvl'

        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 解析配置参数
        config = {}
        num_row=0

        for i, line in enumerate(lines):
            line = line.strip()

            if line.startswith('%TOTALENEMYNUM:'):
                config['total_enemy_num'] = int(line.split(':')[1])
            elif line.startswith('%MAXENEMYNUM:'):
                config['max_enemy_num'] = int(line.split(':')[1])
            elif line.startswith('%HOMEPOS:'):
                pos_str = line.split(':')[1]
                x, y = map(int, pos_str.split(','))
                config['home_pos'] = (x, y)
            elif line.startswith('%HOMEAROUNDPOS:'):
                pos_str = line.split(':')[1]
                positions = []
                for pos in pos_str.split():
                    x, y = map(int, pos.split(','))
                    positions.append((x, y))
                config['home_around_pos'] = positions
            elif line.startswith('%PLAYERTANKPOS:'):
                pos_str = line.split(':')[1]
                positions = []
                for pos in pos_str.split():
                    x, y = map(int, pos.split(','))
                    positions.append((x, y))
                config['player_tank_pos'] = positions
            elif line.startswith('%ENEMYTANKPOS:'):
                pos_str = line.split(':')[1]
                positions = []
                for pos in pos_str.split():
                    x, y = map(int, pos.split(','))
                    positions.append((x*self.cell_len, y*self.cell_len))
                config['enemy_tank_pos'] = positions
            elif line and not line.startswith('#') and not line.startswith('%'):
                print('加载第'+str(num_row)+'行数据')
                for row_i, elem in enumerate(line.split(' ')):
                    self.create_element((row_i*self.cell_len, num_row*self.cell_len), elem)
                num_row += 1

        # 保存关卡配置
        self.level_config = config
        print(config)

        # 更新敌方坦克数量
        self.max_enemy_tanks = config.get('max_enemy_num', 6)
        self.total_enemy_tanks = config.get('total_enemy_num', 12)
        self.reborn_position =(config.get('player_tank_pos')[0][0]*self.cell_len, config.get('player_tank_pos')[0][1]*self.cell_len)
        self.enemy_tanks_positions = config.get('enemy_tank_pos')

        # 清除现有对象
        # MainGame.walls.empty()
        # MainGame.enemy_tanks.empty()
        # MainGame.all_collision.empty()
        # MainGame.my_bullets.empty()
        # MainGame.enemy_bullets.empty()
        # MainGame.explosions.empty()



    def check_collision(self):
        # 子弹和敌方坦克的碰撞
        default_collided = pygame.sprite.collide_rect_ratio(0.8)

        hits=groupcollide(self.my_bullets,self.enemy_tanks,True,False,collided=default_collided)
        for bullet,tanks in hits.items():
            for tank in tanks:
                tank.hp-=1
                if tank.hp <= 0:
                    tank.live = False
                    tank.kill()
                self.create_explosion(tank)

        groupcollide(self.enemy_bullets,self.my_bullets,True,True)

        #我方坦克和子弹的碰撞
        if self.my_tank and self.my_tank.live:
            hits = spritecollide(self.my_tank, self.enemy_bullets, False,collided=default_collided)
            if hits:
                self.my_tank.hp-=1
                self.my_tank.live = False
                self.all_collision.remove(self.my_tank)
                self.create_explosion(self.my_tank)
                self.my_tank_dead_time=pygame.time.get_ticks()

        #子弹与墙的碰撞
        hits=pygame.sprite.groupcollide( self.my_bullets,self.walls, True, False)
        for bullet,walls in hits.items():
            self.create_bullet_explosion(bullet)
            for wall in walls:
                if wall.type=='brick':
                    wall.hp-=1
                if wall.hp<=0:
                    wall.live=False
                    wall.kill()

        hits = pygame.sprite.groupcollide(self.walls, self.enemy_bullets, False, True)
        for wall, bullets in hits.items():
            self.create_bullet_explosion(wall)
            if wall.type=='brick':
                wall.hp-=1
            if wall.hp<=0:
                wall.live=False
                wall.kill()





    def update(self):

        #生成敌方坦克
        self.random_create_enemy_tanks()

        # 移动所有子弹
        for bullet in self.my_bullets:
            bullet.move(self.window_size)
        for bullet in self.enemy_bullets:
            bullet.move(self.window_size)

        # 敌方坦克移动和射击
        self.enemy_tank_event()

        # 我的坦克移动
        self.my_tank_event()

        # 碰撞检测（关键步骤）
        self.check_collision()


    def render(self):
        """渲染所有元素"""
        self.window.fill(cfg.WINDOW_COLOR)

        if self.my_tank and self.my_tank.live:
            self.my_tank.display_tank()
        elif pygame.time.get_ticks()-self.my_tank_dead_time>self.reborn_interval and self.my_tank.hp>=0:#考虑移至更新模块中处理
            self.reborn_tank(self.my_tank,self.reborn_position)

        for enemy in self.enemy_tanks:
            enemy.display_tank()

        for bullet in self.my_bullets:
            bullet.display_bullet(self.window)
        for bullet in self.enemy_bullets:
            bullet.display_bullet(self.window)

        #加载墙壁
        for wall in self.walls:
            wall.display_static_entity(self.window)

        if MainGame.explosions:
            ready_remove = []
            for explosion in MainGame.explosions:
                if explosion.live:
                    explosion.display_explode(self.window)
                else:
                    ready_remove.append(explosion)
            MainGame.explosions = Group([e for e in MainGame.explosions if e not in ready_remove])

        # 显示血量等UI
        text = self.get_text_surface(f"敌人数: {len(self.enemy_tanks)}")
        self.window.blit(text, (10, 10))

        pygame.display.update()

    def menu(self):
        pass

    def create_element(self,position,type):
        if type=='B':
            self.create_brick_wall(position)
        elif type=='I':
            self.create_steel_wall(position)
        elif type=='R':
            self.create_river_wall(position)
        elif type=='C':
            self.create_ice_wall(position)
        elif type=='T':
            self.create_tree_wall(position)

    def create_explosion(self,tank:Tank):
        explode = Explode(tank)
        MainGame.explosions.add(explode)
        self.hit_music.play_music()

    def create_bullet_explosion(self,bullet):
        explode = BulletExplode(bullet)
        MainGame.explosions.add(explode)
        self.hit_music.play_music()


    def create_all_players(self):
        self.create_my_tank(self.reborn_position)
    def create_my_tank(self,initial_reborn):
        self.my_tank = MyTank((initial_reborn[0],initial_reborn[1]),self.window,self.window_size)
        MainGame.all_collision.add(self.my_tank)


    def random_create_enemy_tanks(self):
        if len(self.enemy_tanks)<self.max_enemy_tanks and self.total_created_enemy_tanks<self.total_enemy_tanks:
            position = random.choice(self.enemy_tanks_positions)
            self.create_enemy_tank(position)
    def create_enemy_tank(self,position):
        print("创建敌方坦克"+str(position))
        left, top = position[0], position[1]
        enemy_tank = EnemyTank((left,top),self.window,self.window_size)
        other_tanks = Group([t for t in MainGame.all_collision if t != enemy_tank])  # 考虑n*n矩阵，空间换时间
        if not pygame.sprite.spritecollideany(enemy_tank, other_tanks):
            self.enemy_tanks.add(enemy_tank)
            MainGame.all_collision.add(enemy_tank)
            self.total_created_enemy_tanks+=1

    def create_steel_wall(self,position):
        print("创建铁墙"+str(position))
        left, top = position[0], position[1]
        wall = SteelWall((left, top))
        MainGame.walls.add(wall)
        MainGame.all_collision.add(wall)

    def create_brick_wall(self,position):
        print("创建砖墙"+str(position))
        left, top = position[0], position[1]
        wall = BrickWall((left, top))
        MainGame.walls.add(wall)
        MainGame.all_collision.add(wall)


    def create_river_wall(self,position):
        pass
    def create_ice_wall(self,position):
        pass
    def create_tree_wall(self,position):
        pass

    def reborn_tank(self,tank,position):
        tank.rect.left, tank.rect.top = position
        tank.direction = 'U1'
        other_tanks = Group([t for t in MainGame.all_collision if t != tank])  # 考虑n*n矩阵，空间换时间
        if not pygame.sprite.spritecollideany(tank, other_tanks):
            self.all_collision.add(tank)
            tank.live= True

    def my_tank_move(self,tank,direction):
        old_rect = tank.rect.copy()
        old_direction = tank.direction

        tank.move(direction)

        if old_direction[0] != direction:
            self.move_check(tank,direction,old_rect)#考虑减少耦合的修改


        other_tanks = Group([t for t in MainGame.all_collision if t != tank])  # 考虑n*n矩阵，空间换时间
        if pygame.sprite.spritecollideany(tank, other_tanks):
            tank.rect = old_rect

    def enemy_tank_move(self,tank):
        old_rect = tank.rect.copy()
        old_direction = tank.direction

        tank.rand_move()

        if old_direction[0] != tank.direction:
            self.move_check(tank,tank.direction,old_rect)

        other_tanks = Group([t for t in MainGame.all_collision if t != tank])  # 考虑n*n矩阵，空间换时间
        if pygame.sprite.spritecollideany(tank, other_tanks):
            tank.rect = old_rect

    def move_check(self,tank,direction,old_rect):
        cell_size = self.cell_len

        if direction in ['L', 'R']:
            offset=tank.rect.top % cell_size
            if offset < cell_size:
                if offset > cell_size / 2:
                    tank.rect.top -= cell_size-offset
                else:
                    tank.rect.top -= offset
                old_rect.top = tank.rect.top
        elif direction in ['U', 'D']:
            offset=tank.rect.left % cell_size
            if offset < cell_size:
                if offset > cell_size / 2:
                    tank.rect.left -= cell_size-offset
                else:
                    tank.rect.left -= offset
                old_rect.left = tank.rect.left
    def enemy_tank_event(self):
        for enemy in self.enemy_tanks:
            self.enemy_tank_move(enemy)
            bullet = enemy.shot()
            if bullet:
                self.enemy_bullets.add(bullet)

    def my_tank_event(self):

        if self.key_order and self.my_tank and self.my_tank.live:
            last_direction = self.key_order[-1]
            self.my_tank_move(self.my_tank, last_direction)

    def get_text_surface(self, text):

        my_font = pygame.font.Font(cfg.FONTPATH, 25)
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
        if keys_pressed[pygame.K_SPACE] and self.my_tank and self.my_tank.live:
            bullet = self.my_tank.shot()
            if bullet:
                self.my_bullets.add(bullet)
                self.fire_music.play_music()


    def end_game(self):
        print("退出游戏")
        pygame.quit()
        exit()