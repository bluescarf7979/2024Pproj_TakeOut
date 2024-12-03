from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import RoadInfo
from .serializers import RoadInfoSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny


def is_valid(json, key):
    try:
        buf = json[key]
    except KeyError:
        return False

    return True

class RoadInfoList(APIView):
    permission_classes = [AllowAny]  # 누구나 접근 가능

    def get(self, request):
        if is_valid(request.data, "info_id"):
            try:
                road_infos = RoadInfo.objects.get(info_id=request.data["info_id"])
                serializer = RoadInfoSerializer(road_infos, many=True)
                return Response(serializer.data)
            except RoadInfo.DoesNotExist:
                    return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            road_infos = RoadInfo.objects.all()
            serializer = RoadInfoSerializer(road_infos, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)


    def post(self, request):
        serializer = RoadInfoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def delete(self, request):
        try:
            road_info = RoadInfo.objects.get(id=request.data["info_id"])
            road_info.delete()
            return Response({'message': 'Road Info deleted successfully'}, status=status.HTTP_200_OK)
        except RoadInfo.DoesNotExist:
            return Response({'error': 'Road Info not found'}, status=status.HTTP_404_NOT_FOUND)
