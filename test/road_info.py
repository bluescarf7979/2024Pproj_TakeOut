import requests

# API URL
POST_URL = "http://127.0.0.1:8000/api/road_info/"

# !4d
# 요청 데이터
data = {
    "user": 1,
    "bad_type": 1,
    "road_category": 2,
    "road_name": "송파대로",
    "condition": 1,
    "latitude": 37.478555,
    "longitude": 127.126443,
    "risk_level": 2,
    "address": "서울특별시 송파구 장지동 216-2",
    "speed": 50,
}

# 이미지 파일 추가
files = {
    "image": open("/home/a/workspace/p_proj/Screenshot from 2024-12-02 12-43-24.png", "rb")
}

# POST 요청
response = requests.post(POST_URL, data=data, files=files)

# 응답 확인
if response.status_code == 201:
    print("요청 성공:", response.json())
else:
    print("요청 실패:", response.status_code, response.json())
