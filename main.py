import os
import threading


def _suppress_libpng_warnings():
    """屏蔽libpng的stderr警告输出"""
    r_fd, w_fd = os.pipe()
    original_fd = os.dup(2)
    os.dup2(w_fd, 2)
    os.close(w_fd)

    def _filter():
        while True:
            try:
                data = os.read(r_fd, 4096)
                if not data:
                    break
                text = data.decode('utf-8', errors='replace')
                if 'libpng warning' not in text:
                    os.write(original_fd, data)
            except Exception:
                break

    t = threading.Thread(target=_filter, daemon=True)
    t.start()


_suppress_libpng_warnings()

from modules.LoginMenu import LoginMenu
from modules.MainMenu import MainMenu


if __name__ == '__main__':
    try:
        login_menu = LoginMenu()
        username = login_menu.run()
        if username:
            MainMenu(username).run()
    except Exception as e:
        print(f"[错误] 游戏运行时发生异常: {e}")
