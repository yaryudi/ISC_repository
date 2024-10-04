from pymongo import MongoClient

try:
    # 연결 테스트
    client = MongoClient("mongodb+srv://rjh0162_rw:difbel0162@cluster0.6twyc.mongodb.net/")
    db = client.sample_mflix  # 데이터베이스 이름
    print("MongoDB 연결 성공!")
    print(db.list_collection_names())  # 연결 성공 시 컬렉션 목록 출력
except Exception as e:
    print(f"MongoDB 연결 실패: {e}")