import rospy
from sensor_msgs.msg import NavSatFix
import requests
from collections import deque
import copy
from risk_model import ObjectAreaEstimator, RoadRiskCalculator
import numpy as np
import json
from road_detection_msgs.msg import DetectionResult 
import requests
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
import cv2

class RoadMatcher:
    def __init__(self, app_key):
        """
        Tmap API를 사용하여 NavSatFix 메시지로부터 도로 매칭을 수행하는 클래스.
        
        Parameters:
            app_key (str): Tmap API 호출에 필요한 AppKey
        """
        self.app_key = app_key
        self.queue = deque(maxlen=50)  # 좌표를 저장할 큐
        self.api_url = "https://apis.openapi.sk.com/tmap/road/matchToRoads"
        
        pitch = 30.0  # degrees
        camera_height = 1.5  # meters
        intrinsic_matrix = np.array([[800,   0, 320],
                                    [  0, 800, 240],
                                    [  0,   0,   1]], dtype=np.float32)
        distortion_coeffs = np.zeros(5, dtype=np.float32)
        image_width = 320*2
        image_height = 240*2
        self.estimator = ObjectAreaEstimator(pitch, camera_height, intrinsic_matrix, distortion_coeffs, image_width, image_height)
        self.calculator = RoadRiskCalculator()
        self.bridge = CvBridge()
        self.POST_URL = "http://127.0.0.1:8000/api/road_info/"
        self.LOGIN_URL = "http://127.0.0.1:8000/api/token/"
        self.user_data = {
            "username": "a",
            "password": "a"
        }
        # ROS Subscriber 설정
        rospy.init_node("risk_analyst_node")
        rospy.Subscriber("/gps/fix", NavSatFix, self.gps_callback)
        rospy.Subscriber("/yolov11/result", DetectionResult, self.detection_callback)
        rospy.Subscriber("/yolov5/result", DetectionResult, self.detection_callback)


    def detection_callback(self, msg):
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')


        if msg.is_boundingbox:
            area_list = []
            depth_list = []
            for i, box in enumerate(msg.bounding_boxes):
                real_area, object_depth = self.estimator.calc_area_from_bbox(box)
                area_list.append(real_area)
                depth_list.append(object_depth)
        else:
            area_list = []
            depth_list = []
            for i, seg in enumerate(msg.segmentations):
                polygon_x = seg.polygon_x
                polygon_y = seg.polygon_y

                real_area, object_depth = self.estimator.calc_area_from_yolo_seg(polygon_x, polygon_y)
                area_list.append(real_area)
                depth_list.append(object_depth)

        total_area = sum(area_list)
        depth_mean = sum(depth_list)/len(depth_list)
        api_result = self.tmap_api_process()
        risk = self.calculator.calculate_total_risk(defect_type=1, 
                    defect_area=total_area, recognition_dist=depth_mean, 
                    speed=api_result["speed"], road_type=api_result["road_category"])
        api_result["risk_level"] = risk

        self.post_result(cv_image, api_result)

    def post_result(self, cv_image, result):
        
        # login
        response = requests.post(self.LOGIN_URL, json=self.user_data)
        # 응답 확인
        if response.status_code == 200:
            tokens = response.json()  # access와 refresh 토큰 반환
            access_token = tokens["access"]
        else:
            return
        
        ret, buffer = cv2.imencode('.jpg', cv_image)
        if not ret:
            rospy.logerr("Failed to encode image")
            return
        jpeg_bytes = buffer.tobytes()

        headers = {"Authorization": f"Bearer {access_token}"}

        files = {
            'image': (f'{rospy.Time.now().to_sec()}.jpg', jpeg_bytes, 'image/jpeg')
        }
        try:
            response = requests.post(self.POST_URL, headers=headers, data=result, files=files)
            if response.status_code == 200:
                rospy.loginfo("Image successfully sent to the server")
            else:
                rospy.logwarn("Failed to send image. Status code: %d", response.status_code)
        except Exception as e:
            rospy.logerr("Exception occurred while sending image: %s", str(e))

    def gps_callback(self, msg):
        """
        ROS NavSatFix 메시지 콜백 함수.
        
        Parameters:
            msg (NavSatFix): NavSatFix 메시지
        """
        lat, lon = msg.latitude, msg.longitude
        self.queue.append((lon, lat))
        rospy.loginfo(f"좌표 추가: {lon}, {lat}")

    def match_to_road(self, coordinates):
        """
        Tmap '이동한 도로 찾기' API 요청을 보내는 함수.
        
        Parameters:
            coordinates (str): 매핑에 사용될 좌표 목록 (예: "127.925710,37.557086|127.954464,37.556542")
        
        Returns:
            dict: API 응답 데이터
        """
        headers = {"appKey": self.app_key}
        data = {
            "version": "1",
            "responseType": "1",
            "coords": coordinates
        }

        try:
            response = requests.post(self.api_url, headers=headers, data=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            rospy.logerr(f"API 요청 실패: {e}")
            return None

    def reverse_geocode(self, coord):
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
            "appKey": self.app_key
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
        
    def tmap_api_process(self):
        """
        큐에 저장된 좌표를 API 호출 형식으로 변환하고 Tmap API 호출.
        """
        if len(self.queue) == 0:
            rospy.loginfo("큐가 비어 있습니다. 처리할 좌표가 없습니다.")
            return
        
        coord_queue = copy.deepcopy(self.queue)
        coordinates = ""
        while len(coord_queue) != 0:
            lon, lat = coord_queue.popleft()
            if coordinates:
                coordinates += "|"
            coordinates += f"{lon},{lat}"

        # API 호출
        rospy.loginfo(f"API 호출 좌표수: {len(self.queue)}")
        result = self.match_to_road(coordinates)

        if not result:
            rospy.logerr("match_to_road API 응답 처리 중 오류가 발생했습니다.")
            return None

        res_len = len(result["resultData"]["matchedPoints"])
        matchedPoint = result["resultData"]["matchedPoints"][res_len//2]
        coord = matchedPoint["matchedLocation"]
        result_geocode = self.reverse_geocode(coord)

        if not result_geocode:
            rospy.logerr("reverse_geocode API 응답 처리 중 오류가 발생했습니다.")
            return None

        fullAddress = result_geocode["addressInfo"]["fullAddress"].split(",")[0]
        result = {
            "address": fullAddress, 
            "condition": "보수 필요",
            "longitude": coord["longitude"],
            "latitude": coord["latitude"],
            "road_category": matchedPoint["roadCategory"],
            "road_name": result_geocode["addressInfo"]["roadName"],
            "speed": matchedPoint["speed"]
        }
        return result

    def test(self):
        """
        ROS 노드를 실행하며 API 호출 처리 루프를 실행.
        """
        rospy.loginfo("도로 매칭 노드가 실행 중입니다...")
        rate = rospy.Rate(1/2)  # n초당 1회 실행

        self.queue.append((126.95042955033101,37.39952907832974))
        self.queue.append((126.95100890747277,37.39935861417968))
        self.queue.append((126.95184575668353, 37.399171103167795))
        try:
            while not rospy.is_shutdown():
                result = self.tmap_api_process()
                if not result:
                    print("API가 정상동작 되지 않음")
                else:
                    print(result)
                rate.sleep()
        except rospy.ROSInterruptException:
            rospy.loginfo("도로 매칭 노드가 종료되었습니다.")

    def run(self):
        rospy.spin()

# 실행 코드
if __name__ == "__main__":
    app_key = "MQqnwXaxbE4bE8WxFe5Hkbnx6JNlVN28EegAtct1"
    matcher = RoadMatcher(app_key)
    matcher.test()