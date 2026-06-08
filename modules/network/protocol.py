"""
网络协议定义模块
定义UDP通信的消息类型、数据结构和序列化/反序列化方法
"""
import json
from enum import Enum, auto
from dataclasses import dataclass, field, asdict
from typing import Optional


class MessageType(str, Enum):
    """消息类型枚举"""
    # 连接握手
    CONNECT = "connect"
    CONNECT_ACK = "connect_ack"
    CONNECT_REJECT = "connect_reject"
    # 游戏数据
    INPUT = "input"           # 客户端输入
    STATE = "state"           # 服务端全量状态快照
    EVENT = "event"           # 事件通知（爆炸、音效等）
    LEVEL_DATA = "level_data"  # 关卡数据
    GAME_START = "game_start"  # 游戏开始
    GAME_OVER = "game_over"    # 游戏结束
    # 断开连接
    DISCONNECT = "disconnect"


@dataclass
class TankData:
    """坦克状态数据"""
    id: int
    x: int
    y: int
    direction: str
    hp: int
    live: bool
    tank_type: str  # "player1", "player2", "enemy"
    enemy_type: str = ""  # 敌人类型 '1'-'4'
    is_host: bool = False  # 是否为主机方坦克


@dataclass
class BulletData:
    """子弹状态数据"""
    id: int
    x: int
    y: int
    direction: str
    live: bool
    owner_type: str  # "player1", "player2", "enemy"


@dataclass
class WallData:
    """墙体状态数据"""
    id: int
    x: int
    y: int
    wall_type: str  # "brick", "steel"
    hp: int
    live: bool


@dataclass
class ExplosionData:
    """爆炸效果数据"""
    id: int
    x: int
    y: int
    step: int
    explode_type: str  # "explode", "bullet_explode"


@dataclass
class GameInfo:
    """游戏全局信息"""
    remaining_enemies: int
    player1_hp: int = 3
    player2_hp: int = 3
    game_win: bool = False
    game_lose: bool = False


@dataclass
class InputData:
    """客户端输入数据"""
    key_order: list = field(default_factory=list)
    space_pressed: bool = False
    seq: int = 0


@dataclass
class GameStateSnapshot:
    """游戏全量状态快照"""
    seq: int = 0
    tanks: list = field(default_factory=list)
    bullets: list = field(default_factory=list)
    walls: list = field(default_factory=list)
    explosions: list = field(default_factory=list)
    game_info: Optional[dict] = None


class NetworkMessage:
    """网络消息封装 - 负责序列化/反序列化"""

    ENCODING = 'utf-8'
    MAX_PACKET_SIZE = 65536  # UDP最大缓冲区

    @staticmethod
    def encode(msg_type: MessageType, data: dict = None) -> bytes:
        """将消息编码为JSON字节串"""
        message = {"type": msg_type.value}
        if data:
            message.update(data)
        json_str = json.dumps(message, separators=(',', ':'))
        return json_str.encode(NetworkMessage.ENCODING)

    @staticmethod
    def decode(raw_data: bytes) -> dict:
        """将JSON字节串解码为字典"""
        json_str = raw_data.decode(NetworkMessage.ENCODING)
        return json.loads(json_str)

    @staticmethod
    def get_type(message: dict) -> Optional[MessageType]:
        """从解码后的消息中提取消息类型"""
        try:
            return MessageType(message.get("type", ""))
        except ValueError:
            return None

    # ---- 工厂方法：创建各类消息 ----

    @classmethod
    def connect(cls) -> bytes:
        return cls.encode(MessageType.CONNECT)

    @classmethod
    def connect_ack(cls, player_id: str) -> bytes:
        return cls.encode(MessageType.CONNECT_ACK, {"player_id": player_id})

    @classmethod
    def connect_reject(cls, reason: str) -> bytes:
        return cls.encode(MessageType.CONNECT_REJECT, {"reason": reason})

    @classmethod
    def input_msg(cls, input_data: InputData) -> bytes:
        return cls.encode(MessageType.INPUT, asdict(input_data))

    @classmethod
    def state_snapshot(cls, snapshot: GameStateSnapshot) -> bytes:
        return cls.encode(MessageType.STATE, asdict(snapshot))

    @classmethod
    def event(cls, event_name: str, event_data: dict = None) -> bytes:
        return cls.encode(MessageType.EVENT, {
            "event": event_name,
            "data": event_data or {}
        })

    @classmethod
    def level_data(cls, level_config: dict, walls_data: list) -> bytes:
        return cls.encode(MessageType.LEVEL_DATA, {
            "config": level_config,
            "walls": walls_data
        })

    @classmethod
    def game_start(cls) -> bytes:
        return cls.encode(MessageType.GAME_START)

    @classmethod
    def game_over(cls, result: str) -> bytes:
        """result: 'win' or 'lose'"""
        return cls.encode(MessageType.GAME_OVER, {"result": result})

    @classmethod
    def disconnect(cls, reason: str = "") -> bytes:
        return cls.encode(MessageType.DISCONNECT, {"reason": reason})

    # ---- 辅助方法：从实体构建数据对象 ----

    @staticmethod
    def tank_to_data(tank, tank_type: str, is_host: bool = False) -> dict:
        """将Tank精灵转换为可序列化的字典"""
        return asdict(TankData(
            id=tank.id,
            x=tank.rect.left,
            y=tank.rect.top,
            direction=tank.direction if tank.live else tank.direction,
            hp=tank.hp,
            live=tank.live,
            tank_type=tank_type,
            enemy_type=getattr(tank, 'enemy_type', ''),
            is_host=is_host
        ))

    @staticmethod
    def bullet_to_data(bullet, owner_type: str) -> dict:
        """将Bullet精灵转换为可序列化的字典"""
        return asdict(BulletData(
            id=bullet.id,
            x=bullet.rect.left,
            y=bullet.rect.top,
            direction=bullet.direction,
            live=getattr(bullet, 'live', True),
            owner_type=owner_type
        ))

    @staticmethod
    def wall_to_data(wall) -> dict:
        """将墙体精灵转换为可序列化的字典"""
        return asdict(WallData(
            id=wall.id,
            x=wall.rect.left,
            y=wall.rect.top,
            wall_type=wall.type,
            hp=wall.hp,
            live=wall.live
        ))

    @staticmethod
    def explosion_to_data(explosion) -> dict:
        """将爆炸精灵转换为可序列化的字典"""
        return asdict(ExplosionData(
            id=explosion.id,
            x=explosion.rect.center[0],
            y=explosion.rect.center[1],
            step=explosion.step,
            explode_type=explosion.type
        ))

    @staticmethod
    def game_info_to_data(normal_variables, my_tank, teammate_tank=None) -> dict:
        """提取游戏全局信息"""
        info = GameInfo(
            remaining_enemies=normal_variables.remaining_enemies,
            player1_hp=my_tank.hp if my_tank else 0,
            player2_hp=teammate_tank.hp if teammate_tank else 0,
            game_win=normal_variables.game_win,
            game_lose=normal_variables.game_lose,
        )
        return asdict(info)
