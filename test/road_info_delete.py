import requests

# API URL
POST_URL = "http://127.0.0.1:8000/api/road_info/"

# 요청 데이터
data = {
    "info_id":6
}
# POST 요청
response = requests.delete(POST_URL, data=data)

# 응답 확인
print(response.json())