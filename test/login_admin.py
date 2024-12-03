import requests

# 로그인 엔드포인트 URL
LOGIN_URL = "http://127.0.0.1:8000/api/token/"

# 관리자 로그인 정보
admin_credentials = {
    "username": "a",  # 관리자 계정 사용자명
    "password": "a"  # 관리자 계정 비밀번호
}

# 로그인 요청
response = requests.post(LOGIN_URL, json=admin_credentials)

# 응답 확인
if response.status_code == 200:
    tokens = response.json()  # access와 refresh 토큰 반환
    access_token = tokens["access"]
    refresh_token = tokens["refresh"]
    print("관리자 로그인 성공!")
    print("Access Token:", access_token)
    print("Refresh Token:", refresh_token)
else:
    print("관리자 로그인 실패:", response.status_code, response.json())

USER_LIST_URL = "http://127.0.0.1:8000/api/auth/user/"

# access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTczMzEyMDQ2MywiaWF0IjoxNzMzMDM0MDYzLCJqdGkiOiI3ZjYwMzdlMWZjZjU0MDU5OTM4YjhiNzI1NjlhZTA0NyIsInVzZXJfaWQiOjF9.TfkoTuQa3rUf-Kl7nnnAj6UoEJsYCldam6zpmBwwbwU"
# 헤더에 Access Token 추가
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