import requests

# 회원가입 엔드포인트
REGISTER_URL = "http://127.0.0.1:8000/api/auth/user/register/"

# 회원가입 요청 데이터
user_data = {
    "username": "leeeee",
    "email": "john@example.com",
    "first_name": "lee",
    "last_name": "yyyy",
    "password": "aa"
}

# 회원가입 요청
response = requests.post(REGISTER_URL, json=user_data)

# 응답 확인
if response.status_code == 201:
    print("회원가입 성공:", response.json())
else:
    print("회원가입 실패:", response.status_code, response.json())
