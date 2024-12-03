from django.urls import path
from .views import UserListView, UserCreateView

urlpatterns = [
    path('', UserListView.as_view(), name='user-list'),
    path('register/', UserCreateView.as_view(), name='user-register'),  # 회원가입
]
