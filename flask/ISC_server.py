"""
db - flask - 프론트 로그인 페이지 기능 구현 코드

https://duckgugong.tistory.com/274
-> 해당 예제를 참고하였음


"""
from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    session,
    redirect,
    url_for,
    make_response,
)

import os

import jwt
from datetime import datetime, timedelta
import hashlib
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, join_room, leave_room, emit
from bson import ObjectId
import math

#!!!!!암호화키!!!!!
SECRET_KEY = "SPARTA"

# 서버 구동 초기 설정
app = Flask(__name__, static_folder="static")
app.config["SECRET_KEY"] = "비밀번호 설정"
socketio = SocketIO(app, cors_allowed_origins="*")


# 데이터 베이스 설정
client = MongoClient("mongodb+srv://rjh0162_rw:difbel0162@cluster0.6twyc.mongodb.net/")
db = client.ISC_database  # 사용자 탐색용 db

# 사용자 토큰 명
USERTOKEN = "usertoken"

# JWT토큰 암호/복호화 알고리즘 
ALGORITHMS_JWT = "HS256"

TOKENTIME = 100000

# 업로드 설정
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

HTML_INDEX = "index.html"
HTML_LOGIN = "login.html"
HTML_SIGNUP = "sign-up.html"

HTML_MAIN_KEEP = "home_keeper.html"
HTML_MAIN_CARE = "home_carecody.html"

HTML_OUTROOM = "chat_test_outroom.html"
HTML_INROOM = "chat.html"

HTML_MATCH_CHECK = "match_check.html"
HTML_MATCH_FIND = "find_codi.html"
HTML_MATCH = "match_page.html"
HTML_REQUEST = "match_personal.html"

HTML_SENIOR_INFO1 = "senior-info-(1).html"
HTML_SENIOR_INFO2 = "senior-info-(2).html"
HTML_SENIOR_INFO3 = "senior-info-(3).html"
HTML_SENIOR_INFO4 = "senior-info-(4).html"
HTML_SENIOR_INFO5 = "senior-info-(5).html"

HTML_RESUME = "resume.html"

HTML_TODO_CARE = "todo_carecody.html"
HTML_TODO_KEEP = "todo_maker.html"
HTML_TODO_DIARY = "diary.html"

####################
#  범용       함수   # --> 보안이나 편의성을 위하여 전반적으로 사용되는 함수
####################

# 업로드 가능한 파일 형식 확인
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 보안: 유효한 캐시를 가지고 있는 사용자만
#  api_valid() -> 프론트에서 요청, is_valid(asdf) -> 백에서 알아서 검사
def is_valid():

    token_receive = request.cookies.get(USERTOKEN)

    if token_receive is None:
        # 쿠키가 없을 때의 처리
        return False
    try:
        # token을 시크릿키로 디코딩합니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=[ALGORITHMS_JWT])
        # payload 안에 id가 들어있습니다. 이 id로 유저정보를 찾습니다.
        userinfo = db.user.find_one({"id": payload["id"]}, {"_id": 0})
        return True
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return False
    except jwt.exceptions.DecodeError:
        # 로그인 정보가 없으면 에러가 납니다!
        return False

# 현재 토큰 보유자의 json를 리턴한다.
def what_user():
    token_receive = request.cookies.get(USERTOKEN)

    if token_receive is None:
        # 쿠키가 없을 때의 처리
        return None
    try:
        # token을 시크릿키로 디코딩합니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=[ALGORITHMS_JWT])
        # payload 안에 id가 들어있습니다. 이 id로 유저정보를 찾습니다.
        userinfo = db.user.find_one({"id": payload["id"]})
        return userinfo
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return None
    except jwt.exceptions.DecodeError:
        # 로그인 정보가 없으면 에러가 납니다!
        return None

# 백엔드에서 캐시 방지 헤더 -> 지금은 안씀
def render_template_nocash(html):
    response = make_response(render_template(html))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# 주별 날짜 계산 함수 (일요일 시작)
def get_week_dates(base_date):
    # 일요일 기준으로 주의 시작일 계산
    start_of_week = base_date - timedelta(days=(base_date.weekday() + 1) % 7)
    return [start_of_week + timedelta(days=i) for i in range(7)]

# 월 내에서 주차 계산 함수
def week_number_in_month(date):
    first_day_of_month = date.replace(day=1)
    # 일요일 기준으로 첫 번째 날의 위치를 조정
    first_day_adjusted = (first_day_of_month.weekday() + 1) % 7
    return math.ceil((date.day + first_day_adjusted) / 7)

# 월에 몇 주가 있는지 계산
def total_weeks_in_month(date):
    first_day_of_month = date.replace(day=1)
    last_day_of_month = (date.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    last_day_adjusted = (last_day_of_month.weekday() + 1) % 7
    return math.ceil((last_day_of_month.day + last_day_adjusted) / 7)


####################
#  페이지 이동 함수   # --> render_template를 이용해 html을 불러오는 함수
####################


# index - 첫 페이지, 잘못된 접근 시 해당 페이지로 이동
@app.route("/")
def home():
    if is_valid():
        return redirect("/main")
    return render_template(HTML_INDEX)

# 로그인 페이지
@app.route("/login")
def login():
    if is_valid():
        return redirect("/main")
    return render_template(HTML_LOGIN)

# 회원가입 페이지
@app.route("/signup")
def signup():
    if is_valid():
        return redirect("/main")
    return render_template(HTML_SIGNUP)

# 메칭 페이지 - 매칭 요청, 관게 끊기
@app.route("/match")
def match():
    if not is_valid():
        return redirect("/")
    return render_template((HTML_MATCH))

# 메인 페이지 - 정보 확인 및 페이지 이동가능
@app.route("/main")
def main():

    if not is_valid():
        return redirect("/")

    token_receive = request.cookies.get(USERTOKEN)
    # token을 시크릿키로 디코딩합니다.
    if token_receive:
        try:
            # token을 시크릿키로 디코딩합니다.
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=[ALGORITHMS_JWT])
            # payload 안에 id가 들어있습니다. 이 id로 유저정보를 찾습니다.
            user = db.user.find_one({"id": payload["id"]}, {"_id": 0})
            username = user["nick"] if user else ""
            role = user["role"] if user else ""
        except jwt.ExpiredSignatureError:
            # 토큰이 만료된 경우
            username = ""
            role = ""
        except jwt.InvalidTokenError:
            # 토큰이 유효하지 않은 경우
            username = ""
            role = ""
    else:
        # 토큰이 없는 경우
        username = ""
        role = ""
    if role == "care_coordi":
        senior_info_1 = db.page1.find_one({"nick":user["mate"]})
        senior_info_2 = db.page2.find_one({"nick":user["mate"]})
        senior_info_3 = db.page3.find_one({"nick":user["mate"]})
        senior_info_4 = db.page4.find_one({"nick":user["mate"]})
        senior_info_5 = db.page5.find_one({"nick":user["mate"]})
        codi_info = db.information.find_one({"nick":user["nick"]})
        codi_todo = db.todo.find({"cody":user["nick"]})
        codi_todo = list(codi_todo)
        #데이터 받아오기 - 시니어 정보. todo 
        word = "되지 않았어요!"
        if(user["mate"] != ""):
            word = "되었어요!"
        
            return render_template(HTML_MAIN_CARE, username=username, role="케어코디",
                               codi_todo=codi_todo, senior_info_1 = senior_info_1,
                               senior_info_2 = senior_info_2, senior_info_3 = senior_info_3,
                               senior_info_4 = senior_info_4, senior_info_5 = senior_info_5,
                                word = word, codi_info = codi_info)
        else: 
            return render_template(HTML_MAIN_CARE, username=username, codi_info = codi_info, role="케어코디", word=word)
        #else: 
        #    return render_template(HTML_MAIN_CARE, username=username, codi_info = codi_info, role="케어코디", word=word)
        
    elif role == "keeper":
        #데이터 받아오기 투두 실행 + 케어코디 정보 
        codi_info = db.information.find_one({"nick":user["mate"]})
        codi_todo = db.todo.find({"cody":user["mate"]})
        codi_todo = list(codi_todo)
        word = "되지 않았어요!"
        if(user["mate"] != ""):
            word = "되었어요!"
            return render_template(HTML_MAIN_KEEP, username=username, role="보호자", codi_info = codi_info, codi_todo = codi_todo,
                               word=word)
        else: 
            return render_template(HTML_MAIN_KEEP, username=username, role="보호자", codi_info = codi_info, word=word)

    # 비정상적인 접근 차단
    return redirect("/")

