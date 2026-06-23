import pygame
import cfg


class Button:
    """通用按钮组件"""
    def __init__(self, x, y, width, height, text, font_path, font_size=30,
                 color=(255, 255, 255), hover_color=(255, 255, 0),
                 bg_color=(100, 100, 100)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        try:
            self.font = pygame.font.Font(font_path, font_size)
        except (pygame.error, FileNotFoundError) as e:
            print(f"[警告] 加载按钮字体失败: {e}")
            self.font = None
        self.color = color
        self.hover_color = hover_color
        self.bg_color = bg_color
        self.is_hovered = False

    def draw(self, surface):
        """绘制按钮"""
        current_color = self.hover_color if self.is_hovered else self.color

        pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=5)
        pygame.draw.rect(surface, current_color, self.rect, 3, border_radius=5)

        if self.font:
            try:
                text_surface = self.font.render(self.text, True, current_color)
                text_rect = text_surface.get_rect(center=self.rect.center)
                surface.blit(text_surface, text_rect)
            except pygame.error as e:
                print(f"[警告] 渲染按钮文字失败: {e}")

    def check_hover(self, mouse_pos):
        """检查鼠标悬停状态"""
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered

    def is_clicked(self, mouse_pos):
        """判断按钮是否被点击"""
        return self.rect.collidepoint(mouse_pos)


class BaseMenu:
    """菜单基类，提供所有菜单类的公共功能"""

    def __init__(self, title_suffix="", caption=None, init_display=True):
        """
        初始化菜单基类
        Args:
            title_suffix: 标题后缀（自动拼接 "坦克大战 - xxx"）
            caption: 自定义完整标题（优先级高于 title_suffix）
            init_display: 是否初始化显示模式（某些子菜单使用已有窗口）
        """
        self.running = None
        if init_display:
            pygame.display.init()
            pygame.font.init()

        self.window_size = (cfg.WIDTH, cfg.HEIGHT)
        if init_display:
            self.window = pygame.display.set_mode(self.window_size)
        else:
            self.window = pygame.display.get_surface()

        if caption:
            pygame.display.set_caption(caption)
        elif title_suffix and init_display:
            pygame.display.set_caption(cfg.TITLE + f" - {title_suffix}")

        if init_display:
            pygame.display.set_icon(pygame.image.load(cfg.ICON_PATH))

        self.clock = pygame.time.Clock()

    def run(self):
        """运行菜单主循环"""
        self.running = True
        while self.running:
            self.clock.tick(60)
            self.update()
            self.render()

    def render(self):
        """渲染界面，由子类重写"""
        self.window.fill(cfg.WINDOW_COLOR)
        pygame.display.update()

    def update(self):
        """更新状态，由子类重写"""
        self.get_event()

    def get_event(self):
        """处理事件，由子类重写"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()

    def quit_game(self):
        """退出游戏"""
        self.running = False
        print("退出游戏")
        pygame.quit()
        exit()

    @staticmethod
    def load_font(font_path, size):
        """安全加载字体，失败时返回 None"""
        try:
            return pygame.font.Font(font_path, size)
        except (pygame.error, FileNotFoundError) as e:
            print(f"[警告] 加载字体失败: {e}")
            return None
