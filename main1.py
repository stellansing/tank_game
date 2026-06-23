from modules.LoginMenu import LoginMenu
from modules.MainMenu import MainMenu


if __name__ == '__main__':
    """游戏入口：启动登录菜单，成功后进入主菜单"""
    try:
        login_menu = LoginMenu()
        username = login_menu.run()
        if username:
            MainMenu(username).run()
    except Exception as e:
        print(f"[错误] 游戏运行时发生异常: {e}")