# 매칭 요청 관리 페이지 - 매칭 요청 거절, 매칭 요청 수락
@app.route("/match_personal")
def match_personal():
    if not is_valid():
        return redirect("/match_personal")
    return render_template((HTML_REQUEST))

# 매칭 요청 관리 페이지 - 매칭 요청 거절, 매칭 요청 수락
@app.route("/match_check")
def match_check():
    if not is_valid():
        return redirect("/")
    return render_template((HTML_MATCH_CHECK))

@app.route('/resume', methods=['GET', 'POST'])
def manage_resume():
    user = what_user()
    if request.method == 'POST' and user["role"] != "keeper":
        action = request.form.get('action')  # 버튼의 value 값 가져오기
        name = request.form.get('name')
        age = request.form.get('age')
        gender = request.form.get('gender')
        experience = request.form.get('experience')
        introduction = request.form.get('introduction')

        file = request.files.get('photo')  # 업로드된 파일 가져오기
        photo_filename = None
        
        resume_db = db.information.find_one({"nick": user["nick"]})

        if not resume_db  :
            resume_data = {
                    "name": name or "",
                    "age": age or "",
                    "gender": gender or "",
                    "experience": experience or "",
                    "introduction": introduction or "",
                    "photo": photo_filename or "",
                    "nick" : user["nick"]
                }
            print("asdfasdfasdfasdf")
            db.information.insert_one(resume_data)

        if action == 'upload_photo' and file and allowed_file(file.filename):
            # 사진 업로드 처리
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            photo_filename = f"uploads/{filename}"

            
            # 기존 데이터에 사진 경로 추가/수정
            resume_id = request.form.get('resume_id')
            
            if resume_id:

                db.information.update_one(
                    {"_id": ObjectId(resume_id)},
                    {"$set": {"photo": photo_filename}}
                )
            else:
                # 새로운 데이터 생성 시
                resume_data = {
                    "name": name or "",
                    "age": age or "",
                    "gender": gender or "",
                    "experience": experience or "",
                    "introduction": introduction or "",
                    "photo": photo_filename,
                    "nick" : user["nick"]
                }
                db.information.insert_one(resume_data)
                
            

            return redirect('/resume')
        
        elif action == 'update':  # 수정 요청
            resume_id = request.form.get('resume_id')
            update_data = {
                "name": name,
                "age": age,
                "gender": gender,
                "experience": experience,
                "introduction": introduction,
                "nick": user["nick"]
            }
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                update_data["photo"] = f"uploads/{filename}"
            db.information.update_one(
                {"nick": user["nick"]},
                {"$set": update_data}
            )

        
             
            
        
        return redirect('/resume')

    # GET 요청: 기존 데이터 가져오기
    resume = db.information.find_one({"nick" :user["nick"]})
    return render_template('resume.html', resume=resume)

@app.route('/resume_onlysee', methods=['GET', 'POST'])
def resume_onlysee():
    nick = (request.args.get('nick'))
    print(nick + "asdfasdf")
    
    # nick 값이 없는 경우 처리
    if not nick:
        return "유효하지 않은 요청입니다. 'nick'이 필요합니다.", 400

    resume = db.information.find_one({"name":nick})
    print(resume)
    
    if resume:
        return render_template('resume_onlysee.html', resume=resume)
    else:
        return "이력서를 찾을 수 없습니다.", 404

@app.route('/match_find', methods=['GET'])
def find_codi():
    # 모든 이력서 데이터를 조회
    resumes = list(db.information.find())
    max_length = 5  # 글자수 제한
    processed_resumes = []

    for resu in resumes:
        resu = dict(resu)  # Cursor 객체를 딕셔너리로 변환
        intro = resu.get('introduction', '')  # introduction 키가 없는 경우 기본값으로 빈 문자열 설정
        if len(intro) > max_length:
            resu['introduction'] = intro[:max_length] + "..."
        processed_resumes.append(resu)

    return render_template(HTML_MATCH_FIND, resumes=processed_resumes)

# 채팅방 내부 - 채팅 가능
@app.route("/inroom", methods=["GET", "POST"])
def go_inroom():

    if not is_valid():
        return redirect("/")

    token_receive = request.cookies.get(USERTOKEN)
    # token을 시크릿키로 디코딩합니다.
    if token_receive:
        try:
            # token을 시크릿키로 디코딩합니다.
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=[ALGORITHMS_JWT])
            # payload 안에 id가 들어있습니다. 이 id로 유저정보를 찾습니다.
            user = db.user.find_one({"id": payload["id"]}, {"id": 0})
            if user["role"] == "keeper":
                codi_info = db.information.find_one({"nick":user["mate"]})
            else:
                codi_info = db.information.find_one({"nick":user["nick"]})
            matename = user["mate"]
        except jwt.ExpiredSignatureError:
            # 토큰이 만료된 경우
            matename == ""
        except jwt.InvalidTokenError:
            # 토큰이 유효하지 않은 경우
            matename == ""
    else:
        # 토큰이 없는 경우
        matename == ""
        return redirect("/")

    return render_template(HTML_INROOM, matename=matename, codi_info = codi_info)

# 채팅방 외부 - 채팅방을 골라서 들어갈 수 있음, 다만 디버깅 용임
@app.route("/chat")
def go_outroom():

    if not is_valid():
        return redirect("/")

    token_receive = request.cookies.get(USERTOKEN)
    # token을 시크릿키로 디코딩합니다.
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=[ALGORITHMS_JWT])
    # payload 안에 id가 들어있습니다. 이 id로 유저정보를 찾습니다.
    username = db.user.find_one({"id": payload["id"]}, {"_id": 0})

    return render_template((HTML_OUTROOM), username=username["nick"])

@app.route('/todo', methods=['GET', 'POST'])
def manage_todo():
    
    if not is_valid():
        return redirect("/")
    
    user = what_user()
    if request.method == 'POST':
        # 데이터 추가
        time = request.form.get('time')
        content = request.form.get('content')

        # 현재 날짜 가져오기
        current_date = datetime.now().strftime('%Y-%m-%d')

        if time and content:
            db.todo.insert_one({
                "time": time,
                "content": content,
                "date": current_date,  # 현재 날짜 추가
                "keeper": user["nick"],
                "cody" : user["mate"],
                "comment" : ""
                })
                
            
        return redirect('/todo')
    
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    # 데이터 조회 (출근/퇴근 제외)
    todos = list(
        db.todo.find(
        {
            "content": {"$nin": ["출근", "퇴근"]},
            "keeper": user["nick"],  # nick 필터 추가
            "date": current_date
        }
        ).sort("time", 1)
    )   
    
    return render_template('todo_maker.html', todos=todos)

@app.route('/todo/delete/<todo_id>', methods=['POST'])
def delete_todo(todo_id):
    # 데이터 삭제
    db.todo.delete_one({"_id": ObjectId(todo_id)})
    return redirect('/todo')

###내 ToDo (케어코디가 입력하는 페이지)###
@app.route('/todo_carecody', methods=['GET'])
def care_record():
    if not is_valid():
        return redirect("/")
    
    #사용자의 정보를 가져온다
    user = what_user()
    
    # GET 요청: 모든 todo 데이터를 조회
    # 오늘 날짜 가져오기 (형식: "YYYY-MM-DD")
    today_date = datetime.now().strftime("%Y-%m-%d")
    # MongoDB 쿼리에서 오늘 날짜 사용
    cares = list(db.todo.find({"cody": user["nick"], "date": today_date}).sort("time", 1))  # 시간순으로 정렬
    return render_template('todo_carecody.html', cares=cares)

@app.route('/care/update/<care_id>', methods=['POST'])
def update_care(care_id):
    # 특정 케어 업데이트
    photo = request.files.get('photo')  # 업로드된 사진
    comment = request.form.get('comment')  # 작성된 코멘트

    update_data = {}

    if photo:
        # 사진 저장
        filename = secure_filename(photo.filename)
        photo_path = os.path.join('static/uploads', filename)
        photo.save(photo_path)
        update_data['photo'] = f'uploads/{filename}'

    if comment:
        # 코멘트 업데이트
        update_data['comment'] = comment

    if update_data:
        # MongoDB 업데이트
        db.todo.update_one({"_id": ObjectId(care_id)}, {"$set": update_data})

    return redirect('/todo_carecody')

from datetime import datetime

