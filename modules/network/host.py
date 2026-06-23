
import json
import time
import threading

import pygame

from modules.network.protocol import (
    NetworkMessage, MessageType, GameStateSnapshot, InputData
)
from modules.network.udp_socket import UDPSocket
import cfg


class HostNetwork:
    """主机端网络管理，处理客户端连接、状态同步和输入接收"""

    def __init__(self, port=cfg.NETWORK_PORT):
        self._port = port
        self._socket = UDPSocket()
        self._client_addr = None
        self._connected = False
        self.running = False

        # 状态同步
        self._sync_interval = cfg.NETWORK_SYNC_INTERVAL
        self._frame_counter = 0

        # 客户端输入缓存
        self._latest_input = None
        self._input_lock = threading.Lock()

        # 等待连接状态
        self._waiting_for_client = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def client_addr(self):
        return self._client_addr

    @property
    def latest_input(self):
        with self._input_lock:
            inp = self._latest_input
            self._latest_input = None
            return inp

    def start_listening(self) -> bool:
        """绑定端口并开始监听客户端连接"""
        try:
            self._socket.bind(self._port)
            self._waiting_for_client = True
            self.running = True
            print(f"[Host] 正在监听端口 {self._port}，等待客户端连接...")
            return True
        except OSError as e:
            print(f"[Host] 绑定端口 {self._port} 失败: {e}")
            return False

    def wait_for_client(self) -> bool:
        while self.running and not self._connected:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return False
            self._process_incoming()
            time.sleep(0.01)
        return self._connected

    def update(self):
        if not self.running:
            return
        self._process_incoming()

    def send_state(self, snapshot: GameStateSnapshot):
        if not self._connected:
            return
        self._frame_counter += 1
        if self._frame_counter % self._sync_interval == 0:
            data = NetworkMessage.state_snapshot(snapshot)
            self._socket.send(data, self._client_addr)

    def send_level_data(self, level_config: dict, walls_data: list):
        if not self._connected:
            return
        data = NetworkMessage.level_data(level_config, walls_data)
        self._socket.send(data, self._client_addr)

    def send_game_start(self):
        if not self._connected:
            return
        self._socket.send(NetworkMessage.game_start(), self._client_addr)

    def send_game_over(self, result: str):
        if not self._connected:
            return
        self._socket.send(NetworkMessage.game_over(result), self._client_addr)

    def send_disconnect(self, reason: str = ""):
        if not self._connected:
            return
        self._socket.send(NetworkMessage.disconnect(reason), self._client_addr)

    def close(self):
        """关闭网络连接"""
        self.running = False
        if self._connected:
            self.send_disconnect("host_shutdown")
        self._connected = False
        self._client_addr = None
        self._socket.close()
        print("Host网络已关闭")

    def _process_incoming(self):
        """处理所有待接收的消息"""
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
        if msg_type == MessageType.CONNECT:
            self._handle_connect(addr, msg)
        elif msg_type == MessageType.INPUT:
            self._handle_input(msg)
        elif msg_type == MessageType.DISCONNECT:
            self._handle_disconnect(msg)

    def _handle_connect(self, addr, msg):
        self._client_addr = addr
        self._connected = True
        self._waiting_for_client = False
        self._socket.send(
            NetworkMessage.connect_ack("player2"),
            self._client_addr
        )
        print(f"[Host] 客户端已连接: {addr}")

    def _handle_input(self, msg):
        if self._connected:
            input_data = InputData(
                key_order=msg.get("key_order", []),
                space_pressed=msg.get("space_pressed", False),
            )
            with self._input_lock:
                self._latest_input = input_data

    def _handle_disconnect(self, msg):
        reason = msg.get("reason", "unknown")
        print(f"[Host] 客户端断开连接: {reason}")
        self._connected = False
        self._client_addr = None
        self._waiting_for_client = True
