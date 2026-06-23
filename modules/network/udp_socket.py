
import socket
import select
from typing import Tuple


class UDPSocket:
    """UDP套接字封装，提供绑定、发送和接收功能"""

    def __init__(self, buffer_size=65536):

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.setblocking(False)
        self._buffer_size = buffer_size
        self._remote_addr = None

    def bind(self, port=5555):
        """绑定端口"""
        self._sock.bind(('0.0.0.0', port))

    def set_remote(self, host, port):
        """设置远程地址"""
        self._remote_addr = (host, port)

    def send(self, data: bytes, addr: Tuple = None) -> bool:
        """发送UDP数据包"""
        target = addr or self._remote_addr
        if target is None:
            return False
        try:
            self._sock.sendto(data, target)
            return True
        except (OSError, socket.error):
            return False

    def receive(self, timeout=0.5):
        """接收UDP数据包（非阻塞，可设置超时）"""
        try:
            ready = select.select([self._sock], [], [], timeout)
            if ready[0]:
                data, addr = self._sock.recvfrom(self._buffer_size)
                return data, addr
        except BlockingIOError:
            pass
        except (OSError, socket.error):
            pass
        return None, None

    def close(self) -> None:
        """关闭套接字"""
        try:
            self._sock.close()
        except (OSError, socket.error):
            pass