@app.route('/care/attendance', methods=['POST'])
def record_attendance():
    current_time = datetime.now().strftime('%H:%M')  # 현재 시간 HH:MM 형식으로 저장
    last_entry = db.todo.find_one(sort=[('_id', -1)])  # 가장 최근의 데이터 가져오기

    if last_entry and last_entry.get('content') == '출근':
        # 최근 데이터가 '출근'이라면 '퇴근' 데이터 저장
        db.todo.insert_one({'time': current_time, 'content': '퇴근'})
    else:
        # 최근 데이터가 '출근'이 아니면 '출근' 데이터 저장
        db.todo.insert_one({'time': current_time, 'content': '출근'})

    return redirect('/todo_carecody')  # 내 ToDo 페이지로 리다이렉트

### 돌봄 다이어리(날짜별 모음) ###
@app.route('/diary', methods=['GET'])
def care_record_page():
    if not is_valid():
        return redirect("/")
    
    user = what_user()  # 유저 정보
    
    # URL 파라미터 처리
    week_offset = int(request.args.get('week', 0))  # 기본값은 현재 주(week=0)
    base_date = datetime.now() + timedelta(weeks=week_offset)

    # 주차 계산 (월 기준)
    current_month = base_date.month
    current_year = base_date.year
    current_week_number = week_number_in_month(base_date)
    total_weeks = total_weeks_in_month(base_date)

    # 주차 이동 제한
    if current_week_number > total_weeks:
        base_date = base_date.replace(day=1) + timedelta(days=32)  # 다음 달로 이동
        base_date = base_date.replace(day=1)
    elif current_week_number < 1:
        base_date = base_date.replace(day=1) - timedelta(days=1)  # 이전 달로 이동
        base_date = base_date.replace(day=1)

    # 주간 날짜 계산
    start_of_week = base_date - timedelta(days=base_date.weekday() + 1)  # 주의 일요일
    week_dates = get_week_dates(base_date)
    formatted_week = [date.strftime('%Y-%m-%d') for date in week_dates]
    days = ['일', '월', '화', '수', '목', '금', '토']

    # MongoDB 쿼리
    selected_date = request.args.get('date')  # 특정 날짜 선택
    if not selected_date:  # 날짜가 선택되지 않은 경우 현재 날짜 사용
        if week_offset == 0:  # 첫 진입 시, 오늘 날짜 사용
            selected_date = datetime.now().strftime('%Y-%m-%d')
        else:  # 이전주/다음주 버튼을 눌렀을 때는 해당 주의 일요일 사용
            selected_date = start_of_week.strftime('%Y-%m-%d')
    
    if user["role"] == "keeper":
        query = {"date": selected_date, "keeper": user["nick"]}
    else:
        query = {"date": selected_date, "cody": user["nick"]}
    
    # 선택된 날짜의 요일 계산
    selected_date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
    current_day = days[(selected_date_obj.isoweekday() % 7)]

    cares = list(db.todo.find(query).sort("time", 1))  # 시간순 정렬

    # 데이터를 템플릿으로 전달
    return render_template(
        'diary.html',
        cares=cares,
        week_dates=zip(days, formatted_week),
        current_week=f"{current_year}년 {current_month}월 {current_week_number}째주",
        current_date=selected_date,
        current_day=current_day,  # 선택된 요일 전달
        week_offset=week_offset
    )

####################
#       기능 함수   # - @app.route("/api 를 사용하는 함수, 주로 methods= 가 존재함
####################

#### 계정 관련 함수 ####

# 회원가입
@app.route("/api/signup", methods=["POST"])
def api_register():
    # id가 ~~인 빈 칸에서 입력값을 받아온다.
    id_receive = request.form["id_give"]
    pw_receive = request.form["pw_give"]
    nickname_receive = request.form["nickname_give"]
    role_receive = request.form["role"]  # keeper 혹은 care_coordi을 전달받게 된다.

    # 암호화를 한다.
    pw_hash = hashlib.sha256(pw_receive.encode("utf-8")).hexdigest()

    # 빈칸 입력시 경고
    if (
        id_receive == ""
        or pw_receive == ""
        or nickname_receive == ""
        or role_receive == ""
    ):
        return jsonify({"result": "fail", "msg": "공란이 존재합니다!"})
    # 이미 존재하는 아이디면 패스!
    user_exists = db.user.find_one(
        {"$or": [{"id": id_receive}, {"nick": nickname_receive}]}
    )
    if user_exists:
        if user_exists["id"] == id_receive:
            return jsonify({"result": "fail", "msg": "이미 존재하는 아이디입니다!"})
        elif user_exists["nick"] == nickname_receive:
            return jsonify({"result": "fail", "msg": "이미 존재하는 닉네임입니다!"})
    else:
        # db에 기입
        db.user.insert_one(
            {
                "id": id_receive,
                "pw": pw_hash,
                "nick": nickname_receive,
                "role": role_receive,
                "mate": "",
            }
        )
        # 결과를 반환 - 프론트에 결과 전송
        return jsonify({"result": "success"})

# 로그인
@app.route("/api/login", methods=["POST"])
def api_login():
    id_receive = request.form["id_give"]
    pw_receive = request.form["pw_give"]
    role_receive = request.form["role"]  # keeper 혹은 care_coordi을 전달받게 된다.

    # 회원가입 때와 같은 방법으로 pw를 암호화합니다.
    pw_hash = hashlib.sha256(pw_receive.encode("utf-8")).hexdigest()

    # id, 암호화된pw을 가지고 해당 유저를 찾습니다.
    result = db.user.find_one({"id": id_receive, "pw": pw_hash, "role": role_receive})

    # 찾으면 JWT 토큰을 만들어 발급합니다. - not None -> 존재한다면
    if result is not None:
        # JWT 토큰 생성 -> 해당 토큰에 id와 만료시간에 관련된 정보 삽입
        # 토큰 유효기간은 TOKENTIME = 1000초
        payload = {
            "id": id_receive,
            "exp": datetime.utcnow() + timedelta(seconds=TOKENTIME),
        }
        # 토큰의 암호화!
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHMS_JWT)

        # token을 줍니다.
        return jsonify({"result": "success", "token": token, "role": role_receive})
        
    # 찾지 못하면
    else:
        return jsonify(
            {"result": "fail", "msg": "아이디/비밀번호/역할 (이)가 일치하지 않습니다."}
        )

# 로그아웃
@app.route("/api/logout", methods=["POST"])
def api_logout():
    # 클라이언트에서 보내는 JWT 토큰을 지워줍니다.
    resp = jsonify({"result": "success", "msg": "로그아웃 되었습니다."})
    resp.set_cookie(
        USERTOKEN, "", expires=0
    )  # JWT 토큰을 삭제하기 위해 만료 시간을 0으로 설정
    return resp

# 보안: 로그인한 사용자만 통과할 수 있는 API - front에서 사용
@app.route("/api/isAuth", methods=["GET"])
def api_valid():
    token_receive = request.cookies.get(USERTOKEN)

    if token_receive is None:
        # 쿠키가 없을 때의 처리
        return jsonify({"result": "fail", "msg": "로그인 정보가 존재하지 않습니다."})

    try:
        # token을 시크릿키로 디코딩합니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=[ALGORITHMS_JWT])
        # payload 안에 id가 들어있습니다. 이 id로 유저정보를 찾습니다.
        userinfo = db.user.find_one({"id": payload["id"]}, {"_id": 0})
        return jsonify({"result": "success", "nickname": userinfo["nick"]})
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({"result": "fail", "msg": "로그인 시간이 만료되었습니다."})
    except jwt.exceptions.DecodeError:
        # 로그인 정보가 없으면 에러가 납니다!
        return jsonify({"result": "fail", "msg": "로그인 정보가 존재하지 않습니다."})

#### 채팅 관련 함수 ####

