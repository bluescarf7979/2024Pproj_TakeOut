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
            126.95042955033101, 37.39952907832974,
            126.95100890747277, 37.39935861417968,
            126.95184575668353, 37.399171103167795,
            126.95238219849246, 37.39836991446609,
            126.95221053711612, 37.39727892033366,
            126.95343362442138, 37.39680160540712,
            126.95515023819372, 37.397790325810476,
            126.95680247894435, 37.397994887024126,
            126.95695268264977, 37.39847219435172,
            126.95695268264977, 37.39956317111266,
            126.95645915619167, 37.400790500985025,
            126.95703851334244, 37.40133597447641,
            126.95800410858769, 37.40179621464611,
            126.95937739959838, 37.40169393929715,
            126.96064340225449, 37.40106323822738,
            126.96074264399483, 37.4001811001235,
            126.96189062945639, 37.39907308586036,
            126.96211593503247, 37.398126999177244,
            126.96302788610492, 37.39865118381423,
            126.9626470124259, 37.398114214139916
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
