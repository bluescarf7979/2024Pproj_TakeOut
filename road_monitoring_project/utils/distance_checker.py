import math
from pyproj import Transformer

class DistanceChecker:
    def __init__(self, 
                 source_crs="EPSG:4326", 
                 target_crs="EPSG:5179"):
        # 좌표계 변환기 초기화
        self.transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
        self.polyline_wtm = []
        
    def latlon_to_wtm(self, lat, lon):
        """
        위경도 -> WTM 좌표 변환
        입력: lat(위도), lon(경도)
        출력: (x, y) in WTM
        """
        x, y = self.transformer.transform(lon, lat)
        return x, y

    def polyline_to_wtm(self, polyline_latlon):
        """
        [(lat1, lon1), (lat2, lon2), ...] 형태의 위경도 리스트를
        [(x1, y1), (x2, y2), ...] 형태의 WTM 좌표 리스트로 변환
        """
        return [self.latlon_to_wtm(lat, lon) for lat, lon in polyline_latlon]

    def point_to_segment_distance(self, px, py, x1, y1, x2, y2):
        """
        점 (px, py)와 선분 (x1, y1)-(x2, y2) 사이 최소 거리 계산 (WTM 좌표 기준)
        """
        seg_len_sq = (x2 - x1)**2 + (y2 - y1)**2
        if seg_len_sq == 0:
            # 선분 길이가 0인 경우 점-점 거리
            return math.sqrt((px - x1)**2 + (py - y1)**2)

        # 정사영 비율 t 계산
        t = ((px - x1)*(x2 - x1) + (py - y1)*(y2 - y1)) / seg_len_sq

        if t < 0:
            # closest point is x1,y1
            closest_x, closest_y = x1, y1
        elif t > 1:
            # closest point is x2,y2
            closest_x, closest_y = x2, y2
        else:
            closest_x = x1 + t*(x2 - x1)
            closest_y = y1 + t*(y2 - y1)

        dist = math.sqrt((px - closest_x)**2 + (py - closest_y)**2)
        return dist

    def point_to_polyline_distance(self, px, py, polyline_wtm):
        """
        점 (px, py)와 WTM 좌표계의 폴리라인( [(x1,y1),(x2,y2),...] ) 사이 최소 거리
        """
        if len(polyline_wtm) < 2:
            if len(polyline_wtm) == 1:
                x1, y1 = polyline_wtm[0]
                return math.sqrt((px - x1)**2 + (py - y1)**2)
            return float('inf')

        min_dist = float('inf')
        for i in range(len(polyline_wtm) - 1):
            x1, y1 = polyline_wtm[i]
            x2, y2 = polyline_wtm[i+1]
            dist = self.point_to_segment_distance(px, py, x1, y1, x2, y2)
            if dist < min_dist:
                min_dist = dist
        return min_dist
    
    def polyline_register(self, polyline_latlon):
        # 폴리라인 변환
        self.polyline_wtm = self.polyline_to_wtm(polyline_latlon)
    
    def is_within_threshold(self, point_lat, point_lon, threshold):
        """
        위경도 좌표로 주어진 점과 폴리라인, threshold(미터)를 받아
        폴리라인까지의 최소 거리를 계산하고 threshold 이하이면 True, 초과면 False 반환
        """
        # 점 변환
        px, py = self.latlon_to_wtm(point_lat, point_lon)

        dist = self.point_to_polyline_distance(px, py, self.polyline_wtm)
        print("Dist\t:", dist)
        return dist <= threshold


# 사용 예시
if __name__ == "__main__":
    # 임의의 위경도 폴리라인 (서울 주변 예시)
    polyline_latlon = [
        (37.5665, 126.9780),  # 서울시청 근처
        (37.5700, 126.9800),
        (37.5750, 126.9850)
    ]
    
    test_point_lat = 37.5710
    test_point_lon = 126.9820
    threshold_distance = 200.0  # 200m 이내면 True

    checker = DistanceChecker()
    checker.polyline_register(polyline_latlon)
    result = checker.is_within_threshold(test_point_lat, test_point_lon, threshold_distance)
    print("폴리라인과 점 사이 거리가 threshold 이하?", result)