# outroom에서 사용하는 방 생성및 입장 코드
@app.route("/api/findchatroom", methods=["POST"])
def api_findchatroom():
    token_receive = request.cookies.get(USERTOKEN)
    try:
        # token에서 정보를 뽑아 냅니다.
        # 입력받은 id의 유저를 찾습니다.
        payload_user = jwt.decode(
            token_receive, SECRET_KEY, algorithms=[ALGORITHMS_JWT]
        )
        id_receive = request.form["id_give"]

        # 예외조건 - 자신 - 자신 제외, 상대가 DB에 없을 시 오류 출력
        if payload_user["id"] == id_receive:
            return jsonify(
                {"result": "fail", "msg": "자기자신과의 대화는 지금도 할 수 있습니다."}
            )

        if db.user.find_one({"id": id_receive}) is None:
            return jsonify({"result": "fail", "msg": "대화상대가 존재하지않습니다."})

        # 두 유저가 존재하면서 활성화된 방이 없다면 새로운 방을 생성
        chatroom_info = db.chat_room.find_one(
            {
                "talker_box": {"$all": [payload_user["id"], id_receive]},
                "Is_room_active": True,
            }
        )  # 하나의 문서만 반환됩니다

        # 활성화된 채팅방이 없을 경우 채팅방을 생성한다.
        if not chatroom_info:
            chatroom_data = {
                "talker_box": [payload_user["id"], id_receive],
                "talk_box": [],
                "Is_room_active": True,
            }
            # MongoDB에 채팅 방 데이터 삽입
            result = db.chat_room.insert_one(chatroom_data)
            # 새로 생성된 채팅방 정보 가져오기 - none이기 때문
            chatroom_info = db.chat_room.find_one({"_id": result.inserted_id})

        # 토큰에 넣을 데이터 생성
        payload_chat = {
            "_id": str(chatroom_info["_id"]),
            "exp": datetime.utcnow() + timedelta(seconds=TOKENTIME),
        }

        # 토큰의 암호화!
        token = jwt.encode(payload_chat, SECRET_KEY, algorithm=ALGORITHMS_JWT)

        # token을 줍니다. - 채팅방 입장
        return jsonify({"result": "success", "token": token, "msg": "채팅방 접속 성공"})

    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({"result": "fail", "msg": "로그인 시간이 만료되었습니다."})
    except jwt.exceptions.DecodeError:
        # 로그인 정보가 없으면 에러가 납니다!
        return jsonify({"result": "fail", "msg": "로그인 정보가 존재하지 않습니다."})

@app.route("/api/findchatroom_mate", methods=["POST"])
def api_findchatroom_mate():
    token_receive = request.cookies.get(USERTOKEN)
    try:
        # token에서 정보를 뽑아 냅니다.
        # 입력받은 id의 유저를 찾습니다.
        payload_user = jwt.decode(
            token_receive, SECRET_KEY, algorithms=[ALGORITHMS_JWT]
        )
        user = db.user.find_one({"id": payload_user["id"]})
        if "mate" in user:
            user_mate = db.user.find_one({"nick": user["mate"]})
        else:
            return jsonify({"result": "fail", "msg": "mate된 상대가 없습니다.."})

        # 자신의 mate상대가 없다면 실패
        if user["mate"] == "":
            return jsonify({"result": "fail", "msg": "mate된 상대가 없습니다.."})

        if user_mate is None:
            return jsonify(
                {
                    "result": "fail",
                    "msg": "mate가 존재하지않습니다. 운영팀에 연락바랍니다.",
                }
            )

        # 두 유저가 존재하면서 활성화된 방이 없다면 새로운 방을 생성
        chatroom_info = db.chat_room.find_one(
            {
                "talker_box": {"$all": [payload_user["id"], user_mate["id"]]},
                "Is_room_active": True,
            }
        )  # 하나의 문서만 반환됩니다

        # 활성화된 채팅방이 없을 경우 채팅방을 생성한다.
        if not chatroom_info:
            chatroom_data = {
                "talker_box": [payload_user["id"], user_mate["id"]],
                "talk_box": [],
                "Is_room_active": True,
            }
            # MongoDB에 채팅 방 데이터 삽입
            result = db.chat_room.insert_one(chatroom_data)
            # 새로 생성된 채팅방 정보 가져오기 - none이기 때문
            chatroom_info = db.chat_room.find_one({"_id": result.inserted_id})

        # 토큰에 넣을 데이터 생성
        payload_chat = {
            "_id": str(chatroom_info["_id"]),
            "exp": datetime.utcnow() + timedelta(seconds=TOKENTIME),
        }

        # 토큰의 암호화!
        token = jwt.encode(payload_chat, SECRET_KEY, algorithm=ALGORITHMS_JWT)

        # token을 줍니다. - 채팅방 입장
        return jsonify({"result": "success", "token": token, "msg": "채팅방 접속 성공"})

    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({"result": "fail", "msg": "로그인 시간이 만료되었습니다."})
    except jwt.exceptions.DecodeError:
        # 로그인 정보가 없으면 에러가 납니다!
        return jsonify({"result": "fail", "msg": "로그인 정보가 존재하지 않습니다."})

#### 시니어 정보 관련 함수 ####

# 주소 입력 및 입력값 출력
@app.route("/address", methods=["GET", "POST"])
def address():
    # 기본 값
    address = ""
    detail_address = ""

    if request.method == "POST":
        # 입력 데이터 받기
        address = request.form.get("address")
        detail_address = request.form.get("detail_address")

        # 기존 데이터 확인
        existing_address = db.page1.find_one()

        if existing_address:
            # 기존 데이터 업데이트
            db.page1.update_one(
                {"_id": existing_address["_id"]},  # 기존 데이터 조건 (_id 사용)
                {"$set": {"address": address, "detail_address": detail_address}},
            )
        else:
            # 새로운 데이터 삽입
            db.page1.insert_one(
                {
                    "address": address or "",
                    "detail_address": detail_address or "",
                }
            )

        # 입력값 확인 (빈 값 처리)
        if not (address and detail_address):
            # 값이 없을 경우 에러 처리
            error_message = "모든 필드를 입력해 주세요."
            return render_template(
                HTML_SENIOR_INFO1,
                address=address,
                detail_address=detail_address,
                error=error_message,
            )

    # GET 요청 시 데이터 불러오기
    latest_data = db.page1.find_one()
    if latest_data:
        address = latest_data.get("address", "")
        detail_address = latest_data.get("detail_address", "")

    return render_template(
        HTML_SENIOR_INFO1, address=address, detail_address=detail_address
    )

@app.route("/senior_info_1", methods=["GET", "POST"])
def senior_info_1(): 
    
    if not is_valid():
        return redirect("/")
    
    #현 클라이언트의 정보 습득
    user = what_user()
    
    if request.method == "POST":
        data = request.get_json()
        basic_address = str(data.get("basic_address")).strip()
        detail_address = str(data.get("detail_address")).strip()

        # 유효성 검사
        if not (basic_address != "" and detail_address != ""):
            return jsonify({"message": "모든 필드를 입력해주세요."}), 400

        # 데이터베이스 저장
        existing_entry = db.page1.find_one({"nick":user["nick"]})
        if existing_entry:
            print("기존 업데이트")
            # 기존 데이터 업데이트
            db.page1.update_one(
                {"_id": existing_entry["_id"] },
                {
                    "$set": {
                        "basic_address": basic_address,
                        "detail_address": detail_address,
                        "nick":user["nick"]
                    }
                },
            )
        else:
            print("새로운 업데이트")
            # 새로운 데이터 삽입
            db.page1.insert_one(
                {  # page1 컬렉션에 데이터 삽입
                    "basic_address": basic_address,
                    "detail_address": detail_address,
                    "nick":user["nick"]
                }
            )

        return jsonify({"message": "데이터가 성공적으로 저장되었습니다."}), 200

    # GET 요청 처리
    senior = db.page1.find_one({"nick":user["nick"]})
    basic_address = senior["basic_address"] if senior else ""
    detail_address = (
        senior["detail_address"] if senior else ""
    )  # detail_address를 올바르게 할당

    return render_template(
        HTML_SENIOR_INFO1,  # 이 부분은 적절한 템플릿 파일명을 사용해야 합니다.
        basic_address=basic_address,
        detail_address=detail_address
    )

# 2 페이지 - 성함, 성별, 출생년도, 체중
@app.route("/senior_info_2", methods=["GET", "POST"])
def senior_info_2():
    
    if not is_valid():
        return redirect("/")
    
    #현 클라이언트의 정보 습득
    user = what_user()
    
    if request.method == "POST":
        data = request.get_json()
        name = data.get("name")
        gender = data.get("gender")
        birth = data.get("birth")
        weight = data.get("weight")

        # 유효성 검사
        if not (name and gender and birth and weight):
            return jsonify({"message": "모든 필드를 입력해주세요."}), 400

        # 데이터베이스 저장
        existing_entry = db.page2.find_one({"nick":user["nick"]})
        if existing_entry:
            print("기존 업데이트")
            # 기존 데이터 업데이트
            db.page2.update_one(
                {"_id": existing_entry["_id"]},
                {
                    "$set": {
                        "name": name,
                        "gender": gender,
                        "birth": birth,
                        "weight": weight,
                        "nick":user["nick"]
                    }
                },
            )
        else:
            print("새로운 업데이트")
            # 새로운 데이터 삽입
            db.page2.insert_one(
                {"name": name, "gender": gender, "birth": birth, "weight": weight, "nick":user["nick"]}
            )

        return jsonify({"message": "데이터가 성공적으로 저장되었습니다."}), 200

    # GET 요청 처리
    senior = db.page2.find_one({"nick":user["nick"]})
    name = senior["name"] if senior else ""
    gender = senior["gender"] if senior else ""
    birth = senior["birth"] if senior else ""
    weight = senior["weight"] if senior else ""

    return render_template(
        HTML_SENIOR_INFO2,
        name=name,
        gender=gender,
        birth=birth,
        weight=weight,
    )

