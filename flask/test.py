from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# 사용자 데이터 예시 (간단한 딕셔너리로 가짜 데이터베이스를 대체)
user_data = {
    "username": "john_doe",
    "email": "john.doe@example.com",
    "age": 30
}


# HTML 파일 렌더링
@app.route('/')
def index():
    return render_template('match_senior.html')

# 사용자 데이터를 반환하는 API
@app.route('/get_user_data', methods=['GET'])
def get_user_data():
    return jsonify(user_data)

# 이메일 데이터를 처리하는 API
@app.route('/api/process_email', methods=['POST'])
def process_email():
    data = request.get_json()
    email = data.get('email')
    if email:
        print(f"Received email: {email}")
        return jsonify({"message": f"Email {email} processed successfully"})
    return jsonify({"message": "Email not provided"}), 400

# 이메일 데이터를 처리하는 API
@app.route('/api/next_request', methods=['POST'])
def next_request():
    data = request.get_json()
    email = data.get('email')
    if email:
        print(f"Received email: {email}")
        return jsonify({"message": f"Email {email} processed successfully"})
    return jsonify({"message": "Email not provided"}), 400

# 이메일 데이터를 처리하는 API
@app.route('/api/pred_request', methods=['POST'])
def pred_request():
    data = request.get_json()
    email = data.get('email')
    if email:
        print(f"Received email: {email}")
        return jsonify({"message": f"Email {email} processed successfully"})
    return jsonify({"message": "Email not provided"}), 400

if __name__ == '__main__':
    app.run(debug=True)