import cv2
import numpy as np
from enum import Enum

class RoadType(Enum):
    HIGHWAY = 0  # 고속국도
    URBAN_EXPRESSWAY = 1  # 도시고속화도로
    NATIONAL_HIGHWAY = 2  # 국도
    NATIONAL_SUPPORTED_LOCAL_ROAD = 3  # 국가지원지방도
    LOCAL_ROAD = 4  # 지방도
    MAIN_ROAD_1 = 5  # 주요도로 1
    MAIN_ROAD_2 = 6  # 주요도로 2
    MAIN_ROAD_3 = 7  # 주요도로 3
    OTHER_ROAD_1 = 8  # 기타도로 1
    SIDE_ROAD = 9  # 이면도로
    FERRY_ROUTE = 10  # 페리항로
    COMPLEX_ROAD = 11  # 단지내도로
    SIDE_ROAD_2 = 12  # 이면도로 2(세도로)

# 숫자 입력 -> 도로 이름 반환 함수
def get_road_name(road_code):
    try:
        road_name = RoadType(road_code).name
        return road_name.replace("_", " ").title()  # 이름을 읽기 쉽게 변환
    except ValueError:
        return "Unknown Road Type"

# 도로 분류 -> 중요도 매핑 함수
def get_importance(road_code):
    importance_map = {
        0: 6,  # 고속국도: 중요도 10
        1: 5,   # 도시고속화도로: 중요도 9
        2: 4,   # 국도: 중요도 8
        3: 3,   # 국가지원지방도: 중요도 7
        4: 3,   # 지방도: 중요도 6
        5: 5,   # 주요도로 1: 중요도 5
        6: 4,   # 주요도로 2: 중요도 4
        7: 4,   # 주요도로 3: 중요도 3
        8: 1,   # 기타도로 1: 중요도 2
        9: 2,   # 이면도로: 중요도 1
        10: 0,  # 페리항로: 중요도 0
        11: 0,  # 단지내도로: 중요도 0
        12: 2   # 이면도로 2: 중요도 1
    }
    return importance_map.get(road_code, 0)  # -1은 알 수 없는 도로 유형

class ObjectAreaEstimator:
    def __init__(self, pitch, camera_height, intrinsic_matrix, distortion_coeffs, image_width, image_height):
        self.pitch = pitch
        self.camera_height = camera_height
        self.intrinsic_matrix = intrinsic_matrix
        self.distortion_coeffs = distortion_coeffs
        
        self.fx = intrinsic_matrix[0, 0]
        self.fy = intrinsic_matrix[1, 1]
        self.cx = intrinsic_matrix[0, 2]
        self.cy = intrinsic_matrix[1, 2]
        
        self.image_width = image_width
        self.image_height = image_height

    def _undistort_point(self, point):
        point = np.array(point, dtype=np.float32).reshape(1,1,2)
        undistorted = cv2.undistortPoints(
            point, self.intrinsic_matrix, self.distortion_coeffs, None, self.intrinsic_matrix
        )
        return undistorted.reshape(-1)

    def _estimate_depth_from_pixel(self, u, v):
        """
        객체 중심점의 픽셀 좌표 (u,v)를 이용해 깊이를 추정하는 메서드.
        """
        # pitch 라디안으로 변환
        pitch_rad = np.radians(self.pitch)

        # 정규화된 수직 좌표
        normalized_y = (v - self.cy) / self.fy

        # 수직 방향 추가 각도 alpha
        alpha = np.arctan(normalized_y)

        # 깊이 추정
        # D = h / tan(pitch + alpha)
        depth = self.camera_height / np.tan(pitch_rad + alpha)
        return depth

    def calc_area_from_bbox(self, bounding_box):
        xmin=bounding_box.xmin
        ymin=bounding_box.ymin
        xmax=bounding_box.xmax
        ymax=bounding_box.ymax
        bbox_width = xmax - xmin
        bbox_height = ymax - ymin
        bbox_center = ((xmin + xmax) / 2, (ymin + ymax) / 2)

        # 왜곡 보정
        bbox_center_undistorted = self._undistort_point(bbox_center)
        u, v = bbox_center_undistorted[0], bbox_center_undistorted[1]

        # 객체 중심점을 통한 깊이 추정
        object_depth = self._estimate_depth_from_pixel(u, v)

        # 실제 폭, 높이 계산
        real_width = (bbox_width / self.fx) * object_depth
        real_height = (bbox_height / self.fy) * object_depth
        real_area = real_width * real_height
        return real_area, object_depth

    def calc_area_from_segmentation(self, segmentation_mask):
        obj_pixels = np.count_nonzero(segmentation_mask)
        if obj_pixels == 0:
            return 0.0
        
        coords = np.argwhere(segmentation_mask > 0)
        centroid_y, centroid_x = coords.mean(axis=0)
        centroid_undistorted = self._undistort_point((centroid_x, centroid_y))
        u, v = centroid_undistorted[0], centroid_undistorted[1]

        # 깊이 추정
        object_depth = self._estimate_depth_from_pixel(u, v)

        # 픽셀 당 실제 면적 (단순 가정)
        pixel_area = (object_depth**2) / (self.fx * self.fy)
        real_area = obj_pixels * pixel_area
        return real_area, object_depth

    def calc_area_from_yolo_seg(self, poly_x, poly_y):
        """
        YOLO 형식의 세그멘테이션 라벨(폴리곤 좌표)을 이용해 실제 넓이를 계산
        yolo_poly: [x1,y1,x2,y2,...] 형태로, 각 좌표는 이미지 크기에 정규화된 (0~1)
        
        Parameters:
        - yolo_poly (list or np.ndarray): YOLO 세그멘테이션 폴리곤 좌표 (정규화)
        - image_width (int): 원본 이미지 폭
        - image_height (int): 원본 이미지 높이
        
        Returns:
        - real_area: 객체 실제 넓이 (m^2)
        """
        # 정규화 좌표를 픽셀 좌표로 변환
        xs = poly_x * self.image_width
        ys = poly_y * self.image_height
        polygon = np.stack([xs, ys], axis=-1).astype(np.int32)
        
        # 빈 마스크 생성 후 폴리곤 영역 채우기
        segmentation_mask = np.zeros((self.image_height, self.image_width), dtype=np.uint8)
        cv2.fillPoly(segmentation_mask, [polygon], 1)
        
        # 기존 세그멘테이션 메서드 활용
        real_area = self.calc_area_from_segmentation(segmentation_mask)
        return real_area