# 3 페이지  - 질환, 일상생활 능력
@app.route("/senior_info_3", methods=["GET", "POST"])
def senior_info_3():
    
    if not is_valid():
        return redirect("/")
    
    #현 클라이언트의 정보 습득
    user = what_user()
    
    if request.method == "POST":
        print("POST 요청 수신됨")
        print("요청 데이터:", request.form)
        # 사용자가 선택한 데이터 수집
        
        # 기존 데이터베이스 항목 가져오기
        existing_entry = db.page3.find_one({"nick":user["nick"]})
        
        
        selected_diseases = request.form.get("selected-diseases", "").split(", ")
        selected_mobility = request.form.get("selected-mobility", "")
        selected_meal = request.form.get("selected-meal", "")
        selected_relation = request.form.get("selected-relation", "")

        print("POST 요청 수신")
        print(
            "수신한 데이터:",
            selected_diseases,
            selected_mobility,
            selected_meal,
            selected_relation,
        )
        
        if(selected_diseases == "" or selected_mobility == "" or selected_meal == "" or selected_relation == "" ):
            return jsonify({"message": "모든 필드를 입력해주세요."}), 400

        

        if existing_entry:
            # 기존 데이터 업데이트
            db.page3.update_one(
                {"_id": existing_entry["_id"]},
                {
                    "$set": {
                        "selected_diseases": selected_diseases,
                        "selected_mobility": selected_mobility,
                        "selected_meal": selected_meal,
                        "selected_relation": selected_relation,
                        "nick":user["nick"]
                    }
                },
            )
        else:
            # 새로운 데이터 삽입
            db.page3.insert_one(
                {
                    "selected_diseases": selected_diseases,
                    "selected_mobility": selected_mobility,
                    "selected_meal": selected_meal,
                    "selected_relation": selected_relation,
                    "nick":user["nick"]
                }
            )

        # POST 요청 후 페이지 리다이렉트
        return redirect("/senior_info_3")

    # GET 요청 시 기존 데이터 불러오기
    senior_info = db.page3.find_one({"nick":user["nick"]})
    selected_diseases = senior_info["selected_diseases"] if senior_info else []
    selected_mobility = senior_info["selected_mobility"] if senior_info else ""
    selected_meal = senior_info["selected_meal"] if senior_info else ""
    selected_relation = senior_info["selected_relation"] if senior_info else ""

    # HTML 템플릿 렌더링
    return render_template(
        HTML_SENIOR_INFO3,
        selected_diseases=selected_diseases,
        selected_mobility=selected_mobility,
        selected_meal=selected_meal,
        selected_relation=selected_relation
    )

# 4페이지 라우트 - 시간에 관한 거
@app.route("/senior_info_4", methods=["GET", "POST"])
def senior_info_4():
    
    if not is_valid():
        return redirect("/")
    
    #현 클라이언트의 정보 습득
    user = what_user()
    
    if request.method == "POST":
        # POST 요청 처리
        print("POST 요청 수신됨")
        # JSON 형식으로 데이터를 받음
        data = request.get_json()  # 요청 데이터를 JSON 형식으로 받음
        start_time = data.get("start_time")
        end_time = data.get("end_time")

        print("수신한 데이터:", start_time, end_time)

        # 기존 데이터베이스 항목 가져오기
        existing_entry = db.page4.find_one({"nick":user["nick"]})

        if existing_entry:
            # 기존 데이터 업데이트
            db.page4.update_one(
                {"_id": existing_entry["_id"]},
                {"$set": {"start_time": start_time, "end_time": end_time}},
                
            )
        else:
            # 새로운 데이터 삽입
            db.page4.insert_one({"start_time": start_time, "end_time": end_time, "nick":user["nick"]})

        # POST 요청 후 페이지 리다이렉트
        return redirect("/senior_info_5")

    else:
        # GET 요청 처리
        # 기존 데이터 불러오기
        senior_info = db.page4.find_one({"nick":user["nick"]})
        start_time = senior_info["start_time"] if senior_info else ""
        end_time = senior_info["end_time"] if senior_info else ""

        # HTML 템플릿 렌더링
        return render_template(
            HTML_SENIOR_INFO4, start_time=start_time, end_time=end_time
        )

# 5페이지 라우트
@app.route("/senior_info_5", methods=["GET", "POST"])
def senior_info_5():
    
    if not is_valid():
        return redirect("/")
    
    #현 클라이언트의 정보 습득
    user = what_user()

    if request.method == "POST":
        print("POST 요청 수신됨")
        print("요청 데이터:", request.form)
        # 사용자가 선택한 데이터 수집
        data = request.get_json()  # JSON 데이터 받기
        services = data.get("services")
        gender = data.get("gender")

        print("POST 요청 수신")
        print("수신한 데이터:", services, gender)

        # 기존 데이터베이스 항목 가져오기
        existing_entry = db.page5.find_one({"nick":user["nick"]})

        if existing_entry:
            # 기존 데이터 업데이트
            db.page5.update_one(
                {"_id": existing_entry["_id"]},
                {"$set": {"selected_gender": gender, "selected_service": services}},
            )
        else:
            # 새로운 데이터 삽입
            db.page5.insert_one(
                {"selected_gender": gender, "selected_service": services, "nick":user["nick"]}
            )

        # POST 요청 후 페이지 리다이렉트
        return redirect("/senior_info_5")

    # GET 요청 시 기존 데이터 불러오기
    senior_info = db.page5.find_one({"nick":user["nick"]})
    gender = senior_info["selected_gender"] if senior_info else ""
    services = senior_info["selected_service"] if senior_info else []

    # HTML 템플릿 렌더링
    return render_template(
        HTML_SENIOR_INFO5, selected_gender=gender, selected_service=services
    )

#### mate 관련 함수 ####

# mate 요청 보내기
@app.route("/api/send_match", methods=["POST"])
def api_send_match():
    # id가 ~~인 빈 칸에서 입력값을 받아온다.
    nickname_receive = request.form["nick_give"]

    # 빈칸 입력시 경고
    if nickname_receive == "":
        return jsonify({"result": "fail", "msg": "공란이 존재합니다!"})

    token_receive = request.cookies.get(USERTOKEN)
    try:
        # token을 시크릿키로 디코딩합니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=[ALGORITHMS_JWT])

        # 요청자와 수신자의 정보 확인
        userinfo_sender = db.user.find_one({"id": payload["id"]})
        userinfo_receiver = db.user.find_one({"nick": nickname_receive})

        # 존재하는 아이디일 경우, 해당 요청을 보낼 수 있는지 확인 -> 요청자와 role이 동일한가?, mate된 상대가 존재하는가?
        if userinfo_receiver is None:
            return jsonify({"result": "fail", "msg": "해당 사용자를 찾을 수 없습니다"})
        #역할이 달라야 서로에게 요청을 보낼 수 있음
        if userinfo_receiver["role"] == userinfo_sender["role"]:
            return jsonify(
                {"result": "fail", "msg": "동일 역할끼리는 매칭을 맺을 수 없습니다."}
            )
        #요청 송신자가 이미 매칭이 되있는 경우
        if userinfo_sender["mate"] != "":
            return jsonify(
                {"result": "fail","msg": "매칭자가 있는 상태에서는 매칭 요청을 할 수 없습니다."}
            )
        #요청 수신자가 이미 매칭이 되있는 경우
        if userinfo_receiver["mate"] != "":
            return jsonify({"result": "fail", "msg": "이미 다른 매칭이 된 상대입니다."})
        #동일 요청 중복 방지
        if(db.mate_request.find_one({"sender": userinfo_sender["nick"], "receiver": userinfo_receiver["nick"]})):
            return jsonify({"result": "fail", "msg": "이미 해당 요청을 보냈습니다"})
            


        result = db.mate_request.find(
            {"sender":  ["nick"], "receiver": userinfo_receiver["nick"]}
        )
        if result is None:
            return jsonify(
                {"result": "fail", "msg": "이미 해당 하는 매칭을 요청하셨습니다"}
            )

        # 해당 요청을 DB에 업로드
        print(userinfo_sender["nick"])
        print("asdfasdfasdfasdfasdfasdfasdf")
        print(userinfo_receiver["nick"])
        
       
        
        result = db.mate_request.insert_one(
            {"sender": userinfo_sender["nick"], "receiver": userinfo_receiver["nick"]}
        )
        if result is None:
            return jsonify({"fail": "DB업로드 오류"})
        return jsonify({"result": "success"})

    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({"result": "fail", "msg": "로그인 시간이 만료되었습니다."})
    except jwt.exceptions.DecodeError:
        # 로그인 정보가 없으면 에러가 납니다!
        return jsonify({"result": "fail", "msg": "로그인 정보가 존재하지 않습니다."})

    # mate 요청 보내기

