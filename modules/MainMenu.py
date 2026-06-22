import pygame
import cfg
from modules.LoadGame import MainGame, MultiplayerGame
from modules.network import HostNetwork, ClientNetwork
from globalCache import OtherImageCache
import os
import socket
import threading


class Button:
    def __init__(self, x, y, width, height, text, font_path, font_size=30,
                 color=(255, 255, 255), hover_color=(255, 255, 0),
                 bg_color=(100, 100, 100)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(font_path, font_size)
        self.color = color
        self.hover_color = hover_color
        self.bg_color = bg_color
        self.is_hovered = False

    def draw(self, surface):
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
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)


class LevelSelectMenu:

    def __init__(self):
        self.running = None
        pygame.display.init()
        pygame.font.init()

        self.window_size = (cfg.WIDTH, cfg.HEIGHT)
        self.window = pygame.display.set_mode(self.window_size)
        pygame.display.set_caption(cfg.TITLE + " - 选择关卡")

        self.clock = pygame.time.Clock()

        title_font = pygame.font.Font(cfg.FONT_PATH, 36)
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
        center_x = [center_x_cell, center_x_cell * 3, center_x_cell * 5]
        button_spacing = 20

        start_y = 80
        for i, level in enumerate(self.levels):
            button = Button(
                center_x[i % 3] - button_width // 2,
                start_y + (i // 3) * (button_height + button_spacing),
                button_width,
                button_height,
                f"第 {level} 关",
                cfg.FONT_PATH,
                font_size=24,
                color=(255, 255, 255),
                hover_color=(255, 255, 0),
                bg_color=(50, 50, 50)
            )
            self.level_buttons.append((level, button))

        # 返回按钮
        num_rows = (len(self.levels) + 2) // 3
        self.back_button = Button(
            self.window_size[0] // 2 - button_width // 2,
            start_y + num_rows * (button_height + button_spacing) + 20,
            button_width,
            button_height,
            "返回",
            cfg.FONT_PATH,
            font_size=24,
            color=(255, 255, 255),
            hover_color=(255, 255, 0),
            bg_color=(80, 50, 50)
        )

    def get_available_levels(self):
        levels = []
        level_dir = cfg.LEVEL_FILE_DIR
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
        self.running = True
        while self.running:
            self.clock.tick(60)
            self.update()
            self.render()

        return self.selected_level

    def render(self):
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
        self.get_event()

    def get_event(self):
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
        self.running = False
        print("退出游戏")
        pygame.quit()
        exit()


class MultiplayerMenu:

    def __init__(self):
        self.running = None
        pygame.display.init()
        pygame.font.init()

        self.window_size = (cfg.WIDTH, cfg.HEIGHT)
        self.window = pygame.display.set_mode(self.window_size)
        pygame.display.set_caption(cfg.TITLE + " - 多人游戏")

        self.clock = pygame.time.Clock()

        # 标题
        title_font = pygame.font.Font(cfg.FONT_PATH, 36)
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
            cfg.FONT_PATH,
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
            cfg.FONT_PATH,
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
            cfg.FONT_PATH,
            font_size=24,
            color=(255, 255, 255),
            hover_color=(255, 255, 0),
            bg_color=(80, 50, 50)
        )

        self.selected_mode = None

    def run(self):
        self.running = True
        while self.running:
            self.clock.tick(60)
            self.render()
            self.update()

        return self.selected_mode

    def render(self):
        self.window.fill(cfg.WINDOW_COLOR)

        # 绘制标题
        self.window.blit(self.title_surface, self.title_rect)

        # 绘制按钮
        self.create_host_button.draw(self.window)
        self.join_host_button.draw(self.window)
        self.back_button.draw(self.window)

        pygame.display.update()

    def update(self):
        self.get_event()

    def get_event(self):
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
        self.running = False
        print("退出游戏")
        pygame.quit()
        exit()


