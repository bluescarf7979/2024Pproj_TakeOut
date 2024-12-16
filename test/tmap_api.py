import requests
import time
from math import radians, cos, sin, sqrt, atan2

class RoadMatcher:
    def __init__(self, app_key, buffer_size=10, split_value=20, req_limit_per_sec=1):
        self.app_key = app_key
        self.buffer_size = buffer_size
        self.split_value = split_value
        self.req_limit_per_sec = req_limit_per_sec

        self.points = []
        self.total_distance = 0
        self.total_point_count = 0
        self.matched_ids = []

    def load_points(self):
        """초기 좌표 데이터를 로드합니다."""
        self.points = [
            127.126853, 37.470745,
            127.126855, 37.470746,
        ]

    def request_api(self, coords):
        """Tmap API 요청을 보냅니다."""
        url = "https://apis.openapi.sk.com/tmap/road/matchToRoads"
        headers = {
            "appKey": self.app_key
        }
        data = {
            "version": "1",
            "responseType": "1",
            "coords": coords
        }
        print(self.app_key)
        print(coords)
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API 요청 오류: {response.status_code}, {response.text}")
            return None

    def split_and_request(self):
        """포인트 데이터를 분할하고 API 요청을 처리합니다."""
        total_points = len(self.points)
        current_index = 0

        while current_index < total_points:
            coord_string = ""
            for i in range(current_index, min(current_index + self.split_value * 2, total_points), 2):
                if coord_string:
                    coord_string += "|"
                coord_string += f"{self.points[i]},{self.points[i+1]}"

            # API 요청
            response = self.request_api(coord_string)
            if response:
                self.process_response(response)

            # 딜레이 추가 (초당 요청 제한 준수)
            time.sleep(1 / self.req_limit_per_sec)

            # 다음 포인트로 이동
            current_index += self.split_value * 2

    def process_response(self, response):
        """API 응답 데이터를 처리합니다."""
        if "matchedPoints" in response.get("resultData", {}):
            matched_points = response["resultData"]["matchedPoints"]
            for point in matched_points:
                matched_id = f"{point['linkId']}_{point['idxName']}"
                if matched_id not in self.matched_ids:
                    self.matched_ids.append(matched_id)

                self.total_point_count += 1

                # 거리 계산 (이전 점과의 거리)
                if len(matched_points) > 1:
                    self.total_distance += self.calculate_distance(
                        matched_points[0]["sourceLocation"]["longitude"],
                        matched_points[0]["sourceLocation"]["latitude"],
                        matched_points[-1]["sourceLocation"]["longitude"],
                        matched_points[-1]["sourceLocation"]["latitude"]
                    )

    @staticmethod
    def calculate_distance(lon1, lat1, lon2, lat2):
        """위도와 경도로 두 점 사이의 거리를 계산합니다."""
        r = 6371e3  # 지구 반지름 (미터)
        φ1, φ2 = radians(lat1), radians(lat2)
        Δφ = radians(lat2 - lat1)
        Δλ = radians(lon2 - lon1)

        a = sin(Δφ / 2) ** 2 + cos(φ1) * cos(φ2) * sin(Δλ / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return r * c

    def run(self):
        """프로세스를 실행합니다."""
        self.load_points()
        self.split_and_request()
        print(f"총 거리: {self.total_distance:.2f}m")
        print(f"매칭된 좌표의 개수: {self.total_point_count}")
        print(f"매칭된 링크 ID 개수: {len(self.matched_ids)}")


# 실행
if __name__ == "__main__":
    app_key = "MQqnwXaxbE4bE8WxFe5Hkbnx6JNlVN28EegAtct1"
    matcher = RoadMatcher(app_key)
    matcher.run()