# mate관계를 끊는다.
@app.route("/api/dis_match", methods=["POST"])
def api_dis_match():
    # 우선 사용자가 매칭된 상대가 있는지 확인한다. - 사용자가 누군지는 토큰 활용
    token_receive = request.cookies.get(USERTOKEN)
    try:
        # token을 시크릿키로 디코딩합니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=[ALGORITHMS_JWT])

        # 요청자와 수신자의 정보 확인
        user = db.user.find_one({"id": payload["id"]})
        if "mate" in user:
            user_mate = db.user.find_one({"id": user["mate"]})
        else:
            return jsonify(
                {
                    "result": "fail",
                    "msg": '비정상적인 계정입니다. - "mate"데이터 미존재',
                }
            )

        # 자신의 mate상대가 있다면 실패
        if user["mate"] == "":
            return jsonify({"result": "fail", "msg": "mate된 상대가 없습니다.."})

        if user_mate is None:
            return jsonify(
                {
                    "result": "fail",
                    "msg": "mate가 존재하지않습니다. 운영팀에 연락바랍니다.",
                }
            )

        # 유저 정보 또한 업데이트
        result_user = db.user.update_one({"nick": user["nick"]}, {"$set": {"mate": ""}})
        result_mate = db.user.update_one(
            {"nick": user_mate["nick"]}, {"$set": {"mate": ""}}
        )

        # 두 문서가 모두 수정되었는지 확인
        if result_user.modified_count > 0 and result_mate.modified_count > 0:
            return jsonify({"result": "success"})
        else:
            return jsonify({"result": "failure"})

    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({"result": "fail", "msg": "로그인 시간이 만료되었습니다."})
    except jwt.exceptions.DecodeError:
        # 로그인 정보가 없으면 에러가 납니다!
        return jsonify({"result": "fail", "msg": "로그인 정보가 존재하지 않습니다."})

# DB에서 자신에게 요청된 match를 list화 시켜서 보관한다. - 사용하지 않음
@app.route("/api/hear_match", methods=["POST"])
def api_hear_match():
    token_receive = request.cookies.get(USERTOKEN)
    try:
        # token에서 정보를 뽑아 냅니다.
        # 입력받은 id의 유저를 찾습니다.
        payload_user = jwt.decode(
            token_receive, SECRET_KEY, algorithms=[ALGORITHMS_JWT]
        )
        # 유저에게 온 요청들을 처리한다. - 과거에 온 요청을 우선적으로 띄운다.
        request_list = db.mate_request.find({"receiver": payload_user["id"]}).sort(
            "_id", 1
        )

        for request_part in request_list:
            payload_chat = {
                "id": str(request_part.get("id")),  # 'id' 필드
                "exp": datetime.utcnow() + timedelta(seconds=TOKENTIME),
            }

        # 토큰의 암호화! -> 해당 리스트는 클라이언트에 저장된다. -> 항후 페이지 넘김에 적용
        token = jwt.encode(payload_chat, SECRET_KEY, algorithm=ALGORITHMS_JWT)

        # token을 줍니다. - 채팅방 입장
        return jsonify(
            {"result": "success", "token": token, "msg": "매칭 요청 조회 성공"}
        )

    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({"result": "fail", "msg": "로그인 시간이 만료되었습니다."})
    except jwt.exceptions.DecodeError:
        # 로그인 정보가 없으면 에러가 납니다!
        return jsonify({"result": "fail", "msg": "로그인 정보가 존재하지 않습니다."})
    #

# 자신에게 요청된 요청을 리스트에서 찾아서 허가한다.
@app.route("/api/allow_match", methods=["POST"])
def api_allow_match():
    nickname_receive = request.form["nick_give"]
    token_receive = request.cookies.get(USERTOKEN)

    if nickname_receive == "":
        return jsonify({"result": "fail", "msg": "대상이 공란입니다. 입력해주세요"})

    try:
        # token을 시크릿키로 디코딩합니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=[ALGORITHMS_JWT])

        # 수신자 정보 확인
        user = db.user.find_one({"id": payload["id"]})
        if user["mate"] != "":
            return jsonify(
                {
                    "result": "fail",
                    "msg": "매칭이 된 상태입니다. 추가로 매칭할 수 없습니다.",
                }
            )

        # 요청자 정보확인
        user_mate = db.user.find_one({"nick": nickname_receive})
        if user_mate["mate"] != "":
            return jsonify(
                {
                    "result": "fail",
                    "msg": "상대가 매칭이 된 상태입니다. 매칭되지 않습니다.",
                }
            )

        # 해당 요청이 현재 존재하는 지 확인
        request_inform = db.mate_request.find_one(
            {"receiver": user["nick"], "sender": user_mate["nick"]}
        )
        if request_inform == None:
            return jsonify(
                {"result": "fail", "msg": "해당 요청은 존재하지 않는 요청입니다."}
            )

        # 자신이 받은 요청을 삭제한다.
        result = db.mate_request.delete_one(
            {"receiver": user["nick"], "sender": user_mate["nick"]}
        )
        # mate를 바꾼다.

        db.user.update_one(
            {"nick": user["nick"]},  # user의 mate를 요청자의 닉네임으로 설정
            {"$set": {"mate": user_mate["nick"]}},
        )

        db.user.update_one(
            {"nick": user_mate["nick"]},  # user_mate의 mate를 수신자의 닉네임으로 설정
            {"$set": {"mate": user["nick"]}},
        )
        return jsonify({"result": "success", "msg": "매칭 요청 허가 성공"})

    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({"result": "fail", "msg": "로그인 시간이 만료되었습니다."})
    except jwt.exceptions.DecodeError:
        # 로그인 정보가 없으면 에러가 납니다!
        return jsonify({"result": "fail", "msg": "로그인 정보가 존재하지 않습니다."})

# 자신에게 요청된 요청을 거절한다. - 사용자가 누군지는 토큰 활용
@app.route("/api/disallow_match", methods=["POST"])
def disallow_match():
    nickname_receive = request.form["nick_give"]
    token_receive = request.cookies.get(USERTOKEN)

    if nickname_receive == "":
        return jsonify({"result": "fail", "msg": "대상이 공란입니다. 입력해주세요"})

    try:
        # token을 시크릿키로 디코딩합니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=[ALGORITHMS_JWT])

        # 요청자와 수신자의 정보 확인
        user = db.user.find_one({"id": payload["id"]})

        # 해당 로직은 메이트를 바깥에서 받아야한다.
        user_mate = db.user.find_one({"nick": nickname_receive})


        # 해당 요청이 현재 존재하는 지 확인
        request_inform = db.mate_request.find_one(
            {"receiver": user["nick"], "sender": user_mate["nick"]}
        )
        if request_inform == None:
            return jsonify(
                {"result": "fail", "msg": "해당 요청은 존재하지 않는 요청입니다."}
            )

        # 자신이 받은 요청을 삭제한다.
        result = db.mate_request.delete_one(
            {"receiver": user["nick"], "sender": user_mate["nick"]}
        )

        return jsonify({"result": "success", "msg": "매칭 요청 거절 성공"})

    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({"result": "fail", "msg": "로그인 시간이 만료되었습니다."})
    except jwt.exceptions.DecodeError:
        # 로그인 정보가 없으면 에러가 납니다!
        return jsonify({"result": "fail", "msg": "로그인 정보가 존재하지 않습니다."})

