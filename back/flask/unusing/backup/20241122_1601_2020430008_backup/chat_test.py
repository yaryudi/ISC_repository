'''
채팅 예제 구현 코드: https://bokyeong-kim.github.io/python/flask/2020/05/09/flask(1).html

관련 파일: 
chat_test_inroom.html   - 사용자 토큰 + 방 토큰을 바탕으로 채팅 환경 생성 및 DB와의 데이터 상호작용
chat_test_outroom.html  - DB정보 + 사용자토큰을 바탕으로 방 토큰 생성
chat_test_login.html    - 사용자 토큰 생성

테스트시 창 2개를 띄우고 socketio 통신이 잘 되는 지 확인
'''

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import jwt
import datetime
import hashlib
from pymongo import MongoClient
from flask_socketio import SocketIO

SECRET_KEY = 'SPARTA'

app = Flask(__name__)
app.config['SECRET_KEY'] = '비밀번호 설정'
socketio = SocketIO(app)

client = MongoClient('mongodb+srv://rjh0162_rw:difbel0162@cluster0.6twyc.mongodb.net/')
db = client.user_data
db_chat = client.ChatDB


#함수


#메시지 수신 신호
def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')
    

#단순 이동 함수

    
#채팅방 내부로 이동 
@app.route('/inroom')
def go_inroom():
    return render_template('chat_test_inroom.html')

#채팅방 외부로 이동
@app.route('/outroom')
def go_outroom():
    return render_template('chat_test_outroom.html')

#채팅방 시작 전 로그인 환경
@app.route('/')
def go_login():
    return render_template('chat_test_login.html')


#API 기능 함수


@app.route('/api/login', methods=['POST'])
def api_login():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    # 회원가입 때와 같은 방법으로 pw를 암호화합니다.
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    # id, 암호화된pw을 가지고 해당 유저를 찾습니다.
    result = db.user.find_one({'id': id_receive, 'pw': pw_hash})

    # 찾으면 JWT 토큰을 만들어 발급합니다. - not None -> 존재한다면
    if result is not None:
        # JWT 토큰 생성 -> 해당 토큰에 id와 만료시간에 관련된 정보 삽입
        payload = {
            'id': id_receive,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=500)
        }
        #토큰의 암호화!
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        # token을 줍니다.
        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})

# 로그아웃
@app.route('/api/logout', methods=['POST'])
def api_logout():
    # 클라이언트에서 보내는 JWT 토큰을 지워줍니다.
    resp = jsonify({'result': 'success', 'msg': '로그아웃 되었습니다.'})
    resp.set_cookie('mytoken', '', expires=0)  # JWT 토큰을 삭제하기 위해 만료 시간을 0으로 설정
    return resp

# 보안: 로그인한 사용자만 통과할 수 있는 API
@app.route('/api/isAuth', methods=['GET'])
def api_valid():
    token_receive = request.cookies.get('mytoken')
    try:
        # token을 시크릿키로 디코딩합니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # payload 안에 id가 들어있습니다. 이 id로 유저정보를 찾습니다.
        userinfo = db.user.find_one({'id': payload['id']}, {'_id': 0})
        return jsonify({'result': 'success', 'nickname': userinfo['nick']})
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        # 로그인 정보가 없으면 에러가 납니다!
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})

#클라이언트-> socket.emit('my event', data), 서버에서 이 이벤트를 처리하는 함수가 실행
@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    #클라이언트로부터 받은 json 데이터를 로그로 출력합니다.
    print('received my event: ' + str(json))
    
    #여기서 받은 채팅기록을 DB에 저장 - 발신자 + 전송 시간 + 전송내용
    
    
    #socketio.emit은 서버가 클라이언트로 메시지를 보낼 때 사용하는 함수 + json과 같이 보낸다.
    #callback=messageReceived, 클라이언트에서 응답을 보내면 messageReceived 함수를 실행(callback)
    socketio.emit('my response', json, callback=messageReceived)

if __name__ == '__main__':
    socketio.run(app, debug=True)