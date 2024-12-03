import requests

# API URL
POST_URL = "http://127.0.0.1:8000/api/road_info/"

# 요청 데이터
data = {
    "user": 1,
    "surface_type": 2,
    "road_traffic": 3,
    "road_name": "Main Street",
    "condition": 1,
    "latitude": 37.7749,
    "longitude": -122.4194,
    "risk_level": 0.8,
    "bounding_box": """{"x":10, "y":20, "width":30, "height":40}""",
    "updated_at": "2024-12-01"
}


# 이미지 파일 추가
files = {
    "image": open("/home/a/Pictures/Screenshot from 2024-11-14 10-19-18.png", "rb")
}

# POST 요청
response = requests.post(POST_URL, data=data, files=files)

# 응답 확인
if response.status_code == 201:
    print("요청 성공:", response.json())
else:
    print("요청 실패:", response.status_code, response.json())