# 자신에게 온 요청들을 확인한다.
# 메인 페이지에서 요청 확인 페이지로 가는 버튼을 누른 후에 작동한다.
@app.route("/api/first_match", methods=["POST"])
def first_match():
    nickname_receive = request.form["nick_give"]
    token_receive = request.cookies.get(USERTOKEN)
    
    if(nickname_receive != ""):
        return (
                jsonify(
                    {"result": "fail", "msg": "첫 요청이 아님.", "data": "요청없음"}
                )
            )
        

    try:
        # token을 시크릿키로 디코딩합니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=[ALGORITHMS_JWT])
        # 수신자 정보 확인
        user = db.user.find_one({"id": payload["id"]})
        # 첫 페이지 입장 시, 사용자에게 온 요청이 있는지 확인
        request_inform = (
            db.mate_request.find({"receiver": user["nick"]})
            .sort("createdAt", 1)
            .limit(1)
        )

        # 커서를 리스트로 변환하여 요청이 없을 경우 처리
        request_inform_list = list(request_inform)

        if request_inform_list:
            print("데이터를 찾았습니다:", request_inform_list)
        else:
            print("데이터를 찾지 못했습니다.")
            return (
                jsonify(
                    {"result": "fail", "msg": "온 요청이 없습니다.", "data": "요청없음"}
                )
            )
        if len(request_inform_list) == 0:
            return (
                jsonify(
                    {"result": "fail", "msg": "온 요청이 없습니다.", "data": "요청없음"}
                )
            )
            

        # 요청이 있을 경우 첫 번째 항목 가져오기
        request_data = request_inform_list[0]  # 첫 번째 요청

        # 관련 정보를 프론트로 다시 넘겨준다
        return jsonify(
            {
                "result": "success",
                "msg": "매칭 요청 확인 성공",
                "data": request_data["sender"],
            }
        )

    except jwt.ExpiredSignatureError:
        return jsonify({"result": "fail", "msg": "로그인 시간이 만료되었습니다."})
    except jwt.exceptions.DecodeError:
        return jsonify({"result": "fail", "msg": "로그인 정보가 존재하지 않습니다."})

# 지금 보고 있는 페이지의 이전 요청을 확인한다.
@app.route("/api/pred_match", methods=["POST"])
def pred_match():
    nickname_receive = request.form["nick_give"]
    token_receive = request.cookies.get(USERTOKEN)

    try:
        # 첫 페이지 입장시
        # 우선 현재 페이지에 nick이 공란인지 확인한다.
        if nickname_receive == "":
            return jsonify({"result": "fail", "msg": "오류입니다."})
        # 공란이라면 오류 메시지를 출력후 메인페이지로 이동한다.

        # 수신자 정보 확인
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=[ALGORITHMS_JWT])
        user = db.user.find_one({"id": payload["id"]})

        # 공란이 아니라면 해당 nick을 db에서 사용자에게 온 요청중 찾아본다
        # request_inform을 커서로 가져온 후, 리스트로 변환
        request_inform_list = list(
            db.mate_request.find({"receiver": user["nick"]}).sort("createdAt", 1)
        )

        # 찾고자 하는 특정 요소 (예: sender가 "example_sender"인 요소)의 인덱스를 찾기
        target_sender = nickname_receive
        index_of_element = next(
            (
                index
                for index, item in enumerate(request_inform_list)
                if item["sender"] == target_sender
            ),
            -1,
        )

        print(
            nickname_receive
            + "는 "
            + str(index_of_element)
            + " 번째 인덱스에 있습니다."
        )
        if index_of_element != -1:
            print(
                nickname_receive
                + "는 "
                + str(index_of_element)
                + " 번째 인덱스에 있습니다."
            )
        else:
            print(nickname_receive + "를 찾을 수 없습니다.")
            return jsonify({"result": "fail", "msg": "찾을 수 없습니다."})

        if index_of_element == 0:
            return jsonify(
                {"result": "fail", "msg": "이전 페이지가 존재하지 않습니다."}
            )

        # 주어진 인덱스 (예: 2번째 인덱스)로 문서 찾기
        index_to_find = index_of_element - 1  # 예시로 2번째 인덱스를 찾고자 할 때

        if index_to_find < len(request_inform_list):
            document = request_inform_list[index_to_find]
            print(f"인덱스 {index_to_find}에 해당하는 문서: {document}")
        else:
            print(f"인덱스 {index_to_find}가 범위를 벗어났습니다.")

        request_data = request_inform_list[index_to_find]

        return jsonify(
            {
                "result": "success",
                "msg": "이전 매칭 요청 확인 성공",
                "data": request_data["sender"],
            }
        )

    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({"result": "fail", "msg": "로그인 시간이 만료되었습니다."})
    except jwt.exceptions.DecodeError:
        # 로그인 정보가 없으면 에러가 납니다!
        return jsonify({"result": "fail", "msg": "로그인 정보가 존재하지 않습니다."})

# 지금 보고 있는 페이지의 다음 요청을 확인한다.
@app.route("/api/next_match", methods=["POST"])
def next_match():
    nickname_receive = request.form["nick_give"]
    token_receive = request.cookies.get(USERTOKEN)

    try:
        # 첫 페이지 입장시
        # 우선 현재 페이지에 nick이 공란인지 확인한다.
        if nickname_receive == "":
            return jsonify({"result": "fail", "msg": "오류입니다."})
        # 공란이라면 오류 메시지를 출력후 메인페이지로 이동한다.

        # 수신자 정보 확인
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=[ALGORITHMS_JWT])
        user = db.user.find_one({"id": payload["id"]})

        # 공란이 아니라면 해당 nick을 db에서 사용자에게 온 요청중 찾아본다
        # request_inform을 커서로 가져온 후, 리스트로 변환
        request_inform_list = list(
            db.mate_request.find({"receiver": user["nick"]}).sort("createdAt", 1)
        )

        # 찾고자 하는 특정 요소 (예: sender가 "example_sender"인 요소)의 인덱스를 찾기
        target_sender = nickname_receive
        index_of_element = next(
            (
                index
                for index, item in enumerate(request_inform_list)
                if item["sender"] == target_sender
            ),
            -1,
        )

        print(
            nickname_receive
            + "는 "
            + str(index_of_element)
            + " 번째 인덱스에 있습니다."
        )
        if index_of_element != -1:
            print(
                nickname_receive
                + "는 "
                + str(index_of_element)
                + " 번째 인덱스에 있습니다."
            )
        else:
            print(nickname_receive + "를 찾을 수 없습니다.")
            return jsonify({"result": "fail", "msg": "찾을 수 없습니다."})

        if index_of_element == len(request_inform_list) - 1:
            return jsonify(
                {"result": "warn", "msg": "다음 페이지가 존재하지 않습니다."}
            )

        # 주어진 인덱스 (예: 2번째 인덱스)로 문서 찾기
        index_to_find = index_of_element + 1  # 예시로 2번째 인덱스를 찾고자 할 때

        if index_to_find < len(request_inform_list):
            document = request_inform_list[index_to_find]
            print(f"인덱스 {index_to_find}에 해당하는 문서: {document}")
        else:
            print(f"인덱스 {index_to_find}가 범위를 벗어났습니다.")

        request_data = request_inform_list[index_to_find]

        return jsonify(
            {
                "result": "success",
                "msg": "다음 매칭 요청 확인 성공",
                "data": request_data["sender"],
            }
        )

    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({"result": "fail", "msg": "로그인 시간이 만료되었습니다."})
    except jwt.exceptions.DecodeError:
        # 로그인 정보가 없으면 에러가 납니다!
        return jsonify({"result": "fail", "msg": "로그인 정보가 존재하지 않습니다."})

# 현재 html의 데이터를 고친다.
@app.route("/api/match_check_info_update", methods=["POST"])
def match_check_info_update():
    nickname_receive = request.form["nick_give"]
    token_receive = request.cookies.get(USERTOKEN)

    try:
        # token을 시크릿키로 디코딩합니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=[ALGORITHMS_JWT])

        # 수신자 정보 확인
        user = db.user.find_one({"id": payload["id"]})

        # 요청자 정보확인
        senior_info_1 = db.page1.find_one({"nick": nickname_receive})
        senior_info_2 = db.page2.find_one({"nick": nickname_receive})
        senior_info_3 = db.page3.find_one({"nick": nickname_receive})
        senior_info_4 = db.page4.find_one({"nick": nickname_receive})
        senior_info_5 = db.page5.find_one({"nick": nickname_receive})

        #요청자의 정보를 담는다.
        detail_address = senior_info_1["detail_address"]
        basic_address = senior_info_1["basic_address"]
        name = senior_info_2["name"]
        gender = senior_info_2["gender"]
        weight = senior_info_2["weight"]
        birth = senior_info_2["birth"]
        selected_diseases = senior_info_3["selected_diseases"]
        selected_mobility = senior_info_3["selected_mobility"]
        selected_meal = senior_info_3["selected_meal"]
        selected_relation = senior_info_3["selected_relation"]
        start_time = senior_info_4["start_time"]
        end_time = senior_info_4["end_time"]    
        selected_gender = senior_info_5["selected_gender"]
        selected_service = senior_info_5["selected_service"] 
        
        #데이터를 넘긴다
        return jsonify({
            "result": "success",
            "msg": "매칭 요청 허가 성공",
            "data": {
                "detail_address": detail_address,
                "basic_address": basic_address,
                "name": name,
                "gender": gender,
                "weight": weight,
                "birth": birth,
                "selected_diseases": selected_diseases,
                "selected_mobility": selected_mobility,
                "selected_meal": selected_meal,
                "selected_relation": selected_relation,
                "start_time": start_time,
                "end_time": end_time,
                "selected_gender": selected_gender,
                "selected_service": selected_service
            }   
        })

    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({"result": "fail", "msg": "로그인 시간이 만료되었습니다."})
    except jwt.exceptions.DecodeError:
        # 로그인 정보가 없으면 에러가 납니다!
        return jsonify({"result": "fail", "msg": "로그인 정보가 존재하지 않습니다."})

