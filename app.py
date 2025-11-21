from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import threading
import time
from datetime import datetime
import os
import eventlet

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Хранилище сообщений и пользователей
messages = []
users = []

@app.route('/')
def home():
    return "🚀 Мессенджер сервер запущен! Используйте WebSocket для подключения."

@app.route('/status')
def status():
    return jsonify({
        "status": "online",
        "users_count": len(users),
        "messages_count": len(messages)
    })

@socketio.on('connect')
def handle_connect():
    print(f"🔗 Новое подключение: {request.sid}")
    emit('connected', {'message': 'Connected to server'})

@socketio.on('join')
def handle_join(data):
    username = data.get('username')
    if username:
        users.append({'sid': request.sid, 'username': username})
        print(f"👤 {username} присоединился к чату")
        
        # Отправляем историю сообщений новому пользователю
        emit('message_history', messages)
        
        # Уведомляем всех о новом пользователе
        socketio.emit('user_joined', {
            'username': username,
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'users_online': [u['username'] for u in users]
        })

@socketio.on('send_message')
def handle_message(data):
    username = data.get('username')
    message_text = data.get('message')
    
    if username and message_text:
        message_data = {
            'id': len(messages) + 1,
            'username': username,
            'message': message_text,
            'timestamp': datetime.now().strftime("%H:%M:%S")
        }
        
        messages.append(message_data)
        print(f"💬 {username}: {message_text}")
        
        # Отправляем сообщение всем подключенным клиентам
        socketio.emit('new_message', message_data)

@socketio.on('disconnect')
def handle_disconnect():
    user_to_remove = None
    for user in users:
        if user['sid'] == request.sid:
            user_to_remove = user
            break
    
    if user_to_remove:
        users.remove(user_to_remove)
        print(f"👋 {user_to_remove['username']} покинул чат")
        socketio.emit('user_left', {
            'username': user_to_remove['username'],
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'users_online': [u['username'] for u in users]
        })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
