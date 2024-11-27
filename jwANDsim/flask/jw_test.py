import os
from flask import Flask, render_template, request, redirect, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import math

app = Flask(__name__)

# MongoDB 설정
app.config["MONGO_URI_RESUME"] = "mongodb+srv://jw:chk00825@cluster0.6twyc.mongodb.net/Resume"
app.config["MONGO_URI_TODO"] = "mongodb+srv://jw:chk00825@cluster0.6twyc.mongodb.net/todo"

resume_db = PyMongo(app, uri=app.config["MONGO_URI_RESUME"])
todo_db = PyMongo(app, uri=app.config["MONGO_URI_TODO"])

# 업로드 설정
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 업로드 가능한 파일 형식 확인
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

try:
    resume_db.db.information.find_one()
    todo_db.db.todo.find_one()
    print("MongoDB 연결 성공")
except Exception as e:
    print(f"MongoDB 연결 실패: {e}")

@app.route('/', methods=['GET', 'POST'])
def manage_resume():
    if request.method == 'POST':
        action = request.form.get('action')  # 버튼의 value 값 가져오기
        name = request.form.get('name')
        age = request.form.get('age')
        gender = request.form.get('gender')
        experience = request.form.get('experience')
        introduction = request.form.get('introduction')

        file = request.files.get('photo')  # 업로드된 파일 가져오기
        photo_filename = None

        if action == 'upload_photo' and file and allowed_file(file.filename):
            # 사진 업로드 처리
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            photo_filename = f"uploads/{filename}"

            # 기존 데이터에 사진 경로 추가/수정
            resume_id = request.form.get('resume_id')
            if resume_id:
                resume_db.db.information.update_one(
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
                }
                resume_db.db.information.insert_one(resume_data)

            return redirect('/')

        elif action == 'update':  # 수정 요청
            resume_id = request.form.get('resume_id')
            update_data = {
                "name": name,
                "age": age,
                "gender": gender,
                "experience": experience,
                "introduction": introduction,
            }
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                update_data["photo"] = f"uploads/{filename}"
            resume_db.db.information.update_one(
                {"_id": ObjectId(resume_id)},
                {"$set": update_data}
            )

        return redirect('/')

    # GET 요청: 기존 데이터 가져오기
    resume = resume_db.db.information.find_one()
    return render_template('resume.html', resume=resume)

@app.route('/todo', methods=['GET', 'POST'])
def manage_todo():
    if request.method == 'POST':
        # 데이터 추가
        time = request.form.get('time')
        content = request.form.get('content')

        # 현재 날짜 가져오기
        current_date = datetime.now().strftime('%Y-%m-%d')

        if time and content:
            todo_db.db.todo.insert_one({
                "time": time,
                "content": content,
                "date": current_date  # 현재 날짜 추가
            })
        return redirect('/todo')

    # 데이터 조회 (출근/퇴근 제외)
    todos = list(todo_db.db.todo.find({"content": {"$nin": ["출근", "퇴근"]}}))
    return render_template('todo_maker.html', todos=todos)

@app.route('/todo/delete/<todo_id>', methods=['POST'])
def delete_todo(todo_id):
    # 데이터 삭제
    todo_db.db.todo.delete_one({"_id": ObjectId(todo_id)})
    return redirect('/todo')

@app.route('/resume') #이력서 페이지로 이동 버튼
def resume_page():
    # Resume 데이터를 가져오거나 기본 페이지 렌더링
    resume = resume_db.db.information.find_one()  # Resume 데이터베이스에서 정보 가져오기
    return render_template('resume.html', resume=resume)

###내 ToDo (케어코디가 입력하는 페이지)###
@app.route('/todo_carecody', methods=['GET'])
def care_record():
    # GET 요청: 모든 todo 데이터를 조회
    cares = list(todo_db.db.todo.find().sort("time", 1))  # 시간순으로 정렬
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
        todo_db.db.todo.update_one({"_id": ObjectId(care_id)}, {"$set": update_data})

    return redirect('/todo_carecody')

from datetime import datetime

@app.route('/care/attendance', methods=['POST'])
def record_attendance():
    current_time = datetime.now().strftime('%H:%M')  # 현재 시간 HH:MM 형식으로 저장
    last_entry = todo_db.db.todo.find_one(sort=[('_id', -1)])  # 가장 최근의 데이터 가져오기

    if last_entry and last_entry.get('content') == '출근':
        # 최근 데이터가 '출근'이라면 '퇴근' 데이터 저장
        todo_db.db.todo.insert_one({'time': current_time, 'content': '퇴근'})
    else:
        # 최근 데이터가 '출근'이 아니면 '출근' 데이터 저장
        todo_db.db.todo.insert_one({'time': current_time, 'content': '출근'})

    return redirect('/todo_carecody')  # 내 ToDo 페이지로 리다이렉트

##############################################################################

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

### 돌봄 다이어리(날짜별 모음) ###
@app.route('/diary', methods=['GET'])
def care_record_page():
    # URL 파라미터 처리
    week_offset = int(request.args.get('week', 0))  # 주 이동 (기본값 0)
    base_date = datetime.now() + timedelta(weeks=week_offset)

    # 주차 계산 (월 기준)
    current_month = base_date.month
    current_year = base_date.year
    current_week_number = week_number_in_month(base_date)
    total_weeks = total_weeks_in_month(base_date)

    # 주차 이동이 월 범위를 넘어가지 않도록 제한
    if current_week_number + week_offset > total_weeks:
        base_date = base_date.replace(day=1) + timedelta(days=32)  # 다음 달로 이동
        base_date = base_date.replace(day=1)  # 다음 달 1일로 설정
    elif current_week_number + week_offset < 1:
        base_date = base_date.replace(day=1) - timedelta(days=1)  # 이전 달로 이동
        base_date = base_date.replace(day=1)  # 이전 달 1일로 설정

    # 주별 날짜 계산 (일요일 시작)
    week_dates = get_week_dates(base_date)
    formatted_week = [date.strftime('%Y-%m-%d') for date in week_dates]
    days = ['일', '월', '화', '수', '목', '금', '토']

    # MongoDB 쿼리 조건
    selected_date = request.args.get('date')  # 특정 날짜 선택
    if selected_date:  # 특정 날짜 선택
        query = {"date": selected_date}
        current_date = selected_date
    else:  # 기본적으로 주 전체 데이터를 로드
        query = {"date": {"$in": formatted_week}}
        current_date = None

    cares = list(todo_db.db.todo.find(query).sort("time", 1))  # 시간순 정렬

    # 데이터를 HTML 템플릿으로 전달
    return render_template(
        'diary_jw.html',
        cares=cares,
        week_dates=zip(days, formatted_week),
        current_week=f"{current_year}년 {current_month}월 {week_number_in_month(base_date)}째주",
        current_date=current_date
    )

@app.route('/test', methods=['GET'])
def test_page():
    # 모든 todo 데이터를 조회
    cares = list(todo_db.db.todo.find().sort("time", 1))  # 시간순으로 정렬
    return render_template('diary.html', cares=cares)

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)