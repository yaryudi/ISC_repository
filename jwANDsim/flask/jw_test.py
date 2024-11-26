import os
from flask import Flask, render_template, request, redirect, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename

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

        if time and content:
            todo_db.db.todo.insert_one({"time": time, "content": content})
        return redirect('/todo')

    # 데이터 조회 (출근/퇴근 제외)
    todos = list(todo_db.db.todo.find({"content": {"$nin": ["출근", "퇴근"]}}))
    return render_template('todo2.html', todos=todos)

@app.route('/todo/delete/<todo_id>', methods=['POST'])
def delete_todo(todo_id):
    # 데이터 삭제
    todo_db.db.todo.delete_one({"_id": ObjectId(todo_id)})
    return redirect('/todo')

@app.route('/resume') #이력서 페이지로 이동 버튼
def resume_page():
    # Resume 데이터를 가져오거나 기본 페이지 렌더링
    resume = resume_db.db.information.find_one()  # Resume 데이터베이스에서 정보 가져오기
    return render_template('resumeCSS.html', resume=resume)

@app.route('/care_record', methods=['GET'])
def care_record():
    # GET 요청: 모든 todo 데이터를 조회
    cares = list(todo_db.db.todo.find().sort("time", 1))  # 시간순으로 정렬
    return render_template('care_record.html', cares=cares)

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

    return redirect('/care_record')

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

    return redirect('/care_record')  # 케어 기록 페이지로 리다이렉트

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)