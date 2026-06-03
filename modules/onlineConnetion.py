import socket
import json
import threading
import time
import pygame

class UDPNetwork:
    """UDP局域网联机网络类"""
    
    def __init__(self, port=12345):
        self.port = port
        self.socket = None
        self.is_host = False
        self.connected = False


        self.is_update = False
        
        # 玩家数据
        self.players = []
        self.local_address = None

        self.connected_address = None
        
        # 线程控制
        self.running = False
        self.receive_thread = None
        
        # 广播地址
        self.broadcast_address = '<broadcast>'
        
    def initialize(self):
        """初始化UDP socket"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            #健壮性设置
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.socket.settimeout(0.1)  # 非阻塞模式
            return True
        except Exception as e:
            print(f"Socket初始化失败: {e}")
            return False
    
    def create_host(self):
        """创建主机(房主)"""
        if not self.initialize():
            return False
            
        try:
            self.socket.bind(('0.0.0.0', self.port))
            self.is_host = True
            self.connected = True
            self.running = True
            
            # 启动接收线程
            self.receive_thread = threading.Thread(target=self._receive_messages, daemon=True)
            self.receive_thread.start()
            
            print(f"主机已创建，等待玩家连接... (端口: {self.port})")
            return True
        except Exception as e:
            print(f"创建主机失败: {e}")
            return False
    
    def join_game(self, host_ip=None):
        """加入游戏(客户端)"""
        if not self.initialize():
            return False
            
        try:
            # 如果没有指定主机IP，使用广播查找
            if host_ip is None:
                host_ips = self._find_host()

                if len(host_ips)==0:
                    print("未找到可用的主机")
                    return False
                else:
                    print(f"已找到主机: {host_ip}")
                    host_ip = host_ips[0]

            self.local_address = (host_ip, self.port)
            self.connected = True
            self.running = True
            
            # 发送加入请求
            self.send_message({'type': 'join_request'}, (host_ip, self.port))
            
            # 启动接收线程
            self.receive_thread = threading.Thread(target=self._receive_messages, daemon=True)
            self.receive_thread.start()
            
            print(f"已连接到主机: {host_ip}:{self.port}")
            return True
        except Exception as e:
            print(f"加入游戏失败: {e}")
            return False
    
    def _find_host(self):
        """广播查找主机"""
        try:
            # 创建临时socket用于查找
            temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            temp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            temp_socket.settimeout(2.0)
            
            # 发送广播查询
            query_msg = json.dumps({'type': 'host_query'})
            temp_socket.sendto(query_msg.encode('utf-8'), (self.broadcast_address, self.port))
            
            # 等待响应
            hosts = []
            start_time = time.time()
            timeout = 2.0

            while time.time() - start_time < timeout:
                try:
                    data, addr = temp_socket.recvfrom(1024)
                    response = json.loads(data.decode('utf-8'))
                    if response.get('type') == 'host_response':
                        host_ip = addr[0]
                        if host_ip not in hosts:  # 避免重复添加
                            hosts.append(host_ip)
                            print(f"找到主机: {host_ip}")
                except socket.timeout:
                    break
            
            temp_socket.close()
            return hosts
        except Exception as e:
            print(f"查找主机失败: {e}")
            return None
    
    def _receive_messages(self):
        """接收消息的后台线程"""
        while self.running:
            try:
                data, address = self.socket.recvfrom(4096)
                message = json.loads(data.decode('utf-8'))
                self._handle_message(message, address)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"接收消息错误: {e}")
                break
    
    def _handle_message(self, message, address):
        """处理接收到的消息"""
        msg_type = message.get('type')
        
        if msg_type == 'host_query' and self.is_host:
            # 响应主机查询
            self.send_message({'type': 'host_response'}, address)
            
        elif msg_type == 'join_request' and self.is_host:
            # 处理加入请求
            player = {'tank': None, 'bullets': [], 'last_update': time.time(),'address': address}
            self.players.append(player)
            # 发送确认和当前游戏状态
            self.send_message({
                'type': 'join_confirm',
                'player_count': len(self.players)
            }, address)
            
        elif msg_type == 'join_confirm' and not self.is_host:
            # 加入确认
            print("成功加入游戏")
            self.connected_address = address
            
        elif msg_type == 'keyboard_event':
            # {
            #     'type': 'keyboard_event',
            #     'events': []
            # }
            self.is_updated = True
            self.receive_datas = message

        elif msg_type == 'entity_update':
            self.is_updated = True
            self.receive_datas = message
                
        elif msg_type == 'player_disconnect':
            for i, player in enumerate(self.players):
                if player['address'] == address:
                    del self.players[i]
                    print(f"玩家 {address} 已断开")
                    break

    def send_message(self, message, address=None):
        """发送消息"""
        if not self.socket or not self.connected:
            return False
            
        try:
            data = json.dumps(message).encode('utf-8')
            if address:
                self.socket.sendto(data, address)
            else:
                # 广播给所有已知玩家
                for player in self.players:
                    self.socket.sendto(data, player.get('address'))
            return True
        except Exception as e:
            print(f"发送消息失败: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        self.running = False

        # 发送断开通知
        if self.connected:
            self.send_message({'type': 'player_disconnect'})

        # 关闭socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        self.connected = False
        self.is_host = False
        self.players.clear()
        print("已断开连接")


class ServerHandler:
    """服务器处理类"""
    def __init__(self, port=5000):
        self.is_connected = False
        self.network = UDPNetwork(port)
        self.is_connected=self.network.create_host()
        self.connected_address=self.network.connected_address


    def run(self):
        """运行服务器"""
        data = None
        if self.network.is_updated:
            data = self.handle_updates(self.network.receive_datas)
            self.network.is_updated = False

        if data:
            return data
        return None
    def handle_updates(self, receive_datas):
        events=receive_datas.get('events')
        if events:
            return events
        return None

    def send_data(self, data):
        """发送数据"""
        message={
            'type': 'entity_update',
            'data': data
        }
        self.network.send_message(message, self.connected_address)

    def serialize_tank_data(self, tank):
        if not tank:
            return None
        
        return {
            'id': tank.id,
            'position': (tank.rect.left, tank.rect.top),
            'live': tank.live,
            'direction': tank.direction
        }

    def serialize_bullet_data(self, bullet):
        if not bullet:
            return None

        return {
            'type': 'shoot',
            'tank_id': bullet.owner_tank.id,
            'bullet_pos': list(bullet.rect.topleft),
            'direction': bullet.direction,
            'timestamp': pygame.time.get_ticks()
        }

    def disconnect(self):
        """断开连接"""
        self.network.disconnect()
