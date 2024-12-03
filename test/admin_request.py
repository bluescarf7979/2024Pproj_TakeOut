import requests

# 보호된 엔드포인트 URL
USER_LIST_URL = "http://127.0.0.1:8000/api/auth/user/"

access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzMzMDM0NjEzLCJpYXQiOjE3MzMwMzQzMTMsImp0aSI6IjI5MmZkODk4M2RkOTRhYThiMDgxZDI1MTk5ZTI2ZmMzIiwidXNlcl9pZCI6MX0.YsN3TM3wvsoJ9ZJfTK2TeaLufpuyejh-Vddm4nvp98A"

headers = {"Authorization": f"Bearer {access_token}"}

# 사용자 목록 요청
response = requests.get(USER_LIST_URL, headers=headers)

# 응답 확인
if response.status_code == 200:
    print("전체 사용자 목록:")
    for user in response.json():
        print(user)
else:
    print("사용자 목록 조회 실패:", response.status_code, response.json())