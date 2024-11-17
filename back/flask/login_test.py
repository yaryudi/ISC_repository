"""
db - flask - 프론트 로그인 페이지 기능 구현 코드

https://duckgugong.tistory.com/274
-> 해당 예제를 참고하였음

"""


from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import jwt
import datetime
import hashlib
from pymongo import MongoClient

SECRET_KEY = 'SPARTA'

app = Flask(__name__)

client = MongoClient('mongodb+srv://rjh0162_rw:difbel0162@cluster0.6twyc.mongodb.net/user_data')
db = client.user_data

#페이지 이동
@app.route('/')
def home():
    return render_template('logintest_home.html')

@app.route('/login')
def login():
    return render_template('logintest_login.html')

@app.route('/signup')
def signup():
    return render_template('logintest_signup.html')

@app.route('/main')
def main():
    return render_template('logintest_main.html')



# 회원가입
@app.route('/api/signup', methods=['POST'])
def api_register():
    #id가 ~~인 빈 칸에서 입력값을 받아온다.
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']
    nickname_receive = request.form['nickname_give']
    #암호화를 한다.
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest() 

    # 이미 존재하는 아이디면 패스!
    result = db.user.find_one({'id': id_receive})
    if result is not None:
        return jsonify({'result': 'fail', 'msg': '이미 존재하는 ID입니다!'})
    else:
        #db에 기입
        db.user.insert_one({'id': id_receive, 'pw': pw_hash, 'nick': nickname_receive})
        #결과를 반환 - 프론트에 결과 전송
        return jsonify({'result': 'success'})

# 로그인
@app.route('/api/login', methods=['POST'])
def api_login():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    # 회원가입 때와 같은 방법으로 pw를 암호화합니다.
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    # id, 암호화된pw을 가지고 해당 유저를 찾습니다.
    result = db.user.find_one({'id': id_receive, 'pw': pw_hash})

    # 찾으면 JWT 토큰을 만들어 발급합니다.
    if result is not None:
        # JWT 토큰 생성
        payload = {
            'id': id_receive,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=100)
        }
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

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)