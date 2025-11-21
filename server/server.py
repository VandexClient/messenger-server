import socket
import threading
import json
from datetime import datetime
import os

class ChatServer:
    def __init__(self):
        # Получаем порт из переменной окружения или используем по умолчанию
        self.port = int(os.environ.get('PORT', 5555))
        self.host = '0.0.0.0'  # Принимаем подключения со всех интерфейсов
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self.clients = {}
        self.lock = threading.Lock()
        
    def start(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"🚀 Сервер запущен на {self.host}:{self.port}")
            print("Ожидание подключений...")
            
            while True:
                client_socket, address = self.server_socket.accept()
                print(f"🔗 Новое подключение от {address}")
                
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except Exception as e:
            print(f"❌ Ошибка сервера: {e}")
        finally:
            self.server_socket.close()
    
    def handle_client(self, client_socket, address):
        username = None
        try:
            # Получаем имя пользователя
            username_data = client_socket.recv(1024).decode('utf-8')
            if username_data:
                username = username_data.strip()
                
                with self.lock:
                    self.clients[username] = {
                        'socket': client_socket,
                        'address': address
                    }
                
                print(f"👤 Пользователь '{username}' присоединился к чату")
                
                # Уведомляем всех о новом пользователе
                self.broadcast_system_message(f"🟢 {username} присоединился к чату")
                self.broadcast_user_list()
                
                # Основной цикл обработки сообщений
                while True:
                    message_data = client_socket.recv(1024).decode('utf-8')
                    if not message_data:
                        break
                    
                    try:
                        message_obj = json.loads(message_data)
                        self.broadcast_message(message_obj, username)
                    except json.JSONDecodeError:
                        pass
                        
        except Exception as e:
            print(f"❌ Ошибка с клиентом {address}: {e}")
        finally:
            if username:
                with self.lock:
                    if username in self.clients:
                        del self.clients[username]
                
                print(f"👋 Пользователь '{username}' покинул чат")
                self.broadcast_system_message(f"🔴 {username} покинул чат")
                self.broadcast_user_list()
            
            client_socket.close()
    
    def broadcast_message(self, message_obj, sender_username):
        """Отправляет сообщение всем клиентам"""
        message_obj['sender'] = sender_username
        message_obj['timestamp'] = datetime.now().strftime("%H:%M:%S")
        
        message_data = json.dumps(message_obj)
        
        with self.lock:
            disconnected_clients = []
            for username, client_info in self.clients.items():
                try:
                    client_info['socket'].send(message_data.encode('utf-8'))
                except:
                    disconnected_clients.append(username)
            
            # Удаляем отключившихся клиентов
            for username in disconnected_clients:
                del self.clients[username]
                if disconnected_clients:
                    self.broadcast_user_list()
    
    def broadcast_system_message(self, message):
        """Отправляет системное сообщение всем клиентам"""
        system_message = {
            'type': 'system',
            'content': message,
            'timestamp': datetime.now().strftime("%H:%M:%S")
        }
        
        message_data = json.dumps(system_message)
        
        with self.lock:
            disconnected_clients = []
            for username, client_info in self.clients.items():
                try:
                    client_info['socket'].send(message_data.encode('utf-8'))
                except:
                    disconnected_clients.append(username)
            
            for username in disconnected_clients:
                del self.clients[username]
    
    def broadcast_user_list(self):
        """Отправляет обновленный список пользователей всем клиентам"""
        with self.lock:
            user_list = list(self.clients.keys())
        
        user_list_message = {
            'type': 'user_list',
            'users': user_list
        }
        
        message_data = json.dumps(user_list_message)
        
        with self.lock:
            disconnected_clients = []
            for username, client_info in self.clients.items():
                try:
                    client_info['socket'].send(message_data.encode('utf-8'))
                except:
                    disconnected_clients.append(username)
            
            for username in disconnected_clients:
                del self.clients[username]

if __name__ == "__main__":
    server = ChatServer()
    server.start()
