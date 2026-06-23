import pygame
import cfg
from modules.user_manager import UserManager


class LoginMenu:
    """登录/注册菜单"""

    def __init__(self):
        self.running = None
        self.username = None
        pygame.display.init()
        pygame.font.init()

        self.window_size = (cfg.WIDTH, cfg.HEIGHT)
        self.window = pygame.display.set_mode(self.window_size)
        pygame.display.set_caption(cfg.TITLE + " - 登录")

        self.clock = pygame.time.Clock()

        # 加载logo图片
        try:
            logo_image = pygame.image.load(cfg.OTHER_IMAGE_PATHS.get('logo'))
            logo_width = 250
            logo_height = int(logo_image.get_height() * (logo_width / logo_image.get_width()))
            self.logo_image = pygame.transform.scale(logo_image, (logo_width, logo_height))
            self.logo_rect = self.logo_image.get_rect(center=(self.window_size[0] // 2, 60))
        except Exception:
            self.logo_image = None

        # 字体
        try:
            self.font = pygame.font.Font(cfg.FONT_PATH, 28)
            self.small_font = pygame.font.Font(cfg.FONT_PATH, 22)
            self.message_font = pygame.font.Font(cfg.FONT_PATH, 20)
        except (pygame.error, FileNotFoundError) as e:
            print(f"[警告] 加载字体文件失败: {e}")
            self.font = None
            self.small_font = None
            self.message_font = None

        # 输入框
        input_width = 300
        input_height = 50
        center_x = self.window_size[0] // 2

        self.username_label = "用户名:"
        self.password_label = "密  码:"

        # 用户名输入框
        self.username_rect = pygame.Rect(
            center_x - input_width // 2, 180, input_width, input_height
        )
        self.username_text = ""
        self.username_active = False

        # 密码输入框
        self.password_rect = pygame.Rect(
            center_x - input_width // 2, 260, input_width, input_height
        )
        self.password_text = ""
        self.password_active = False

        # 登录按钮
        button_width = 150
        button_height = 50
        self.login_button_rect = pygame.Rect(
            center_x - button_width // 2, 350, button_width, button_height
        )

        # 消息
        self.message = ""
        self.message_color = (255, 255, 255)
        self.message_timer = 0

        # 输入框焦点
        self.active_input = 0  # 0: 用户名, 1: 密码
        self.username_active = True

    def run(self):
        """运行登录菜单，返回用户名（登录成功时）"""
        self.running = True
        while self.running:
            self.clock.tick(60)
            self.update()
            self.render()
        return self.username  # 登录成功时返回用户名，退出时返回None

    def render(self):
        """渲染登录界面"""
        self.window.fill(cfg.WINDOW_COLOR)

        # 绘制logo
        if self.logo_image:
            self.window.blit(self.logo_image, self.logo_rect)

        # 绘制标题
        title = self.font.render("玩家登录", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.window_size[0] // 2, 120))
        self.window.blit(title, title_rect)

        # 绘制用户名标签
        username_label_surf = self.small_font.render(self.username_label, True, (200, 200, 200))
        label_x = self.username_rect.x - username_label_surf.get_width() - 10
        label_y = self.username_rect.y + (self.username_rect.height - username_label_surf.get_height()) // 2
        self.window.blit(username_label_surf, (label_x, label_y))

        # 绘制用户名输入框
        username_color = (255, 255, 0) if self.username_active else (255, 255, 255)
        pygame.draw.rect(self.window, (50, 50, 50), self.username_rect, border_radius=5)
        pygame.draw.rect(self.window, username_color, self.username_rect, 2, border_radius=5)

        # 显示用户名文本
        display_text = self.username_text
        text_surf = self.small_font.render(display_text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(midleft=(self.username_rect.x + 10, self.username_rect.centery))
        self.window.blit(text_surf, text_rect)

        # 用户名输入框光标
        if self.username_active and pygame.time.get_ticks() % 1000 < 500:
            cursor_x = text_rect.right + 2
            cursor_y = self.username_rect.y + 10
            pygame.draw.line(self.window, (255, 255, 0),
                             (cursor_x, cursor_y),
                             (cursor_x, cursor_y + self.username_rect.height - 20), 2)

        # 绘制密码标签
        pwd_label_surf = self.small_font.render(self.password_label, True, (200, 200, 200))
        pwd_label_x = self.password_rect.x - pwd_label_surf.get_width() - 10
        pwd_label_y = self.password_rect.y + (self.password_rect.height - pwd_label_surf.get_height()) // 2
        self.window.blit(pwd_label_surf, (pwd_label_x, pwd_label_y))

        # 绘制密码输入框
        pwd_color = (255, 255, 0) if self.password_active else (255, 255, 255)
        pygame.draw.rect(self.window, (50, 50, 50), self.password_rect, border_radius=5)
        pygame.draw.rect(self.window, pwd_color, self.password_rect, 2, border_radius=5)

        # 显示密码文本（用*代替）
        pwd_display = '*' * len(self.password_text)
        pwd_surf = self.small_font.render(pwd_display, True, (255, 255, 255))
        pwd_rect = pwd_surf.get_rect(midleft=(self.password_rect.x + 10, self.password_rect.centery))
        self.window.blit(pwd_surf, pwd_rect)

        # 密码输入框光标
        if self.password_active and pygame.time.get_ticks() % 1000 < 500:
            cursor_x = pwd_rect.right + 2
            cursor_y = self.password_rect.y + 10
            pygame.draw.line(self.window, (255, 255, 0),
                             (cursor_x, cursor_y),
                             (cursor_x, cursor_y + self.password_rect.height - 20), 2)

        # 绘制登录按钮
        mouse_pos = pygame.mouse.get_pos()
        button_hover = self.login_button_rect.collidepoint(mouse_pos)
        button_color = (255, 255, 0) if button_hover else (255, 255, 255)
        pygame.draw.rect(self.window, (50, 50, 50), self.login_button_rect, border_radius=5)
        pygame.draw.rect(self.window, button_color, self.login_button_rect, 3, border_radius=5)

        btn_text = self.small_font.render("登录 / 注册", True, button_color)
        btn_rect = btn_text.get_rect(center=self.login_button_rect.center)
        self.window.blit(btn_text, btn_rect)

        # 绘制提示文字
        hint = self.small_font.render("Tab切换输入框 | Enter登录", True, (120, 120, 120))
        hint_rect = hint.get_rect(center=(self.window_size[0] // 2, 420))
        self.window.blit(hint, hint_rect)

        # 绘制消息
        if self.message and pygame.time.get_ticks() - self.message_timer < 3000:
            msg_surf = self.message_font.render(self.message, True, self.message_color)
            msg_rect = msg_surf.get_rect(center=(self.window_size[0] // 2, 470))
            self.window.blit(msg_surf, msg_rect)

        pygame.display.update()

    def update(self):
        """更新状态"""
        self.get_event()

    def get_event(self):
        """处理键盘和鼠标事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                pygame.quit()
                exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # 切换输入框焦点
                    self.username_active = self.username_rect.collidepoint(event.pos)
                    self.password_active = self.password_rect.collidepoint(event.pos)

                    # 登录按钮
                    if self.login_button_rect.collidepoint(event.pos):
                        self.try_login()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    # Tab切换输入框
                    self.username_active = not self.username_active
                    self.password_active = not self.password_active

                elif event.key == pygame.K_RETURN:
                    self.try_login()

                elif event.key == pygame.K_BACKSPACE:
                    if self.username_active:
                        self.username_text = self.username_text[:-1]
                    elif self.password_active:
                        self.password_text = self.password_text[:-1]

                else:
                    # 输入字符
                    if event.unicode and event.unicode.isprintable():
                        if self.username_active and len(self.username_text) < 16:
                            self.username_text += event.unicode
                        elif self.password_active and len(self.password_text) < 20:
                            self.password_text += event.unicode

    def try_login(self):
        """尝试登录"""
        success, msg = UserManager.login(self.username_text, self.password_text)
        self.message = msg
        self.message_color = (0, 255, 0) if success else (255, 0, 0)
        self.message_timer = pygame.time.get_ticks()

        if success:
            self.username = self.username_text
            # 短暂延迟后自动进入主菜单
            pygame.time.wait(800)
            self.running = False
