from flask import Flask, render_template, redirect, url_for
from flask_socketio import SocketIO, send

# Flask 앱 생성
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# 초기 페이지 라우트
@app.route('/')
def index():
    return render_template('index.html')

# 채팅 페이지 라우트
@app.route('/chat')
def chat():
    return render_template('chat.html')

# 메시지 처리
@socketio.on('message')
def handleMessage(msg):
    print(f"Message: {msg}")
    send(msg, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)