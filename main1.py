from modules.LoginMenu import LoginMenu
from modules.MainMenu import MainMenu


if __name__ == '__main__':
    login_menu = LoginMenu()
    username = login_menu.run()
    if username:
        MainMenu(username).run()