# 현재 html의 데이터를 고친다.
@app.route("/api/main_check_info_update", methods=["POST"])
def main_check_info_update():
    token_receive = request.cookies.get(USERTOKEN)

    try:
        # token을 시크릿키로 디코딩합니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=[ALGORITHMS_JWT])

        # 수신자 정보 확인
        user = db.user.find_one({"id": payload["id"]})
        
        if(user["mate"] == "") :
            jsonify({
            "result": "fail",
            "msg": "mate가 없어 데이터를 불러오기 어려움",
            "data": {
                "todo_list_content": todo_list_content,
                "todo_list_comment": todo_list_comment
            }   
        })
        
        #오늘 날짜 가져오기 (형식: "YYYY-MM-DD")
        today_date = datetime.now().strftime("%Y-%m-%d")


        # 'mate'와 일치하는 todo 항목들을 찾기
        if (user["role"] == "keeper"):
            todo_list_cursor = db.todo.find({"cody": user["mate"], "date" : today_date})
        else : 
            todo_list_cursor = db.todo.find({"cody": user["nick"], "date" : today_date})
        todo_list_cursor = list(todo_list_cursor)

# 'content' 값만 추출하여 리스트로 변환
        todo_list_content = [todo["content"] for todo in todo_list_cursor]
        todo_list_comment = [tod["comment"] for tod in todo_list_cursor]

        
        #데이터를 넘긴다
        return jsonify({
            "result": "success",
            "msg": "todo 기록 불러오기 성공",
            "data": {
                "todo_list_content": todo_list_content,
                "todo_list_comment": todo_list_comment
            }   
        })

    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({"result": "fail", "msg": "로그인 시간이 만료되었습니다."})
    except jwt.exceptions.DecodeError:
        # 로그인 정보가 없으면 에러가 납니다!
        return jsonify({"result": "fail", "msg": "로그인 정보가 존재하지 않습니다."})


####################
#   socket.io 함수  # - @socketio을 사용하는 함수
####################

# 클라이언트가 특정 채팅방에 참여하는 이벤트 핸들러 -> 항후 오류 및 예외 처리 필요!
# 해당 함수에는 그 그거 함수랑 딸려오는 그거 그 변수 그거 필요없음! 그 캐시로 데이터를 받아오기 때문!
@socketio.on("join_chat")
def join_chat():
    print("hello,")
    try:
        # 쿠키에서 토큰 가져오기
        token_receive_user = request.cookies.get(USERTOKEN)
        token_receive_chat = request.cookies.get("chattoken")
        if not token_receive_user or not token_receive_chat:
            print("Error: Missing tokens in cookies.")
            return

        print("hello,")
        # 토큰 디코딩
        payload_user = jwt.decode(
            token_receive_user, SECRET_KEY, algorithms=[ALGORITHMS_JWT]
        )
        payload_chat = jwt.decode(
            token_receive_chat, SECRET_KEY, algorithms=[ALGORITHMS_JWT]
        )

        room_id = payload_chat["_id"]  # 대화방 ID
        customer_id = payload_user["id"]  # 고객 ID

        # 방 참여
        join_room(room_id)
        print(f"Customer {customer_id} has successfully joined room {room_id}")

        # DB에 있던 대화기록 출력 ->
        # DB의 object를 담는 array를 하나 만든다.
        # array에 따른 반복문 하나
        # 반복문은 emit을 통해서 서서히 출력한다.
        #socketio.emit("clean_message")
        # DB에 저장된 대화 기록 가져오기
        document = db.chat_room.find_one({"_id": ObjectId(room_id)})
        talk_box = document.get("talk_box", [])

        # 새로 접속한 사용자에게만 초기화 명령 전송
        socketio.emit("clean_message", room=request.sid)

        # 대화 기록을 새로 접속한 사용자에게만 전송
        for item in talk_box:
            sender = item.get("talker", "Unknown")
            message = item.get("talk", "")
            timestamp = item.get("date", "")

            # 메시지를 새로 접속한 사용자에게만 보냄
            if customer_id == sender:
                socketio.emit(
                    "receive_message_me",
                    {"talker": sender, "talk": message, "date": timestamp},
                    room=request.sid,
                )
            else:
                socketio.emit(
                    "receive_message_you",
                    {"talker": sender, "talk": message, "date": timestamp},
                    room=request.sid,
                )

    except jwt.ExpiredSignatureError:
        print("Error: Token has expired.")
    except jwt.DecodeError:
        print("Error: Invalid token.")
    except Exception as e:
        print(f"Unexpected error: {e}")

# 채팅방에 메시지 보내기
@socketio.on("send_message")
def send_message(data):
    try:
        # 쿠키에서 토큰 가져오기
        token_receive_user = request.cookies.get(USERTOKEN)
        token_receive_chat = request.cookies.get("chattoken")
        if not token_receive_user or not token_receive_chat:
            print("Error: Missing tokens in cookies.")
            return

        # 토큰 디코딩
        payload_user = jwt.decode(
            token_receive_user, SECRET_KEY, algorithms=[ALGORITHMS_JWT]
        )
        payload_chat = jwt.decode(
            token_receive_chat, SECRET_KEY, algorithms=[ALGORITHMS_JWT]
        )

        room_id = payload_chat["_id"]  # 대화방 ID
        user_id = payload_user["id"]  # 고객 ID
        
        user_nick = db.user.find_one( {"id" : user_id})

        message = data["message"]  # 메시지 - 프론트에서 받은 정보
        time = data["time"]  # 메시지 시간
        
        message = data["message"].strip()  # 공백 제거
        if not message:  # 공백 메시지 필터링
            print("Error: Empty message cannot be sent.")
            socketio.emit("error", {"message": "Message cannot be empty."}, room=request.sid)
            return

        filter_query = {"_id": ObjectId(room_id)}  # 대상 문서 조건

        # DB와 클라이언트에 전송할 대화 내용
        talk_box = {"talker": user_nick["nick"], "talk": message, "date": time}

        
        # 배열에 객체 삽입
        result = db.chat_room.update_one(
            filter_query, {"$push": {"talk_box": talk_box}}
        )
        if result.matched_count == 0:
            print("No document matched the filter query.")
            socketio.emit(
                "error",
                {"message": "Failed to find the chat room in the database."},
                room=request.sid,
            )
            return
        elif result.modified_count == 0:
            print("Document matched but was not modified.")
        else:
            print("Document updated successfully.")
            
            
        
        if user_nick["role"] == "keeper":
            codi_info = db.information.find_one({"nick":user_nick["mate"]})
        else:
            codi_info = db.information.find_one({"nick":user_nick["nick"]})
        

        codi_photo = url_for('static', filename=codi_info["photo"], _external=True)
        
        # 자신에게 메시지를 전송
        socketio.emit(
            "receive_message_me",
            {"talker": user_id, "talk": message, "date": time, "codi_photo_url" : codi_photo},
            room=request.sid,  # 현재 사용자에게만 보냄
        )

        # 다른 사용자들에게 메시지를 전송
        socketio.emit(
            "receive_message_you",
            {"talker": user_id, "talk": message, "date": time},
            room=room_id,  # 같은 방에 있는 사용자들에게 전송
            skip_sid=request.sid,  # 현재 사용자 제외
        )

    # jwt 관련 예외 처리
    except jwt.ExpiredSignatureError:
        print("Error: Token has expired.")
        socketio.emit("error", {"message": "Authentication token expired."}, room=request.sid)
    except jwt.DecodeError:
        print("Error: Invalid token.")
        socketio.emit("error", {"message": "Invalid authentication token."}, room=request.sid)
    except Exception as e:
        print(f"Unexpected error: {e}")
        socketio.emit(
            "error", {"message": "An error occurred while sending the message."}, room=request.sid
        )
        
if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run("0.0.0.0", port=8080, debug=True)
