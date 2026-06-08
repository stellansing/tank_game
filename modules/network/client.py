"""
Client（客户端）网络模块
Client是纯渲染端，只发送输入并接收/渲染Host的状态快照
"""
import json
import time
import threading
from typing import Optional, Callable

import pygame

from modules.network.protocol import (
    NetworkMessage, MessageType, GameStateSnapshot,
    InputData
)
from modules.network.udp_socket import UDPSocket
import cfg


class ClientNetwork:
    """
    Client端网络管理器
    负责：连接Host、发送输入、接收状态快照、心跳管理
    """

    def __init__(self):
        self._socket = UDPSocket(buffer_size=65536)
        self._host_addr = None
        self._connected = False
        self._running = False
        # self._player_id = "player2"

        # 状态接收
        self._latest_snapshot: Optional[GameStateSnapshot] = None
        self._snapshot_lock = threading.Lock()
        self._level_config: Optional[dict] = None
        self._walls_data: Optional[list] = None
        self._game_started = False
        self._game_result: Optional[str] = None

        # 事件队列
        self._events: list = []
        self._events_lock = threading.Lock()

        # 输入发送
        self._input_seq = 0
        self._last_input_time = 0.0
        self._input_send_interval = 1.0 / 60.0  # 最多60次/秒

        # 重连
        self._max_reconnect = cfg.NETWORK_MAX_RECONNECT
        self._reconnect_count = 0

        # 回调
        self._on_connected: Optional[Callable] = None
        self._on_disconnected: Optional[Callable] = None
        self._on_state_received: Optional[Callable] = None

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def latest_snapshot(self) -> Optional[GameStateSnapshot]:
        """线程安全地获取最新状态快照"""
        with self._snapshot_lock:
            return self._latest_snapshot

    @property
    def level_config(self) -> Optional[dict]:
        return self._level_config

    @property
    def walls_data(self) -> Optional[list]:
        return self._walls_data

    @property
    def game_started(self) -> bool:
        return self._game_started

    @property
    def game_result(self) -> Optional[str]:
        return self._game_result

    def set_callbacks(self, on_connected: Callable = None,
                      on_disconnected: Callable = None,
                      on_state_received: Callable = None):
        """设置回调函数"""
        self._on_connected = on_connected
        self._on_disconnected = on_disconnected
        self._on_state_received = on_state_received

    def connect(self, host, port= None) -> bool:
        """
        连接到Host服务器
        :param host: Host IP地址
        :param port: Host端口号
        :return: 是否初始化成功
        """
        port = port or cfg.NETWORK_PORT
        self._host_addr = (host, port)

        try:
            self._socket.bind(0)  # 系统自动分配端口
            self._socket.set_remote(host, port)
            self._running = True
            print(f"[Client] 正在连接 {host}:{port}...")
            return True
        except OSError as e:
            print(f"[Client] 初始化失败: {e}")
            return False

    def try_connect_handshake(self, timeout= None) -> bool:
        """
        尝试握手连接（阻塞式，在游戏循环外调用）
        :param timeout: 超时秒数
        :return: 是否连接成功
        """
        while self._running and not self._connected:

            # 处理pygame事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                    return False

            # 发送连接请求
            self._socket.send(NetworkMessage.connect())

            # 等待ACK
            data, _ = self._socket.receive(timeout=0.5)
            if data:
                try:
                    msg = NetworkMessage.decode(data)
                    msg_type = NetworkMessage.get_type(msg)
                    if msg_type == MessageType.CONNECT_ACK:
                        self._connected = True
                        # self._player_id = msg.get("player_id", "player2")
                        print(f"[Client] 已连接到Host")
                        if self._on_connected:
                            self._on_connected()
                        return True
                    elif msg_type == MessageType.CONNECT_REJECT:
                        print(f"[Client] 连接被拒绝: {msg.get('reason', '未知原因')}")
                        return False
                except (json.JSONDecodeError, KeyError):
                    pass

            time.sleep(0.1)

        return False

    def update(self):
        """每帧调用：处理网络消息"""
        if not self._running:
            return

        self._process_incoming()


    def send_input(self, key_order: list, space_pressed: bool):
        """发送玩家输入到Host"""
        if not self._connected:
            return

        now = time.time()
        # 限频发送
        if now - self._last_input_time < self._input_send_interval:
            return
        self._last_input_time = now

        self._input_seq += 1
        input_data = InputData(
            key_order=list(key_order),
            space_pressed=space_pressed,
            seq=self._input_seq
        )
        data = NetworkMessage.input_msg(input_data)
        self._socket.send(data)

    def pop_events(self) -> list:
        """取出所有待处理事件"""
        with self._events_lock:
            events = self._events.copy()
            self._events.clear()
            return events

    def close(self):
        """关闭网络连接"""
        self._running = False
        if self._connected:
            self._socket.send(NetworkMessage.disconnect("client_shutdown"))
        self._connected = False
        self._socket.close()
        print("[Client] 网络已关闭")

    # ---- 内部方法 ----

    def _process_incoming(self):
        """处理所有待处理的入站消息"""
        while True:
            data, addr = self._socket.receive(timeout=0.0)
            if data is None:
                break
            self._handle_message(data, addr)

    def _handle_message(self, data: bytes, addr):
        """处理单条消息"""
        try:
            msg = NetworkMessage.decode(data)
            msg_type = NetworkMessage.get_type(msg)
        except (json.JSONDecodeError, UnicodeDecodeError, KeyError):
            return

        if msg_type is None:
            return

        if msg_type == MessageType.CONNECT_ACK:
            self._handle_connect_ack(msg)
        elif msg_type == MessageType.CONNECT_REJECT:
            self._handle_connect_reject(msg)

        elif msg_type == MessageType.STATE:
            self._handle_state(msg)
        elif msg_type == MessageType.EVENT:
            self._handle_event(msg)
        elif msg_type == MessageType.LEVEL_DATA:
            self._handle_level_data(msg)
        elif msg_type == MessageType.GAME_START:
            self._game_started = True
            print("[Client] 游戏开始!")
        elif msg_type == MessageType.GAME_OVER:
            self._game_result = msg.get("result", "lose")
            print(f"[Client] 游戏结束: {self._game_result}")
        elif msg_type == MessageType.DISCONNECT:
            reason = msg.get("reason", "unknown")
            print(f"[Client] Host断开连接: {reason}")
            self._connected = False
            if self._on_disconnected:
                self._on_disconnected()

    def _handle_connect_ack(self, msg):
        self._connected = True
        # self._player_id = msg.get("player_id", "player2")
        print(f"[Client] 连接确认")
        if self._on_connected:
            self._on_connected()

    def _handle_connect_reject(self, msg):
        reason = msg.get("reason", "未知原因")
        print(f"[Client] 连接被拒绝: {reason}")

    def _handle_state(self, msg):
        """处理状态快照"""
        snapshot = GameStateSnapshot(
            seq=msg.get("seq", 0),
            tanks=msg.get("tanks", []),
            bullets=msg.get("bullets", []),
            walls=msg.get("walls", []),
            explosions=msg.get("explosions", []),
            game_info=msg.get("game_info", {})
        )
        with self._snapshot_lock:
            self._latest_snapshot = snapshot
        if self._on_state_received:
            self._on_state_received(snapshot)

    def _handle_event(self, msg):
        """处理事件通知"""
        event_name = msg.get("event", "")
        event_data = msg.get("data", {})
        with self._events_lock:
            self._events.append((event_name, event_data))

    def _handle_level_data(self, msg):
        """处理关卡数据"""
        self._level_config = msg.get("config", {})
        self._walls_data = msg.get("walls", [])
