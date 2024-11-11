from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from pymongo import MongoClient

app = Flask(__name__)

# MongoDB Atlas URI (올바른 값으로 설정)
app.config["MONGO_URI"] = "mongodb+srv://rjh0162_rw:difbel0162@cluster0.6twyc.mongodb.net/sample_mflix"

# 또는 로컬 MongoDB URI
# app.config["MONGO_URI"] = "mongodb://localhost:27017/myDatabase"

mongo = PyMongo(app)


try:
    # MongoDB 컬렉션에 연결이 성공했는지 테스트 
    mongo.db.sample_mflix.find_one()
    #여기서 sample_mflix는 해당 데이터베이스에의 컬렉션의 이름이다.
    print("MongoDB 연결 성공")
except Exception as e:
    print(f"MongoDB 연결 실패: {e}")
    

@app.route('/')
def index():
    return "Hello, Flask with MongoDB!"

# 데이터 추가
@app.route('/add', methods=['POST'])
def add_data():
    name = request.json.get('name')
    age = request.json.get('age')
    if name and age:
        mongo.db.myCollection.insert_one({"name": name, "age": age})
        return jsonify({"message": "Data added!"}), 201
    return jsonify({"error": "Missing data"}), 400

# 이름으로 데이터 조회
@app.route('/data/<name>', methods=['GET'])
def get_data_by_name(name):
    document = mongo.db.myCollection.find_one({"name": name})
    if document:
        document['_id'] = str(document['_id'])  # ObjectId를 문자열로 변환
        return jsonify(document), 200
    return jsonify({"error": "Data not found"}), 404

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)