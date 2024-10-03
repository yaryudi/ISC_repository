from flask import Flask, jsonify, request
from flask_pymongo import PyMongo

app = Flask(__name__)

# MongoDB URI 설정 (로컬 MongoDB의 경우)
app.config["MONGO_URI"] = "mongodb+srv://rjh0162:difbel0162@cluster0.6twyc.mongodb.net/"  # 로컬 MongoDB 사용
# MongoDB Atlas 사용 시 주석 처리된 부분을 활성화하고 사용하세요
# app.config["MONGO_URI"] = "mongodb+srv://<username>:<password>@cluster.mongodb.net/myDatabase?retryWrites=true&w=majority"

mongo = PyMongo(app)

@app.route('/')
def index():
    return "Hello, Flask with MongoDB!"

# 데이터 추가
@app.route('/add', methods=['POST'])
def add_data():
    name = request.json.get('name')
    age = request.json.get('age')
    mongo.db.myCollection.insert_one({"name": name, "age": age})
    return jsonify({"message": "Data added!"}), 201

# 데이터 조회
@app.route('/data', methods=['GET'])
def get_data():
    data = mongo.db.myCollection.find()
    result = []
    for document in data:
        document['_id'] = str(document['_id'])  # ObjectId를 문자열로 변환
        result.append(document)
    return jsonify(result), 200

# 특정 데이터 조회 (예: 이름으로 조회)
@app.route('/data/<name>', methods=['GET'])
def get_data_by_name(name):
    document = mongo.db.myCollection.find_one({"name": name})
    if document:
        document['_id'] = str(document['_id'])  # ObjectId를 문자열로 변환
        return jsonify(document), 200
    return jsonify({"error": "Data not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)