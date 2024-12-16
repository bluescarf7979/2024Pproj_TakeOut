from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import RoadInfo
from .serializers import RoadInfoSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from datetime import datetime
from django.http import JsonResponse
import json
from utils.distance_checker import DistanceChecker


state = 0
count = 0
def is_valid(json, key):
    try:
        buf = json[key]
    except KeyError:
        return False

    return True

class RoadInfoList(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        info_id = request.query_params.get('info_id')
        if info_id:
            try:
                road_infos = RoadInfo.objects.get(info_id=request.data["id"])
                serializer = RoadInfoSerializer(road_infos)
                return Response(serializer.data)
            except RoadInfo.DoesNotExist:
                    return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            road_infos = RoadInfo.objects.all()
            serializer = RoadInfoSerializer(road_infos, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        # `info_id`를 통해 업데이트할 RoadInfo 객체를 찾음
        print("AAAAAA\t",request.data)
        try:
            road_info = RoadInfo.objects.get(id=request.data["id"])
        except RoadInfo.DoesNotExist:
            return Response({'error': 'Road Info not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # 기존 객체를 새 데이터로 업데이트
        serializer = RoadInfoSerializer(road_info, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()  # 데이터 저장
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def post(self, request):
        serializer = RoadInfoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def delete(self, request):
        try:
            road_info = RoadInfo.objects.get(id=request.data["id"])
            road_info.delete()
            return Response({'message': 'Road Info deleted successfully'}, status=status.HTTP_200_OK)
        except RoadInfo.DoesNotExist:
            return Response({'error': 'Road Info not found'}, status=status.HTTP_404_NOT_FOUND)

class RoadInfoFilter(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')
        sort_order = request.query_params.get('sort_order', 'asc')
        region = request.query_params.get('region')
        surface_type = request.query_params.get('surface_type')

        road_infos = RoadInfo.objects.all()
        if start_time and end_time:
            try:
                # 문자열을 datetime 객체로 변환
                start_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S')
                end_time = datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S')

                # 시간 범위에 맞는 RoadInfo 객체 필터링
                road_infos = road_infos.filter(created_at__range=[start_time, end_time])

            except ValueError:
                return Response({'error': 'Invalid date format. Use YYYY-MM-DDTHH:MM:SS.'}, status=status.HTTP_400_BAD_REQUEST)

        if region:
            road_infos = road_infos.filter(address__icontains=region)
        if surface_type:
            road_infos = road_infos.filter(surface_type=surface_type)
        if sort_order == 'desc':
            road_infos = road_infos.order_by("-created_at")
        else:
            road_infos = road_infos.order_by("-created_at")        
        serializer = RoadInfoSerializer(road_infos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class RoadInfoNavigation(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        global state, count
        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        polyline_latlon = data.get('polyline')
        threshold = data.get('threshold', 50)

        print("threshold:\t",threshold)
        # 위경도 입력값이 float로 파싱 가능한지 검사
        try:
            threshold = float(threshold)
            # polyline_latlon: [[lat, lon], [lat, lon], ...] 형태 가정
            polyline_latlon = [(float(lat), float(lon)) for lat, lon in polyline_latlon]
        except ValueError:
            return JsonResponse({'error': 'Invalid parameter type'}, status=400)

        checker = DistanceChecker()
        checker.polyline_register(polyline_latlon)

        road_infos = RoadInfo.objects.all()
        
        filtered_road_infos = []

        for info in road_infos:
            lat = info.latitude
            lon = info.longitude
            in_polygon = checker.is_within_threshold(lat, lon, threshold)
            if in_polygon and state == 0:
                filtered_road_infos.append(info)
                state = 1
                count = 10
            elif in_polygon and state == 1:
                count -=1
                if count == 0:
                    state = 0
            print("count\t", count)
            print("state\t", state)
        serializer = RoadInfoSerializer(filtered_road_infos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)