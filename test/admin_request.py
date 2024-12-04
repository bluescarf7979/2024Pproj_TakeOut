import requests

# 보호된 엔드포인트 URL
USER_LIST_URL = "http://127.0.0.1:8000/api/auth/user/"

access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzMzMjMyMTM0LCJpYXQiOjE3MzMyMjg1MzQsImp0aSI6ImY3OWE0MzNiZDYyNTRlNWJhZDA4YTlmN2Q4MmE4OWJiIiwidXNlcl9pZCI6MX0.3JU-TEkzFNxHfPG5FgZJPJ2IuIRlkeHb8jSnLrWNylc"

headers = {"Authorization": f"Bearer {access_token}"}
data = {
    "username": "AAA",
    "password": "AAA"
}
# 사용자 목록 요청
response = requests.post(USER_LIST_URL, headers=headers, json=data)

# 응답 확인
if response.status_code == 200:
    print("요청성공:")
    for user in response.json():
        print(user)
else:
    print("요청 실패:", response.status_code, response.json())