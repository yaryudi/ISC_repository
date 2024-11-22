'''
채팅 예제 구현 코드: https://bokyeong-kim.github.io/python/flask/2020/05/09/flask(1).html

관련 파일: 
chat_test_inroom.html   - 사용자 토큰 + 방 토큰을 바탕으로 채팅 환경 생성 및 DB와의 데이터 상호작용
chat_test_outroom.html  - DB정보 + 사용자토큰을 바탕으로 방 토큰 생성
chat_test_login.html    - 사용자 토큰 생성

문제 발생 시 류 문의 주세요~

테스트시 창 2개를 띄우고 socketio 통신이 잘 되는 지 확인
'''
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import jwt
import datetime
import hashlib
from pymongo import MongoClient
from flask_socketio import SocketIO, join_room, leave_room, emit
from bson import ObjectId

SECRET_KEY = 'SPARTA'

app = Flask(__name__)
app.config['SECRET_KEY'] = '비밀번호 설정'
socketio = SocketIO(app)

client = MongoClient('mongodb+srv://rjh0162_rw:difbel0162@cluster0.6twyc.mongodb.net/')
db = client.user_data #사용자 탐색용 db
db_chat = client.ChatDB #채팅 탐색용 db

############
#   함수   #
############

#메시지 수신 신호
def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')
    

####################
#   단순 이동 함수   #
####################

    
#채팅방 내부로 이동 
@app.route('/inroom' , methods=['GET', 'POST'])
def go_inroom():
    return render_template('chat_test_inroom.html')

#채팅방 외부로 이동
@app.route('/outroom')
def go_outroom():
    
    token_receive = request.cookies.get('usertoken')
        # token을 시크릿키로 디코딩합니다.
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # payload 안에 id가 들어있습니다. 이 id로 유저정보를 찾습니다.
    username = db.user.find_one({'id': payload['id']}, {'_id': 0})
    
    return render_template('chat_test_outroom.html', username=username['id'])

#채팅방 시작 전 로그인 환경
@app.route('/')
def go_login():
    return render_template('chat_test_login.html')


####################
#   API 기능 함수   #
####################


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
    resp.set_cookie('usertoken', '', expires=0)  # JWT 토큰을 삭제하기 위해 만료 시간을 0으로 설정
    return resp

# 보안: 로그인한 사용자만 통과할 수 있는 API
@app.route('/api/isAuth', methods=['GET'])
def api_valid():
    token_receive = request.cookies.get('usertoken')
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

#outroom에서 사용하는 방 생성및 입장 코드
@app.route('/api/findchatroom', methods=['POST'])
def api_findchatroom():
    token_receive = request.cookies.get('usertoken')
    try:
        # token에서 정보를 뽑아 냅니다.
        #입력받은 id의 유저를 찾습니다.
        payload_user = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        id_receive = request.form['id_give']
        
        #예외조건 - 자신 - 자신 제외, 상대가 DB에 없을 시 오류 출력
        if payload_user['id'] == id_receive:
            return jsonify({'result': 'fail', 'msg': '자기자신과의 대화는 지금도 할 수 있습니다.'})
        
        if db.user.find_one({"id" : id_receive}) is None:
            return jsonify({'result': 'fail', 'msg': '대화상대가 존재하지않습니다.'})

        #두 유저가 존재하면서 활성화된 방이 없다면 새로운 방을 생성
        chatroom_info = db_chat.chat_room.find_one({
            "talker_box": {"$all": [payload_user['id'], id_receive]},
            "Is_room_active": True
        })  # 하나의 문서만 반환됩니다  
        
        #활성화된 채팅방이 없을 경우 채팅방을 생성한다.
        if not chatroom_info:
            chatroom_data = {
            "talker_box": [payload_user['id'], id_receive],
            "talk_box": [],
            "Is_room_active": True
        }    
            # MongoDB에 채팅 방 데이터 삽입
            result = db_chat.chat_room.insert_one(chatroom_data)
            # 새로 생성된 채팅방 정보 가져오기 - none이기 때문
            chatroom_info = db_chat.chat_room.find_one({"_id": result.inserted_id}) 
            
        #토큰에 넣을 데이터 생성
        payload_chat = {
            '_id': str(chatroom_info['_id']),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=500)
        }

        #토큰의 암호화!
        token = jwt.encode(payload_chat, SECRET_KEY, algorithm='HS256')

        # token을 줍니다. - 채팅방 입장
        return jsonify({'result': 'success', 'token': token, 'msg': '채팅방 접속 성공'})

    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        # 로그인 정보가 없으면 에러가 납니다!
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})
    

####################
#   socket.io 함수   #
####################
    
