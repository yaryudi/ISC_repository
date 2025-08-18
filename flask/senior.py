import os
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
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename

import jwt

app = Flask(__name__)

# MongoDB 설정
app.config["MONGO_URI_SENIOR"] = "mongodb+srv://jw:chk00825@cluster0.6twyc.mongodb.net/senior"

senior_db = PyMongo(app, uri=app.config["MONGO_URI_SENIOR"])

try:
    senior_db.db.information.find_one()
    print("MongoDB 연결 성공")
except Exception as e:
    print(f"MongoDB 연결 실패: {e}")

##### 주소 입력 및 입력값 출력 #####
@app.route('/address', methods=['GET', 'POST'])
def address():
    # 기본 값
    address = ""
    detail_address = ""

    if request.method == 'POST':
        # 입력 데이터 받기
        address = request.form.get('address')
        detail_address = request.form.get('detail_address')

        # 기존 데이터 확인
        existing_address = senior_db.db.page1.find_one()

        if existing_address:
            # 기존 데이터 업데이트
            senior_db.db.page1.update_one(
                {"_id": existing_address["_id"]},  # 기존 데이터 조건 (_id 사용)
                {"$set": {
                    "address": address,
                    "detail_address": detail_address
                }}
            )
        else:
            # 새로운 데이터 삽입
            senior_db.db.page1.insert_one({
                "address": address or "",
                "detail_address": detail_address or "",
            })

        # 입력값 확인 (빈 값 처리)
        if not (address and detail_address):
            # 값이 없을 경우 에러 처리
            error_message = "모든 필드를 입력해 주세요."
            return render_template('senior.html', address=address, detail_address=detail_address, error=error_message)

    # GET 요청 시 데이터 불러오기
    latest_data = senior_db.db.page1.find_one()
    if latest_data:
        address = latest_data.get("address", "")
        detail_address = latest_data.get("detail_address", "")

    return render_template('senior1.html', address=address, detail_address=detail_address)

##### 2 페이지 - 성함, 성별, 출생년도, 체중 #####
@app.route('/senior_info_2', methods=['GET', 'POST'])
def senior_info_2():
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        gender = data.get('gender')
        birth = data.get('birth')
        weight = data.get('weight')

        # 유효성 검사
        
        # if not (name and gender and birth and weight):
            # return jsonify({"message": "모든 필드를 입력해주세요."}), 400

        # 데이터베이스 저장
        existing_entry = senior_db.db.page2.find_one()
        if existing_entry:
            # 기존 데이터 업데이트
            senior_db.db.page2.update_one(
                {"_id": existing_entry["_id"]},
                {"$set": {
                    "name": name,
                    "gender": gender,
                    "birth": birth,
                    "weight": weight,
                }},
            )
        else:
            # 새로운 데이터 삽입
            senior_db.db.page2.insert_one({
                "name": name,
                "gender": gender,
                "birth": birth,
                "weight": weight,
            })

        return jsonify({"message": "데이터가 성공적으로 저장되었습니다."}), 200

    # GET 요청 처리
    senior = senior_db.db.page2.find_one()
    name = senior["name"] if senior else ""
    gender = senior["gender"] if senior else ""
    birth = senior["birth"] if senior else ""
    weight = senior["weight"] if senior else ""

    return render_template(
        'senior-info-(2).html',
        name=name,
        gender=gender,
        birth=birth,
        weight=weight,
    )


##### 3 페이지  - 질환, 일상생활 능력 #####
@app.route('/senior_info_3', methods=['GET', 'POST'])
def senior_info_3():
    if request.method == 'POST':
        print("POST 요청 수신됨")
        print("요청 데이터:", request.form)
        # 사용자가 선택한 데이터 수집
        selected_diseases = request.form.get('selected-diseases', '').split(", ")
        selected_mobility = request.form.get('selected-mobility', '')
        selected_meal = request.form.get('selected-meal', '')
        selected_relation = request.form.get('selected-relation', '')

        print("POST 요청 수신")
        print("수신한 데이터:", selected_diseases, selected_mobility, selected_meal, selected_relation)


        # 기존 데이터베이스 항목 가져오기
        existing_entry = senior_db.db.page3.find_one()

        if existing_entry:
            # 기존 데이터 업데이트
            senior_db.db.page3.update_one(
                {"_id": existing_entry["_id"]},
                {"$set": {
                    "selected_diseases": selected_diseases,
                    "selected_mobility": selected_mobility,
                    "selected_meal": selected_meal,
                    "selected_relation": selected_relation
                }}
            )
        else:
            # 새로운 데이터 삽입
            senior_db.db.page3.insert_one({
                "selected_diseases": selected_diseases,
                "selected_mobility": selected_mobility,
                "selected_meal": selected_meal,
                "selected_relation": selected_relation
            })

        # POST 요청 후 페이지 리다이렉트
        return redirect('/senior_info_3')

    # GET 요청 시 기존 데이터 불러오기
    senior_info = senior_db.db.page3.find_one()
    selected_diseases = senior_info["selected_diseases"] if senior_info else []
    selected_mobility = senior_info["selected_mobility"] if senior_info else ""
    selected_meal = senior_info["selected_meal"] if senior_info else ""
    selected_relation = senior_info["selected_relation"] if senior_info else ""

    # HTML 템플릿 렌더링
    return render_template(
        'senior-info-(3).html',
        selected_diseases=selected_diseases,
        selected_mobility=selected_mobility,
        selected_meal=selected_meal,
        selected_relation=selected_relation
    )

##### 4페이지 라우트 #####
@app.route('/senior_info_4', methods=['GET'])
def senior_info_4():
    return render_template('senior-info-(4).html')

if __name__ == '__main__':
    app.run(debug=True)