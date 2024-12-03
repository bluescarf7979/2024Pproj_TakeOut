from django.urls import path
from .views import RoadInfoList

urlpatterns = [
    path('', RoadInfoList.as_view(), name='road-info-list'),
]
