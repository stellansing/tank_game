
import json
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional


class MessageType(str, Enum):
    # 连接握手
    CONNECT = "connect"
    CONNECT_ACK = "connect_ack"
    # 游戏数据
    INPUT = "input"           # 客户端输入
    STATE = "state"           # 服务端全量状态快照
    LEVEL_DATA = "level_data"  # 关卡数据
    GAME_START = "game_start"  # 游戏开始
    GAME_OVER = "game_over"    # 游戏结束
    # 断开连接
    DISCONNECT = "disconnect"


@dataclass
class TankData:
    id: int
    x: int
    y: int
    direction: str
    hp: int
    live: bool
    tank_type: str
    enemy_type: str = ""  # 敌人种类


@dataclass
class BulletData:
    id: int
    x: int
    y: int
    direction: str


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
class HomeData:
    """基地（home）状态数据"""
    x: int
    y: int
    live: bool
    destroyed: bool


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
    remaining_enemies: int
    player1_hp: int = 3
    player2_hp: int = 3
    game_win: bool = False
    game_lose: bool = False
    player1_kills: int = 0
    player2_kills: int = 0
    current_level: int = 1
    level_transition: bool = False


@dataclass
class InputData:
    key_order: list = field(default_factory=list)
    space_pressed: bool = False


@dataclass
class GameStateSnapshot:
    tanks: list = field(default_factory=list)
    bullets: list = field(default_factory=list)
    walls: list = field(default_factory=list)
    explosions: list = field(default_factory=list)
    home: Optional[dict] = None
    game_info: Optional[dict] = None


class NetworkMessage:

    ENCODING = 'utf-8'

    @staticmethod
    def encode(msg_type: MessageType, data: dict = None) -> bytes:
        """将消息编码为JSON字节串"""
        message = {"type": msg_type.value}
        if data:
            message.update(data)
        json_str = json.dumps(message, separators=(',', ':'))  # 压缩传输量
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
            return MessageType(message.get("type"))
        except ValueError:
            return None

    # ---- 创建各类消息 ----

    @classmethod
    def connect(cls) -> bytes:
        return cls.encode(MessageType.CONNECT)

    @classmethod
    def connect_ack(cls, player_id: str) -> bytes:
        return cls.encode(MessageType.CONNECT_ACK, {"player_id": player_id})

    @classmethod
    def input_msg(cls, input_data: InputData) -> bytes:
        return cls.encode(MessageType.INPUT, asdict(input_data))

    @classmethod
    def state_snapshot(cls, snapshot: GameStateSnapshot) -> bytes:
        return cls.encode(MessageType.STATE, asdict(snapshot))

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
        return cls.encode(MessageType.GAME_OVER, {"result": result})

    @classmethod
    def disconnect(cls, reason: str = "") -> bytes:
        return cls.encode(MessageType.DISCONNECT, {"reason": reason})

    # ---- 从实体构建数据对象 ----

    @staticmethod
    def tank_to_data(tank, tank_type: str) -> dict:
        return asdict(TankData(
            id=tank.id,
            x=tank.rect.left,
            y=tank.rect.top,
            direction=tank.direction if tank.live else tank.direction,
            hp=tank.hp,
            live=tank.live,
            tank_type=tank_type,
            enemy_type=getattr(tank, 'enemy_type', ''),
        ))

    @staticmethod
    def bullet_to_data(bullet) -> dict:
        return asdict(BulletData(
            id=bullet.id,
            x=bullet.rect.left,
            y=bullet.rect.top,
            direction=bullet.direction,
        ))

    @staticmethod
    def wall_to_data(wall) -> dict:
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
        return asdict(ExplosionData(
            id=explosion.id,
            x=explosion.rect.center[0],
            y=explosion.rect.center[1],
            step=explosion.step,
            explode_type=explosion.type
        ))

    @staticmethod
    def home_to_data(home) -> dict:
        return asdict(HomeData(
            x=home.rect.left,
            y=home.rect.top,
            live=home.live,
            destroyed=home.destroyed,
        ))

    @staticmethod
    def game_info_to_data(normal_variables, my_tank, teammate_tank=None) -> dict:
        info = GameInfo(
            remaining_enemies=normal_variables.remaining_enemies,
            player1_hp=my_tank.hp if my_tank else 0,
            player2_hp=teammate_tank.hp if teammate_tank else 0,
            game_win=normal_variables.game_win,
            game_lose=normal_variables.game_lose,
            player1_kills=my_tank.kills if my_tank else 0,
            player2_kills=teammate_tank.kills if teammate_tank else 0,
            current_level=normal_variables.current_level,
            level_transition=normal_variables.level_transition,
        )
        return asdict(info)
