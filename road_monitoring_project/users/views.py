from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from .serializers import UserSerializer


def is_valid(json, key):
    try:
        buf = json[key]
    except KeyError:
        return False

    return True

class UserCreateView(APIView):
    """
    POST: 사용자 생성 (회원가입)
    """
    permission_classes = [AllowAny]  # 누구나 접근 가능

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # 비밀번호 해싱
            user.set_password(request.data['password'])
            user.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserListView(APIView):
    """
    GET: 전체 사용자 목록 조회
    POST: 새 사용자 추가
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        if is_valid(request.data, "user_id"):
            try:
                user = User.objects.get(id=request.data["user_id"])
                serializer = UserSerializer(user)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            users = User.objects.all()
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = UserSerializer(data=request.data["user_id"])
        if serializer.is_valid():
            user = serializer.save()
            # 비밀번호 해싱
            user.set_password(request.data['password'])
            user.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        try:
            user = User.objects.get(id=request.data["user_id"])
            user.delete()
            return Response({'message': 'User deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
