import pygame
import cfg
from modules.LoadGame import *
import os

class Button:
    """按钮类"""
    def __init__(self, x, y, width, height, text, font_path, font_size=30, 
                 color=(255, 255, 255), hover_color=(255, 255, 0), bg_color=(100, 100, 100)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(font_path, font_size)
        self.color = color
        self.hover_color = hover_color
        self.bg_color = bg_color
        self.is_hovered = False
        
    def draw(self, surface):
        """绘制按钮"""
        # 根据鼠标悬停状态选择颜色
        current_color = self.hover_color if self.is_hovered else self.color
        
        # 绘制按钮背景
        pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=5)
        pygame.draw.rect(surface, current_color, self.rect, 3, border_radius=5)
        
        # 绘制按钮文字
        text_surface = self.font.render(self.text, True, current_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
        
    def check_hover(self, mouse_pos):
        """检查鼠标是否悬停在按钮上"""
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered
        
    def is_clicked(self, mouse_pos):
        """检查按钮是否被点击"""
        return self.rect.collidepoint(mouse_pos)


class LevelSelectMenu:
    """关卡选择菜单类"""
    
    def __init__(self):
        self.running = None
        pygame.display.init()
        pygame.font.init()
        
        self.window_size = (cfg.WIDTH, cfg.HEIGHT)
        self.window = pygame.display.set_mode(self.window_size)
        pygame.display.set_caption(cfg.TITLE + " - 选择关卡")
        
        self.clock = pygame.time.Clock()

        title_font = pygame.font.Font(cfg.FONTPATH, 36)
        self.title_surface = title_font.render("选择关卡", True, (255, 255, 255))
        self.title_rect = self.title_surface.get_rect(center=(self.window_size[0] // 2, 50))

        # 获取可用关卡列表
        self.levels = self.get_available_levels()
        self.selected_level = None
        
        # 创建关卡按钮
        self.level_buttons = []
        button_width = 150
        button_height = 60
        center_x_cell = self.window_size[0] // 6
        center_x=[center_x_cell,center_x_cell*3,center_x_cell*5]
        button_spacing = 20
        
        start_y = 80
        for i, level in enumerate(self.levels):
            button = Button(
                center_x[i%3] - button_width // 2,
                start_y + (i//3) * (button_height + button_spacing),
                button_width,
                button_height,
                f"第 {level} 关",
                cfg.FONTPATH,
                font_size=24,
                color=(255, 255, 255),
                hover_color=(255, 255, 0),
                bg_color=(50, 50, 50)
            )
            self.level_buttons.append((level, button))
        
        # 返回按钮
        self.back_button = Button(
            center_x_cell - button_width // 2,
            start_y + len(self.levels) * (button_height + button_spacing) + 20,
            button_width,
            button_height,
            "返回",
            cfg.FONTPATH,
            font_size=24,
            color=(255, 255, 255),
            hover_color=(255, 255, 0),
            bg_color=(80, 50, 50)
        )
    
    def get_available_levels(self):
        """获取可用的关卡文件列表"""
        levels = []
        level_dir = cfg.LEVELFILEDIR
        if os.path.exists(level_dir):
            for file in os.listdir(level_dir):
                if file.endswith('.lvl'):
                    try:
                        level_num = int(file.replace('.lvl', ''))
                        levels.append(level_num)
                    except ValueError:
                        continue
        return sorted(levels)
    
    def run(self):
        """运行关卡选择菜单"""
        self.running = True
        while self.running:
            self.clock.tick(60)
            self.update()
            self.render()

        return self.selected_level
    
    def render(self):
        """渲染关卡选择界面"""
        self.window.fill(cfg.WINDOW_COLOR)
        
        # 绘制标题
        self.window.blit(self.title_surface, self.title_rect)

        
        # 绘制关卡按钮
        for level, button in self.level_buttons:
            button.draw(self.window)
        
        # 绘制返回按钮
        self.back_button.draw(self.window)
        
        pygame.display.update()
    
    def update(self):
        """更新状态"""
        self.get_event()

    
    def get_event(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()
            
            elif event.type == pygame.MOUSEMOTION:
                # 更新按钮悬停状态
                for level, button in self.level_buttons:
                    button.check_hover(event.pos)
                self.back_button.check_hover(event.pos)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    for level, button in self.level_buttons:
                        if button.is_clicked(event.pos):
                            print(f"选择第 {level} 关")
                            self.selected_level = level
                            self.running = False
                    
                    if self.back_button.is_clicked(event.pos):
                        print("返回主菜单")
                        self.running = False
    
    def quit_game(self):
        """退出游戏"""
        self.running = False
        print("退出游戏")
        pygame.quit()
        exit()


class MultiplayerMenu:
    """多人游戏菜单类"""
    
    def __init__(self):
        self.running = None
        pygame.display.init()
        pygame.font.init()
        
        self.window_size = (cfg.WIDTH, cfg.HEIGHT)
        self.window = pygame.display.set_mode(self.window_size)
        pygame.display.set_caption(cfg.TITLE + " - 多人游戏")
        
        self.clock = pygame.time.Clock()
        
        # 标题
        title_font = pygame.font.Font(cfg.FONTPATH, 36)
        self.title_surface = title_font.render("多人游戏", True, (255, 255, 255))
        self.title_rect = self.title_surface.get_rect(center=(self.window_size[0] // 2, 50))
        
        # 创建按钮
        button_width = 200
        button_height = 60
        center_x = self.window_size[0] // 2
        start_y = 150
        button_spacing = 20
        
        self.create_host_button = Button(
            center_x - button_width // 2,
            start_y,
            button_width,
            button_height,
            "创建房间",
            cfg.FONTPATH,
            font_size=24,
            color=(255, 255, 255),
            hover_color=(255, 255, 0),
            bg_color=(50, 50, 50)
        )
        
        self.join_host_button = Button(
            center_x - button_width // 2,
            start_y + button_height + button_spacing,
            button_width,
            button_height,
            "加入房间",
            cfg.FONTPATH,
            font_size=24,
            color=(255, 255, 255),
            hover_color=(255, 255, 0),
            bg_color=(50, 50, 50)
        )
        
        self.back_button = Button(
            center_x - button_width // 2,
            start_y + (button_height + button_spacing) * 2 + 20,
            button_width,
            button_height,
            "返回",
            cfg.FONTPATH,
            font_size=24,
            color=(255, 255, 255),
            hover_color=(255, 255, 0),
            bg_color=(80, 50, 50)
        )
        
        self.selected_mode = None  # 'host' or 'join'
    
    def run(self):
        """运行多人游戏菜单"""
        self.running = True
        while self.running:
            self.clock.tick(60)
            self.update()
            self.render()
        
        return self.selected_mode
    
    def render(self):
        """渲染多人游戏界面"""
        self.window.fill(cfg.WINDOW_COLOR)
        
        # 绘制标题
        self.window.blit(self.title_surface, self.title_rect)
        
        # 绘制按钮
        self.create_host_button.draw(self.window)
        self.join_host_button.draw(self.window)
        self.back_button.draw(self.window)
        
        pygame.display.update()
    
    def update(self):
        """更新状态"""
        self.get_event()
    
    def get_event(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()
            
            elif event.type == pygame.MOUSEMOTION:
                self.create_host_button.check_hover(event.pos)
                self.join_host_button.check_hover(event.pos)
                self.back_button.check_hover(event.pos)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.create_host_button.is_clicked(event.pos):
                        print("创建房间")
                        self.selected_mode = 'host'
                        self.running = False
                    
                    elif self.join_host_button.is_clicked(event.pos):
                        print("加入房间")
                        self.selected_mode = 'join'
                        self.running = False
                    
                    elif self.back_button.is_clicked(event.pos):
                        print("返回主菜单")
                        self.running = False
    
    def quit_game(self):
        """退出游戏"""
        self.running = False
        print("退出游戏")
        pygame.quit()
        exit()


class MainMenu:
    """主菜单类"""
    
    def __init__(self):
        self.running = None
        pygame.display.init()
        pygame.font.init()
        
        self.window_size = (cfg.WIDTH, cfg.HEIGHT)
        self.window = pygame.display.set_mode(self.window_size)
        pygame.display.set_caption(cfg.TITLE)
        
        self.clock = pygame.time.Clock()
        
        # 加载logo图片
        try:
            self.logo_image = pygame.image.load(cfg.OTHER_IMAGE_PATHS['logo'])
            # 缩放logo到合适大小
            logo_width = 300
            logo_height = int(self.logo_image.get_height() * (logo_width / self.logo_image.get_width()))
            self.logo_image = pygame.transform.scale(self.logo_image, (logo_width, logo_height))
            self.logo_rect = self.logo_image.get_rect(center=(self.window_size[0] // 2, 50))
        except:
            self.logo_image = None
            
        # 创建按钮
        button_width = 200
        button_height = 60
        center_x = self.window_size[0] // 2
        
        # 计算按钮位置（垂直居中排列）
        button_spacing = 20
        total_height = button_height * 2 + button_spacing
        start_y = (self.window_size[1] - total_height) // 2 + 100
        
        self.single_player_button = Button(
            center_x - button_width // 2,
            start_y,
            button_width,
            button_height,
            "单人游戏",
            cfg.FONTPATH,
            font_size=28,
            color=(255, 255, 255),
            hover_color=(255, 255, 0),
            bg_color=(50, 50, 50)
        )
        
        self.multi_player_button = Button(
            center_x - button_width // 2,
            start_y + button_height + button_spacing,
            button_width,
            button_height,
            "多人游戏",
            cfg.FONTPATH,
            font_size=28,
            color=(255, 255, 255),
            hover_color=(255, 255, 0),
            bg_color=(50, 50, 50)
        )
        
    def run(self):
        """运行主菜单"""

        
        self.running = True
        while self.running:
            self.clock.tick(60)

            self.update()

            self.render()

        
        pygame.quit()
        exit()

    def render(self):
        # 渲染
        self.window.fill(cfg.WINDOW_COLOR)

        # 绘制logo
        if self.logo_image:
            self.window.blit(self.logo_image, self.logo_rect)

        # 绘制按钮
        self.single_player_button.draw(self.window)
        self.multi_player_button.draw(self.window)

        pygame.display.update()
    def update(self):
        self.get_event()

    def get_event(self):
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()

            elif event.type == pygame.MOUSEMOTION:
                # 更新按钮悬停状态
                self.single_player_button.check_hover(event.pos)
                self.multi_player_button.check_hover(event.pos)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    if self.single_player_button.is_clicked(event.pos):
                        # 点击单人游戏，进入关卡选择
                        print("进入关卡选择")
                        level_select = LevelSelectMenu()
                        selected_level = level_select.run()
                        
                        if selected_level is not None:
                            # 开始游戏
                            game = MainGame()
                            game.start_game(str(selected_level))

                    elif self.multi_player_button.is_clicked(event.pos):
                       pass

    def quit_game(self):
        self.running = False
        print("退出游戏")
        pygame.quit()
        exit()
