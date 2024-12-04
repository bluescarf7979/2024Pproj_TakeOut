from django.urls import path
from .views import RoadInfoList
from .views import RoadInfoFilter

urlpatterns = [
    path('', RoadInfoList.as_view(), name='road-info-list'),
    path('filter/', RoadInfoFilter.as_view(), name='road-info-filter'),
]
