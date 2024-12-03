from django.db import models
from users.models import User

class RoadInfo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    surface_type = models.IntegerField()
    road_traffic = models.IntegerField()
    road_name = models.CharField(max_length=255)
    condition = models.IntegerField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    risk_level = models.FloatField()
    image = models.ImageField(upload_to='road_images/', blank=True, null=True)  # 이미지 필드 추가
    bounding_box = models.JSONField()
    updated_at = models.DateField()