# 클라이언트가 특정 채팅방에 참여하는 이벤트 핸들러 -> 항후 오류 및 예외 처리 필요!
# 해당 함수에는 그 그거 함수랑 딸려오는 그거 그 변수 그거 필요없음! 그 캐시로 데이터를 받아오기 때문!
@socketio.on('join_chat')
def join_chat():
    print("hello,")
    try:
        # 쿠키에서 토큰 가져오기
        token_receive_user = request.cookies.get('usertoken')
        token_receive_chat = request.cookies.get('chattoken')
        if not token_receive_user or not token_receive_chat:
            print("Error: Missing tokens in cookies.")
            return

        print("hello,")
        # 토큰 디코딩
        payload_user = jwt.decode(token_receive_user, SECRET_KEY, algorithms=['HS256'])
        payload_chat = jwt.decode(token_receive_chat, SECRET_KEY, algorithms=['HS256'])

        room_id = payload_chat['_id']  # 대화방 ID
        customer_id = payload_user['id']  # 고객 ID

        # 방 참여
        join_room(room_id)
        print(f"Customer {customer_id} has successfully joined room {room_id}")
        
        #DB에 있던 대화기록 출력 -> 
        #DB의 object를 담는 array를 하나 만든다.
        #array에 따른 반복문 하나
        #반복문은 emit을 통해서 서서히 출력한다.
        socketio.emit('clean_message')
        document = db_chat.chat_room.find_one({"_id": ObjectId(room_id)})
        talk_box = document.get("talk_box", [])
        for item in talk_box:
            sender = item.get("talker", "Unknown")
            message = item.get("talk", "")
            timestamp = item.get("date", "")
            #둘 중 한 명이라도 접속하면 작동, => 대화방에 한 명이 들어가 있으면 중복 출력되는 문제가 있음
            #해당 명령어 이전에 html의 기록을 제거하는 식으로 해결함
            #socketio.emit('clean_message') 활용할것
            #다만, 상대 접속시 재출력 현상 - 깜박이는 현상 발생 => 기능적 문제로 볼 수는 없으나 항후 기회가 되면 해결바람
            socketio.emit('receive_message', {'talker': sender, "talk": message, "date": timestamp}, room=room_id)

    except jwt.ExpiredSignatureError:
        print("Error: Token has expired.")
    except jwt.DecodeError:
        print("Error: Invalid token.")
    except Exception as e:
        print(f"Unexpected error: {e}")

# 채팅방에 메시지 보내기
@socketio.on('send_message')
def send_message(data):
    try:
        # 쿠키에서 토큰 가져오기
        token_receive_user = request.cookies.get('usertoken')
        token_receive_chat = request.cookies.get('chattoken')
        if not token_receive_user or not token_receive_chat:
            print("Error: Missing tokens in cookies.")
            return

        print("hello,207")
        # 토큰 디코딩
        payload_user = jwt.decode(token_receive_user, SECRET_KEY, algorithms=['HS256'])
        payload_chat = jwt.decode(token_receive_chat, SECRET_KEY, algorithms=['HS256'])

        room_id = payload_chat['_id']  # 대화방 ID
        user_id = payload_user['id']  # 고객 ID

        message = data['message']   #메시지 - 이는 프론트에서 받아온 정보를 사용한다.
        time = data['time']   #메시지 - 이는 프론트에서 받아온 정보를 사용한다.
    
        filter_query = {"_id": ObjectId(room_id)}  # 대상 문서를 찾기 위한 조건
        
        #DB와 클라이언트에 전송할 대화 내용
        talk_box = {
            "talker": user_id,
            "talk": message,
            "date": time
        }
        print("why 안돼")
        # 배열에 객체 삽입
        try:
            result = db_chat.chat_room.update_one(filter_query, {"$push": {"talk_box": talk_box}})
            if result.matched_count == 0:
                print("No document matched the filter query.")
            elif result.modified_count == 0:
                print("Document matched but was not modified.")
            else:
                print("Document updated successfully.")
            socketio.emit('receive_message', {'talker': user_id, "talk": message, "date": time}, room=room_id)
        except Exception as e:
            
            print(f"Database update error: {e}")
            socketio.emit('error', {'message': 'Failed to update the database.'}) 
            return
        
        #이후 클라이언트에서 해당 데이터를 출력
        
        
    #jwt 관련 예외처리    
    except jwt.ExpiredSignatureError:
            print("Error: Token has expired.")
            socketio.emit('error', {'message': 'Authentication token expired.'})
            return
    except jwt.DecodeError:
            print("Error: Invalid token.")
            socketio.emit('error', {'message': 'Invalid authentication token.'})
            return
    except Exception as e:
            print(f"Unexpected error: {e}")
            socketio.emit('error', {'message': 'An error occurred while sending the message.'})
            return


if __name__ == '__main__':
    socketio.run(app, debug=True)