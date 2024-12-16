from django.db import models
from users.models import User

class RoadInfo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bad_type = models.IntegerField()
    road_category = models.CharField(max_length=255)
    speed = models.IntegerField()
    road_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    condition = models.IntegerField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    risk_level = models.FloatField()
    image = models.ImageField(upload_to='road_images/', blank=True, null=True)  # 이미지 필드 추가
    created_at = models.DateTimeField(auto_now_add=True)