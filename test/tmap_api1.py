import requests
import json

def match_to_road(app_key, coordinates):
    """
    Tmap '이동한 도로 찾기' API 요청을 보내는 함수.
    
    Parameters:
        version (str): API 버전 (예: "1")
        app_key (str): Tmap APP_KEY
        response_type (str): 요청 데이터 유형 (1: 전체 데이터 요청, 2: 요청좌표 제외)
        coordinates (str): 매핑에 사용될 좌표 목록 (예: "127.925710,37.557086|127.954464,37.556542")
    
    Returns:
        dict: API 응답 데이터
    """
    url = "https://apis.openapi.sk.com/tmap/road/matchToRoads"
    headers = {
        "appKey": app_key
    }
    data = {
        "version": "1",
        "responseType": "1",
        "coords": coordinates
    }

    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"API 요청 오류: {response.status_code}, {response.text}")
        return None

def reverse_geocode(app_key, coord):
    """
    Tmap Reverse Geocoding API를 호출하여 위도와 경도를 주소로 변환하는 함수.

    Parameters:
        app_key (str): Tmap API AppKey
        coord (json): Tmap API result

    Returns:
        dict: 변환된 주소 정보
    """
    lon = coord["longitude"]
    lat = coord["latitude"]
    print(lon, lat)
    url = "https://apis.openapi.sk.com/tmap/geo/reversegeocoding"
    headers = {
        "appKey": app_key
    }
    params = {
        "version": "1",
        "format": "json",
        "coordType": "WGS84GEO",
        "addressType": "A10",
        "lon": lon,
        "lat": lat
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"API 요청 오류: {response.status_code}, {response.text}")
        return None
    
# 예시 사용법
if __name__ == "__main__":
    app_key = "MQqnwXaxbE4bE8WxFe5Hkbnx6JNlVN28EegAtct1"  # 자신의 APP_KEY를 입력하세요
    coordinates = "126.95042955033101,37.39952907832974|126.95100890747277,37.39935861417968"
    
    result = match_to_road(app_key, coordinates)
    if not result:
        exit()
    print("API 응답 데이터:")
    # print(json.dumps(result, indent=4))
    res_len = len(result["resultData"]["matchedPoints"])
    print(res_len)
    coord = result["resultData"]["matchedPoints"][res_len//2]["matchedLocation"]
    result_geocode = reverse_geocode(app_key, coord)    
    res_organize = json.dumps(result, indent=4, ensure_ascii=False)
    # print(res_organize)
    print("\n\n")
    fullAddress = result_geocode["addressInfo"]["fullAddress"].split(",")[0]
    
    print(fullAddress)
    print(coord["roadCategory"], coord["speed"])