class IPInputMenu:
    """IP地址输入对话框"""

    def __init__(self, default_ip="127.0.0.1"):
        self.running = None
        pygame.display.init()
        pygame.font.init()

        self.window_size = (cfg.WIDTH, cfg.HEIGHT)
        self.window = pygame.display.set_mode(self.window_size)
        pygame.display.set_caption(cfg.TITLE + " - 连接房间")

        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(cfg.FONT_PATH, 28)
        self.small_font = pygame.font.Font(cfg.FONT_PATH, 20)

        self.ip_text = default_ip
        self.result = None

    def run(self):
        self.running = True
        while self.running:
            self.clock.tick(60)
            self.update()
            self.render()

        return self.result

    def render(self):
        self.window.fill(cfg.WINDOW_COLOR)

        # 标题
        title = self.font.render("输入主机IP地址", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.window_size[0] // 2, 80))
        self.window.blit(title, title_rect)

        # IP输入框背景
        input_rect = pygame.Rect(
            self.window_size[0] // 2 - 150, 180, 300, 50
        )
        pygame.draw.rect(self.window, (50, 50, 50), input_rect, border_radius=5)
        pygame.draw.rect(self.window, (255, 255, 255), input_rect, 2, border_radius=5)

        # IP文本
        ip_surface = self.font.render(self.ip_text, True, (255, 255, 0))
        ip_rect = ip_surface.get_rect(center=input_rect.center)
        self.window.blit(ip_surface, ip_rect)

        # 光标
        if pygame.time.get_ticks() % 1000 < 500:
            cursor_x = ip_rect.right + 2
            cursor_y = ip_rect.top + 5
            pygame.draw.line(self.window, (255, 255, 0),
                             (cursor_x, cursor_y),
                             (cursor_x, cursor_y + ip_rect.height - 10), 2)

        # 提示文字
        hint = self.small_font.render("按ENTER连接 | ESC返回", True, (180, 180, 180))
        hint_rect = hint.get_rect(center=(self.window_size[0] // 2, 260))
        self.window.blit(hint, hint_rect)

        pygame.display.update()

    def update(self):
        self.get_event()

    def get_event(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.try_connect()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_BACKSPACE:
                    self.ip_text = self.ip_text[:-1]
                elif event.key == pygame.K_PERIOD or event.key == pygame.K_KP_PERIOD:
                    self.ip_text += '.'
                elif event.unicode.isdigit():
                    if len(self.ip_text) < 15:
                        self.ip_text += event.unicode

    def try_connect(self):
        ip = self.ip_text.strip()

        self.result = ip
        self.running = False

    def quit_game(self):
        self.running = False
        print("退出游戏")
        pygame.quit()
        exit()


class HostWaitingScreen:

    def __init__(self, host_network: HostNetwork):
        self.host_network = host_network
        self.running = None
        self.window = pygame.display.get_surface()
        self.window_size = (cfg.WIDTH, cfg.HEIGHT)
        self.font = pygame.font.Font(cfg.FONT_PATH, 28)
        self.small_font = pygame.font.Font(cfg.FONT_PATH, 20)

        # 获取本机IP
        self.local_ip = self._get_local_ip()

    # 临时socket用于获取本机IP
    @staticmethod
    def _get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            pass

    def run(self):
        self.running = True

        # 在子线程中等待客户端连接，不阻塞主线程
        wait_thread = threading.Thread(target=self.host_network.wait_for_client, daemon=True)
        wait_thread.start()

        while self.running:

            self.update()
            self.render()

            # 检查是否连接成功
            if self.host_network.is_connected:
                return True

        # 用户退出，通知HostNetwork停止等待
        self.host_network.running = False
        return False

    def render(self):
        self.window.fill(cfg.WINDOW_COLOR)

        # 标题
        title = self.font.render("等待玩家加入...", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.window_size[0] // 2, 80))
        self.window.blit(title, title_rect)

        # 本机IP信息
        ip_label = self.font.render(
            f"本机IP: {self.local_ip}  端口: {cfg.NETWORK_PORT}",
            True, (255, 255, 0)
        )
        ip_rect = ip_label.get_rect(center=(self.window_size[0] // 2, 180))
        self.window.blit(ip_label, ip_rect)

        pygame.display.update()

    def update(self):

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False


class MainMenu:

    def __init__(self, username=None):
        self.username = username
        self.running = None
        pygame.display.init()
        pygame.font.init()

        self.window_size = (cfg.WIDTH, cfg.HEIGHT)
        self.window = pygame.display.set_mode(self.window_size)
        pygame.display.set_caption(cfg.TITLE + f" - {username}" if username else cfg.TITLE)

        self.clock = pygame.time.Clock()

        # 初始化图片缓存
        OtherImageCache.initialize(cfg)

        # 加载logo图片
        try:
            self.logo_image = OtherImageCache.get_other_image('logo')
            # 缩放logo到合适大小
            logo_width = 300
            logo_height = int(self.logo_image.get_height() * (logo_width / self.logo_image.get_width()))
            self.logo_image = pygame.transform.scale(self.logo_image, (logo_width, logo_height))
            self.logo_rect = self.logo_image.get_rect(center=(self.window_size[0] // 2, 50))
        except Exception:
            self.logo_image = None

        # 创建按钮
        button_width = 200
        button_height = 60
        center_x = self.window_size[0] // 2

        # 计算按钮位置
        button_spacing = 20
        total_height = button_height * 2 + button_spacing
        start_y = (self.window_size[1] - total_height) // 2 + 100

        self.single_player_button = Button(
            center_x - button_width // 2,
            start_y,
            button_width,
            button_height,
            "单人游戏",
            cfg.FONT_PATH,
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
            cfg.FONT_PATH,
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
                        selected_level = LevelSelectMenu().run()

                        if selected_level is not None:
                            game = MainGame(username=self.username)
                            game.start_game(str(selected_level))

                    elif self.multi_player_button.is_clicked(event.pos):
                        # 点击多人游戏，进入联机菜单
                        print("进入多人游戏")
                        mode = MultiplayerMenu().run()

                        if mode == 'host':
                            self.start_host_game()
                        elif mode == 'join':
                            self.start_client_game()

    def start_host_game(self):
        host_network = HostNetwork()
        host_network.start_listening()

        # 显示等待界面
        connected = HostWaitingScreen(host_network).run()

        if connected:
            # 选择关卡
            level_select = LevelSelectMenu()
            selected_level = level_select.run()
            if selected_level is not None:
                game = MultiplayerGame(host_network=host_network, username=self.username)
                game.start_game(str(selected_level), is_host=True)
        else:
            host_network.close()

    def start_client_game(self):
        host_ip = IPInputMenu().run()

        if host_ip is None:
            return  # 用户取消

        # 初始化client网络，等待从host接收关卡数据
        game = MultiplayerGame(host_ip=host_ip, username=self.username)
        game.start_game(is_host=False)

    def quit_game(self):
        self.running = False
        print("退出游戏")
        pygame.quit()
        exit()
