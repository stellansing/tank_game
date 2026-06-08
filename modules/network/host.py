"""
Host（服务端）网络模块
Host运行权威游戏逻辑，接收客户端输入，发送全量状态快照
"""
import json
import time
import threading
from typing import Optional, Callable

import pygame

from modules.network.protocol import (
    NetworkMessage, MessageType, GameStateSnapshot, InputData
)
from modules.network.udp_socket import UDPSocket
import cfg


class HostNetwork:
    """
    Host端网络管理器
    负责：等待客户端连接、接收输入、发送状态快照、心跳管理
    """

    def __init__(self, port=cfg.NETWORK_PORT):
        self._port = port
        self._socket = UDPSocket()
        self._client_addr = None
        self._connected = False
        self.running = False

        # 状态同步
        self._sync_interval = cfg.NETWORK_SYNC_INTERVAL
        self._frame_counter = 0
        self._state_seq = 0

        # 客户端输入缓存
        self._latest_input: Optional[InputData] = None
        self._input_lock = threading.Lock()

        # 回调
        self._on_client_connected: Optional[Callable] = None
        self._on_client_disconnected: Optional[Callable] = None

        # 等待连接状态
        self._accept_timeout = cfg.NETWORK_ACCEPT_TIMEOUT
        self._waiting_for_client = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def client_addr(self):
        return self._client_addr

    @property
    def latest_input(self):
        """线程安全地获取最新客户端输入"""
        with self._input_lock:
            inp = self._latest_input
            self._latest_input = None  # 消费后清空
            return inp

    @property
    def has_input(self) -> bool:
        with self._input_lock:
            return self._latest_input is not None

    def set_callbacks(self, on_connected: Callable = None, on_disconnected: Callable = None):
        """设置回调函数"""
        self._on_client_connected = on_connected
        self._on_client_disconnected = on_disconnected

    def start_listening(self) -> bool:
        """启动监听，等待客户端连接"""
        try:
            self._socket.bind(self._port)
            self._waiting_for_client = True
            self.running = True
            print(f"[Host] 正在监听端口 {self._port}，等待客户端连接...")
            return True
        except OSError as e:
            print(f"[Host] 绑定端口 {self._port} 失败: {e}")
            return False

    def wait_for_client(self, timeout= None) -> bool:
        """
        阻塞式等待客户端连接（在游戏循环外调用）
        :param timeout: 超时秒数，None使用默认配置
        :return: 是否成功连接
        """

        while self.running and not self._connected:

            # 处理pygame事件以保持窗口响应
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return False

            self._process_incoming()
            time.sleep(0.01)

        return self._connected

    def update(self):
        """
        每帧调用:处理网络消息
        应在游戏主循环中调用
        """
        if not self.running:
            return

        self._process_incoming()

    def send_state(self, snapshot: GameStateSnapshot):
        """发送游戏状态快照给客户端"""
        if not self._connected:
            return

        self._frame_counter += 1
        if self._frame_counter % self._sync_interval == 0:
            self._state_seq += 1
            snapshot.seq = self._state_seq
            data = NetworkMessage.state_snapshot(snapshot)
            self._socket.send(data, self._client_addr)

    def send_event(self, event_name: str, event_data: dict = None):
        """发送事件通知"""
        if not self._connected:
            return
        data = NetworkMessage.event(event_name, event_data)
        self._socket.send(data, self._client_addr)

    def send_level_data(self, level_config: dict, walls_data: list):
        """发送关卡数据"""
        if not self._connected:
            return
        data = NetworkMessage.level_data(level_config, walls_data)
        self._socket.send(data, self._client_addr)

    def send_game_start(self):
        """发送游戏开始信号"""
        if not self._connected:
            return
        self._socket.send(NetworkMessage.game_start(), self._client_addr)

    def send_game_over(self, result: str):
        """发送游戏结束信号"""
        if not self._connected:
            return
        self._socket.send(NetworkMessage.game_over(result), self._client_addr)

    def send_disconnect(self, reason: str = ""):
        """通知客户端断开连接"""
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
        print("[Host] 网络已关闭")

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
            return  # 忽略无法解析的消息
        if msg_type is None:
            return

        if msg_type == MessageType.CONNECT:
            self._handle_connect(addr, msg)
        elif msg_type == MessageType.INPUT:
            self._handle_input(msg)
        elif msg_type == MessageType.DISCONNECT:
            self._handle_disconnect(msg)



    def _handle_connect(self, addr, msg):
        """处理客户端连接请求"""
        self._client_addr = addr
        self._connected = True
        self._waiting_for_client = False

        # 发送确认
        self._socket.send(
            NetworkMessage.connect_ack("player2"),
            self._client_addr
        )
        print(f"[Host] 客户端已连接: {addr}")

        if self._on_client_connected:
            self._on_client_connected()


    def _handle_input(self, msg):
        """处理客户端输入"""
        if self._connected:
            input_data = InputData(
                key_order=msg.get("key_order", []),
                space_pressed=msg.get("space_pressed", False),
                seq=msg.get("seq", 0)
            )
            with self._input_lock:
                self._latest_input = input_data

    def _handle_disconnect(self, msg):
        """处理客户端断开连接"""
        reason = msg.get("reason", "unknown")
        print(f"[Host] 客户端断开连接: {reason}")
        self._connected = False
        self._client_addr = None
        self._waiting_for_client = True  # 重置等待状态，允许新客户端重连
        if self._on_client_disconnected:
            self._on_client_disconnected()
