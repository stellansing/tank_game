"""
UDP Socket 封装模块
提供非阻塞UDP通信能力，支持超时、错误处理和地址管理
"""
import socket
import select
from typing import Optional, Tuple


class UDPSocket:
    """UDP Socket非阻塞封装"""

    def __init__(self, port=5555, timeout: float = 0.0, buffer_size= 65536):
        """
        初始化UDP Socket
        :param port: 绑定端口，0表示系统自动分配
        :param timeout: recv超时时间（秒），0表示非阻塞
        :param buffer_size: 接收缓冲区大小
        """
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.setblocking(False)
        self._buffer_size = buffer_size
        self._bound_port = port
        self._remote_addr= None
        self._is_bound = False

    @property
    def sock(self) -> socket.socket:
        return self._sock

    @property
    def remote_addr(self) -> Optional[Tuple[str, int]]:
        return self._remote_addr

    @property
    def bound_port(self) -> int:
        return self._bound_port

    def bind(self, port= 5555):
        """绑定到指定端口"""
        self._sock.bind(('0.0.0.0', port))
        self._bound_port = port or self._sock.getsockname()[1]
        self._is_bound = True

    def set_remote(self, host, port) -> None:
        """设置远程目标地址（客户端使用）"""
        self._remote_addr = (host, port)

    def send(self, data: bytes, addr:Tuple= None) -> bool:
        """
        发送数据
        :param data: 要发送的字节数据
        :param addr: 目标地址，None则使用已设置的remote_addr
        :return: 是否发送成功
        """
        target = addr or self._remote_addr
        if target is None:
            return False
        try:
            self._sock.sendto(data, target)
            return True
        except (OSError, socket.error):
            return False

    def receive(self, timeout= 0.0):
        """
        非阻塞接收数据
        :param timeout: 等待超时（秒），0表示立即返回
        :return: (data, addr) 或 (None, None) 如果无数据
        """
        try:
            ready = select.select([self._sock], [], [], timeout)
            #ready[0]对应sock可读列表
            if ready[0]:
                data, addr = self._sock.recvfrom(self._buffer_size)
                return data, addr
        except BlockingIOError:
            pass
        except (OSError, socket.error):
            pass
        return None, None

    def receive_from(self, timeout= 0.0):
        """接收数据并自动记录发送方地址"""
        data, addr = self.receive(timeout)
        #记录发送方地址
        if data and addr and self._remote_addr is None:
            self._remote_addr = addr
        return data, addr

    def close(self) -> None:
        """关闭Socket"""
        try:
            self._sock.close()
        except (OSError, socket.error):
            pass

    def __del__(self):
        self.close()
