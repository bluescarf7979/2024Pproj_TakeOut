import requests

access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzMzMjMyODEwLCJpYXQiOjE3MzMyMjkyMTAsImp0aSI6IjM2MzdhYThiODI3NjQyY2RhNzYyOWUwNzhkMzI2MDQwIiwidXNlcl9pZCI6Nn0.eB0JYNIKeWBVJz2Ab2fTKRaOaXhe3fktXyRq2jp1QNE"
# headers = {"Authorization": f"Bearer {access_token}"}
url = 'http://localhost:8000/api/road_info/filter/'
params = {
    'start_time': '2024-12-01T00:00:00',
    'end_time': '2024-12-31T23:59:59'
}

response = requests.get(url)

if response.status_code == 200:
    print(response.json())  # 응답된 데이터 출력
else:
    print(f"Error: {response.status_code}")
    print(response.json())
