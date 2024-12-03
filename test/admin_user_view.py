import requests

# 특정 사용자 조회 엔드포인트
USER_DETAIL_URL = "http://127.0.0.1:8000/api/auth/user/"

access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzMzMDM1MzgyLCJpYXQiOjE3MzMwMzUwODIsImp0aSI6ImMyNjU3ODc0ZDFmMDQyZjFhZDQ1MTM3M2M5ZDY3MmI2IiwidXNlcl9pZCI6MX0.GdQ6JmMFa6RQSZdPFg0-u6DgQmJL1LGCzRRvD0xXQds"
headers = {"Authorization": f"Bearer {access_token}"}

# 요청 데이터 (user_id)
user_id = 2
data = {"user_id": user_id}

# 사용자 조회 요청
response = requests.get(USER_DETAIL_URL, json=data, headers=headers)

# 응답 확인
if response.status_code == 200:
    print("사용자 정보:", response.json())
else:
    print("사용자 조회 실패:", response.status_code, response.json())
