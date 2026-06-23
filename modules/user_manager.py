import cfg
import json
import os
from datetime import datetime


class UserManager:
    """用户管理类，处理登录、注册和游戏记录"""

    USERS_FILE = cfg.USERS_FILE
    RECORDS_FILE = cfg.RECORDS_FILE

    @classmethod
    def _ensure_data_dir(cls):
        """确保数据目录存在"""
        data_dir = os.path.dirname(cls.USERS_FILE)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

    @classmethod
    def _load_users(cls):
        """加载用户数据"""
        cls._ensure_data_dir()
        if not os.path.exists(cls.USERS_FILE):
            return {}
        try:
            with open(cls.USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    @classmethod
    def _save_users(cls, users):
        """保存用户数据"""
        try:
            cls._ensure_data_dir()
            with open(cls.USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
        except (OSError, PermissionError) as e:
            print(f"[警告] 保存用户数据失败: {e}")

    @classmethod
    def login(cls, username, password):
        """用户登录
        返回: (success: bool, message: str)
        """
        username = username.strip()
        password = password.strip()

        if not username or not password:
            return False, "用户名和密码不能为空！"

        users = cls._load_users()

        if username in users:
            # 用户存在，验证密码
            if users[username] == password:
                return True, f"欢迎回来，{username}！"
            else:
                return False, "密码错误！"
        else:
            # 用户不存在，自动注册
            users[username] = password
            cls._save_users(users)
            return True, f"注册成功，欢迎 {username}！"

    @classmethod
    def _load_records(cls):
        """加载游戏记录"""
        cls._ensure_data_dir()
        if not os.path.exists(cls.RECORDS_FILE):
            return {}
        try:
            with open(cls.RECORDS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    @classmethod
    def _save_records(cls, records):
        """保存游戏记录"""
        try:
            cls._ensure_data_dir()
            with open(cls.RECORDS_FILE, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
        except (OSError, PermissionError) as e:
            print(f"[警告] 保存游戏记录失败: {e}")

    @classmethod
    def save_game_record(cls, username, level, is_win, kills, is_multiplayer=False, teammate=None):
        """保存游戏记录
        Args:
            username: 用户名
            level: 关卡号
            is_win: 是否胜利
            kills: 击杀敌人数
            is_multiplayer: 是否联机
            teammate: 联机队友用户名（联机时）
        """
        records = cls._load_records()

        if username not in records:
            records[username] = []

        record = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'level': level,
            'result': 'win' if is_win else 'lose',
            'kills': kills,
            'is_multiplayer': is_multiplayer,
        }

        if is_multiplayer and teammate:
            record['teammate'] = teammate

        records[username].append(record)
        cls._save_records(records)

    @classmethod
    def get_user_records(cls, username):
        """获取用户的所有游戏记录"""
        records = cls._load_records()
        return records.get(username, [])
