
import json
import time
import threading
from typing import Optional

import pygame

from modules.network.protocol import (
    NetworkMessage, MessageType, GameStateSnapshot,
    InputData
)
from modules.network.udp_socket import UDPSocket
import cfg


class ClientNetwork:

    def __init__(self):
        self._socket = UDPSocket(buffer_size=65536)
        self._host_addr = None
        self._connected = False
        self._running = False

        # 状态接收
        self._latest_snapshot: Optional[GameStateSnapshot] = None
        self._snapshot_lock = threading.Lock()
        self._level_config: Optional[dict] = None
        self._walls_data: Optional[list] = None
        self._game_started = False

        # 关卡切换
        self._pending_level_reset = False

        # 输入发送
        self._last_input_time = 0.0
        self._input_send_interval = 1.0 / 60.0  # 最多60次/秒

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def latest_snapshot(self):
        with self._snapshot_lock:
            return self._latest_snapshot

    @property
    def level_config(self):
        return self._level_config

    @property
    def walls_data(self):
        return self._walls_data

    @property
    def game_started(self):
        return self._game_started

    @property
    def pending_level_reset(self):
        """检查是否需要因关卡切换重置渲染数据（一次性消费）"""
        if self._pending_level_reset:
            self._pending_level_reset = False
            return True
        return False

    def connect(self, host, port=None) -> bool:
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

    def try_connect_handshake(self) -> bool:

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
                        print(f"[Client] 已连接到Host")

                        return True
                except (json.JSONDecodeError, KeyError):
                    pass

            time.sleep(0.1)

        return False

    def update(self):
        if not self._running:
            return

        self._process_incoming()

    def send_input(self, key_order: list, space_pressed: bool):
        if not self._connected:
            return

        now = time.time()
        # 限频发送
        if now - self._last_input_time < self._input_send_interval:
            return
        self._last_input_time = now

        input_data = InputData(
            key_order=list(key_order),
            space_pressed=space_pressed,
        )
        data = NetworkMessage.input_msg(input_data)
        self._socket.send(data)

    def close(self):
        self._running = False
        if self._connected:
            self._socket.send(NetworkMessage.disconnect("client_shutdown"))
        self._connected = False
        self._socket.close()
        print("[Client] 网络已关闭")

    def _process_incoming(self):
        while True:
            data, addr = self._socket.receive(timeout=0.0)
            if data is None:
                break
            self._handle_message(data, addr)

    def _handle_message(self, data: bytes, addr):
        try:
            msg = NetworkMessage.decode(data)
            msg_type = NetworkMessage.get_type(msg)
        except (json.JSONDecodeError, UnicodeDecodeError, KeyError):
            return

        if msg_type is None:
            return

        if msg_type == MessageType.CONNECT_ACK:
            self._handle_connect_ack(msg)

        elif msg_type == MessageType.STATE:
            self._handle_state(msg)
        elif msg_type == MessageType.LEVEL_DATA:
            self._handle_level_data(msg)
        elif msg_type == MessageType.GAME_START:
            self._game_started = True
            print("游戏开始!")
        elif msg_type == MessageType.DISCONNECT:
            reason = msg.get("reason", "unknown")
            print(f"Host断开连接: {reason}")
            self._connected = False

    def _handle_connect_ack(self, msg):
        self._connected = True
        print(f"连接确认")

    def _handle_state(self, msg):
        snapshot = GameStateSnapshot(
            tanks=msg.get("tanks", []),
            bullets=msg.get("bullets", []),
            walls=msg.get("walls", []),
            explosions=msg.get("explosions", []),
            home=msg.get("home"),
            game_info=msg.get("game_info", {})
        )
        with self._snapshot_lock:
            self._latest_snapshot = snapshot

    def _handle_level_data(self, msg):
        self._level_config = msg.get("config", {})
        self._walls_data = msg.get("walls", [])
        self._pending_level_reset = True