class RoadRiskCalculator:
    def calculate_R1(self, defect_area, total_area = 300):
        """
        불량 면적에 따른 위험도 계산 (R1)
        :param total_area: 전체 면적
        :param defect_area: 불량 면적
        :return: R1 값
        """
        defect_ratio = (defect_area/total_area)*100
        SPI1 = 10-2.23*defect_ratio**0.3
        return SPI1

    def calculate_R2(self, recognition_dist, speed):
        """
        인지 거리에 따른 위험도 계산 (R2)
        :return: R2 값
        """
        braking_dist = speed**2/(254*2) + speed*0.1
        SPI2 = 10-2.23*(braking_dist*20/recognition_dist)**0.3
        return SPI2

    def calculate_R3(self, road_type):
        """
        도로 종류와 교통량에 따른 위험도 계산 (R3)
        :param road_type: 도로 종류
        :param traffic_volume: 교통량
        :return: R3 값
        """
        SPI3 = 10 - get_importance(road_type)
        return SPI3
    
    def calculate_total_risk(self, defect_type, defect_area, recognition_dist, speed, road_type):
        """
        전체 위험도 계산 (R_total)
        :param defect_type: 불량 유형
        :param defect_area: 불량 면적
        :param road_type: 도로 종류
        :param recognition_dist: 인식거리
        :param speed: 제한속도
        :return: 전체 위험도 (R_total)
        """
        R1 = self.calculate_R1(defect_type, defect_area)
        R2 = self.calculate_R2(recognition_dist, speed)
        R3 = self.calculate_R3(road_type)

        # 가중치를 고려하여 최종 위험도 계산
        R_total = ((10-R1)**5+(10-R2)**5+(10-R3)**5)**0.2
        result = max(min(10,R_total),0)
        return 10-result




# 사용 예시
if __name__ == "__main__":
    # 가상의 intrinsic, distortion, pitch, height
    pitch = 30.0  # degrees
    camera_height = 1.5  # meters
    intrinsic_matrix = np.array([[800,   0, 320],
                                 [  0, 800, 240],
                                 [  0,   0,   1]], dtype=np.float32)
    distortion_coeffs = np.zeros(5, dtype=np.float32)
    image_width = 320*2
    image_height = 240*2
    estimator = ObjectAreaEstimator(pitch, camera_height, intrinsic_matrix, distortion_coeffs, image_width, image_height)
    bbox = (100, 100, 200, 200)
    area_from_bbox = estimator.calculate_area_from_bbox(bbox)
    print("Real area from YOLO segmentation:", area_from_bbox, "m^2")
    # YOLO seg 예제: 이미지 크기 640x480, 폴리곤 좌표(정규화)
    # 사각형 형태 (0.15625,0.41666 ... ~ 0.3125,0.625) 약 100x100픽셀 영역
    yolo_polygon = [0.15625, 0.41666, 
                    0.3125, 0.41666, 
                    0.3125, 0.625, 
                    0.15625, 0.625]
    real_area_from_yolo = estimator.calculate_area_from_yolo_seg(yolo_polygon)
    print("Real area from YOLO segmentation:", real_area_from_yolo, "m^2")

    calculator = RoadRiskCalculator()

    # 위험도 계산 예시
    total_risk = calculator.calculate_total_risk(defect_type=1, defect_area=10, recognition_dist=50, speed=80, road_type=3)
    print(f"Total Risk: {total_risk}")