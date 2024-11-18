'''
채팅 예제 구현 코드: https://bokyeong-kim.github.io/python/flask/2020/05/09/flask(1).html

관련 파일: chattest_exam1.html

테스트시 창 2개를 띄우고 socketio 통신이 잘 되는 지 확인
'''

from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = '비밀번호 설정'
socketio = SocketIO(app)

#시작 시 페이지로 이동
@app.route('/')
def sessions():
    return render_template('chat_test_exam1.html')

#메시지 수신 신호
def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')

#??? 이게 뭐임
@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    print('received my event: ' + str(json))
    socketio.emit('my response', json, callback=messageReceived)

if __name__ == '__main__':
    socketio.run(app, debug=True)